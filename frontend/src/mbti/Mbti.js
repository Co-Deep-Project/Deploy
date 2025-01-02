import React, { useState } from "react";
import StartScreen from "./StartScreen"; 
import QuestionScreen from "./QuestionScreen"; 
import ResultScreen from "./ResultScreen"; 

const Mbti = () => {
  const [screen, setScreen] = useState("start");

  const handleComplete = () => {
    setScreen("result");
  };

  const handleRestart = () => {
    setScreen("start");
  };

  return (
    <div className="mbti-container">
      {screen === "start" && <StartScreen onNext={() => setScreen("question")} />}
      {screen === "question" && <QuestionScreen onComplete={handleComplete} />}
      {screen === "result" && <ResultScreen onRestart={handleRestart} />}
    </div>
  );
};

export default Mbti;
