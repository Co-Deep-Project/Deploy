import React, { useState, useEffect } from "react";
import "./QuestionScreen.css";
import logo from '../assets/polilogo.png';
import { useNavigate } from 'react-router-dom';

const QuestionScreen = ({ onComplete }) => {
    const navigate = useNavigate();
    const handleHomeClick = () => {
      if (window.confirm("진행 중인 작업이 저장되지 않습니다. 그래도 나가시겠습니까?")) {
        navigate('/'); // 사용자가 '확인'을 클릭하면 홈 페이지로 이동
      }
      // 사용자가 '취소'를 클릭하면 현재 페이지에 머무름
    };
    
  const questions = [
    {
      question: "1. 어느 농민이 '나의 생계가 너무 어려워요'라고 말했어요. 이를 들은 왕은 어떻게 해야 할까요?",
      answers: [
        "농민들이 더 나은 삶을 살 수 있도록, 임금을 올려야 한다고 생각해요.",
        "농민들은 더 열심히 일하고, 자립적으로 생계를 꾸려나가야 한다고 생각해요."
      ],
    },
    {
      question: "2. 사람들이 집을 사고 싶어하지만, 땅값이 너무 비싸요. 이에 대해 왕은 어떻게 해야 할까요?",
      answers: [
        "왕이 땅값을 낮추기 위해 노력하고, 백성들이 집을 쉽게 얻을 수 있도록 해야 한다고 생각해요.",
        "왕은 땅값에 간섭하지 않고, 자연스럽게 시장에 맡겨야 한다고 생각해요."
      ],
    },
    {
      question: "3. 귀족들과 가난한 농민들 사이의 격차가 점점 커지고 있습니다. 이에 대해 왕은 어떻게 해야 할까요?",
      answers: [
        "왕이 귀족들에게 더 많은 세금을 거둬 가난한 농민들을 돕는 데 사용해야 한다고 생각해요.",
        "귀족과 농민 사이의 차이는 자연스러운 것이며, 왕이 이를 따로 조정할 필요는 없다고 생각해요."
      ],
    },
    {
      question: "4. 많은 백성들이 일거리를 찾지 못해 힘들어하고 있습니다. 이에 대해 왕은 어떻게 해야 할까요?",
      answers: [
        "왕이 직접 나서서 농업이나 토목 사업 등을 시작해 백성들에게 일할 기회를 만들어야 한다고 생각해요.",
        "왕은 백성들이 스스로 생업을 찾아 해결하도록 두고, 필요한 최소한의 여건만 마련해야 한다고 생각해요."
      ],
    },
    {
      question: "5. 왕은 상인들을 도와야 할까요?",
      answers: [
        "왕은 상인들의 거래가 공정하게 이루어지도록 관리하고, 국가의 이익을 위해 상인들이 번성할 수 있도록 도와야 해요.",
        "왕은 상인들의 일에 간섭하지 말고, 상인들이 자유롭게 무역을 하고 활동할 수 있도록 해야 돼요."
      ],
    },
    {
      question: "6. 신라, 고구려, 백제가 나뉘어 서로 대립하고 있습니다. 이를 해결하기 위해 왕은 어떻게 해야 할까요?",
      answers: [
        "모든 나라를 하나로 통일하여 백성들이 평화롭게 살 수 있도록 노력해야 해요.",
        "각 나라는 독립적으로 존재해야 하며, 통일을 위해 힘쓸 필요는 없다고 생각해요."
      ],
    },
    {
      question: "7. 신라가 주변국 (당나라)와 군사 동맹을 맺어야 한다는 주장에 대해 왕은 어떻게 해야 할까요?",
      answers: [
        "동맹을 유지하되, 신라가 불리한 조건을 받지 않도록 신중히 접근해야 해요.",
        "당나라와의 동맹을 강화하고, 협력을 통해 나라를 더 안전하게 만들어야 해요."
      ],
    },
    {
      question: "8. 최근 나라의 산림이 자주 훼손되고 있습니다. 왕은 이를 어떻게 해결할까요?",
      answers: [
        "산림 보호는 매우 중요하기 때문에, 이를 위한 강력한 정책을 지금 당장 시행해야 해요.",
        "지나친 규제는 농민들에게 부담을 줄 수 있으므로, 너무 엄격한 규제는 피해야 해요."
      ],
    },
    {
      question: "9. 당나라가 전쟁으로 피폐해지거나, 일본이 가뭄에 시달릴 경우, 어떻게 해야 할까요?",
      answers: [
        "다른 나라가 어려움에 처했을 때, 우리나라가 힘을 합쳐 돕는 것이 중요하므로, 돕는 것이 옳아요.",
        "우리나라 백성들도 어려운 시기이기 때문에, 우리나라에 더 많은 신경을 써야 해요."
      ],
    },
    {
      question: "10. 외적이 나라에 해를 끼쳤을 때, 응징을 해야 할까요?",
      answers: [
        "외적과의 충돌을 피하고, 협상과 대화를 통해 문제를 평화적으로 해결하는 것이 중요해요.",
        "나라의 안전을 지키기 위해서는 외적에 대한 단호한 처벌이 필요해요."
      ],
    },
    {
      question: "11. 지방에 사는 자손들에게 교육 기회를 더 많이 제공해야 할까요?",
      answers: [
        "지방의 자손들도 수도나 큰 고을의 자손들과 똑같이 배워야 합니다. 그러므로 왕이나 관리들은 지방에 사는 자손들에게 더 많은 교육 기회를 제공해야 해요.",
        "지방 자손들에게도 도움이 필요하지만, 수도나 큰 고을의 자손들이 양보하는 것은 역차별이 될 수 있습니다. 지방에 사는 자손들에게 교육 기회를 더 많이 제공하는 것은 옳지 않습니다."
      ],
    },
    {
      question: "12. 엄중한 범죄를 저지른 사람에게는 사형이라는 처벌을 내려도 될까요?",
      answers: [
        "아니요. 범죄자를 교화할 수 있는 인간적인 처벌이 필요해요.",
        "네. 범죄를 막기 위해서는 엄격한 법이 필요해요."
      ],
    },
    {
      question: "13. 엄마가 아기를 낳을지 말지 스스로 결정할 수 있어야 할까요?",
      answers: [
        "네! 엄마가 선택할 수 있어야 해요.",
        "아기도 소중한 생명이기 때문에 낙태는 안돼요."
      ],
    },
    {
      question: "14. 하인의 근무 시간과 왕을 누가 정해야 할까요?",
      answers: [
        "나라가 규제하여 하인들의 권리를 보호하고, 그들의 삶을 보장해야 해요.",
        "주인이 자유롭게 운영할 수 있어야 해요."
      ],
    },
    {
      question: "15. 고려시대에는 왕이 전통적인 혼인 규범을 벗어나 왕족이 아닌 사람이나 외국인과 결혼한 사례가 있을 경우, 이에 대해 어떻게 생각하나요?",
      answers: [
        "결혼은 사랑에 따라 자유롭게 이루어져야 해요.",
        "전통적인 규범을 지키는 것이 중요한 것 같아요.",
      ]
    }
  ];

  const totalQuestions = questions.length;
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [scores, setScores] = useState({
        economicProgressive: 0,
        economicConservative: 0,
        diplomaticProgressive: 0,
        diplomaticConservative: 0,
        socialProgressive: 0,
        socialConservative: 0
    });
    const [answers, setAnswers] = useState(Array(totalQuestions).fill(null)); // 각 질문의 선택값 기록

    
    const handleNext = () => {
      if (selectedAnswer === null) {
          alert("선지를 선택해주세요!");
          return;
      }
  
      // 현재 질문의 점수 유형 계산
      const scoreType = currentQuestion < 5 ? "economic" :
          currentQuestion < 10 ? "diplomatic" : "social";
      const resultType = selectedAnswer === 0 ? "Progressive" : "Conservative";
  
      // 점수 추가
      const newScores = { ...scores };
      newScores[scoreType + resultType] += 1;
  
      setScores(newScores);
  
      // 선택값 기록
      setAnswers((prevAnswers) => {
          const updatedAnswers = [...prevAnswers];
          updatedAnswers[currentQuestion] = selectedAnswer;
          return updatedAnswers;
      });
  
      setSelectedAnswer(null);
  
      if (currentQuestion < totalQuestions - 1) {
          setCurrentQuestion(currentQuestion + 1);
      } else {
          if (window.confirm("테스트가 끝났습니다. 결과를 보러 가시겠습니까?")) {
              handleGoToResults();
          }
      }
  
      console.log("현재 점수 상태:", newScores);

        
  if (currentQuestion === totalQuestions - 1) {
    localStorage.setItem('results', JSON.stringify(newScores));
    setTimeout(() => navigate('/result'), 100); // 저장 후 약간의 지연을 두고 이동
  } else {
    setCurrentQuestion(currentQuestion + 1);
  }

  setSelectedAnswer(null);
  };
  
  const handlePrevious = () => {
    if (currentQuestion > 0) {
        // 이전 질문의 선택값 가져오기
        const prevAnswer = answers[currentQuestion - 1];
        if (prevAnswer !== null) {
            // 이전 질문의 점수 유형 계산
            const scoreType = currentQuestion - 1 < 5 ? "economic" :
                currentQuestion - 1 < 10 ? "diplomatic" : "social";
            const resultType = prevAnswer === 0 ? "Progressive" : "Conservative";

            // 점수 차감
            const newScores = { ...scores };
            newScores[scoreType + resultType] -= 1;

            setScores(newScores);

            console.log(`질문 ${currentQuestion}의 선택이 점수에서 제거되었습니다.`);
            console.log("현재 점수 상태:", newScores);
        }

        // 이전 질문의 선택값 초기화
        setAnswers((prevAnswers) => {
            const updatedAnswers = [...prevAnswers];
            updatedAnswers[currentQuestion - 1] = null; // 이전 선택 제거
            return updatedAnswers;
        });

        setSelectedAnswer(null);
        setCurrentQuestion(currentQuestion - 1);
    }
};

    const handleAnswerClick = (index) => {
        setSelectedAnswer(index);
    };

    const handleGoToResults = () => {
        console.log("Result before saving:", scores);
        localStorage.setItem('results', JSON.stringify(scores));
        onComplete && onComplete(); // onComplete이 함수로 정의되어 있을 때만 호출
        navigate('/result'); // 결과 페이지로 이동
    };

    return (
      <>
        <div className="question-header">
          <div className="logo-container">
            <img src={logo} alt="PoliTracker Logo" onClick={handleHomeClick} className="poliLogo" />
          </div>
          <div className="menu">
            <button onClick={handleHomeClick} className = "home-button">Home</button>
          </div>
        </div>
    
        <div className="question-box">
          <>
            <div className="progress-wrapper">
              <p className="progress-text">{currentQuestion + 1} / {totalQuestions}</p>
              <div className="status-bar">
                <div
                  className="status-bar-fill"
                  style={{ width: `${((currentQuestion + 1) / totalQuestions) * 100}%` }}
                ></div>
              </div>
            </div>
            <div className="qBox">
              <h2>{questions[currentQuestion].question}</h2>
            </div>
            <div className="answerBox">
              {questions[currentQuestion].answers.map((answer, index) => (
                <button
                  key={index}
                  className={`answer-button ${selectedAnswer === index ? "selected" : ""}`}
                  onClick={() => handleAnswerClick(index)}
                >
                  {answer}
                </button>
              ))}
            </div>
            <div className="button-container">
              <button
                className="prev-button"
                onClick={handlePrevious}
                disabled={currentQuestion === 0} // 1번에서는 항상 비활성화
              >
                이전
              </button>
              <button className="next-button" onClick={handleNext}>
                다음
              </button>
            </div>
          </>
        </div>
    
        <footer className="footer">
          <p>
            성균관대학교 트래커스꾸
            <br />
            서울특별시 종로구 성균관로 25-2
            <br />
            trackerskku@g.skku.edu
          </p>
        </footer>
      </>
    );
};

export default QuestionScreen;
