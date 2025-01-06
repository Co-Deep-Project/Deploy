import sqlite3
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, world!"}


# test.db 파일에 연결
conn = sqlite3.connect('./test.db')
cursor = conn.cursor()

# bills 테이블의 모든 데이터 조회
print("📋 Bills 테이블 데이터:")
cursor.execute("SELECT * FROM bills")
bills_rows = cursor.fetchall()
for row in bills_rows:
    print(row)

#votes 테이블의 모든 데이터 조회
print("\n📋 Votes 테이블 데이터:")
cursor.execute("SELECT * FROM votes")
votes_rows = cursor.fetchall()
for row in votes_rows:
    print(row)

# 연결 닫기
conn.close()