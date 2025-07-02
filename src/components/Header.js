import React from "react";
import "./Header.css";

const Header = ({ connectionStatus = "connecting" }) => {
  const getStatusText = (status) => {
    switch (status) {
      case "connected":
        return "Connected";
      case "disconnected":
        return "Disconnected";
      default:
        return "Connecting...";
    }
  };

  return (
    <header className="header">
      <div className="container">
        <h1 className="logo">
          <i className="fas fa-chart-line"></i>
          Crypto Trading Dashboard
        </h1>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus}`}></span>
          <span>{getStatusText(connectionStatus)}</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
