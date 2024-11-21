import requests
import openai
import html
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


# 네이버 뉴스 검색 API 정보
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# OpenAI API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# 글로벌 컨텍스트
session_context = {}

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
        return response.json()
    else:
        return {"error": response.status_code, "message": response.text}

def format_news_results(news_results):
    """
    뉴스 검색 결과를 포맷팅하여 사용자에게 표시할 텍스트로 변환합니다.
    :param news_results: 뉴스 검색 결과 JSON
    :return: 포맷팅된 텍스트
    """
    if not news_results or "items" not in news_results:
        return "검색 결과를 찾을 수 없습니다."
    
    formatted_results = []
    for item in news_results['items']:
        title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "")
        description = html.unescape(item['description']).replace("<b>", "").replace("</b>", "")
        link = item['originallink']
        formatted_results.append(f"제목: {title}\n설명: {description}\n링크: {link}\n")
    
    return "\n".join(formatted_results)


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

    if "뉴스" in user_query:
        keyword = user_query.replace("뉴스", "").strip()
        news_results = search_news(keyword)
        formatted_results = format_news_results(news_results)
        session_context["last_search"] = keyword  # 맥락 저장
        return formatted_results

    elif "last_search" in session_context:
        keyword = session_context["last_search"]
        prompt = f"{keyword}와 관련된 뉴스에 대해 질문: {user_query}"
        return generate_response(prompt)

    else:
        return generate_response(user_query)

# 테스트 실행
async def test_queries():
    """
    다양한 테스트 쿼리를 실행하여 시스템을 확인합니다.
    """
    global session_context

    # 테스트 1: 뉴스 검색
    print("\n[테스트 1: 뉴스 검색]")
    query1 = "종로구 뉴스"
    response1 = await handle_query(query1)
    print("응답:\n", response1)

    # 테스트 2: 일반 질문
    print("\n[테스트 2: 일반 질문]")
    query2 = "탄핵이란 무엇인가요?"
    response2 = await handle_query(query2)
    print("응답:\n", response2)

    # 테스트 3: 뉴스와 관련된 추가 질문
    print("\n[테스트 3: 뉴스와 관련된 추가 질문]")
    query3 = "중요한 점은 무엇인가요?"
    response3 = await handle_query(query3)
    print("응답:\n", response3)

    # 테스트 4: 대화형 질문
    print("\n[테스트 4: 대화형 질문]")
    query4 = "오늘의 날씨는 어떤가요?"
    response4 = await handle_query(query4)
    print("응답:\n", response4)

# asyncio.run을 사용하여 테스트 실행
if __name__ == "__main__":
    asyncio.run(test_queries())