import React from 'react';
import CardProfile from './cardprofile';

const LeftPanel = ({ handleButtonClick }) => (
  <div className="left-panel">
    <CardProfile handleButtonClick={handleButtonClick} />
  </div>
);

export default LeftPanel;
