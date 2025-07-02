import React from "react";
import "./ErrorMessage.css";

const ErrorMessage = ({ onRetry }) => {
  return (
    <div className="error-message">
      <i className="fas fa-exclamation-triangle"></i>
      <p>
        Failed to load cryptocurrency data. Please check your connection and try
        again.
      </p>
      <button className="retry-btn" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
};

export default ErrorMessage;
