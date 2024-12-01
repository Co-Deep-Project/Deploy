import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import asyncio
from cachetools import TTLCache
from dotenv import load_dotenv
from .chatbot_data import search_news, generate_response, format_news_results

load_dotenv()

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

# 캐싱 (10분 유지)
cache = TTLCache(maxsize=100, ttl=600)

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
        cache["bills"] = await fetch_bills("곽상언")
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
                vote_data.extend(response["nojepdqqaweusdfbi"][1]["row"])

        print("Final vote data:", vote_data)
        cache["votes"] = vote_data
        return vote_data

    except Exception as e:
        print(f"Error in fetch_vote_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 발의 법률 데이터 API
@app.get("/api/bills")
async def fetch_bills(member_name: str = Query(..., description="Name of the member")):
    bills_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"

    if "bills" in cache:
        print(f"Returning cached bills data for {member_name}")
        return cache["bills"]

    try:
        response = requests.get(bills_url, params={
            "Key": API_KEY,
            "Type": "json",
            "pIndex": 1,
            "pSize": 100,
            "PROPOSER": member_name,
            "AGE": "22"
        }).json()
        bills = [
            {
                "bill_id": item.get("BILL_NO"),
                "bill_name": item.get("BILL_NAME"),
                "propose_date": item.get("PROPOSE_DT"),
                "committee": item.get("COMMITTEE"),
                "proposer": item.get("PROPOSER"),
                "co_proposer": item.get("PUBL_PROPOSER")
            }
            for item in response.get("nzmimeepazxkubdpn", [])[1].get("row", [])
        ]

        cache["bills"] = bills 
        return bills
    except Exception as e:
        print(f"Error in fetch_bills: {e}")
        raise HTTPException(status_code=500, detail=str(e))
