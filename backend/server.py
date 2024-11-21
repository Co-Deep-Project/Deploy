import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .chatbot_data import search_news, generate_response, format_news_results

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