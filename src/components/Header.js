import React, { useState } from "react";
import "./Header.css";
import { useAuth } from '../contexts/AuthContext';

const Header = () => {
  const { user, logout } = useAuth();
  const [showDropdown, setShowDropdown] = useState(false);

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

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
            <button 
              className="user-btn"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <span className="user-avatar">👤</span>
              <span className="user-name">{user?.username || 'Trader'}</span>
            </button>
            {showDropdown && (
              <div className="user-dropdown">
                <div className="user-info">
                  <div className="user-details">
                    <strong>{user?.username}</strong>
                    <small>{user?.email}</small>
                  </div>
                  <div className="user-balance">
                    Balance: ${user?.portfolio_balance?.toFixed(2) || '0.00'}
                  </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
