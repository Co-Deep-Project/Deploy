import React from "react";
import "./StartScreen.css"; // 시작 화면 스타일링
import { motion } from "framer-motion";
import { Typewriter } from "react-simple-typewriter";
import { useNavigate } from "react-router-dom";
import logo from '../assets/polilogo.png';

const StartScreen = () => {
  const navigate = useNavigate(); // 컴포넌트 내부에서 useNavigate 호출

  const onNext = () => {
    navigate('/question'); 
  }

  const handleHomeClick = () => {
    if (window.confirm("진행 중인 작업이 저장되지 않습니다. 그래도 나가시겠습니까?")) {
      navigate('/'); // 사용자가 '확인'을 클릭하면 홈 페이지로 이동
    }
    // 사용자가 '취소'를 클릭하면 현재 페이지에 머무름
  };

  return (
    <div className="start-header">
      <div className="logo-container">
          <img src={logo} alt="PoliTracker Logo" onClick = {handleHomeClick} className="poliLogo" />
      </div>
      <div className="menu">
          <button onClick={handleHomeClick}>Home</button>
      </div>
      <div className="start-screen">
        <div className="content">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1 }}
          >
            <h1 className="start-title">
              {" "}
              <span className="start-highlight">
                <Typewriter
                  words={["정치 성향 테스트에 오신 것을 환영합니다", "Welcome!!"]}
                  loop={Infinity}
                  cursor
                  cursorStyle="|"
                  typeSpeed={70}
                  deleteSpeed={50}
                  delaySpeed={1000}
                />
              </span>
            </h1>
          </motion.div>
          <p className="sub-heading">지금 확인해보세요!</p>
          <button className="start-button" onClick={onNext}>
            시작하기
          </button>
        </div>
      </div>
      <footer className="start-footer">
        <p>성균관대학교 트래커스꾸<br />서울특별시 종로구 성균관로 25-2<br />trackerskku@g.skku.edu</p>
      </footer>
    </div>
  );
};

export default StartScreen;
