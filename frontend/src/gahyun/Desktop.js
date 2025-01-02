import React, {useEffect} from "react";
import { useNavigate } from "react-router-dom";
import "./style.css"; 
import "./styleguide.css";
import arrow1 from "../assets/arrow-1.svg";
import logo from "../assets/polilogo.png"; 

const Desktop = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const textArray = [
      "객관적 정보, 주체적 판단", 
      "청년을 위한 정치 플랫폼"
    ];
    const textContainer = document.getElementById("animated-text");

    if (textContainer) {
      textArray.forEach((line, lineIndex) => {
        line.split("").forEach((letter, letterIndex) => {
          const span = document.createElement("span");
          span.textContent = letter === " " ? "\xa0" : letter;
          span.style.animationDelay = `${(lineIndex * 20 + letterIndex) * 50}ms`;
          span.classList.add("text-animated");
          textContainer.appendChild(span);
        });
        // 줄바꿈을 추가
        if (lineIndex < textArray.length - 1) {
          const br = document.createElement("br");
          textContainer.appendChild(br);
        }
      });
    }
  }, []);

  const navigateToMbti = () => {
    navigate("/mbti"); // Navigate to the MBTI page
  };

  const navigateToSelectRegion = () => {
    navigate("/select-region"); // Navigate to the Select Region page
  };

  const navigateToChatbot = () => {
    navigate("/chatbot");
  };

  return (
    <div className="desktop">
      {/* header section */}
      <div className="landing-page">
        <div className="navigation-bar">
          <div className="POLITRACKER">
            <img
              src={logo}
              alt="POLITRACKER 로고"
              style={{ width: "160px", height: "auto" }}
            />
          </div>
        </div>

        <header className="desktop-header">
          <p id="animated-text" className="p"></p> {/* 애니메이션 텍스트 위치 */}
        </header>
      </div>

      {/* Intro Section */}
      <div className="heading-subheading">
        <p className="div">
          정치가 어렵게 느껴지시나요?
          <br />
          폴리트래커로 중요한 사안과 정보를 한눈에, 쉽게 확인하세요!
        </p>
      </div>

      <div className="overlap-2">
        {/* Cards Section */}
        <div className="card">
          <div className="heading-and-link">
            <div className="heading">
              <div className="label">
                <div className="label-3">
                  나의 정치 성향
                  <br />
                  분석하기
                </div>
              </div>
            </div>
            <br></br>
            <div className="link" onClick={navigateToMbti} style={{ cursor: "pointer" }}>
              <div className="icon">
                <img className="arrow" src={arrow1} alt="Arrow" />
              </div>
              <div className="label-4">Learn more</div>
            </div>
          </div>
        </div>
        <div className="cards-section">
          <div className="card-2">
            <div className="heading-and-link">
              <div className="heading">
                <div className="label">
                  <div className="label-3">
                    우리 지역 정치인
                    <br />
                    트래킹하기
                  </div>
                </div>
              </div>
              <br></br>
              <div className="link" onClick={navigateToSelectRegion} style={{ cursor: "pointer" }}>
                <div className="arrow-wrapper">
                  <img className="arrow" src={arrow1} alt="Arrow 1" />
                </div>
                <div className="label-5">Learn more</div>
              </div>
            </div>
          </div>
        </div>
        <div className="card-3">
          <div className="heading-and-link">
            <div className="heading">
              <div className="label">
                <div className="label-3">
                  정치 용어 및 뉴스
                  <br />
                  물어보기
                </div>
              </div>
            </div>
            <br></br>
            <div className="link" onClick={navigateToChatbot} style={{ cursor: "pointer" }}>
              <div className="arrow-wrapper">
                <img className="arrow" src={arrow1} alt="Arrow" />
              </div>
              <div className="label-6">Learn more</div>
            </div>
          </div>
        </div>
      </div>

      <br />
      <p className="element-trackerskku-g">
        성균관대학교 트래커스꾸
        <br />
        서울특별시 종로구 성균관로 25-2
        <br />
        trackerskku@g.skku.edu
      </p>
    </div>
  );
};

export default Desktop;