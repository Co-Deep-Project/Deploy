import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import './RightPanel.css';

const RightPanel = () => {
  const [activeGroup, setActiveGroup] = useState(''); // 드롭다운 선택 상태 추가

  // 데이터 설정: 이행률 범위별 정책 개수
const humanityCultureProgress = [
  { id: "hc-1", range: "0-25%", count: 6 },
  { id: "hc-2", range: "26-50%", count: 6 },
  { id: "hc-3", range: "51-75%", count: 4 },
  { id: "hc-4", range: "76-100%", count: 7 }
];

const worldCultureProgress = [
  { id: "wc-1", range: "0-25%", count: 1 },
  { id: "wc-2", range: "26-50%", count: 1 },
  { id: "wc-3", range: "51-75%", count: 3 },
  { id: "wc-4", range: "76-100%", count: 3 }
];

const futureInnovationProgress = [
  { id: "fi-1", range: "0-25%", count: 3 },
  { id: "fi-2", range: "26-50%", count: 5 },
  { id: "fi-3", range: "51-75%", count: 3 },
  { id: "fi-4", range: "76-100%", count: 3 }
];

const harmonyInclusionProgress = [
  { id: "hi-1", range: "0-25%", count: 3 },
  { id: "hi-2", range: "26-50%", count: 0 },
  { id: "hi-3", range: "51-75%", count: 2 },
  { id: "hi-4", range: "76-100%", count: 8 }
];

  // 드롭다운 선택에 따라 표시할 데이터 설정
  const getCurrentProgressData = () => {
    switch (activeGroup) {
      case '인류문화의 본':
        return humanityCultureProgress;
      case '세계문화의 본':
        return worldCultureProgress;
      case '미래혁신의 본':
        return futureInnovationProgress;
      case '화합포용의 본':
        return harmonyInclusionProgress;
      default:
        return [];
    }
  };

  const handleSelectChange = (e) => {
    setActiveGroup(e.target.value);
  };

  return (
    <div className="right-panel">
      <h3>정책 이행률 평가</h3>
      <select onChange={handleSelectChange} value={activeGroup} className="dropdown">
        <option value="">선택하세요</option>
        <option value="인류문화의 본">인류문화의 본</option>
        <option value="세계문화의 본">세계문화의 본</option>
        <option value="미래혁신의 본">미래혁신의 본</option>
        <option value="화합포용의 본">화합포용의 본</option>
      </select>

      {/* 선택된 그룹에 따라 히스토그램 표시 */}
      {activeGroup && (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={getCurrentProgressData()} layout="horizontal" margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" type="category" />
          <YAxis type="number" domain={[0, 10]} />
          <Tooltip />
          <Bar dataKey="count" fill="#B19CD9" name="정책 개수" />
        </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default RightPanel;
