import requests
from bs4 import BeautifulSoup

session = requests.Session()

def get_csrf_token():
    url = "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do?monaCd=FIE6569O&st=22&viewType=CONTBODY&tabId=collabill"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    response = session.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ 받은 쿠키:", session.cookies.get_dict())
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("meta", {"name": "_csrf"})["content"]
        print(f"✅ CSRF 토큰: {csrf_token}")
        return csrf_token
    else:
        raise Exception(f"❌ GET 요청 실패! 상태 코드: {response.status_code}")

def fetch_data():
    url = "https://www.assembly.go.kr/portal/assm/assmPrpl/findCollaPrpsBill.json"
    csrf_token = get_csrf_token()
    
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.assembly.go.kr",
        "Referer": "https://www.assembly.go.kr/portal/assm/assmPrpl/prplMst.do",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-CSRF-TOKEN": csrf_token,
        "X-Requested-With": "XMLHttpRequest"
    }
    
    data = {
        "pageIndex": "1",
        "rowSize": "10",
        "represent": "법률안",
        "monaCd": "FIE6569O",
        "age": "",
        "billName": "",
        "procResultCd": "",
        "searchStartDt": "",
        "searchEndDt": ""
    }
    
    all_data = []
    first_response = session.post(url, headers=headers, data=data)
    
    if first_response.status_code == 200:
        first_result = first_response.json()
        total_pages = first_result["paginationInfo"]["totalPageCount"]
        print(f"총 {total_pages} 페이지를 가져옵니다...")
        
        all_data.extend(first_result["resultList"])
        
        for page in range(2, total_pages + 1):
            print(f"{page} 페이지 가져오는 중...")
            data["pageIndex"] = str(page)
            response = session.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                result = response.json()
                all_data.extend(result["resultList"])
            else:
                print(f"❌ {page} 페이지 요청 실패! 상태 코드: {response.status_code}")
    else:
        print(f"❌ 첫 번째 요청 실패! 상태 코드: {first_response.status_code}")
    

    print(f"{all_data}")
    print(f"✅ 총 {len(all_data)} 건의 데이터를 가져왔습니다.")
    return all_data

if __name__ == "__main__":
    fetch_data()