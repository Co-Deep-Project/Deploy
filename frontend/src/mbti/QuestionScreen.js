import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // useNavigate 추가
import "./QuestionScreen.css";

const QuestionScreen = ({ onComplete }) => {
  // 질문 및 답변 데이터
  const questions = [
    {
      question: "1. 최저임금: 친구가 “나는 최저임금이 너무 낮아서 생활이 힘들어”라고 말했어요. 이에 대해 정부는 어떻게 해야 할까요?",
      answers: [
        "최저임금을 올려서 친구처럼 힘든 사람들이 더 잘 살 수 있도록 해야한다.",
        "최저임금을 조금 올리되, 너무 급격하게 올려서는 안 된다고 생각한다.",
        "친구가 더 열심히 일해서 스스로 돈을 벌도록 해야 한다.",
      ],
    },
    {
      question: "2. 부동산 세제: 사람들이 집을 사고 싶은데 집값이 너무 비싸요. 정부는 어떻게 해야 할까요?",
      answers: [
        "정부가 집값을 낮추려고 노력해야 한다.",
        "정부가 조금 도와주되, 시장에서 자율적으로 해결되도록 해야 한다.",
        "정부는 집값에 개입하지 말고 그대로 두어야 한다.",
      ],
    },
    {
      question: "3. 정부의 시장 개입: 정부가 회사들을 도와야 할까요?",
      answers: [
        "정부가 시장을 잘 관리하고 공정하게 만들어야 한다.",
        "정부가 필요한 때에만 개입하고, 그 외에는 시장에 맡겨야 한다.",
        "정부는 시장에 개입하지 말고 회사들이 자유롭게 운영되도록 해야 한다.",
      ],
    },
    {
      question: "4. 자유무역: 다른 나라와 자유롭게 물건을 사고팔 수 있도록 해야 할까요?",
      answers: [
        "다른 나라와의 거래는 신중하게 진행해야 한다.",
        "다른 나라와 거래하면서도 우리나라를 잘 보호해야 한다.",
        "자유무역을 통해 더 많은 기회를 만들고, 경제를 성장시켜야 한다.",
      ],
    },
    {
      question: "5. 재분배: 부자와 가난한 사람들의 차이를 줄이려면 정부가 어떻게 해야 할까요?",
      answers: [
        "정부가 부자들의 돈을 가난한 사람들에게 나누어줘야 한다.",
        "정부가 가난한 사람에게만 조금 도와주되, 너무 많이 주지 않도록 해야 한다.",
        "정부는 가난한 사람들이 자립할 수 있도록 도와야 한다.",
      ],
    },
    {
      question: "6. 세금 인상: 국가에 세금이 얼마나 더 필요할까요?",
      answers: [
        "세금을 올려서 정부가 더 많은 돈을 갖고 복지와 서비스를 잘 제공해야 한다.",
        "세금을 조금만 올려서 필요한 돈만 모은다면 좋겠다.",
        "세금을 올리지 않고, 다른 방법으로 필요한 돈을 마련하는 게 더 낫다.",
      ],
    },
    {
      question: "7. 경제 성장과 일자리 창출: 많은 사람들이 일자리가 필요해요. 정부는 어떻게 해야 할까요?",
      answers: [
        "정부가 적극적으로 일자리 창출을 위한 프로그램을 만들어야 한다.",
        "정부는 시장이 잘 돌아가게 도와주되, 민간 기업들이 일자리를 만들 수 있도록 지원해야 한다.",
        "정부는 일자리 창출을 민간 기업들이 자유롭게 할 수 있도록 지원해야 하며, 정부는 간섭하지 않아야 한다.",
      ],
    },
  ];

  const totalQuestions = questions.length; // 전체 질문 수
  const [currentQuestion, setCurrentQuestion] = useState(0); // 현재 질문 인덱스
  const [selectedAnswer, setSelectedAnswer] = useState(null); // 선택된 답변

  const handleNext = () => {
    if (currentQuestion < totalQuestions - 1) {
      setCurrentQuestion(currentQuestion + 1); // 다음 질문으로 이동
      setSelectedAnswer(null); // 다음 질문으로 넘어갈 때 선택 초기화
    } else {
      alert("테스트가 끝났습니다!"); // 테스트 종료 알림
      onComplete(); // 부모 컴포넌트로 결과 화면 전환 요청
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1); // 이전 질문으로 이동
      setSelectedAnswer(null); // 이전 질문으로 갈 때 선택 초기화
    }
  };

  const handleAnswerClick = (index) => {
    setSelectedAnswer(index); // 선택된 답변 인덱스 저장
  };

  return (
    <div className="mbti-container">
      <div className="question-box">
        {/* 진행률 표시 */}
        <div className="progress-wrapper">
          <p className="progress-text">
            {currentQuestion + 1} / {totalQuestions}
          </p>
          <div className="status-bar">
            <div
              className="status-bar-fill"
              style={{
                width: `${((currentQuestion + 1) / totalQuestions) * 100}%`,
              }}
            ></div>
          </div>
        </div>

        {/* 질문 */}
        <div className="qBox">
          <h2>{questions[currentQuestion].question}</h2>
        </div>

        {/* 답변 */}
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

        {/* 버튼들 컨테이너 */}
        <div className="button-container">
          {/* 이전 버튼 */}
          <button
            className="next-button"
            onClick={handlePrevious}
            disabled={currentQuestion === 0}
          >
            이전
          </button>

          {/* 다음 버튼 */}
          <button
            className="next-button"
            onClick={handleNext}
            disabled={selectedAnswer === null} // 선택된 답변이 없을 경우 비활성화
          >
            다음
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuestionScreen;