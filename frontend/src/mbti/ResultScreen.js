import React, { useState } from "react";
import "./ResultScreen.css"; // 스타일링을 위한 CSS 파일 임포트

const ResultScreen = ({ onRestart }) => {
  // 예시 정치 성향과 뉴스 헤드라인
  const politicalTraits = [
    {
        label: "LPAG(사회운동가)",
        description:
          "당신은 사회 정의와 평등을 위한 활동에 적극적이며, 사회적 변화에 대한 열정을 가지고 있습니다.",
        recommendedNewspaper: "한겨레 신문",
        newspaperDescription:
          "한겨레 신문은 사회적 책임과 정의를 중시하며, 사회 운동과 관련된 중요 뉴스를 다루고, 여러 사회적 문제에 대한 대안을 제시해줍니다"
      },
    {
      label: "중도",
      description: "당신은 중도적 성향을 가지고 있습니다. 균형을 중요시하며, 양측의 장점을 결합하려고 노력합니다.",
    },
    {
      label: "보수적",
      description: "당신은 보수적인 성향을 가지고 있습니다. 전통적인 가치와 질서를 유지하며, 정부의 개입을 최소화하려고 합니다.",
    },
  ];

  const newsHeadlines = [
    {
      title: "정부의 새로운 사회적 안전망 정책 발표",
      description: "정부는 사회적 불평등을 해결하기 위한 새로운 정책을 발표했습니다. 이 정책은 많은 사람들에게 도움이 될 것입니다.",
    },
    {
      title: "세금 인상에 대한 논란",
      description: "세금 인상이 경제 성장을 방해할 것이라는 우려가 제기되고 있습니다. 이에 대한 다양한 의견이 존재합니다.",
    },
    {
      title: "기업의 자유로운 경제 활동을 보장해야 한다",
      description: "기업들의 자유로운 경제 활동을 보장하는 법안이 상정되었습니다. 이에 대한 찬반 논쟁이 뜨겁습니다.",
    },
  ];

  // 사용자가 선택한 뉴스 헤드라인
  const [selectedHeadline, setSelectedHeadline] = useState(null);

  // 성향 결정 (이 부분은 실제로는 사용자의 선택에 따라 결정됨)
  const userTrait = politicalTraits[0]; // 예시로 "진보적" 성향을 선택한 경우


  const handleHeadlineClick = (headline) => {
    setSelectedHeadline(headline);
  };

  return (
    <div className="result-container">
      <h1>테스트가 완료되었습니다!</h1>
      <header className="result-header">
        <p className = "header2">당신의 정치 성향은 <strong>{userTrait.label}</strong>입니다.</p>
        <p>당신에게 추천하는 신문은 <strong>{userTrait.recommendedNewspaper}</strong>입니다.</p>
      </header>

      <div className="result-description">
        <p>{userTrait.description}</p>
      </div>

      <div className = "newspaper-description">
        <p>{userTrait.newspaperDescription}</p>
      </div>

      <div className="news-headlines">
        <h3>당신의 성향에 맞는 최신 정치 뉴스 헤드라인:</h3>
        <div className="headlines-list">
          {newsHeadlines.map((news, index) => (
            <div
              key={index}
              className={`headline ${selectedHeadline === news ? "selected" : ""}`}
              onClick={() => handleHeadlineClick(news)}
            >
              <h4>{news.title}</h4>
            </div>
          ))}
        </div>
      </div>

      <div className="result-actions">
        <button className="restart-button" onClick={onRestart}>
          다시 시작하기
        </button>
      </div>
    </div>
  );
};

export default ResultScreen;
