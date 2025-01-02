import React from 'react';
import { useNavigate } from 'react-router-dom';
import logo from '../assets/polilogo.png';
import './ResultScreen.css'; // CSS 파일을 사용하여 스타일 추가

const ResultScreen = () => {
  const navigate = useNavigate();

  const onRestart = () => {
    navigate('/start'); // "/start" 경로로 네비게이트
  };

  const handleHomeClick = () => {
    if (window.confirm("나가시면 결과가 초기화됩니다. 그래도 나가시겠습니까?")) {
      navigate('/'); // 사용자가 '확인'을 클릭하면 홈 페이지로 이동
    }
    // 사용자가 '취소'를 클릭하면 현재 페이지에 머무름
  };

  const results = JSON.parse(localStorage.getItem('results')) || {
    economicProgressive: 0,
    economicConservative: 0,
    diplomaticProgressive: 0,
    diplomaticConservative: 0,
    socialProgressive: 0,
    socialConservative: 0,
  };
  
  console.log("Retrieved Results:", results);
  const {
    economicProgressive,
    economicConservative,
    diplomaticProgressive,
    diplomaticConservative,
    socialProgressive,
    socialConservative
  } = results;

  const totalProgressive = results.economicProgressive + results.diplomaticProgressive + results.socialProgressive;
  const totalConservative = results.economicConservative + results.diplomaticConservative + results.socialConservative;
  const finalEconomic = economicProgressive > economicConservative ? "진보" : "보수";
  const finalDiplomatic = diplomaticProgressive > diplomaticConservative ? "진보" : "보수";
  const finalSocial = socialProgressive > socialConservative ? "진보" : "보수";
  let character = "세종대왕";
  let image = "/images/세종대왕.jpg";
  let description = [
    
  ];
  if (
    (totalProgressive === 7 && totalConservative === 8) || 
    (totalProgressive === 8 && totalConservative === 7)
  ) {
  character = "세종대왕";
  image = "/images/세종대왕.jpg";
  description = [
"과학과 기술로 경제를 발전시켜야 해!” 경제 개혁을 위해 새로운 방법을 시도해요.",
    "협력이 중요해!” 외교적으로는 평화와 협력을 중시합니다.",
    "전통과 변화를 균형 있게!” 전통을 존중하면서도 변화가 필요하다고 생각해요.",
    "세종대왕은 경제, 외교, 사회 모든 면에서 균형을 이룬 인물이었어요. 당신도 세상을 더 나은 방향으로 이끌 수 있는 균형 잡힌 리더예요!"
  ];
}
  else if (finalEconomic === "진보" && finalDiplomatic === "진보" && finalSocial === "진보") {
    character = "정약용";
    image = "/images/정약용.jpg";
    description = [
      "“백성이 잘 살아야 나라가 잘 산다!” 실용적이고 공정한 경제를 꿈꿔요.",
      "“협력이 중요해!” 외교적으로는 평화와 협력을 중시하며, 군사적 갈등보다는 대화로 문제를 해결하고, 기후 협정에도 적극 참여해요.",
      "“변화는 두렵지 않아!” 모두를 위한 개혁을 지향합니다.",
      "정약용은 혁신적인 실학자로, 백성을 위한 정책과 사회 변화를 꿈꾼 리더예요."
    ];
  } else if (finalEconomic === "보수" && finalDiplomatic === "진보" && finalSocial === "진보") {
    character = "이순신";
    image = "/images/이순신.jpg";
    description = [
      "“국가의 재정을 지키는 것이 중요!” 안정적인 경제를 중시합니다.",
      "“협력은 필요하지만 신중하게!” 군사적 협력은 중요하지만 지나치게 의존하지 않으려고 해요. 기후 협정은 경제적 부담을 고려해 참여해요.",
      "“백성을 위한 정의로운 사회!” 사회의 안정과 정의를 중요하게 생각해요.",
      "이순신은 나라를 지키기 위해 싸운 영웅으로, 안정적이고 정의로운 사회를 꿈꾸었던 인물입니다."
    ];
  } else if (finalEconomic === "진보" && finalDiplomatic === "보수" && finalSocial === "진보") {
    character = "정몽주";
    image = "/images/정몽주.jpg";
    description = [
      "“국민을 위한 경제, 그게 중요해!” 공평한 경제 발전을 꿈꾸고 있어요.",
      "“협력은 하되, 신중하게” 군사적 협력은 필요하지만, 외교적으로 신중함을 중요시해요. 제재보다는 대화가 우선이에요.",
      "“모두에게 평등한 기회!” 사회의 공정함과 평등을 가장 중요하게 생각해요.",
      "정몽주는 조선의 안정과 경제적 발전을 추구했던 인물로, 공정하고 평등한 사회를 꿈꿨습니다."
    ];
  } else if (finalEconomic === "보수" && finalDiplomatic === "보수" && finalSocial === "진보") {
    character = "안중근";
    image = "/images/안중근.jpg";
    description = [
      "“국가 경제를 튼튼하게!” 국가의 재정과 경제 안정에 신경을 씁니다.",
      "“협력을 전략적으로!” 강경한 외교와 전략적 협력을 선호하며, 기후 협정은 신중하게 접근해요.",
      "“모두가 평등한 사회!” 사회적 약자와 정의를 위해 싸우는 사람입니다.",
      "안중근은 독립을 위해 싸우며 강한 외교적 입장과 정의로운 사회를 추구한 인물이에요."
    ];
  } else if (finalEconomic === "진보" && finalDiplomatic === "진보" && finalSocial === "보수") {
    character = "김유신";
    image = "/images/김유신.jpg";
    description = [
      "“경제 발전을 위해 과학과 기술을!” 경제 개혁을 위해 새로운 기술을 도입하는 걸 중요하게 생각해요.",
      "“평화와 협력을 중요시!” 외교적으로는 협력을 중시하는 태도를 취해요.",
      "“전통과 질서를 지키며 변화!” 사회 안정과 전통을 소중히 여깁니다.",
      "김유신은 과학과 기술을 통해 경제를 발전시키고, 평화로운 외교와 전통적인 사회 질서를 유지하려 했던 리더예요."
    ];
  } else if (finalEconomic === "보수" && finalDiplomatic === "진보" && finalSocial === "보수") {
    character = "황희";
    image = "/images/황희.jpg";
    description = [
      "“경제는 안정이 중요!” 경제적으로 효율적이고 안정적인 시스템을 선호해요.",
      "“협력은 하지만, 국가 이익을 우선!” 외교에서 협력을 중시하고, 기후 협정은 경제적 부담을 최소화해야 해요.",
      "“질서와 전통을 중요하게 생각해요!” 사회의 안정과 전통을 중시하는 보수적인 태도를 가집니다.",
      "황희는 안정과 협력을 중시하며, 전통적 가치와 질서를 존중한 명재상이에요."
    ];
  } else if (finalEconomic === "진보" && finalDiplomatic === "보수" && finalSocial === "보수") {
    character = "흥선대원군";
    image = "/images/흥선대원군.jpg";
    description = [
      "“국가 재정을 튼튼히 해야 한다!” 경제적으로 효율성을 중요하게 생각해요.",
      "“협력은 하되, 신중히!” 강경하고 신중한 외교를 선호하며, 기후 협정은 신중하게 참여해요.",
      "“전통과 질서를 지켜야 한다!” 전통적인 사회 구조와 질서를 중시합니다.",
      "흥선대원군은 국가 재정을 안정시키고 외세의 압박에 강하게 맞서며, 전통적인 사회 질서를 중요시했던 인물이에요."
    ];
  } else if (finalEconomic === "보수" && finalDiplomatic === "보수" && finalSocial === "보수") {
    character = "송시열";
    image = "/images/송시열.jpg";
    description = [
      "“경제는 안정적이어야 한다!” 경제적으로 보수적이고 안정적인 시스템을 선호해요.",
      "“협력은 필요하지만, 신중하게!” 강경하고 신중한 외교를 선호하며, 기후 협정에도 신중하게 접근해요.",
      "“전통을 지키는 것이 중요!” 사회 질서와 전통을 우선시합니다.",
      "송시열은 성리학을 기반으로 한 보수적인 경제, 외교, 사회적 입장을 고수한 인물이에요."
    ];
  }
    // 결과가 없을 때 기본값 설정
    if (!character || !image || !description) {
      return (
        <div className="result-screen">
          <h1>결과를 가져오는 데 문제가 발생했습니다.</h1>
          <button onClick={onRestart}>다시 테스트하기</button>
        </div>
      );
    }

  return (
    <div>
    <div className="header">
    <div className="logo-container">
      <img src={logo} alt="PoliTracker Logo" onClick={handleHomeClick} className = "poliLogo" />
    </div>
    <div className="menu">
      <button onClick={handleHomeClick}>Home</button>
    </div>
  </div>
  
  <div className="result-screen">
    <h1>당신의 역사적 인물은 {character}입니다</h1>
    <img src={image} alt={`역사적 인물 ${character}`} className="character-image" />
  
    <div className="description-container">
          <ul>
            {description.map((line, index) => (
              <li key={index}>{line}</li>
            ))}
          </ul>
        </div>
  
    <button className="finishBtn" onClick={onRestart}>다시 테스트하기</button>
  </div>
  <footer className="footer">
        <p>성균관대학교 트래커스꾸<br />서울특별시 종로구 성균관로 25-2<br />trackerskku@g.skku.edu</p>
      </footer>
  </div>
  );
};

export default ResultScreen;
