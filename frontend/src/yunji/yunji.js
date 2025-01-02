import React, { useState, useEffect } from 'react';
import './yunji.css';
import logo from './assets/polilogo.png';
import LeftPanel from './LeftPanel';
import RightPanel from './RightPanel';
import { useNavigate } from 'react-router-dom';

const Yunji = () => {
  const [message, setMessage] = useState(''); // 메시지 상태
  const [isMobileView, setIsMobileView] = useState(window.innerWidth < 767);
  const navigate = useNavigate();

  const handleButtonClick = (text) => {
    setMessage(text); // 선택된 텍스트 상태 업데이트
  };

  const handleResize = () => {
    setIsMobileView(window.innerWidth < 767);
  };

  const handleHomeClick = () => {
    navigate('/'); // "/" 경로로 이동
  };
  const handlePositionClick = () => {
    navigate('/select-region'); // "/" 경로로 이동
  };
  const handlePoliticianClick = () => {
    navigate('/'); // "/" 경로로 이동
  };

  useEffect(() => {
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div className="app">
      <div className="yunji-header">
        <div className="logo-container">
          <img src={logo} alt="PoliTracker Logo" className="poliLogo" onClick={handleHomeClick}/>
        </div>
        <div className="menu">
            <button
                  id="region-button"
                  onClick={() => {
                    navigate("/select-region", { replace: true });
                  }}
            >
            구 다시 선택하기</button> {/* onClick 이벤트 추가 */}
          <button onClick={handlePoliticianClick}>정치인</button> {/* onClick 이벤트 추가 */}
          <button onClick={handleHomeClick}>Home</button> {/* onClick 이벤트 추가 */}
        </div>
      </div>
      
      <div className={`main-content ${isMobileView ? "stacked" : "side-by-side"}`}>
        <LeftPanel handleButtonClick={handleButtonClick} />
        <RightPanel handleButtonClick={handleButtonClick} message={message} />
      </div>
      <footer className="footer">
        <p>성균관대학교 트래커스꾸<br />서울특별시 종로구 성균관로 25-2<br />trackerskku@g.skku.edu</p>
      </footer>
    </div>
  );
};

export default Yunji;
