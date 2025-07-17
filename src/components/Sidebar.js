import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  FiBarChart2,
  FiBriefcase,
  FiTrendingUp,
  FiPieChart,
  FiActivity,
  FiFileText,
  FiSettings,
  FiUser,
} from "react-icons/fi";
import "./Sidebar.css";

const Sidebar = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleMobileSidebar = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  const closeMobileSidebar = () => {
    setIsMobileOpen(false);
  };

  const navItems = [
    {
      path: "/",
      name: "Dashboard",
      icon: <FiBarChart2 aria-hidden="true" />,
      description: "Overview of crypto markets",
    },
    {
      path: "/portfolio",
      name: "Portfolio",
      icon: <FiBriefcase aria-hidden="true" />,
      description: "Your crypto holdings",
    },
    {
      path: "/trading",
      name: "Trading",
      icon: <FiTrendingUp aria-hidden="true" />,
      description: "Buy and sell crypto",
    },
    {
      path: "/charts",
      name: "Charts",
      icon: <FiPieChart aria-hidden="true" />,
      description: "Trading charts for any coin",
    },
    {
      path: "/analytics",
      name: "Analytics",
      icon: <FiActivity aria-hidden="true" />,
      description: "Market analysis tools",
    },
    {
      path: "/news",
      name: "News",
      icon: <FiFileText aria-hidden="true" />,
      description: "Latest crypto news",
    },
    {
      path: "/settings",
      name: "Settings",
      icon: <FiSettings aria-hidden="true" />,
      description: "App configuration",
    },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div className="sidebar-overlay" onClick={closeMobileSidebar}></div>
      )}

      {/* Mobile menu button */}
      <button
        className="mobile-menu-btn"
        onClick={toggleMobileSidebar}
        aria-label="Toggle navigation menu"
      >
        <span className="hamburger"></span>
      </button>

      {/* Sidebar */}
      <aside
        className={`sidebar ${isCollapsed ? "collapsed" : ""} ${
          isMobileOpen ? "mobile-open" : ""
        }`}
      >
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon" aria-hidden="true">
              <FiTrendingUp />
            </span>
            {!isCollapsed && <span className="logo-text">CryptoTrader</span>}
          </div>
          <button
            className="collapse-btn"
            onClick={toggleSidebar}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? "→" : "←"}
          </button>
        </div>

        <nav className="sidebar-nav" aria-label="Main navigation">
          <ul className="nav-list">
            {navItems.map((item) => (
              <li key={item.path} className="nav-item">
                                  <span className="nav-icon">{item.icon}</span>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `nav-link ${isActive ? "active" : ""}`
                  }
                  onClick={closeMobileSidebar}
                  title={isCollapsed ? item.description : ""}
                >
                  {!isCollapsed && (
                    <>
                      <span className="nav-text">{item.name}</span>
                      <span className="nav-description">
                        {item.description}
                      </span>
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          {!isCollapsed && (
            <div className="user-info">
              <div className="user-avatar" aria-hidden="true">
                <FiUser />
              </div>
              <div className="user-details">
                <span className="user-name">Trader</span>
                <span className="user-status">Online</span>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
