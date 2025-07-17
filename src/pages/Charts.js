import React, { useState } from "react";
import TradingChart from "../components/TradingChart";
import "./Charts.css";

const Charts = () => {
  const [selectedCoin, setSelectedCoin] = useState("bitcoin");
  const [timeframe, setTimeframe] = useState("1D");
  const [chartType, setChartType] = useState("candlestick");
  const [theme, setTheme] = useState("light");
  const [showChart, setShowChart] = useState(true);

  const popularCoins = [
    { id: "bitcoin", name: "Bitcoin", symbol: "BTC" },
    { id: "ethereum", name: "Ethereum", symbol: "ETH" },
    { id: "binancecoin", name: "BNB", symbol: "BNB" },
    { id: "solana", name: "Solana", symbol: "SOL" },
    { id: "cardano", name: "Cardano", symbol: "ADA" },
    { id: "ripple", name: "XRP", symbol: "XRP" },
    { id: "polkadot", name: "Polkadot", symbol: "DOT" },
    { id: "dogecoin", name: "Dogecoin", symbol: "DOGE" },
  ];

  const timeframes = ["1M", "5M", "15M", "1H", "4H", "1D", "1W", "3M", "1Y"];
  const chartTypes = ["candlestick", "line", "area", "bar"];

  const handleCoinChange = (e) => {
    setSelectedCoin(e.target.value);
  };

  const handleTimeframeChange = (timeframe) => {
    setTimeframe(timeframe);
  };

  const handleChartTypeChange = (type) => {
    setChartType(type);
  };

  const handleThemeChange = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const handleChartReady = (chart) => {
    console.log("Chart is ready:", chart);
  };

  return (
    <div className="charts">
      <div className="charts-header">
        <h1>Trading Charts</h1>
        <p>
          Analyze price movements and trading patterns for any cryptocurrency
        </p>
      </div>

      <div className="charts-content">
        <div className="charts-controls">
          <div className="coin-selector">
            <label htmlFor="coin-select">Select Cryptocurrency:</label>
            <select
              id="coin-select"
              value={selectedCoin}
              onChange={handleCoinChange}
              className="coin-select"
            >
              {popularCoins.map((coin) => (
                <option key={coin.id} value={coin.id}>
                  {coin.name} ({coin.symbol})
                </option>
              ))}
            </select>
          </div>

          <div className="timeframe-selector">
            <label>Timeframe:</label>
            <div className="timeframe-buttons">
              {timeframes.map((tf) => (
                <button
                  key={tf}
                  className={`timeframe-btn ${
                    timeframe === tf ? "active" : ""
                  }`}
                  onClick={() => handleTimeframeChange(tf)}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          <div className="chart-type-selector">
            <label>Chart Type:</label>
            <div className="chart-type-buttons">
              {chartTypes.map((type) => (
                <button
                  key={type}
                  className={`chart-type-btn ${
                    chartType === type ? "active" : ""
                  }`}
                  onClick={() => handleChartTypeChange(type)}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="theme-selector">
            <label>Theme:</label>
            <button
              className={`theme-btn ${theme === "dark" ? "active" : ""}`}
              onClick={handleThemeChange}
            >
              {theme === "light" ? "🌙 Dark" : "☀️ Light"}
            </button>
          </div>

          <div className="chart-toggle">
            <label>Chart View:</label>
            <button
              className={`toggle-btn ${showChart ? "active" : ""}`}
              onClick={() => setShowChart(!showChart)}
            >
              {showChart ? "📊 Hide Chart" : "📊 Show Chart"}
            </button>
          </div>
        </div>

        <div className="chart-container">
          <div className="chart-header">
            <h2>
              {popularCoins.find((coin) => coin.id === selectedCoin)?.name} (
              {popularCoins.find((coin) => coin.id === selectedCoin)?.symbol})
            </h2>
            <div className="chart-info">
              <span className="timeframe-display">{timeframe}</span>
              <span className="chart-type-display">
                {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart
              </span>
            </div>
          </div>

          {showChart ? (
            <TradingChart
              coinData={selectedCoin}
              timeframe={timeframe}
              chartType={chartType}
              theme={theme}
              onChartReady={handleChartReady}
            />
          ) : (
            <div className="chart-placeholder">
              <div className="chart-message">
                <div className="chart-icon">📊</div>
                <h3>Chart Coming Soon</h3>
                <p>
                  Interactive {chartType} chart for{" "}
                  {popularCoins.find((coin) => coin.id === selectedCoin)?.name}
                  with {timeframe} timeframe will be displayed here.
                </p>
                <div className="chart-features">
                  <div className="feature">
                    <span className="feature-icon">📈</span>
                    <span>Real-time price data</span>
                  </div>
                  <div className="feature">
                    <span className="feature-icon">🔍</span>
                    <span>Technical indicators</span>
                  </div>
                  <div className="feature">
                    <span className="feature-icon">📱</span>
                    <span>Mobile responsive</span>
                  </div>
                  <div className="feature">
                    <span className="feature-icon">⚡</span>
                    <span>Fast loading</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="chart-actions">
          <button className="action-btn primary" disabled={!showChart}>
            📥 Export Chart
          </button>
          <button className="action-btn secondary" disabled={!showChart}>
            💾 Save Analysis
          </button>
          <button className="action-btn secondary" disabled={!showChart}>
            📤 Share Chart
          </button>
          <button className="action-btn secondary">🔄 Refresh Data</button>
        </div>
      </div>
    </div>
  );
};

export default Charts;
