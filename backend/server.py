import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Query
import requests 
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

from .chatbot_data import search_news, generate_response, format_news_results

# 뉴스 검색
@app.post("/search_news")
async def search_news_endpoint(request: QueryRequest):
    keyword = request.query.replace("뉴스", "").strip()
    news_results = search_news(keyword)
    if "error" in news_results:
        raise HTTPException(status_code=500, detail=news_results["message"])
    formatted_results = format_news_results(news_results)
    return {"response": formatted_results}

# GPT 질문 처리
@app.post("/ask_gpt")
async def ask_gpt_endpoint(request: QueryRequest):
    try:
        answer = generate_response(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 통합 챗봇 엔드포인트
@app.post("/chatbot")
async def chatbot_endpoint(request: QueryRequest):
    user_query = request.query.lower()
    if "뉴스" in user_query:
        keyword = user_query.replace("뉴스", "").strip()
        news_results = search_news(keyword)
        formatted_results = format_news_results(news_results)
        return {"response": formatted_results}
    return {"response": generate_response(user_query)}

# 의안 투표 데이터 (server1.js 기능)
@app.get("/api/vote_data")
async def fetch_vote_data(member_name: str = Query(..., description="Name of the member")):
    vote_url = "https://open.assembly.go.kr/portal/openapi/nojepdqqaweusdfbi"
    bill_list_url = "https://open.assembly.go.kr/portal/openapi/nwbpacrgavhjryiph"
    try:
        # Step 1: 의안 ID 가져오기 (페이지네이션 추가)
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
                pIndex += 1  # 다음 페이지로 이동
            else:
                print("No more rows found in the response for BILL_IDs.")
                has_more_data = False  # 데이터가 없으면 종료

        print("Retrieved BILL_IDs:", bill_ids)  # 디버깅 출력

        # Step 2: 의안별 투표 데이터 가져오기
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

        print("Final vote data:", vote_data)  # 디버깅 출력
        return vote_data

    except Exception as e:
        print(f"Error in fetch_vote_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# 발의 법률 데이터 (server2.js 기능)
@app.get("/api/bills")
async def fetch_bills(member_name: str = Query(..., description="Name of the member")):
    bills_url = "https://open.assembly.go.kr/portal/openapi/nzmimeepazxkubdpn"
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
                "proposer": item.get("PROPOSER")
            }
            for item in response.get("nzmimeepazxkubdpn", [])[1].get("row", [])
        ]
        return bills
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

