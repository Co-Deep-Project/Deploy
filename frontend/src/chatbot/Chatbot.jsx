import React, { useState, useEffect } from "react";
import "./Chatbot.css";

const Chatbot = () => {
  // 챗봇 초기 안내 멘트
  const initialMessages = [
    { 
      sender: "bot", 
      text: `안녕하세요! 👋 저는 POLITRACKER 챗봇입니다.
  정치 뉴스부터 어려운 정치 용어까지, 정치에 관한 모든 궁금증을 쉽게 설명해드릴게요! 💭
  최신 정치 소식이 궁금하시거나 잘 모르는 정치 용어가 있다면 언제든 편하게 물어보세요. 📚✨`
    }
  ];  
  const [isSending, setIsSending] = useState(false);  // 중복호출 방지
  const [isOpen, setIsOpen] = useState(false); // 챗봇 열림/닫힘 상태
  const [messages, setMessages] = useState(initialMessages); // 챗봇 메시지 상태
  const [inputValue, setInputValue] = useState(""); // 채팅 입력 상태
  const [news, setNews] = useState([]); // 뉴스 데이터 상태

  const toggleChatbot = () => setIsOpen(!isOpen); // 챗봇 열기/닫기

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND2_URL}/search_news`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json", // 반드시 JSON 형식으로 설정
          },
          credentials: 'include',  
          body: JSON.stringify({ query: "종로구" }), // FastAPI에서 기대하는 JSON 형식
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
    
  
    fetchNews();
  }, []);  

  // 챗봇이 응답한 뉴스 데이터의 경우 제목 기준으로 데이터 분리
  const parseChatbotNews = (response) => {
    const items = response.split("제목:").filter((item) => item.trim() !== "");
    return items.map((item) => {
      const [title, link] = item.split("링크:").map((part) => part.trim());
      return { title, link };
    });
  };

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
      
      if (currentInput.includes("뉴스")) {
        const newsItems = parseChatbotNews(chatbotResponse);
        const botMessage = { sender: "bot", newsItems };
        setMessages((prev) => [...prev, botMessage]);
      } else {
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
      {/* 뉴스 섹션 */}
      <div className="news-container">
  <h1 className="news-header">최신 뉴스</h1>
  <div className="news-cards">
    {news.map((item) => (
      <div key={item.id} className="news-card">
        <h2 className="news-title">{item.title}</h2>
        <p className="news-description">{item.description}</p>
        <a href="#!" className="news-button">더 보기</a> {/* 링크 추가 */}
      </div>
    ))}
  </div>
</div>


      {/* 챗봇 버튼 */}
      {!isOpen && (
        <div className="chatbot-button" onClick={toggleChatbot}>
          💬
        </div>
      )}

      {/* 챗봇 창 */}
      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <span>POLITRACKER Chatbot</span>
            <button className="close-button" onClick={toggleChatbot}>
              ✖
            </button>
          </div>
          <div className="chatbot-messages">
            {messages.map((message, index) => (
              <div 
                key={index} 
                className={`chatbot-message ${message.sender === "user" ? "user" : "bot"}`}
              >
                {message.newsItems ? (
                  // 뉴스 데이터가 있을 경우 박스 형태로 렌더링
                  <div className="chatbot-news-cards">
                    {message.newsItems.map((news, i) => (
                      <div key={i} className="chatbot-news-card">
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
                  // 일반 메시지 렌더링
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
                  const currentInput = inputValue; // 현재 입력 값 저장
                  setInputValue(""); // 입력 창 초기화
                  handleSend(currentInput); // 현재 입력 값을 handleSend로 전달
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
    </div>
  );
};

export default Chatbot;