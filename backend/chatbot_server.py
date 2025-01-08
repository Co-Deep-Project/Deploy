import os
import sys
import requests
import openai
import html
import re
import datetime
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import Client
from fuzzywuzzy import fuzz
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Response



load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://politrackers.vercel.app", "http://localhost:3000", "https://politracker.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)


class QueryRequest(BaseModel):
    query: str

# 네이버 뉴스 검색 API 정보
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 글로벌 컨텍스트
session_context = {}

# 정치 관련 키워드 리스트
political_keywords = [
    # 일반 정치 키워드
    "정책", "법안", "대통령", "국회의원", "청와대", "정당", "선거", "투표", "외교", "장관", "내각", "개헌", "탄핵", "국회", "총선", "대선", "안보", "국방",
    # 법률 및 사법 키워드
    "법원", "헌법", "형법", "민법", "검찰", "대법원", "판결", "입법", "사법", "행정", "법률", "조례", "공청회", "입법예고",
    # 정책 관련 키워드
    "복지", "사회보장", "연금", "고용", "교육정책", "환경정책", "경제정책", "부동산정책", "세금", "재정", "지방자치", "지방정부", "공공기관", "정부예산", "규제완화", "정부지원", "청년정책",
    # 외교 및 국제정세 키워드
    "외교부", "국제회의", "유엔", "조약", "동맹", "평화협정", "국제분쟁", "무역협정", "비자정책", "외교관", "대사", "국제기구", "국제법",
    # 경제 및 금융 키워드
    "경제", "금융정책", "재정정책", "통화정책", "환율", "무역", "수출입", "통상", "경제협력", "부채", "금융시장", "투자", "소득", "세금개혁",
    # 사회 및 복지 키워드
    "사회복지", "국민건강보험", "고용보험", "실업급여", "저출산", "노인복지", "장애인복지", "기초생활보장", "공공주택", "교육개혁", "보육정책", "저소득층지원",
    # 안보 및 국방 키워드
    "국방부", "군대", "군사훈련", "안보협력", "북핵", "군비감축", "평화유지", "방위산업", "사이버안보", "군사정책", "방위비", "군사전략",
    # 기타 정치 관련 키워드
    "정세", "정부", "행정개혁", "리더십", "사회운동", "공약", "여론조사", "정책분석", "시민단체", "정치운동", "언론자유", "인권", "국가비전", "개발계획", "사업", "구청"
]


def search_news(query, display=50, sort='sim'):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": sort}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result_json = response.json()
        if "items" not in result_json:
            return result_json

        # 검색어에 "정치" 키워드가 포함되어 있는지 확인
        is_political_query = "정치" in query.lower()

        filtered_items = []
        today = datetime.datetime.now(datetime.timezone.utc)

        for item in result_json["items"]:
            title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "")
            description = html.unescape(item['description']).replace("<b>", "").replace("</b>", "")
            pub_date = item.get('pubDate', '')

            # 날짜 필터링
            pub_date_obj = datetime.datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
            days_diff = (today - pub_date_obj).days

            # 최신 뉴스 조건: 최근 30일 이내
            if days_diff <= 30:
                # 중복 검사
                similarity_title = fuzz.partial_ratio(query.lower(), title.lower())
                similarity_desc = fuzz.partial_ratio(query.lower(), description.lower())

                if similarity_title >= 50 or similarity_desc >= 40:
                    is_duplicate = False
                    for f_item in filtered_items:
                        existing_title = html.unescape(f_item['title']).replace("<b>", "").replace("</b>", "")
                        similarity_score = fuzz.ratio(title, existing_title)
                        if similarity_score >= 40:
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        # 정치 관련 질문일 때만 정치 뉴스 필터링 적용
                        if is_political_query:
                            content = f"{title} {description}".lower()
                            keyword_count = sum(1 for keyword in political_keywords if keyword in content)
                            if keyword_count >= 2:
                                filtered_items.append({
                                    "title": item['title'],
                                    "description": item['description'],
                                    "originallink": item['originallink'],
                                    "pubDate": pub_date
                                })
                        else:
                            # 정치 질문이 아니면 모든 뉴스 추가
                            filtered_items.append({
                                "title": item['title'],
                                "description": item['description'],
                                "originallink": item['originallink'],
                                "pubDate": pub_date
                            })

        # 최신순 정렬 추가
        filtered_items.sort(key=lambda x: datetime.datetime.strptime(x['pubDate'], '%a, %d %b %Y %H:%M:%S %z'), reverse=True)

        result_json["items"] = filtered_items[:4]  # 최대 4개만 반환
        return result_json
    else:
        return {"error": response.status_code, "message": response.text}



def format_news_results(news_results):
    if not news_results or "items" not in news_results:
        return "검색 결과를 찾을 수 없습니다."
    
    formatted_results = []
    for item in news_results['items']:
        title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "")
        link = item['originallink']
        formatted_results.append(f"제목: {title}\n링크: {link}\n")
    
    return "\n".join(formatted_results)


client = Client(api_key=OPENAI_API_KEY)

def generate_response(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content


async def handle_query(user_query):
    global session_context

    if "뉴스" in user_query:
        temp_query = user_query.lower()
        temp_query = re.sub(r'[^\w\s]', '', temp_query)

        # 기본 관련도순 정렬 유지
        sort = 'sim'

        # 최신 키워드가 있으면 내부 정렬을 위해 날짜순 추가 정렬
        if "최신" in temp_query:
            sort = 'sim'  # 기본은 관련도순으로 유지

        keyword = temp_query.replace("뉴스", "").replace("에 대해 알려줘", "").strip()

        news_results = search_news(keyword, sort=sort)
        if "items" in news_results:
            news_results["items"] = news_results["items"][:4]

        formatted_results = format_news_results(news_results)
        session_context["last_search"] = keyword
        return formatted_results

    elif "last_search" in session_context:
        keyword = session_context["last_search"]
        prompt = f"{keyword}와 관련된 뉴스에 대해 질문: {user_query}"
        return generate_response(prompt)
    else:
        return generate_response(user_query)


     


@app.get("/")
def root():
    return {"message": "Hello from chatbot server!"}



@app.post("/search_news")
async def search_news_endpoint(request: QueryRequest):
    temp_query = request.query.lower()
    temp_query = re.sub(r'[^\w\s]', '', temp_query)

    # 기본 관련도순 정렬 유지
    sort = 'sim'

    is_latest = "최신" in temp_query

    keyword = temp_query.replace("뉴스", "").replace("에 대해 알려줘", "").strip()

    news_results = search_news(keyword, sort=sort)
    if "error" in news_results:
        raise HTTPException(status_code=500, detail=news_results["message"])

    filtered_items = []
    for i, item in enumerate(news_results.get("items", [])):
        if i >= 4:
            break
        filtered_items.append({
            "title": html.unescape(item["title"]).replace("<b>", "").replace("</b>", ""),
            "description": html.unescape(item["description"]).replace("<b>", "").replace("</b>", ""),
            "link": item["originallink"]
        })

    if is_latest:
        filtered_items.sort(key=lambda x: datetime.datetime.strptime(x['pubDate'], '%a, %d %b %Y %H:%M:%S %z'), reverse=True)

    return {"response": filtered_items}



@app.post("/ask_gpt")
async def ask_gpt_endpoint(request: QueryRequest):
    try:
        answer = generate_response(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chatbot")
async def chatbot_endpoint(request: QueryRequest):
    user_query = request.query
    temp_query = user_query.lower()
    
    # 문장부호(.,!? 등) 제거
    temp_query = re.sub(r'[^\w\s]', '', temp_query)

    # 뉴스 관련 키워드 목록
    news_indicators = ["뉴스", "소식", "기사", "보도", "속보", "최신"]

    # 제거할 불필요 단어들의 리스트
    remove_words = [
        "뉴스", "소식", "기사", "보도", "속보",
        "에 대해 알려줘", "에 대해", "대해", "알려줘",
        "알려주세요", "알려주시겠어요", "알려달라",
        "찾아줘", "검색해줘", "보여줘"
    ]

    # 뉴스 검색 로직으로 분기
    if any(word in temp_query for word in news_indicators):
        # 불필요 단어들 제거 → 핵심 키워드만 추출
        keyword = temp_query
        for word in remove_words:
            keyword = keyword.replace(word, "")
        
        # 앞뒤 공백 제거 및 중복 공백 제거
        keyword = " ".join(keyword.split())

        # 네이버 뉴스 검색
        news_results = search_news(keyword)
        if "items" in news_results:
            # 최대 4개만 추리기
            news_results["items"] = news_results["items"][:4]

        # 포맷팅된 결과 반환
        formatted_results = format_news_results(news_results)
        return {"response": formatted_results}

    # 뉴스 키워드가 없으면 일반 ChatGPT 응답
    return {"response": generate_response(user_query)}


