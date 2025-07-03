import React from "react";
import "./Header.css";

const Header = () => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="logo">
            <i className="fas fa-chart-line"></i>
            Crypto Trading Dashboard
          </h1>
        </div>
        <div className="header-right">
          <div className="connection-status">
            <span className="status-indicator connected"></span>
            <span>Connected</span>
          </div>
          <div className="user-menu">
            <button className="user-btn">
              <span className="user-avatar">👤</span>
              <span className="user-name">Trader</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
