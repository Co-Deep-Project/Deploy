import React, { useState, useEffect, useRef } from "react";
import "./Chatbot.css";
import { useNavigate } from 'react-router-dom';

const Chatbot = () => {
  const navigate = useNavigate();
  const initialMessages = [
    { 
      sender: "bot", 
      text: `안녕하세요! 👋 저는 POLITRACKER 챗봇입니다.
  정치 뉴스부터 어려운 정치 용어까지, 정치에 관한 모든 궁금증을 쉽게 설명해드릴게요! 💭
  최신 정치 소식이 궁금하시거나 잘 모르는 정치 용어가 있다면 언제든 편하게 물어보세요. 📚✨`
    }
  ];

  const [isSending, setIsSending] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [news, setNews] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState("종로구");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedNewsUrl, setSelectedNewsUrl] = useState("");
  const [position, setPosition] = useState({ 
    x: typeof window !== 'undefined' ? window.innerWidth - 420 : 0, 
    y: typeof window !== 'undefined' ? window.innerHeight - 590 : 0 
  });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const chatbotRef = useRef(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  //const [showTooltip, setShowTooltip] = useState(false);
  const [isFullscreenModal, setIsFullscreenModal] = useState(false);

  // 모바일 체크
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      setPosition({
        x: mobile ? 0 : window.innerWidth - 420,
        y: mobile ? window.innerHeight - 100 : window.innerHeight - 590
      });
    };
    
    window.addEventListener("resize", handleResize);
    handleResize(); // 초기 실행
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // 드래그 시작
  const handleMouseDown = (e) => {
    if (e.target.closest('.chatbot-messages') || e.target.closest('.chatbot-input-container')) {
      return;
    }
    setIsDragging(true);
    const chatbotRect = chatbotRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - chatbotRect.left,
      y: e.clientY - chatbotRect.top
    });
  };

  // 드래그 중
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    let newX = e.clientX - dragOffset.x;
    let newY = e.clientY - dragOffset.y;
    
    // 화면 경계 체크
    const maxX = window.innerWidth - chatbotRef.current.offsetWidth;
    const maxY = window.innerHeight - chatbotRef.current.offsetHeight;
    
    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));
    
    setPosition({ x: newX, y: newY });
  };

  // 드래그 종료
  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);

  const toggleChatbot = () => {
    setIsOpen(!isOpen);
    if (isOpen) {
      setIsFullscreenModal(false); // 챗봇이 열릴 때 전체 모달 해제
    }
  };

  // 모달 열기
  const openModal = (url) => {
    setSelectedNewsUrl(url);
    setIsModalOpen(true);
    setIsFullscreenModal(true);
  };

  // 모달 닫기
  const closeModal = (e) => {
    // x 버튼을 클릭한 경우에만 모달 닫기
    if (e && e.target.className === 'modal-close-button') {
      setSelectedNewsUrl("");
      setIsModalOpen(false);
      setIsFullscreenModal(false);
    }
  };

  const fetchNews = async (district) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND2_URL}/search_news`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: 'include',  
        body: JSON.stringify({ query: district }), // 선택된 구를 쿼리로 사용
      });
    
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    
      const data = await response.json();
      console.log("Fetched news data:", data); // 응답 확인
      setNews(data.response); // FastAPI가 반환하는 데이터 처리
    } catch (error) {
      console.error("Error fetching news:", error.message);
      setNews([]); // 에러 발생 시 빈 배열로 초기화
    }
  };

  // 선택된 구가 변경될 때마다 fetchNews 호출
  useEffect(() => {
    fetchNews(selectedDistrict);
  }, [selectedDistrict]); // selectedDistrict가 변경될 때마다 실행

  // 챗봇이 응답한 뉴스 데이터의 경우 제목 기준으로 데이터 분리
  const parseChatbotNews = (response) => {
    const items = response.split("제목:").filter((item) => item.trim() !== "");
    return items.map((item) => {
      const [title, link] = item.split("링크:").map((part) => part.trim());
      return { title, link };
    });
  };

  const newsKeywords = ["뉴스", "소식", "기사", "보도", "속보", "최신"];

  // 챗봇 메시지 전송
  const handleSend = async () => {
    if (inputValue.trim() === "") return;
    
    // 이미 전송 중이면 중복 전송 방지
    if (isSending) return;

    try {
      setIsSending(true); // 전송 시작
      
      const userMessage = { sender: "user", text: inputValue };
      setMessages((prev) => [...prev, userMessage]);
      
      const currentInput = inputValue; // 현재 입력값 저장
      setInputValue(""); // 입력 초기화를 먼저 수행
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND2_URL}/chatbot`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        credentials: 'include',
        body: JSON.stringify({ query: inputValue }),
      });
  
      
      const data = await response.json();
      const chatbotResponse = data.response;

      if (newsKeywords.some((word) => currentInput.toLowerCase().includes(word))) {
        const newsItems = parseChatbotNews(chatbotResponse);
        const botMessage = { sender: "bot", newsItems };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        // 뉴스 키워드가 없을 때만 일반 메시지 추가
        const botMessage = { sender: "bot", text: chatbotResponse };
        setMessages((prev) => [...prev, botMessage]);
      }

    } catch (error) {
      console.error("Error communicating with chatbot:", error);
      const errorMessage = {
        sender: "bot",
        text: "서버와의 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false); // 전송 완료
    }
  };

  return (
    <div className="chatbot-container">
      <header id="tracking-header">
        <img id="logo" src="/images/logo.png" alt="PoliTracker" onClick={() => navigate("/")} />
        <div id="button-container">
          <button id="home-button" onClick={() => navigate("/")}>Home</button>
        </div>
      </header>
  
      <div className="news-container">
        <div className="news-header-container">
          <h1 className="news-header">최신 뉴스</h1>
          <select
            value={selectedDistrict}
            onChange={(e) => setSelectedDistrict(e.target.value)}
            className="district-dropdown"
          >
            {[
              "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구",
              "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구",
              "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구",
              "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
            ].map((district) => (
              <option key={district} value={district}>
                {district}
              </option>
            ))}
          </select>
        </div>
        <div className="news-cards">
          {news.map((item) => (
            <div key={item.id} className="news-card">
              <h2 className="news-title">{item.title}</h2>
              <p className="news-description">{item.description}</p>
              <button className="news-button" onClick={() => openModal(item.link)}>
                더 보기
              </button>
            </div>
          ))}
        </div>
      </div>
  
      {!isOpen && (
        <div 
          className="chatbot-button" 
          onClick={toggleChatbot}
          style={isMobile && isModalOpen ? { bottom: '32%' } : undefined}
        >
          💬
        </div>
      )}
  
      {isOpen && (
        <div
          ref={chatbotRef}
          className={`chatbot-window ${isDragging ? 'dragging' : ''} ${isMobile && isModalOpen ? 'mobile-modal-open' : ''}`}
          // 크롬에서 transform 쓰면 창 아예 안뜨는 에러남 -> position 이용
          style={isMobile && isModalOpen ? {} : {
            top: `${position.y}px`,
            left: `${position.x}px`,
            transition: isDragging ? "none" : "top 0.3s ease, left 0.3s ease"
          }}
          onMouseDown={handleMouseDown}
        >
          <div className="chatbot-header">
            <span>POLITRACKER Chatbot</span>
            <button className="close-button" onClick={() => setIsOpen(false)}>✖</button>
          </div>
          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`chatbot-message ${message.sender === "user" ? "user" : "bot"}`}
              >
                {message.newsItems ? (
                  <div className="chatbot-news-cards">
                    {message.newsItems.map((news, i) => (
                      <div key={news.link} className="chatbot-news-card">
                        <h2 className="chatbot-news-title">{news.title}</h2>
                        <a
                          href={news.link}
                          className="chatbot-news-link"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          더 보기
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div>{message.text}</div>
                )}
              </div>
            ))}
          </div>
          <div className="chatbot-input-container">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.repeat) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="메시지를 입력하세요..."
              className="chatbot-input"
            />
            <button onClick={handleSend} className="send-button">
              전송
            </button>
          </div>
        </div>
      )}
  
      {/* 모달은 한 번만 렌더링 */}
      {isModalOpen && (
        <div 
          className={`modal-overlay ${isMobile ? (isFullscreenModal ? 'mobile-fullscreen' : 'mobile-modal') : ''}`}
          onClick={(e) => {
            // overlay를 클릭했을 때도 모달이 닫히지 않도록 수정
            e.stopPropagation();
          }}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-button" onClick={closeModal}></button>
            <iframe src={selectedNewsUrl} className="modal-iframe" title="뉴스 보기"></iframe>
          </div>
        </div>
      )}
    </div>
  );
      }

export default Chatbot;