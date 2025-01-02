import React, { useState, useEffect } from "react";
import "./Chatbot.css";

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false); // 챗봇 열림/닫힘 상태
  const [messages, setMessages] = useState([]); // 챗봇 메시지 상태
  const [inputValue, setInputValue] = useState(""); // 채팅 입력 상태
  const [news, setNews] = useState([]); // 뉴스 데이터 상태

  const toggleChatbot = () => setIsOpen(!isOpen); // 챗봇 열기/닫기

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch("http://localhost:8001/search_news", {
          method: "POST",
          headers: {
            "Content-Type": "application/json", // 반드시 JSON 형식으로 설정
          },
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

  // 챗봇 메시지 전송
  const handleSend = async () => {
    if (inputValue.trim() === "") return;

    const userMessage = { sender: "user", text: inputValue };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await fetch("http://localhost:8001/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: inputValue }),
        
      });

      const data = await response.json();
      const botMessage = { sender: "bot", text: data.response };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error communicating with chatbot:", error);
      const errorMessage = { sender: "bot", text: "서버와의 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요." };
      setMessages((prev) => [...prev, errorMessage]);
    }

    setInputValue(""); // 입력 초기화
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
                {message.text}
              </div>
            ))}
          </div>
          <div className="chatbot-input-container">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
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
    </div>
  );
};

export default Chatbot;