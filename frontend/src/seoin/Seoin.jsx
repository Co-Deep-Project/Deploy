import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import "./seoin_style.css";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";
import ChartDataLabels from "chartjs-plugin-datalabels";

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

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
  
  const fetchVotesFromServer = async () => {
    setVotesLoading(true);
    try {
      console.log("Fetching votes from:", `${process.env.REACT_APP_BACKEND_URL}/api/vote_data?member_name=${memberName}`);  // URL 확인
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vote_data?member_name=${memberName}`);
      const data = await response.json();
      //console.log("Received vote data:", data); 
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

// 그래프 추가
const groupByCommittee = (bills) => {
  const committeeCount = {};
  bills.forEach((bill) => {
    // 공동발의 법안만 처리
    if (bill.type === "공동발의") {
      const committee = bill.committee || "미분류";
      committeeCount[committee] = (committeeCount[committee] || 0) + 1;
    }
  });
  
  const sortedCommittees = Object.entries(committeeCount).sort(
    (a, b) => b[1] - a[1]
  );

  return Object.fromEntries(sortedCommittees);
};

const prepareChartData = (committeeCount) => {
  const labels = Object.keys(committeeCount);
  const data = Object.values(committeeCount);

  return {
    labels,
    datasets: [
      {
        label: "소관위원회별 공동발의 법안 분포",
        data,
        backgroundColor: [
          "#cfc2e9",
          "#b6a9d4",
          "#8a81a9",
          "#67646c",
          "#3b383e",
          "#9c9c9c",
          "#d3d3d3",
          "#ececec",
          "#7f7f7f",
          "#5a5a5a",
        ],
        hoverOffset: 4,
      },
    ],
  };
};

const CommitteePieChart = ({ bills }) => {
  // useMemo를 사용하여 bills가 변경될 때만 데이터를 다시 계산
  const committeeCount = useMemo(() => groupByCommittee(bills), [bills]);
  const chartData = useMemo(() => prepareChartData(committeeCount), [committeeCount]);

  const [shouldAnimate, setShouldAnimate] = useState(true);

  useEffect(() => {
    setShouldAnimate(true);
    return () => setShouldAnimate(false);
  }, [bills]);

  const options = {
    plugins: {
      legend: {
        display: false, // 범례 표시
        position: "top", // 범례 위치 (top, bottom, left, right)
        labels: {
          boxWidth: 20, // 범례 아이콘 크기
          padding: 10, // 텍스트와 박스 사이 여백
          font: {
            size: 12, // 글씨 크기
          },
        },
      },
      datalabels: {
        color: "#000", // 텍스트 색상
        font: {
          size: 12,
        },
        formatter: (value, context) => {
          const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
          const percentage = ((value / total) * 100).toFixed(1);
          return `${context.chart.data.labels[context.dataIndex]} (${percentage}%)`;
        },
        anchor: "end",
        align: "end",
        offset: 10,
      },
    },
    layout: {
      padding: {
        top: 20, // 위쪽 여백
        bottom: -20, // 아래쪽 여백
      },
    },
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: shouldAnimate ? 800 : 0,
    },
  };  

  return (
    <div style={{ width: "700px", height: "300px", margin: "40px auto" }}>
      <Pie data={chartData} options={options} />
    </div>
  );
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
          {activeTab === "bills" && (
            <div className="chart-container">
              <h2>소관위원회별 공동발의 법안 분포</h2>
              <CommitteePieChart bills={bills} />
            </div>
          )}
          {activeTab === "votes" && (
              <div className="legend-container">
                <span className="legend-item legend-approve">찬성</span>
                <span className="legend-item legend-against">반대</span>
                <span className="legend-item legend-abstain">기권</span>
              </div>)
          } {activeTab === "bills" && (
            <div className="legend-container">
              <span className="legend-item legend-approve">대표발의 의안</span>
              <span className="legend-item legend-against">공동발의 의안</span>
            </div>
          )}
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
                      <p><span className="bold">• 제안이유 및 주요내용 요약: </span></p>
                      <br />
                      <p
                        dangerouslySetInnerHTML={{
                          __html: vote.DETAILS.summary
                            ? vote.DETAILS.summary
                                .replace(/\n{2,3}/g, '\n')
                                .replace(/\n/g, '<br/>')
                            : "내용이 없습니다."
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
                <div
                key={index}
                className={`bill-card ${
                  bill.type === "대표발의" ? "approve" : "against"
                }`}
                >
                  <div className="bill-header">
                    <span>{displayNumber}</span>
                    <a 
                      href={bill.bill_link} 
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
                      <p><span className="bold">• 제안이유 및 주요내용 요약: </span></p>
                      <br />
                      <p
                        dangerouslySetInnerHTML={{
                          __html: (bill.DETAILS?.summary || bill.SUMMARY)  // 두 가지 경우 모두 처리
                            ? (bill.DETAILS?.summary || bill.SUMMARY)
                                .replace(/\n{2,3}/g, '\n')
                                .replace(/\n/g, '<br/>')
                            : "요약 정보를 불러오는 중 오류가 발생했습니다."
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