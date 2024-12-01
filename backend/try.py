import requests
from bs4 import BeautifulSoup

# 함수 정의: 특정 billId로 웹페이지를 크롤링
def crawl_bill_summary(bill_id):
    # URL 구성
    url = f"https://likms.assembly.go.kr/bill/summaryPopup.do?billId={bill_id}"
    
    # HTTP GET 요청
    response = requests.get(url)
    
    # 요청 성공 여부 확인
    if response.status_code == 200:
        # HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 원하는 div 태그 추출
        divs = soup.find_all('div', class_='textType02 mt30')
        
        # 결과 저장
        results = [div.get_text(strip=True) for div in divs]
        return results
    else:
        print(f"Failed to fetch data for billId {bill_id}, Status Code: {response.status_code}")
        return None

# 테스트 실행
if __name__ == "__main__":
    # 여러 billId 값을 시도
    bill_ids = [
        "PRC_Z2Z1Z0Z3X2L4M0H9A2V6K5R0V7P2H1",  # 샘플 ID
        "PRC_J2K4S1T1R0P7Q1O0P4K8L1J2K3J3H2",  # 추가 ID
        # 더 많은 billId 추가 가능
    ]
    
    for bill_id in bill_ids:
        print(f"Results for billId {bill_id}:")
        results = crawl_bill_summary(bill_id)
        if results:
            for result in results:
                print(result)
        print("-" * 80)
