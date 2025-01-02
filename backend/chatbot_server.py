import os
import requests
import openai
import html
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 네이버 뉴스 검색 API 정보
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 글로벌 컨텍스트
session_context = {
    "introduced": False,  # 사용자에게 소개 메시지를 출력했는지 여부
    "last_topic": None,  # 마지막 대화 주제
    "conversation_history": []  # 대화 기록
}

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

def search_news(query, display=5, sort='sim'):
    """
    네이버 뉴스 검색 API를 호출하여 뉴스 데이터를 검색합니다.
    :param query: 검색 키워드
    :param display: 검색 결과 수
    :param sort: 정렬 기준 ('sim' 또는 'date')
    :return: 뉴스 검색 결과 JSON
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": query, "display": display, "sort": sort}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        # 최신 뉴스 3개만 반환하도록 수정
        news_results = response.json()
        # 최신 뉴스 3개의 헤드라인과 URL만 반환
        return [
            {"headline": item["title"].replace("<b>", "").replace("</b>", ""),
             "url": item["originallink"] or item["link"]}
            for item in news_results.get("items", [])[:3]
        ]
    else:
        return {"error": response.status_code, "message": response.text}


def filter_news_by_keyword(news_results, keyword):
    """
    뉴스 제목에 특정 키워드가 포함된 뉴스만 필터링합니다.
    :param news_results: 뉴스 검색 결과 JSON
    :param keyword: 필터링에 사용할 키워드 (예: 지역구 이름)
    :return: 필터링된 뉴스 리스트
    """
    if not news_results or "items" not in news_results:
        return []
    
    # 키워드 전처리 (소문자로 변환 및 공백 제거)
    keyword = keyword.lower().strip()

    filtered_items = []
    for item in news_results['items']:
        title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "").lower()
        if any(k in title for k in keyword.split()):  # 키워드의 각 단어가 제목에 포함되는지 확인
            filtered_items.append(item)
    
    #print("필터링된 뉴스:", filtered_items)  # 디버깅용 출력
    return filtered_items

def format_news_results(filtered_news):
    """
    필터링된 뉴스 검색 결과를 포맷팅하여 사용자에게 표시할 텍스트로 변환합니다.
    :param filtered_news: 필터링된 뉴스 리스트
    :return: 포맷팅된 텍스트
    """
    if not filtered_news:
        #print("필터링된 결과가 없습니다.")  # 디버깅용 출력
        return "검색 결과를 찾을 수 없습니다."
    
    formatted_results = []
    for item in filtered_news:
        title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "")
        description = html.unescape(item['description']).replace("<b>", "").replace("</b>", "")
        link = item['originallink']
        formatted_results.append(f"제목: {title}\n링크: {link}\n")
    
    return "\n".join(formatted_results)

async def introduction_message():
    """
    사용자에게 챗봇의 기능 소개 및 예시 질문을 출력합니다.
    :return: 소개 메시지 텍스트
    """
    intro_text = """
안녕하세요! 저는 여러분의 도우미, 폴리트래커 챗봇입니다. 😊
다음과 같은 기능을 제공합니다:
1. 뉴스 검색: 특정 지역이나 주제에 대한 뉴스를 검색할 수 있어요.
   예: "종로구 뉴스", "기후 변화 뉴스"
2. 일반 질문: 다양한 주제에 대한 정보를 제공해요.
   예: "탄핵이란 무엇인가요?", "인공지능의 정의는?"
3. 대화형 질문: 뉴스와 관련된 추가 질문도 답변할 수 있어요.

원하시는 질문을 입력해 주세요!
"""
    return intro_text

from openai import Client
client = Client(api_key=OPENAI_API_KEY)

def generate_response(prompt):
    """
    OpenAI ChatGPT API를 호출하여 응답을 생성합니다.
    :param prompt: 사용자 입력 프롬프트
    :return: ChatGPT의 응답
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content

async def handle_query(user_query):
    """
    사용자 쿼리를 처리하여 적절한 응답을 반환합니다.
    :param user_query: 사용자 입력 쿼리
    :return: 처리 결과
    """
    global session_context

    # 첫 상호작용: 사용자에게 소개 메시지 제공
    if not session_context["introduced"]:
        session_context["introduced"] = True
        return await introduction_message()

    # 뉴스 관련 대화
    if "뉴스" in user_query:
        keyword = user_query.replace("뉴스", "").strip()
        if not keyword:
            return "검색 키워드를 입력해 주세요!"

        # 간단한 키워드 전처리
        keyword = " ".join(keyword.split())  # 중복 공백 제거
        
        news_results = search_news(keyword)
        filtered_news = filter_news_by_keyword(news_results, keyword)
        if not filtered_news:
            return f"'{keyword}'와(과) 관련된 뉴스가 없습니다. 다른 키워드로 검색하시거나 구체적인 내용을 입력해 주세요!"
        
        formatted_results = format_news_results(filtered_news)
        session_context["last_topic"] = "뉴스"
        session_context["conversation_history"].append({
            "user_query": user_query,
            "bot_response": formatted_results
        })
        return formatted_results

    # 이전 주제와 관련된 대화
    elif session_context.get("last_topic") == "뉴스":
        last_search = session_context["conversation_history"][-1]["user_query"]
        related_prompt = f"{last_search}와 관련된 추가 질문: {user_query}"
        response = generate_response(related_prompt)
        session_context["conversation_history"].append({
            "user_query": user_query,
            "bot_response": response
        })
        return response

    # 일반 대화
    else:
        response = generate_response(user_query)
        session_context["conversation_history"].append({
            "user_query": user_query,
            "bot_response": response
        })
        return response

# 테스트 실행
async def test_queries():
    global session_context

    # 테스트 1: 뉴스 검색
    print("\n[테스트 1: 뉴스 검색]")
    session_context = {"introduced": True, "last_topic": None, "conversation_history": []}
    query1 = "종로구 뉴스"
    response1 = await handle_query(query1)
    print("응답:\n", response1)

    # 테스트 2: 일반 질문
    print("\n[테스트 2: 일반 질문]")
    session_context = {"introduced": True, "last_topic": None, "conversation_history": []}
    query2 = "탄핵이란 무엇인가요?"
    response2 = await handle_query(query2)
    print("응답:\n", response2)

    # 테스트 3: 뉴스와 관련된 추가 질문
    print("\n[테스트 3: 뉴스와 관련된 추가 질문]")
    session_context = {
        "introduced": True,
        "last_topic": "뉴스",
        "conversation_history": [
            {
                "user_query": "종로구 뉴스",
                "bot_response": "종로구 관련 뉴스 예시"
            }
        ]
    }
    query3 = "청년에게 지대한 영향을 미칠 점은 무엇인가요?"
    response3 = await handle_query(query3)
    print("응답:\n", response3)

    # 테스트 4: 대화형 질문
    print("\n[테스트 4: 대화형 질문]")
    session_context = {
        "introduced": True,
        "last_topic": "뉴스",
        "conversation_history": [
            {
                "user_query": "종로구 뉴스",
                "bot_response": "종로구 관련 뉴스 예시"
            }
        ]
    }
    query4 = "다른 지역 뉴스는?"
    response4 = await handle_query(query4)
    print("응답:\n", response4)



@app.post("/search_news")
async def search_news_endpoint(request: QueryRequest):
    keyword = request.query.replace("뉴스", "").strip()
    news_results = search_news(keyword)
    if "error" in news_results:
        raise HTTPException(status_code=500, detail=news_results["message"])
    formatted_results = format_news_results(news_results)
    return {"response": formatted_results}


@app.post("/ask_gpt")
async def ask_gpt_endpoint(request: QueryRequest):
    try:
        answer = generate_response(request.query)
        return {"response": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chatbot")
async def chatbot_endpoint(request: QueryRequest):
    user_query = request.query.lower()
    if "뉴스" in user_query:
        keyword = user_query.replace("뉴스", "").strip()
        news_results = search_news(keyword)
        formatted_results = format_news_results(news_results)
        return {"response": formatted_results}
    return {"response": generate_response(user_query)}