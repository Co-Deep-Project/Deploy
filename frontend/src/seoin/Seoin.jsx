import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./seoin_style.css";

const Seoin = () => {
  const navigate = useNavigate();
  const [votes, setVotes] = useState([]);
  const [bills, setBills] = useState([]);
  const [displayData, setDisplayData] = useState([]);
  const [expanded, setExpanded] = useState({});
  const [activeTab, setActiveTab] = useState("votes");
  const [votesLoading, setVotesLoading] = useState(true); // 의안 투표 로딩 상태
  const [billsLoading, setBillsLoading] = useState(true); // 발의 법률 로딩 상태

  const ITEMS_PER_PAGE = 3;
  const memberName = "곽상언";

  // FastAPI 서버 URL (환경 변수에서 가져옴)
  // const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  

  const fetchVotesFromServer = async () => {
    setVotesLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vote_data?member_name=${memberName}`);
      const data = await response.json();
      setVotes(data);
      if (activeTab === "votes") {
        setDisplayData(data.slice(0, ITEMS_PER_PAGE));
      }
    } catch (error) {
      console.error("서버 요청 오류:", error);
    }
    setVotesLoading(false);
  };
  

  const fetchBillsFromServer = async () => {
    setBillsLoading(true);
    try {
        console.log(`Fetching bills for ${memberName}`); 
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/bills_combined?member_name=${memberName}`);
        const data = await response.json();

        // 최신순 정렬
        const sortedBills = data.sort((a, b) => new Date(b.propose_date) - new Date(a.propose_date));
        setBills(sortedBills);
        if (activeTab === "bills") {
            setDisplayData(sortedBills.slice(0, ITEMS_PER_PAGE));
        }
    } catch (error) {
        console.error("서버 요청 오류:", error);
    }
    setBillsLoading(false);
};

  

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setExpanded({});
    if (tab === "votes") {
      setDisplayData(votes.slice(0, ITEMS_PER_PAGE));
    } else if (tab === "bills") {
      setDisplayData(bills.slice(0, ITEMS_PER_PAGE));
    }
  };

  const loadMore = () => {
    const currentData = activeTab === "votes" ? votes : bills;
    const newDisplayData = currentData.slice(0, displayData.length + ITEMS_PER_PAGE);
    setDisplayData(newDisplayData);
  };

  const toggleExpand = (id) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  useEffect(() => {
    fetchVotesFromServer();
    fetchBillsFromServer();
  }, []);

  const isLoading = activeTab === "votes" ? votesLoading : billsLoading;

  return (
    <div className="desktop">
      <header id="tracking-header">
        <img
          id="logo"
          src="/images/logo.png"
          alt="PoliTracker"
          onClick={() => navigate("/")}
        />
        <div id="button-container">
          <button id="region-button" onClick={() => navigate("/select-region")}>
            구
          </button>
          <button id="home-button" onClick={() => navigate("/")}>
            Home
          </button>
        </div>
      </header>

      <div className="card-profile">
        <div className="profile-container">
          <div className="left">
            <h1 className="profile-name">곽상언</h1>
            <div>
              <p className="profile-details">- 출생: 1971. 11. 18 서울특별시</p>
              <p className="profile-details">- 학력: 서울대학교 법과대학 법학 석사</p>
              <p className="profile-details">- 소속: 대한민국 국회의원</p>
              <p className="profile-details">
                - 경력: <br />
                2024.05~ 제22대 국회의원 (서울 종로구/더불어민주당)
                <br />
                2024.05~ 대법원민주당 원내부대표
              </p>
            </div>
          </div>
          <div className="right">
            <img
              src="https://search.pstatic.net/common?type=b&size=3000&quality=100&direct=true&src=http%3A%2F%2Fsstatic.naver.net%2Fpeople%2FprofileImg%2F3676da74-ffdf-481d-b7ca-a0853d27685b.png"
              alt="Profile Image"
              className="profile-image"
            />
            <div className="button-container">
              <a
                href="https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bjky&x_csa=%7B%22fromUi%22%3A%22kb%22%7D&pkid=1&os=168175&qvt=0&query=%EA%B3%BD%EC%83%81%EC%96%B8%20%EC%84%A0%EA%B1%B0%EC%9D%B4%EB%A0%A5"
                target="_blank"
                className="button"
              >
                선거이력
              </a>
              <a
                href="https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bjky&x_csa=%7B%22fromUi%22%3A%22kb%22%7D&pkid=1&os=168175&qvt=0&query=%EA%B3%BD%EC%83%81%EC%96%B8%20%EC%B5%9C%EA%B7%BC%ED%99%9C%EB%8F%99"
                target="_blank"
                className="button"
              >
                최근활동
              </a>
            </div>
          </div>
        </div>
      </div>

      <main className="main-layout">
        <div className="tab-container">
          <button
            className={`tab-button ${activeTab === "votes" ? "active" : ""}`}
            onClick={() => handleTabChange("votes")}
          >
            의안 투표 추적
          </button>
          <button
            className={`tab-button ${activeTab === "bills" ? "active" : ""}`}
            onClick={() => handleTabChange("bills")}
          >
            발의 법률 추적
          </button>
        </div>

        <div id="process-block" className="process-block">
          {activeTab === "votes" && (
              <div className="legend-container">
                <span className="legend-item legend-approve">찬성</span>
                <span className="legend-item legend-against">반대</span>
                <span className="legend-item legend-abstain">기권</span>
              </div>)
          }
          {isLoading ? (
            <p>데이터를 불러오는 중...</p>
          ) : displayData.length === 0 ? (
            <p>데이터가 없습니다.</p>
          ) : activeTab === "votes" ? (
            displayData.map((vote, index) => {
              const displayNumber = votes.length - index;
              return (
                <div
                  key={index}
                  className={`vote-card ${
                    vote.RESULT_VOTE_MOD === "찬성"
                      ? "approve"
                      : vote.RESULT_VOTE_MOD === "반대"
                      ? "against"
                      : "abstain"
                  }`}
                >
                  <div className="vote-header">
                    <span>{displayNumber}</span>
                    <a 
                        href={vote.BILL_URL} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="tooltip-link"
                      >
                        {vote.BILL_NAME}
                        <span className="tooltip">클릭하면 상세정보로 이동합니다.</span>
                      </a>
                    <button onClick={() => toggleExpand(index)}>
                      {expanded[index] ? "-" : "+"}
                    </button>
                  </div>
                  {expanded[index] && (
                    <div className="vote-details">
                      <p><span className="bold">• 의안 번호 : </span> {vote.BILL_NO}</p>
                      <p><span className="bold">• 의결일자 : </span> {vote.VOTE_DATE}</p>
                      <p><span className="bold">• 소관위원회 : </span> {vote.CURR_COMMITTEE}</p>
                      <p><span className="bold">• 제안이유 및 주요내용 : </span></p>
                      <br />
                      <p
                        dangerouslySetInnerHTML={{
                          __html: vote.DETAILS
                            .replace(/\n{2,3}/g, '\n') // 2~3개의 줄바꿈 -> 1개로 변경
                            .replace(/\n/g, '<br/>'), // 남은 줄바꿈을 <br/>로 변환
                        }}
                      ></p>

                    </div>
                  )}
                </div>
              );
            })
          ) : (
            displayData.map((bill, index) => {
              const displayNumber = bills.length - index; 
              return (
                <div key={index} className="bill-card">
                  <div className="bill-header">
                    <span>{displayNumber}</span>
                    <a 
                      href={bill.bill_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="tooltip-link"
                    >
                      {bill.bill_name}
                      <span className="tooltip">클릭하면 상세정보로 이동합니다.</span>
                    </a>
                    <button onClick={() => toggleExpand(index)}>
                      {expanded[index] ? "-" : "+"}
                    </button>
                  </div>
                  {expanded[index] && (
                    <div className="bill-details">
                      <p><span className="bold">• 제안일자 : </span> {bill.propose_date}</p>
                      <p><span className="bold">• 제안자 : </span> {bill.proposer}</p>
                      {/* <p><span className="bold">• 공동발의자 : </span> {bill.co_proposer}</p>
                      <p><span className="bold">• 의안 번호 : </span> {bill.bill_no}</p> */}
                      <p><span className="bold">• 소관위원회 : </span> {bill.committee}</p>
                      <p><span className="bold">• 제안이유 및 주요내용 : </span></p>
                      <br />
                      <p
                        dangerouslySetInnerHTML={{
                          __html: bill.DETAILS
                            .replace(/\n{2,3}/g, '\n') // 2~3개의 줄바꿈 -> 1개로 변경
                            .replace(/\n/g, '<br/>'), // 남은 줄바꿈을 <br/>로 변환
                        }}
                      ></p>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {displayData.length < (activeTab === "votes" ? votes.length : bills.length) && (
          <button className="load-more" onClick={loadMore}>
            더보기
          </button>
        )}
      </main>

      <footer className="footer">
        <p>성균관대학교 트래커스꾸</p>
        <p>서울특별시 종로구 성균관로 25-2</p>
        <p>trackerskku@g.skku.edu</p>
      </footer>
    </div>
  );
};

export default Seoin;