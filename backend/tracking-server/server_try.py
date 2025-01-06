import os
import sys
import re
import random
import requests
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from fastapi_utils.tasks import repeat_every
from sqlalchemy import and_ 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
from openai import AsyncClient
from cachetools import TTLCache
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text

load_dotenv()

# Heroku
# DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://") + "?sslmode=require"

# if "sslmode=require" not in DATABASE_URL:
#     DATABASE_URL += "?sslmode=require"

# database = Database(DATABASE_URL, min_size=1, max_size=5)

# 로컬테스트 sqlite 사용
DATABASE_URL = "sqlite:///./test.db"
database = Database(DATABASE_URL)

metadata = MetaData()

# 3) 테이블 정의 (bills, votes 예시)
bills_table = Table(
    "bills",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bill_id", String(100), index=True),
    Column("bill_name", String(300)),
    Column("propose_date", String(100)),
    Column("committee", String(200)),
    Column("proposer", String(200)),
    Column("bill_link", String(300)),
    Column("details", Text),
    Column("summary", Text),
    Column("proc_dt", String(100)),
)

votes_table = Table(
    "votes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bill_id", String(100), index=True),
    Column("vote_result", String(50)),  # 예: 가결/부결/찬성/반대 등
    Column("m_name", String(100)),      # 의원 이름
    Column("details", Text),            # 크롤링 결과(DETAILS)
)

cache = TTLCache(maxsize=10000, ttl=14400)


vote_data_loaded = False
bills_data_loaded = False
last_refresh_date = None
REFRESH_HOUR = 4 


API_KEY = os.getenv("API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bills_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
}

app = FastAPI()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://backend-three-theta-46.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vote_data_loaded = False
bills_data_loaded = False

last_refresh_date = None
REFRESH_HOUR = 4  # 새벽 4시

client = AsyncClient(api_key=OPENAI_API_KEY)


class QueryRequest(BaseModel):
    query: str

def is_refresh_time(now: datetime) -> bool:
    return now.hour == REFRESH_HOUR


async def preload_vote_data():
    print("[preload_vote_data] vote 데이터 로드 중...")
    try:
        votes = await force_fetch_vote_data("곽상언")
        cache["votes"] = votes
        print("[preload_vote_data] vote 데이터 로드 완료.")
    except Exception as e:
        print(f"[preload_vote_data] vote 데이터 로드 오류 발생: {e}")

async def preload_bills_data():
    global bills_data_loaded  # ✅ 글로벌 변수 사용
    print("[preload_bills_data] bill 데이터 로드 중...")
    try:
        bills = await force_fetch_bills_combined("곽상언")
        cache["bills"] = bills
        bills_data_loaded = True  # ✅ 데이터 로드 완료 후 설정
        print("[preload_bills_data] bill 데이터 로드 완료.")
    except Exception as e:
        print(f"[preload_bills_data] bill 데이터 로드 오류 발생: {e}")
        bills_data_loaded = False  # 오류 발생 시 False 설정

async def preload_data():
    global vote_data_loaded, bills_data_loaded

    print("[preload_data] 데이터 로드 시작...")
    await asyncio.gather(preload_vote_data(), preload_bills_data())
    await asyncio.gather(preload_bills_data())
    vote_data_loaded = True
    bills_data_loaded = True
    print("[preload_data] 데이터 로드 완료.")


async def summarize_bill_details(content, max_retries=5):
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  
                messages=[
                    {"role": "system", "content": "법안 내용을 300자 이내로 요약. 핵심만 3-4줄로."},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[summarize_bill_details] Error in summarization (attempt={attempt}): {e}")
            # 429 등 rate limit 초과 시 지연
            if "rate_limit_exceeded" in str(e):
                wait_time = 2 ** attempt
                print(f"[summarize_bill_details] Rate limit exceeded. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                break

    print("[summarize_bill_details] Failed to summarize after multiple attempts.")
    return "요약 생성 중 오류가 발생했습니다."


async def crawl_bill_details(bill_id):
    cache_key = f"bill_details_{bill_id}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        url = f"https://likms.assembly.go.kr/bill/summaryPopup.do?billId={bill_id}"
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find("div", class_="textType02 mt30")

        if content_div:
            raw_html = content_div.decode_contents()
            text_with_newlines = raw_html.replace("<br/>", "\n").strip()
            details = BeautifulSoup(text_with_newlines, 'html.parser').get_text()

            if len(details.strip()) > 10:
                try:
                    summary = await summarize_bill_details(details)
                except Exception as e:
                    print(f"[crawl_bill_details] 요약 생성 중 오류: {e}")
                    summary = "요약 생성 중 오류가 발생했습니다."
            else:
                summary = "내용이 충분하지 않아 요약을 생성할 수 없습니다."

            result = {"details": details.strip(), "summary": summary}
            cache[cache_key] = result
            return result
        else:
            return {"details": "내용을 찾을 수 없습니다.", "summary": "요약 불가"}
    except Exception as e:
        print(f"[crawl_bill_details] Error while crawling BILL_ID {bill_id}: {e}")
        return {"details": f"크롤링 중 오류 발생: {str(e)}", "summary": "요약 불가"}
    

async def save_votes_to_db(votes):
    """
    votes는 [{"BILL_ID": "...", "RESULT": "...", "HG_NM": "...", "DETAILS": {...}}, ...] 형태라고 가정
    """
    for v in votes:
        bill_id = v.get("BILL_ID")
        vote_result = v.get("RESULT") or "unknown"
        member_name = v.get("HG_NM") or "unknown"

        # DETAILS라는 dict 안에 details, summary 등이 있다고 가정
        details_str = ""
        if "DETAILS" in v and isinstance(v["DETAILS"], dict):
            # 문자열로 바꿔서 저장
            details_str = (
                f"Details: {v['DETAILS'].get('details', '')}\n"
                f"Summary: {v['DETAILS'].get('summary', '')}"
            )

        # 1) 기존 레코드가 있는지 확인
        existing_vote = await database.fetch_one(
            votes_table.select().where(
                (votes_table.c.bill_id == bill_id) &
                (votes_table.c.m_name == member_name)
            )
        )

        if existing_vote:
            # 2) 있다면 Update
            update_query = (
                votes_table
                .update()
                .where(
                    (votes_table.c.bill_id == bill_id) &
                    (votes_table.c.m_name == member_name)
                )
                .values(
                    vote_result=vote_result,
                    details=details_str
                )
            )
            await database.execute(update_query)
            print(f"[save_votes_to_db] Updated existing vote (bill_id={bill_id}, m_name={member_name})")
        else:
            # 3) 없다면 Insert
            insert_query = votes_table.insert().values(
                bill_id=bill_id,
                vote_result=vote_result,
                m_name=member_name,
                details=details_str
            )
            await database.execute(insert_query)
            print(f"[save_votes_to_db] Inserted new vote (bill_id={bill_id}, m_name={member_name})")

    print(f"[save_votes_to_db] Finished processing {len(votes)} votes.")

async def save_bills_to_db(bills):
    for b in bills:
        bill_id = b.get("bill_id")
        if not bill_id:
            continue

        # 1) bill_id가 이미 있는지 검사
        existing_bill = await database.fetch_one(
            bills_table.select().where(bills_table.c.bill_id == bill_id)
        )

        if existing_bill:
            # 2) 업데이트
            update_query = (
                bills_table
                .update()
                .where(bills_table.c.bill_id == bill_id)
                .values(
                    bill_name=b.get("bill_name"),
                    propose_date=b.get("propose_date"),
                    committee=b.get("committee"),
                    proposer=b.get("proposer"),
                    bill_link=b.get("bill_link"),
                    details=b.get("DETAILS"),
                    summary=b.get("SUMMARY"),
                    proc_dt=b.get("proc_dt"),
                )
            )
            await database.execute(update_query)
            print(f"[save_bills_to_db] Updated existing bill_id={bill_id}")
        else:
            # 3) 없다면 Insert
            insert_query = bills_table.insert().values(
                bill_id=b.get("bill_id"),
                bill_name=b.get("bill_name"),
                propose_date=b.get("propose_date"),
                committee=b.get("committee"),
                proposer=b.get("proposer"),
                bill_link=b.get("bill_link"),
                proc_dt=b.get("proc_dt"),
                details=b.get("DETAILS"),
                summary=b.get("SUMMARY"),
            )
            await database.execute(insert_query)
            print(f"[save_bills_to_db] Inserted new bill_id={bill_id}")

    print(f"[save_bills_to_db] Finished processing {len(bills)} bills.")


async def fetch_collab_bills_with_selenium():
    session = requests.Session()
    
    def get_csrf_token():
        url = "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do?monaCd=FIE6569O&st=22&viewType=CONTBODY&tabId=collabill"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }
        
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            print("✅ 받은 쿠키:", session.cookies.get_dict())
            soup = BeautifulSoup(response.text, "html.parser")
            csrf_token = soup.find("meta", {"name": "_csrf"})["content"]
            print(f"✅ CSRF 토큰: {csrf_token}")
            return csrf_token
        else:
            raise Exception(f"❌ GET 요청 실패! 상태 코드: {response.status_code}")

    def fetch_data():
        url = "https://www.assembly.go.kr/portal/assm/assmPrpl/findCollaPrpsBill.json"
        csrf_token = get_csrf_token()
        
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.assembly.go.kr",
            "Referer": "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-CSRF-TOKEN": csrf_token,
            "X-Requested-With": "XMLHttpRequest"
        }
        
        data = {
            "pageIndex": "1",
            "rowSize": "10",
            "represent": "법률안",
            "monaCd": "FIE6569O",
            "age": "",
            "billName": "",
            "procResultCd": "",
            "searchStartDt": "",
            "searchEndDt": ""
        }
        
        all_data = []
        first_response = session.post(url, headers=headers, data=data)
        
        if first_response.status_code == 200:
            first_result = first_response.json()
            total_pages = first_result["paginationInfo"]["totalPageCount"]
            print(f"총 {total_pages} 페이지를 가져옵니다...")
            
            all_data.extend(first_result["resultList"])
            
            for page in range(2, total_pages + 1):
                print(f"{page} 페이지 가져오는 중...")
                data["pageIndex"] = str(page)
                response = session.post(url, headers=headers, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    all_data.extend(result["resultList"])
                else:
                    print(f"❌ {page} 페이지 요청 실패! 상태 코드: {response.status_code}")
        else:
            print(f"❌ 첫 번째 요청 실패! 상태 코드: {first_response.status_code}")
        

        print(f"{all_data}")
        print(f"✅ 총 {len(all_data)} 건의 데이터를 가져왔습니다.")
        return all_data 
    
    try: 
        collab_bills = fetch_data()  
        return collab_bills

    except Exception as e:
        print(f"[fetch_collab_bills_with_selenium] Error {e}")
        return []


async def force_fetch_bills_combined(member_name: str):
    print(f"[force_fetch_bills_combined] Start fetching bills data for member: {member_name}")

    
    bills = []
    collab_bills = []

    try:
        # 1) 대표발의
        print("[force_fetch_bills_combined] Fetching representative bills...")
        rep_response = requests.get(bills_url, headers=headers, params={
            "Key": API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 100,
            "PROPOSER": member_name,
            "AGE": "22"
        })
        rep_response.raise_for_status()

        rep_data = rep_response.json()
        rep_rows = rep_data.get("nzmimeepazxkubdpn", [{}])[1].get("row", [])
        print(f"[force_fetch_bills_combined] Found {len(rep_rows)} 대표발의법안")

        for row in rep_rows:
            bill_id = row.get("BILL_ID")
            if bill_id:
                details = await crawl_bill_details(bill_id)
                bills.append({
                    "type": "대표발의",
                    "bill_id": bill_id,
                    "bill_name": row.get("BILL_NAME"),
                    "propose_date": row.get("PROPOSE_DT"),
                    "committee": row.get("COMMITTEE"),
                    "proposer": row.get("PROPOSER"),
                    "bill_link": row.get("DETAIL_LINK"),
                    "DETAILS": details["details"],
                    "SUMMARY": details["summary"]
                })

        # 2) 공동발의
        print("[force_fetch_bills_combined] Fetching 공동발의...")
        raw_collab_bills = await fetch_collab_bills_with_selenium()
        print(f"[force_fetch_bills_combined] Received {len(raw_collab_bills)} 공동발의 from Selenium.")

        for bill in raw_collab_bills:
            print(f"[force_fetch_bills_combined] Processing 공동 발의: {bill.get('billId')}")
            bill_id = bill.get("billId")
            if bill_id:
                details = await crawl_bill_details(bill_id)
                collab_bills.append({
                    "type": "공동발의",
                    "bill_id": bill_id,
                    "bill_name": bill.get("billName"),
                    "propose_date": bill.get("proposeDt"),
                    "committee": bill.get("currCommittee"),
                    "proposer": bill.get("proposer"),
                    "bill_link": bill.get("billLinkUrl"),
                    "DETAILS": details["details"],
                    "SUMMARY": details["summary"]
                })
                print(f"[force_fetch_bills_combined] Added 공동 발의: {bill_id}")

    except Exception as e:
        print(f"[force_fetch_bills_combined] Error {e}")


    print(f"공동발의 반환값 출력 \n{collab_bills}")
    final_bills = bills + collab_bills
    print(f"[force_fetch_bills_combined] Final bills data (combined) count: {len(final_bills)}")

    # 공동발의 법안이 포함되었는지 확인
    if len(collab_bills) > 0:
        print(f"✅ 공동발의 법안 {len(collab_bills)}건 포함 완료!")
    else:
        print("❌ 공동발의 법안이 포함되지 않았습니다.")

    # 4) DB 저장
    await save_bills_to_db(final_bills)

    # 5) 캐시에 넣어서 빠른 재응답
    cache["bills"] = final_bills
    return final_bills


async def force_fetch_vote_data(member_name: str):
    print(f"[force_fetch_vote_data] Start fetching vote data for member: {member_name}")
    vote_url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    bill_list_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"

    pIndex = 1
    bill_ids = []
    has_more_data = True

    # 1) 전체 BILL_ID 수집
    while has_more_data:
        print(f"[force_fetch_vote_data] Fetching page {pIndex} for bill IDs...")
        bill_response = requests.get(bill_list_url, params={
            "Key": os.getenv("API_KEY"),
            "Type": "json",
            "AGE": 22,
            "pSize": 10,
            "pIndex": pIndex
        }).json()

        if ("nwbpacrgavhjryiph" in bill_response
            and len(bill_response["nwbpacrgavhjryiph"]) > 1
            and "row" in bill_response["nwbpacrgavhjryiph"][1]):
            rows = bill_response["nwbpacrgavhjryiph"][1]["row"]
            for row in rows:
                if "BILL_ID" in row:
                    bill_ids.append(row["BILL_ID"])
            pIndex += 1
        else:
            has_more_data = False

    # 2) 각 BILL_ID마다 투표 정보 가져오기
    vote_data = []
    tasks = []

    for bill_id in bill_ids:
        print(f"[force_fetch_vote_data] Fetching vote data for BILL_ID: {bill_id}")
        resp = requests.get(vote_url, params={
            "Key": os.getenv("API_KEY"),
            "Type": "json",
            "BILL_ID": bill_id,
            "AGE": 22,
            "HG_NM": member_name
        }).json()

        if (resp
            and "nojepdqqaweusdfbi" in resp
            and len(resp["nojepdqqaweusdfbi"]) > 1
            and "row" in resp["nojepdqqaweusdfbi"][1]):
            for vote in resp["nojepdqqaweusdfbi"][1]["row"]:
                tasks.append({
                    "vote": vote,
                    "task": crawl_bill_details(vote["BILL_ID"])
                })

    # 3) 병렬로 상세 정보 처리
    if tasks:
        bill_details_results = await asyncio.gather(*[t["task"] for t in tasks])
        for t, details in zip(tasks, bill_details_results):
            vote = t["vote"]
            vote["DETAILS"] = details
            vote_data.append(vote)

    # 4) DB에 저장
    await save_votes_to_db(vote_data)

    print("[force_fetch_vote_data] Final vote data with details:", vote_data)
    return vote_data




# DB 연결: startup / shutdown
@app.on_event("startup")
async def startup_event():
    print("[startup_event] 서버 시작 - DB 연결 및 초기화...")
    await database.connect()
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    asyncio.create_task(preload_data())

    # ✅ 1시간 간격으로 요약 실패 재처리
    # @repeat_every(seconds=3600)  # 1시간마다 실행
    # async def retry_failed_summaries():
    #     print("[retry_failed_summaries] 요약 실패 항목 재처리 중...")
    #     query = bills_table.select().where(bills_table.c.summary == "요약 생성 중 오류가 발생했습니다.")
    #     failed_bills = await database.fetch_all(query)

    #     for bill in failed_bills:
    #         bill_id = bill["bill_id"]
    #         details = bill["details"]
    #         if details and len(details.strip()) > 10:
    #             new_summary = await summarize_bill_details(details)
    #         else:
    #             new_summary = "내용이 충분하지 않아 요약을 생성할 수 없습니다."

    #         update_query = (
    #             bills_table.update()
    #             .where(bills_table.c.id == bill["id"])
    #             .values(summary=new_summary)
    #         )
    #         await database.execute(update_query)

    #     print(f"[retry_failed_summaries] {len(failed_bills)}개의 요약 실패 항목을 재처리했습니다.")


@app.on_event("shutdown")
async def shutdown_event():
    print("[shutdown_event] 서버 종료 - DB 연결 해제...")
    await database.disconnect()

@app.get("/status")
async def check_status():
    return {
        "vote_data_loaded": vote_data_loaded,
        "bills_data_loaded": bills_data_loaded
    }


@app.get("/")
async def root():
    print("[root] Status check requested.")
    response_data = {
        "status": "Server is running",
        "vote_data_loaded": vote_data_loaded,
        "bills_data_loaded": bills_data_loaded,
        "last_refresh_date": str(last_refresh_date) if last_refresh_date else None
    }
    return JSONResponse(content=response_data)



# Votes API
@app.get("/api/vote_data")
async def fetch_vote_data(member_name: str = Query(..., description="Name of the member")):
    print(f"[fetch_vote_data] Request with member_name={member_name}")
    global last_refresh_date, vote_data_loaded

    current_time = datetime.now()
    current_date = current_time.date()

    if not vote_data_loaded:
        response = {"message": "loading"}
        print(f"[fetch_vote_data] Response: {response}")
        return response

    # 캐시에 있으면 캐시 반환
    if "votes" in cache:
        if last_refresh_date == current_date:
            response = cache["votes"]
            print(f"[fetch_vote_data] Returning cached vote data. size={len(response)}")
            return response

        if is_refresh_time(current_time):
            print("[fetch_vote_data] Refresh time. Fetching new vote data...")
            votes = await force_fetch_vote_data(member_name)
            cache["votes"] = votes
            last_refresh_date = current_date
            return votes
        else:
            return cache["votes"]
    else:
        return {"message": "loading"}


# Bills API
@app.get("/api/bills_combined")
async def fetch_bills_combined(member_name: str = Query(...)):
    print(f"[fetch_bills_combined] Request with member_name={member_name}")
    global last_refresh_date, bills_data_loaded

    current_time = datetime.now()
    current_date = current_time.date()

    if not bills_data_loaded:
        return {"message": "loading"}

    # 캐시에 있으면 우선 반환
    if "bills" in cache:
        if last_refresh_date == current_date:
            return cache["bills"]

        if is_refresh_time(current_time):
            print("[fetch_bills_combined] It's refresh time (4 AM). Fetching new bills data...")
            bills = await force_fetch_bills_combined(member_name)
            cache["bills"] = bills
            last_refresh_date = current_date
            return bills
        else:
            return cache["bills"]
    else:
        return {"message": "loading"}
