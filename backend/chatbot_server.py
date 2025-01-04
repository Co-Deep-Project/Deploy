import os
import sys
import requests
import openai
import html
import re
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
    allow_origins=["https://backend-three-theta-46.vercel.app", "http://localhost:3000"],
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

        filtered_items = []
        for item in result_json["items"]:
            title = html.unescape(item['title']).replace("<b>", "").replace("</b>", "")
            description = html.unescape(item['description']).replace("<b>", "").replace("</b>", "")

            # (정확 일치) query가 title/description에 포함되어 있는지
            # if (query.lower() in title.lower()) or (query.lower() in description.lower()):
            
            # (부분 일치로 바꾸고 싶다면 ↓ 아래 코드 사용)
            similarity_title = fuzz.partial_ratio(query.lower(), title.lower())
            similarity_desc = fuzz.partial_ratio(query.lower(), description.lower())
            # 예) 50 이상이면 통과
            if similarity_title >= 50 or similarity_desc >= 40:
                # 중복 체크
                is_duplicate = False
                for f_item in filtered_items:
                    existing_title = html.unescape(f_item['title']).replace("<b>", "").replace("</b>", "")
                    similarity_score = fuzz.ratio(title, existing_title)
                    if similarity_score >= 40:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    filtered_items.append({
                        "title": item['title'],
                        "description": item['description'],
                        "originallink": item['originallink']
                    })

        result_json["items"] = filtered_items
        return result_json
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
        link = item['originallink']
        formatted_results.append(f"제목: {title}\n링크: {link}\n")
    
    return "\n".join(formatted_results)


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
    global session_context

    if "뉴스" in user_query:
        # 1) 전부 소문자로 바꾸고
        temp_query = user_query.lower()
        # 2) 문장부호 제거
        temp_query = re.sub(r'[^\w\s]', '', temp_query)
        # 3) 뉴스/최신/에 대해 알려줘 제거
        keyword = (temp_query
                   .replace("뉴스", "")
                   .replace("최신", "")
                   .replace("에 대해 알려줘", "")
                   .strip()
                  )

        news_results = search_news(keyword)
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
    # 문장부호 제거
    temp_query = re.sub(r'[^\w\s]', '', temp_query)
    keyword = (temp_query
               .replace("뉴스", "")
               .replace("최신", "")
               .replace("에 대해 알려줘", "")
               .strip()
              )

    news_results = search_news(keyword)
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
    """
    사용자 쿼리에 대해:
    1) 뉴스 관련 키워드("뉴스", "소식", "기사", "보도", "속보", "최신")가 하나라도 들어있으면,
       - '뉴스' 등 불필요 단어를 제거한 뒤 검색어로 네이버 뉴스 검색 (최대 4개).
    2) 그렇지 않으면 ChatGPT(일반 답변)를 생성하여 반환.
    """
    import re
    
    # 1) 사용자 입력을 소문자로 변환
    user_query = request.query
    temp_query = user_query.lower()
    
    # 2) 문장부호(.,!? 등) 제거
    temp_query = re.sub(r'[^\w\s]', '', temp_query)

    # 3) 뉴스 관련 키워드 목록
    news_indicators = ["뉴스", "소식", "기사", "보도", "속보", "최신"]

    # 4) 한 가지라도 들어있으면 뉴스 검색 로직으로 분기
    if any(word in temp_query for word in news_indicators):
        # 불필요 단어들 제거 → 핵심 키워드만 추출
        keyword = (
            temp_query
            .replace("뉴스", "")
            .replace("소식", "")
            .replace("기사", "")
            .replace("보도", "")
            .replace("속보", "")
            .replace("최신", "")
            .replace("에 대해 알려줘", "")
            .strip()
        )

        # 네이버 뉴스 검색
        news_results = search_news(keyword)
        if "items" in news_results:
            # 최대 4개만 추리기
            news_results["items"] = news_results["items"][:4]

        # 포맷팅된 결과 반환
        formatted_results = format_news_results(news_results)
        return {"response": formatted_results}

    # 5) 뉴스 키워드가 없으면 일반 ChatGPT 응답
    return {"response": generate_response(user_query)}

