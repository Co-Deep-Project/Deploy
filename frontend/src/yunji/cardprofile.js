import React from 'react';
import './cardprofile.css';

const CardProfile = () => (
    <div className="card-profile">
      <div className="profile-container">
        <div>
          <h1 className = "profile-name">정문헌</h1>
          <div className = "left">
          <p className = "profile-details">출생: 1966. 서울특별시</p>
          <p className = "profile-details">학력: 고려대학교 대학원 정치학 박사</p>
          <p className = "profile-details">소속: 서울특별시 종로구(구청장)</p>
          <p className = "profile-details">경력: 2022.07~ 제36대 서울특별시 종로구 구청장<br />2021.08 국민의힘 서울특별시당 종로구 당협위원장</p>
        </div>
      </div>
      <div className = "right">
        <img src="https://search.pstatic.net/sunny/?src=https%3A%2F%2Fi.namu.wiki%2Fi%2FibyqO-nOgXG_SOgebV9TqQlj2aCsSe2IH5DJQr6vxZmu9jcC2rm1xbqAFy_WDUvl2NdXYRRWNdNM9IvPwg-TCw.webp&type=sc960_832" 
        alt="Profile Image" className="profile-image"/>
          <div className="button-container">
            <a href="https://blog.naver.com/cmoonhun" target="_blank" className="button">블로그</a>
            <a href="https://www.youtube.com/channel/UCe-M7_274sPEOkd20gYnH4g" target="_blank" className="button">유튜브</a>
          </div>
        </div>
      </div>
    </div>
);

export default CardProfile;
