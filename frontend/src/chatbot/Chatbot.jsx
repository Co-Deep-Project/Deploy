import React, { useState, useEffect } from "react";
import axios from "axios"; // Axios 추가
import "./Chatbot.css";

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false); // 챗봇 열림/닫힘 상태
  const [messages, setMessages] = useState([]); // 챗봇 메시지 상태
  const [inputValue, setInputValue] = useState(""); // 채팅 입력 상태
  const [news, setNews] = useState([]); // 뉴스 데이터 상태

  const toggleChatbot = () => setIsOpen(!isOpen); // 챗봇 열기/닫기

  // 뉴스 데이터를 가져오는 useEffect
  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await axios.post("http://127.0.0.1:5001/news", {
          query: "종로구",
        });
        console.log("Fetched news:", response.data); // Flask에서 반환된 데이터 확인
        setNews(response.data); // uniqueNews가 아니라 response.data를 사용
      } catch (error) {
        console.error("Error fetching news:", error.response || error.message);
      }
    };
  
    fetchNews();
  }, []);  
  

  // 사용자 입력 처리 및 백엔드와 통신
  const handleSend = async () => {
    if (inputValue.trim() === "") return;
  
    const userMessage = { sender: "user", text: inputValue };
    setMessages((prev) => [...prev, userMessage]);
  
    try {
      const response = await axios.post("http://127.0.0.1:5001/chat", {
        message: inputValue,
      });
  
      const botResponse = { sender: "bot", text: response.data.response };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("Error communicating with backend:", error.response || error.message);
      const botResponse = { sender: "bot", text: "서버와 연결할 수 없습니다." };
      setMessages((prev) => [...prev, botResponse]);
    }
  
    setInputValue(""); // 입력창 초기화
  };
  

  return (
    <div className="chatbot-container">
      {/* 뉴스 섹션 */}
      <div className="news-container">
        <h1 className="news-header">최신 뉴스</h1>
        <div className="news-cards">
          {news.map((item, index) => (
            <div key={index} className="news-card">
              <h2 className="news-title">{item.headline}</h2>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="news-button"
              >
                더 보기
              </a>
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