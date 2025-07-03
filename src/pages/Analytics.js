import React, { useState } from "react";
import "./Analytics.css";

const Analytics = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState("1D");

  const timeframes = ["1H", "1D", "1W", "1M", "3M", "1Y"];

  const marketData = [
    {
      name: "Bitcoin",
      price: 50000,
      change: 2.5,
      volume: "45.2B",
      marketCap: "950B",
    },
    {
      name: "Ethereum",
      price: 3000,
      change: -1.2,
      volume: "28.7B",
      marketCap: "360B",
    },
    {
      name: "Cardano",
      price: 1.6,
      change: 5.8,
      volume: "2.1B",
      marketCap: "52B",
    },
    {
      name: "Solana",
      price: 480,
      change: -3.1,
      volume: "3.8B",
      marketCap: "19B",
    },
    {
      name: "Polkadot",
      price: 30,
      change: 1.7,
      volume: "1.2B",
      marketCap: "32B",
    },
  ];

  const technicalIndicators = [
    { name: "RSI", value: 65, status: "Neutral", color: "#FFA500" },
    { name: "MACD", value: "Bullish", status: "Buy Signal", color: "#4CAF50" },
    {
      name: "Bollinger Bands",
      value: "Upper",
      status: "Overbought",
      color: "#f44336",
    },
    {
      name: "Moving Average",
      value: "50 SMA",
      status: "Support",
      color: "#2196F3",
    },
  ];

  return (
    <div className="analytics">
      <div className="analytics-header">
        <h1>Market Analytics</h1>
        <p>Advanced tools for market analysis and insights</p>
      </div>

      <div className="analytics-controls">
        <div className="timeframe-selector">
          <label>Timeframe:</label>
          <div className="timeframe-buttons">
            {timeframes.map((timeframe) => (
              <button
                key={timeframe}
                className={`timeframe-btn ${
                  selectedTimeframe === timeframe ? "active" : ""
                }`}
                onClick={() => setSelectedTimeframe(timeframe)}
              >
                {timeframe}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="analytics-grid">
        <div className="analytics-card market-overview">
          <h3>Market Overview</h3>
          <div className="market-table">
            <div className="table-header">
              <span>Asset</span>
              <span>Price</span>
              <span>Change</span>
              <span>Volume</span>
              <span>Market Cap</span>
            </div>
            {marketData.map((asset, index) => (
              <div key={index} className="table-row">
                <span className="asset-name">{asset.name}</span>
                <span className="price">${asset.price.toLocaleString()}</span>
                <span
                  className={`change ${
                    asset.change >= 0 ? "positive" : "negative"
                  }`}
                >
                  {asset.change >= 0 ? "+" : ""}
                  {asset.change}%
                </span>
                <span className="volume">{asset.volume}</span>
                <span className="market-cap">{asset.marketCap}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="analytics-card technical-analysis">
          <h3>Technical Indicators</h3>
          <div className="indicators-grid">
            {technicalIndicators.map((indicator, index) => (
              <div key={index} className="indicator-card">
                <div className="indicator-header">
                  <span className="indicator-name">{indicator.name}</span>
                  <span
                    className="indicator-status"
                    style={{ color: indicator.color }}
                  >
                    {indicator.status}
                  </span>
                </div>
                <div className="indicator-value">{indicator.value}</div>
                <div className="indicator-bar">
                  <div
                    className="indicator-fill"
                    style={{
                      backgroundColor: indicator.color,
                      width:
                        indicator.name === "RSI"
                          ? `${indicator.value}%`
                          : "100%",
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="analytics-card price-chart">
          <h3>Price Chart</h3>
          <div className="chart-placeholder">
            <div className="chart-mock">
              <div className="chart-line"></div>
              <div className="chart-points">
                <div className="point"></div>
                <div className="point"></div>
                <div className="point"></div>
                <div className="point"></div>
                <div className="point"></div>
              </div>
            </div>
            <p>Interactive price chart will be displayed here</p>
            <p>Timeframe: {selectedTimeframe}</p>
          </div>
        </div>

        <div className="analytics-card market-sentiment">
          <h3>Market Sentiment</h3>
          <div className="sentiment-indicators">
            <div className="sentiment-item">
              <span className="sentiment-label">Fear & Greed Index</span>
              <div className="sentiment-value">
                <span className="value">65</span>
                <span className="label">Greed</span>
              </div>
            </div>
            <div className="sentiment-item">
              <span className="sentiment-label">Social Sentiment</span>
              <div className="sentiment-value">
                <span className="value">72%</span>
                <span className="label">Bullish</span>
              </div>
            </div>
            <div className="sentiment-item">
              <span className="sentiment-label">Institutional Flow</span>
              <div className="sentiment-value">
                <span className="value">+$2.1B</span>
                <span className="label">Inflow</span>
              </div>
            </div>
          </div>
        </div>

        <div className="analytics-card trading-signals">
          <h3>Trading Signals</h3>
          <div className="signals-list">
            <div className="signal-item buy">
              <div className="signal-icon">📈</div>
              <div className="signal-content">
                <div className="signal-title">Strong Buy - BTC</div>
                <div className="signal-description">
                  Multiple indicators suggest bullish momentum
                </div>
                <div className="signal-time">2 hours ago</div>
              </div>
            </div>
            <div className="signal-item sell">
              <div className="signal-icon">📉</div>
              <div className="signal-content">
                <div className="signal-title">Sell - SOL</div>
                <div className="signal-description">
                  Support level broken, bearish trend forming
                </div>
                <div className="signal-time">4 hours ago</div>
              </div>
            </div>
            <div className="signal-item hold">
              <div className="signal-icon">⏸️</div>
              <div className="signal-content">
                <div className="signal-title">Hold - ETH</div>
                <div className="signal-description">
                  Mixed signals, wait for clearer direction
                </div>
                <div className="signal-time">6 hours ago</div>
              </div>
            </div>
          </div>
        </div>

        <div className="analytics-card news-impact">
          <h3>News Impact Analysis</h3>
          <div className="news-items">
            <div className="news-item positive">
              <div className="news-title">Bitcoin ETF Approval Expected</div>
              <div className="news-impact">+15% potential impact</div>
              <div className="news-time">1 day ago</div>
            </div>
            <div className="news-item negative">
              <div className="news-title">Regulatory Concerns in Asia</div>
              <div className="news-impact">-8% potential impact</div>
              <div className="news-time">2 days ago</div>
            </div>
            <div className="news-item neutral">
              <div className="news-title">Institutional Adoption Growing</div>
              <div className="news-impact">+5% potential impact</div>
              <div className="news-time">3 days ago</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
