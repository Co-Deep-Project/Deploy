const RightPanel = ({ handleButtonClick, message }) => (
    <div className="right-panel">
      <div className="category">
        <h3 className="category-title">정책 일관성 평가</h3>
        <div className="category-items">
          
          <div className="circle-container">
            <div className="grey-circle">
              <div className="green-circle"></div>
            </div>
            <span className="circle-text">경제</span>
          </div>
          
          <div className="circle-container">
            <div className="grey-circle">
              <div className="green-circle"></div>
            </div>
            <span className="circle-text">환경</span>
          </div>
          
          <div className="circle-container">
            <div className="grey-circle">
              <div className="green-circle"></div>
            </div>
            <span className="circle-text">문화</span>
          </div>
          
          <div className="circle-container">
            <div className="grey-circle">
              <div className="green-circle"></div>
            </div>
            <span className="circle-text">모두</span>
          </div>
        </div>
        </div>
    
        {/* 액션카드 */}
        <div className="action-cards">
          <button className="btnComplete" onClick={() => handleButtonClick("완료")}>
            <span>01 완료</span>
          </button>
          <button className="btnProgress" onClick={() => handleButtonClick("이행중")}>
            <span>02 이행중</span>
          </button>
          <button className="btnNotProgress" onClick={() => handleButtonClick("이행하지 못한 것")}>
            <span>03 이행하지 못한 것</span>
          </button>
        </div>
    
        {/* 타임라인 */}
        <div className="timeline">
          <h3>공약 이행 타임라인</h3>
          <div className="timeline-container">
            <div className="timeline-line"></div> {/* 가로 라인 */}
            <div className="timeline-item">
              <div className="timeline-marker"></div>
              <p className="timeline-date">20xx.xx.xx</p>
              <p className="timeline-text">당선</p>
            </div>
            <div className="timeline-item">
              <div className="timeline-marker"></div>
              <p className="timeline-date">20xx.xx.xx</p>
              <p className="timeline-text">1번 공약 이행 완료</p>
            </div>
            <div className="timeline-item">
              <div className="timeline-marker"></div>
              <p className="timeline-date">20xx.xx.xx</p>
              <p className="timeline-text">임기 종료</p>
            </div>
          </div>
        </div>
    
        {/* 타임라인 아래에 메시지 표시 */}
        <div className="message">
          {message && <p className="message-text">{message}</p>}
        </div>
      </div>
    );
    
    export default RightPanel;