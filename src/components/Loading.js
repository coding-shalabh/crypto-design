import React from "react";
import "./Loading.css";

const Loading = () => {
  return (
    <div className="loading">
      <div className="spinner"></div>
      <p>Loading cryptocurrency data...</p>
    </div>
  );
};

export default Loading;
