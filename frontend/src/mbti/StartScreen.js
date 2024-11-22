import React from "react";
import "./StartScreen.css"; // 시작 화면 스타일링
const StartScreen = ({ onNext }) => {
  return (
    <div className="start-screen">
      <div className="content">
        <h2 className="main-heading">당신의 정치 성향은?</h2>
        <p className="sub-heading">지금 확인해보세요!</p>
        <button className="start-button" onClick={onNext}>
          시작하기
        </button>
      </div>
    </div>
  );
};

export default StartScreen;