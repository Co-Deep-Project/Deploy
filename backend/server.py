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
import time
from .chatbot_data import search_news, generate_response, format_news_results

load_dotenv()

# 캐싱 (10분 유지)
cache = TTLCache(maxsize=100, ttl=600)

API_KEY = os.getenv("API_KEY")

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

# 뉴스 검색 API
@app.post("/search_news")
async def search_news_endpoint(request: QueryRequest):
    keyword = request.query.replace("뉴스", "").strip()
    news_results = search_news(keyword)
    if "error" in news_results:
        raise HTTPException(status_code=500, detail=news_results["message"])
    formatted_results = format_news_results(news_results)
    return {"response": formatted_results}


# GPT API 처리
@app.post("/ask_gpt")
async def ask_gpt_endpoint(request: QueryRequest):
    try:
        answer = generate_response(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 통합 챗봇 API
@app.post("/chatbot")
async def chatbot_endpoint(request: QueryRequest):
    user_query = request.query.lower()
    if "뉴스" in user_query:
        keyword = user_query.replace("뉴스", "").strip()
        news_results = search_news(keyword)
        formatted_results = format_news_results(news_results)
        return {"response": formatted_results}
    return {"response": generate_response(user_query)}



def crawl_bill_details(bill_id):
    """
    주어진 BILL_ID에 대해 '제안이유 및 주요내용'을 크롤링하고, 불필요한 부분을 제거합니다.
    """
    url = f"https://likms.assembly.go.kr/bill/summaryPopup.do?billId={bill_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()

        # BeautifulSoup을 이용해 HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find("div", class_="textType02 mt30")

        if content_div:
            # HTML 내용을 텍스트로 변환하며 <br/>을 \n로 변환
            raw_html = content_div.decode_contents()
            text_with_newlines = raw_html.replace("<br/>", "\n").strip()
            return BeautifulSoup(text_with_newlines, 'html.parser').get_text()
        else:
            return "내용을 찾을 수 없습니다."
    except Exception as e:
        print(f"Error while crawling BILL_ID {bill_id}: {e}")
        return "크롤링 중 오류 발생."


# 의안 투표 데이터 API
@app.get("/api/vote_data")
async def fetch_vote_data(member_name: str = Query(..., description="Name of the member")):
    vote_url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    bill_list_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"

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
                    bill_details = crawl_bill_details(vote["BILL_ID"])
                    vote["DETAILS"] = bill_details
                    vote_data.append(vote)

        print("Final vote data with details:", vote_data)
        cache["votes"] = vote_data
        return vote_data

    except Exception as e:
        print(f"Error in fetch_vote_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def fetch_collab_bills_with_selenium():
    url = "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do?monaCd=FIE6569O&st=22&viewType=CONTBODY&tabId=collabill"

    # ChromeDriver를 자동으로 관리
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저 숨김 모드
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get(url)
        time.sleep(3)  # 페이지 로드 대기
        
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
        else:
            print("No tbody found in the page source.")
        return collab_bills
    finally:
        driver.quit()

@app.get("/api/bills_combined")
async def fetch_bills_combined(member_name: str = Query(..., description="Name of the member")):
    """
    '곽상언' 의원이 대표발의한 법률안과 공동발의로 포함된 법률안을
    한 번에 반환합니다.
    """
    # 대표발의 법률 데이터 가져오기
    bills_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
    }
    try:
        response = requests.get(bills_url, headers=headers, params={
            "Key": API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 100,
            "PROPOSER": member_name,
            "AGE": "22"
        }).json()
        bills = []

        for item in response.get("nzmimeepazxkubdpn", [])[1].get("row", []):
            bill_id = item.get("BILL_ID")
            bill_details = crawl_bill_details(bill_id)
            bills.append({
                "type": "대표발의",
                "bill_no": item.get("BILL_NO"),
                "bill_url": item.get("DETAIL_LINK"),
                "bill_id": bill_id,
                "bill_name": item.get("BILL_NAME"),
                "propose_date": item.get("PROPOSE_DT"),
                "committee": item.get("COMMITTEE"),
                "proposer": item.get("PROPOSER"),
                "co_proposer": item.get("PUBL_PROPOSER"),
                "DETAILS": bill_details
            })
    except Exception as e:
        print(f"Error fetching bills: {e}")
        bills = []

    # 공동발의 법률 데이터 가져오기
    try:
        collab_bills = fetch_collab_bills_with_selenium()

                # 공동발의 법률안에 DETAILS 추가
        for bill in collab_bills:
            if bill["bill_id"]:  # bill_id가 존재하는 경우에만 crawl_bill_details 호출
                bill["DETAILS"] = crawl_bill_details(bill["bill_id"])
            else:
                bill["DETAILS"] = "상세 정보가 제공되지 않았습니다."
    except Exception as e:
        print(f"Error fetching collab bills: {e}")
        collab_bills = []

    combined_bills = bills + collab_bills
    print(f"{combined_bills}")
    return combined_bills