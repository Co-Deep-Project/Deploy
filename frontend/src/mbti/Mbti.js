import React, { useState } from "react";
import StartScreen from "./StartScreen"; // 시작 화면 컴포넌트
import QuestionScreen from "./QuestionScreen"; // 질문 화면 컴포넌트
import ResultScreen from "./ResultScreen"; // 결과 화면 컴포넌트
import "./Mbti.css";

const Mbti = () => {
  const [screen, setScreen] = useState("start"); // 현재 화면 상태 ("start", "question", 또는 "result")

  const handleComplete = () => {
    setScreen("result"); // 결과 화면으로 전환
  };

  const handleRestart = () => {
    setScreen("start"); // 시작 화면으로 돌아가기
  };

  return (
    <div className="mbti-container">
      {/* 시작 화면 */}
      {screen === "start" && <StartScreen onNext={() => setScreen("question")} />}

      {/* 질문 화면 */}
      {screen === "question" && <QuestionScreen onComplete={handleComplete} />}

      {/* 결과 화면 */}
      {screen === "result" && <ResultScreen onRestart={handleRestart} />}
    </div>
  );
};

export default Mbti;
