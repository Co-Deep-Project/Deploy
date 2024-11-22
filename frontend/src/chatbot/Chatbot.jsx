import React, { useState } from "react";
import "./Chatbot.css";

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]); 
  const [inputValue, setInputValue] = useState(""); 

  const toggleChatbot = () => setIsOpen(!isOpen); 

  const handleSend = async () => {
    console.log("API URL:", `${process.env.REACT_APP_BACKEND_URL}/chatbot`);

    if (inputValue.trim() === "") return;

    const userMessage = { sender: "user", text: inputValue };
    setMessages((prev) => [...prev, userMessage]);

    try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/chatbot`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: inputValue }),
        });
      

        const data = await response.json();
        const botMessage = { sender: "bot", text: data.response };
        setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
        console.error("Error communicating with chatbot:", error);
        const errorMessage = { sender: "bot", text: "서버와의 연결에 문제가 발생했습니다." };
        setMessages((prev) => [...prev, errorMessage]);
    }

    setInputValue(""); 
  };


  return (
    <div className="chatbot-container">
      {!isOpen && (
        <div className="chatbot-button" onClick={toggleChatbot}>
          💬
        </div>
      )}

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
