import os
import sys
import requests
import openai
import html
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fuzzywuzzy import fuzz
from openai import Client
from pydantic import BaseModel

# 환경 변수 로드
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 모델 정의
class QueryRequest(BaseModel):
    query: str

# 환경 변수에서 API 키 가져오기
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 🛠️ 개선된 네이버 뉴스 검색 함수
def search_news(query, display=50, sort='sim'):
    """
    네이버 뉴스 검색 API를 호출하여 뉴스 데이터를 검색하고
    제목 유사도를 비교하여 중복된 뉴스를 필터링합니다.
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": sort}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        news_items = response.json().get("items", [])
        
        # 키워드 필터링: 제목 또는 내용에 키워드 포함 여부 확인
        filtered_news = [
            item for item in news_items
            if query.lower() in item["title"].lower() or query.lower() in item.get("description", "").lower()
        ]

        # 유사도 비교를 통해 중복 뉴스 제거
        unique_news = []
        for item in filtered_news:
            title = html.unescape(item["title"]).replace("<b>", "").replace("</b>", "")
            if not any(fuzz.ratio(title, existing["headline"]) > 30 for existing in unique_news):
                unique_news.append({
                    "headline": title,
                    "url": item["originallink"] or item["link"]
                })

        return unique_news[:4]  # 최대 4개 반환

    except requests.exceptions.RequestException as e:
        print(f"Error during news search: {e}")
        return []

# 뉴스 검색 결과 포맷팅
def format_news_results(news_results):
    """
    뉴스 검색 결과를 포맷팅하여 사용자에게 표시할 텍스트로 변환합니다.
    """
    if not news_results:
        return "검색 결과를 찾을 수 없습니다."

    formatted_results = []
    for item in news_results:
        formatted_results.append(f"제목: {item['headline']}\n링크: {item['url']}\n")

    return "\n".join(formatted_results)

# OpenAI API를 호출하여 응답 생성
client = Client(api_key=OPENAI_API_KEY)

def generate_response(prompt):
    """
    OpenAI ChatGPT API를 호출하여 응답을 생성합니다.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except openai.error.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return "오류가 발생했습니다. 다시 시도해 주세요."

# 기본 루트 엔드포인트
@app.get("/")
def root():
    return {"message": "Hello from chatbot server!"}

# 뉴스 검색 엔드포인트
@app.post("/search_news")
async def search_news_endpoint(request: QueryRequest):
    keyword = request.query.replace("뉴스", "").strip()
    news_results = search_news(keyword)
    return {"response": news_results}

# OpenAI ChatGPT API 호출 엔드포인트
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
