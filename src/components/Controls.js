import React, { useEffect } from "react";
import "./Controls.css";

const Controls = ({
  searchTerm,
  setSearchTerm,
  currentView,
  setCurrentView,
}) => {
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "k":
            e.preventDefault();
            document.getElementById("search-input")?.focus();
            break;
          case "1":
            e.preventDefault();
            setCurrentView("grid");
            break;
          case "2":
            e.preventDefault();
            setCurrentView("list");
            break;
          default:
            break;
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [setCurrentView]);

  return (
    <section className="controls">
      <div className="search-container">
        <input
          type="text"
          id="search-input"
          placeholder="Search cryptocurrencies..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          aria-label="Search cryptocurrencies"
        />
        <i className="fas fa-search search-icon"></i>
      </div>

      <div className="view-controls">
        <button
          className={`view-btn ${currentView === "grid" ? "active" : ""}`}
          onClick={() => setCurrentView("grid")}
          aria-label="Grid view"
        >
          <i className="fas fa-th"></i>
        </button>
        <button
          className={`view-btn ${currentView === "list" ? "active" : ""}`}
          onClick={() => setCurrentView("list")}
          aria-label="List view"
        >
          <i className="fas fa-list"></i>
        </button>
      </div>
    </section>
  );
};

export default Controls;
