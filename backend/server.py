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
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vote_data_loaded = False
bills_data_loaded = False


class QueryRequest(BaseModel):
    query: str


async def preload_data():
    """
    서버 시작 시 데이터 미리 로드.
    """
    global vote_data_loaded, bills_data_loaded

    print("Preloading vote and bill data...")

    # 의안 투표 데이터 캐싱
    try:
        cache["votes"] = await fetch_vote_data("곽상언")
        vote_data_loaded = True
    except Exception as e:
        print(f"Error preloading vote data: {e}")

    # 발의 법률 데이터 캐싱
    try:
        cache["bills"] = await fetch_bills_combined("곽상언")
        bills_data_loaded = True
    except Exception as e:
        print(f"Error preloading bills data: {e}")

    print("Preloading completed.")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(preload_data()) 


# 요약 추가
client = AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))
async def summarize_bill_details(content):
    """GPT를 사용해 법안 내용을 요약"""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
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
    주어진 BILL_ID에 대해 '제안이유 및 주요내용'을 크롤링하고, 불필요한 부분을 제거합니다.
    """
    cache_key = f"bill_details_{bill_id}"
    
    # 캐시 확인
    if cache_key in cache:
        return cache[cache_key]
    
    try:
        # 기존 크롤링 코드
        url = f"https://likms.assembly.go.kr/bill/summaryPopup.do?billId={bill_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find("div", class_="textType02 mt30")
        
        if content_div:
            raw_html = content_div.decode_contents()
            # 디버깅
            print(f"크롤링된 원본 HTML: {raw_html[:200]}...")
            text_with_newlines = raw_html.replace("<br/>", "\n").strip()
            details = BeautifulSoup(text_with_newlines, 'html.parser').get_text()
            
            # 디버깅
            print(f"정제된 텍스트: {details[:200]}...")
            if len(details.strip()) > 10:  # 의미있는 내용이 있는지 확인
                try:
                    summary = await summarize_bill_details(details)
                    print(f"생성된 요약: {summary}")  # 요약 내용 확인
                except Exception as e:
                    print(f"요약 생성 중 오류: {e}")
                    summary = "요약 생성 중 오류가 발생했습니다."
            else:
                summary = "내용이 충분하지 않아 요약을 생성할 수 없습니다."

            # 요약 생성
            #summary = await summarize_bill_details(details)
            
            result = {
                "details": details.strip(),
                "summary": summary
            }
            
            # 캐시에 저장
            cache[cache_key] = result
            return result
        else:
            # 디버깅
            print(f"content_div를 찾을 수 없음: {bill_id}")
            return {
                "details": "내용을 찾을 수 없습니다.",
                "summary": "요약 불가"
            }
            
    except Exception as e:
        print(f"Error while crawling BILL_ID {bill_id}: {e}")
        print(f"전체 응답 내용: {response.text[:500]}...")
        return {
            "details": f"크롤링 중 오류 발생: {str(e)}",
            "summary": "요약 불가"
        }


last_refresh_time = None


# 의안 투표 데이터 API
@app.get("/api/vote_data")
async def fetch_vote_data(member_name: str = Query(..., description="Name of the member")):
    vote_url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    bill_list_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"


    global last_refresh_time

    # 현재 시간 확인
    current_time = datetime.now()

    # 자정 기준 새로고침 제한
    if last_refresh_time:
        if current_time.date() == last_refresh_time.date():
            print("Returning cached vote data, new refresh is allowed only after midnight.")
            return cache.get("votes", "No cached data available")

    if "votes" in cache:
        print(f"Returning cached vote data for {member_name}")
        return cache["votes"]

    try:
        print(f"Fetching bill IDs for member: {member_name}")
        pIndex = 1
        bill_ids = []
        has_more_data = True

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

        print("Retrieved BILL_IDs:", bill_ids)

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

        # 모든 bill_details를 병렬로 실행
        if tasks:
            bill_details_results = await asyncio.gather(*[task["task"] for task in tasks])
            
            # 결과를 vote_data에 추가
            for task, details in zip(tasks, bill_details_results):
                vote = task["vote"]
                vote["DETAILS"] = details
                vote_data.append(vote)

        print("Final vote data with details:", vote_data)
        cache["votes"] = vote_data
        last_refresh_time = current_time
        print("Vote data refreshed at:", last_refresh_time)
        return vote_data

    except Exception as e:
        print(f"Error in fetch_vote_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def fetch_collab_bills_with_selenium():
    url = "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do?monaCd=FIE6569O&st=22&viewType=CONTBODY&tabId=collabill"

    # ChromeDriver를 자동으로 관리
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저 숨김 모드
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
            print("No tbody found in the page source.")
            return []
    finally:
        driver.quit()

@app.get("/api/bills_combined")
async def fetch_bills_combined(member_name: str = Query(...)):
    global last_refresh_time

    # 현재 시간 확인
    current_time = datetime.now()

    # 자정 기준 새로고침 제한
    if last_refresh_time:
        if current_time.date() == last_refresh_time.date():
            print("Returning cached bills data, new refresh is allowed only after midnight.")
            return cache.get("bills", "No cached data available")


    try:
        # 대표발의 법안 가져오기
        bills = []
        response = requests.get(bills_url, headers=headers, params={
            "Key": API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 100,
            "PROPOSER": member_name,
            "AGE": "22"
        }).json()
        
        # 병렬로 처리하기 위한 태스크 리스트
        tasks = []
        
        for item in response.get("nzmimeepazxkubdpn", [])[1].get("row", []):
            bill_id = item.get("BILL_ID")
            # 비동기로 처리할 태스크 추가
            tasks.append(crawl_bill_details(bill_id))
        
        # 모든 태스크를 동시에 실행
        bill_details_list = await asyncio.gather(*tasks)
        
        # 결과 조합
        for item, details in zip(response.get("nzmimeepazxkubdpn", [])[1].get("row", []), bill_details_list):
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
            
        # 비슷한 방식으로 공동발의 법안도 처리
        collab_bills = await fetch_collab_bills_with_selenium()
        collab_tasks = []
        
        for bill in collab_bills:
            if bill["bill_id"]:
                collab_tasks.append(crawl_bill_details(bill["bill_id"]))
        
        collab_details_list = await asyncio.gather(*collab_tasks)
        
        for bill, details in zip(collab_bills, collab_details_list):
            bill["DETAILS"] = details["details"]
            bill["SUMMARY"] = details["summary"]

        last_refresh_time = current_time
        print("Bills data refreshed at:", last_refresh_time)

        return bills + collab_bills
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
