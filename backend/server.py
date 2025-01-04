import os
import sys
import re
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import asyncio
from cachetools import TTLCache
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from openai import OpenAI, AsyncClient

load_dotenv()

# 캐싱 (10분 유지) -> 24시간으로 변경
# 데이터를 10분간 임시로 저장해둠
cache = TTLCache(maxsize=10000, ttl=86400)

API_KEY = os.getenv("API_KEY")
bills_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
}

app = FastAPI()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://backend-three-theta-46.vercel.app", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vote_data_loaded = False
bills_data_loaded = False

last_refresh_date = None  
REFRESH_HOUR = 4  # 새벽 4시


class QueryRequest(BaseModel):
    query: str


async def preload_data():
    """
    서버 시작 시 데이터 미리 로드해 캐시에 저장 (강제 1회 로드).
    """
    global vote_data_loaded, bills_data_loaded, last_refresh_date

    print("Preloading vote and bill data...")
    # 로딩 중인 상태로 시작
    vote_data_loaded = False
    bills_data_loaded = False

    try:
        # 1) 의안 투표 데이터 캐싱
        votes = await force_fetch_vote_data("곽상언")
        cache["votes"] = votes
        vote_data_loaded = True
        print("Vote data preloaded.")
    except Exception as e:
        print(f"Error preloading vote data: {e}")

    try:
        # 2) 발의 법률 데이터 캐싱
        bills = await force_fetch_bills_combined("곽상언")
        cache["bills"] = bills
        bills_data_loaded = True
        print("Bills data preloaded.")
    except Exception as e:
        print(f"Error preloading bills data: {e}")

    # 오늘 날짜로 세팅 (서버 첫 구동 시점)
    last_refresh_date = datetime.now().date()
    print("Preloading completed.")


@app.on_event("startup")
async def startup_event():
    # 서버 시작 시 비동기로 데이터 로드
    asyncio.create_task(preload_data())

def is_refresh_time(now: datetime) -> bool:
    """
    오전 4시(정각)인지 확인하는 함수.
    분, 초까지 딱 맞출지, hour만 볼지 결정 가능.
    여기서는 'hour == 4'만 만족해도 4시로 간주.
    """
    return now.hour == REFRESH_HOUR

@app.get("/")
async def root():
    if not vote_data_loaded:
        return {"message": "Server is starting up, please wait..."}
    return {"message": "Welcome to the API!"}


# 요약 추가
client = AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))
async def summarize_bill_details(content):
    """GPT를 사용해 법안 내용을 요약"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "법안의 내용을 간단명료하게 300자 이내로 요약해주세요. 핵심 내용만 3-4줄로 정리해주세요."},
                {"role": "user", "content": content}
            ],
            temperature=0.7,
            # max_tokens=  # 토큰 수 제한으로 비용과 시간 절약
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in summarization: {e}")
        return "요약 생성 중 오류가 발생했습니다."

# 요약본도 캐시에 저장
class BillCache(BaseModel):
    details: str
    summary: str

async def crawl_bill_details(bill_id):
    """
    주어진 BILL_ID에 대해 '제안이유 및 주요내용'을 크롤링하고, 필요시 요약을 생성.
    """
    cache_key = f"bill_details_{bill_id}"
    
    # 캐시 확인
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
                    print(f"요약 생성 중 오류: {e}")
                    summary = "요약 생성 중 오류가 발생했습니다."
            else:
                summary = "내용이 충분하지 않아 요약을 생성할 수 없습니다."

            result = {
                "details": details.strip(),
                "summary": summary
            }
            cache[cache_key] = result
            return result
        else:
            return {
                "details": "내용을 찾을 수 없습니다.",
                "summary": "요약 불가"
            }
    except Exception as e:
        print(f"Error while crawling BILL_ID {bill_id}: {e}")
        return {
            "details": f"크롤링 중 오류 발생: {str(e)}",
            "summary": "요약 불가"
        }



@app.get("/api/vote_data")
async def fetch_vote_data(member_name: str = Query(..., description="Name of the member")):
    """
    오전 4시에만 데이터를 새로고침하고, 
    그 외 시간에는 캐시 데이터 반환.
    캐시에 없으면 "로딩 중" 메시지 반환 (서버 스타트 후 미처 로드되지 않았을 경우).
    """
    global last_refresh_date, vote_data_loaded

    current_time = datetime.now()
    current_date = current_time.date()

    # 만약 아직 preload_data()가 끝나지 않았다면 "로딩 중" 상태 반환
    if not vote_data_loaded:
        return {"message": "loading"}

    # 캐시에 데이터가 있는지 확인
    if "votes" in cache:
        # 오늘 이미 새로고침 했다면, 캐시 데이터 반환
        if last_refresh_date == current_date:
            return cache["votes"]
        
        # 아직 오늘 새로고침 안 했는데, 지금이 4시라면 → 새로고침
        if is_refresh_time(current_time):
            votes = await force_fetch_vote_data(member_name)
            cache["votes"] = votes
            last_refresh_date = current_date
            return votes
        else:
            # 4시가 아니므로 강제 새로고침 막기
            return cache["votes"]
    else:
        # 캐시에 데이터가 없는데, 로딩도 안 끝났다?
        # 혹은 로딩 중간에 뭔가 에러가 나서 없을 수 있다
        return {"message": "loading"}


async def force_fetch_vote_data(member_name: str):
    """
    외부 API를 호출해 강제로 의안 투표 데이터를 가져오는 함수.
    preload_data()나 4시 새로고침 시에만 사용.
    """
    vote_url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    bill_list_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"

    print(f"[force_fetch_vote_data] Fetching bill IDs for member: {member_name}")
    pIndex = 1
    bill_ids = []
    has_more_data = True

    # 1) 전체 BILL_ID 수집
    while has_more_data:
        print(f"Fetching page {pIndex} for bill IDs...")
        bill_response = requests.get(bill_list_url, params={
            "Key": API_KEY,
            "Type": "json",
            "AGE": 22,
            "pSize": 10,
            "pIndex": pIndex
        }).json()

        if (
            "nwbpacrgavhjryiph" in bill_response
            and len(bill_response["nwbpacrgavhjryiph"]) > 1
            and "row" in bill_response["nwbpacrgavhjryiph"][1]
        ):
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
        print(f"Fetching vote data for BILL_ID: {bill_id}")
        response = requests.get(vote_url, params={
            "Key": API_KEY,
            "Type": "json",
            "BILL_ID": bill_id,
            "AGE": 22,
            "HG_NM": member_name
        }).json()

        if (
            response
            and "nojepdqqaweusdfbi" in response
            and len(response["nojepdqqaweusdfbi"]) > 1
            and "row" in response["nojepdqqaweusdfbi"][1]
        ):
            for vote in response["nojepdqqaweusdfbi"][1]["row"]:
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

    print("[force_fetch_vote_data] Final vote data with details:", vote_data)
    return vote_data


@app.get("/api/bills_combined")
async def fetch_bills_combined(member_name: str = Query(...)):
    """
    오전 4시에만 데이터 새로고침. 그 외에는 캐시를 반환.
    캐시에 없으면 "loading" 메시지 반환.
    """

    global last_refresh_date, bills_data_loaded

    current_time = datetime.now()
    current_date = current_time.date()

    if not bills_data_loaded:
        return {"message": "loading"}

    # 캐시에 데이터가 있다면
    if "bills" in cache:
        # 오늘 이미 새로고침 했다면 캐시 반환
        if last_refresh_date == current_date:
            return cache["bills"]
        
        # 4시가 맞다면 새로고침
        if is_refresh_time(current_time):
            data = await force_fetch_bills_combined(member_name)
            cache["bills"] = data
            last_refresh_date = current_date
            return data
        else:
            # 4시 아니므로 강제 새로고침 X
            return cache["bills"]
    else:
        # 캐시에 데이터가 전혀 없으면 "loading"
        return {"message": "loading"}


async def force_fetch_bills_combined(member_name: str):
    """
    외부 API + selenium 크롤링해서 의원 법안(대표발의, 공동발의) 정보를 강제로 가져오는 함수
    """
    # 대표발의 법안
    bills = []
    response = requests.get(bills_url, headers=headers, params={
        "Key": API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "PROPOSER": member_name,
        "AGE": "22"
    }).json()
    
    tasks = []
    rows = response.get("nzmimeepazxkubdpn", [{}])[1].get("row", [])
    for item in rows:
        bill_id = item.get("BILL_ID")
        if bill_id:
            tasks.append(crawl_bill_details(bill_id))

    bill_details_list = await asyncio.gather(*tasks)
    
    for item, details in zip(rows, bill_details_list):
        bills.append({
            "type": "대표발의",
            "bill_id": item.get("BILL_ID"),
            "bill_name": item.get("BILL_NAME"),
            "propose_date": item.get("PROPOSE_DT"),
            "committee": item.get("COMMITTEE"),
            "proposer": item.get("PROPOSER"),
            "bill_link": item.get("DETAIL_LINK"),
            "DETAILS": details["details"],
            "SUMMARY": details["summary"]
        })

    # 공동발의 법안
    collab_bills = await fetch_collab_bills_with_selenium()
    collab_tasks = []
    for bill in collab_bills:
        if bill["bill_id"]:
            collab_tasks.append(crawl_bill_details(bill["bill_id"]))
    
    collab_details_list = await asyncio.gather(*collab_tasks)
    for bill, details in zip(collab_bills, collab_details_list):
        bill["DETAILS"] = details["details"]
        bill["SUMMARY"] = details["summary"]

    return bills + collab_bills

async def fetch_collab_bills_with_selenium():
    """
    공동발의 법안을 Selenium으로 크롤링하는 예시.
    """
    url = "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do?monaCd=FIE6569O&st=22&viewType=CONTBODY&tabId=collabill"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        await asyncio.sleep(3)  # 페이지 로드 대기
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        tbody = soup.find("tbody", id="prpl_cont__collabill__list")
        
        collab_bills = []
        if tbody:
            for tr in tbody.find_all("tr"):
                a_tag = tr.find("td", class_="align_left td_block").find("a")
                if a_tag and a_tag.has_attr("href"):
                    bill_link = a_tag["href"].strip()
                    bill_name = a_tag.get_text(strip=True)
                    match = re.search(r"billId=([^&]+)", bill_link)
                    bill_id = match.group(1) if match else None
                else:
                    bill_link = None
                    bill_name = None
                    bill_id = None

                proposer = tr.find("td", class_="list__proposer").get_text(strip=True) if tr.find("td", class_="list__proposer") else None
                committee = tr.find("td", class_="board_text", attrs={"class": "list__currCommittee"}).get_text(strip=True) if tr.find("td", class_="board_text", attrs={"class": "list__currCommittee"}) else None
                propose_date = tr.find("td", class_="list__proposeDt").get_text(strip=True) if tr.find("td", class_="list__proposeDt") else None

                collab_bills.append({
                    "type": "공동발의",
                    "bill_id": bill_id,
                    "bill_name": bill_name,
                    "bill_link": bill_link,
                    "proposer": proposer,
                    "committee": committee,
                    "propose_date": propose_date
                })
            return collab_bills
        else:
            return []
    finally:
        driver.quit()