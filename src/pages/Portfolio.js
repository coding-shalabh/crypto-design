import React, { useState } from "react";
import "./Portfolio.css";

const Portfolio = () => {
  const [portfolioData] = useState([
    {
      id: 1,
      symbol: "BTC",
      name: "Bitcoin",
      amount: 0.5,
      value: 25000,
      change24h: 2.5,
      allocation: 40,
    },
    {
      id: 2,
      symbol: "ETH",
      name: "Ethereum",
      amount: 3.2,
      value: 15000,
      change24h: -1.2,
      allocation: 24,
    },
    {
      id: 3,
      symbol: "ADA",
      name: "Cardano",
      amount: 5000,
      value: 8000,
      change24h: 5.8,
      allocation: 13,
    },
    {
      id: 4,
      symbol: "SOL",
      name: "Solana",
      amount: 25,
      value: 12000,
      change24h: -3.1,
      allocation: 19,
    },
    {
      id: 5,
      symbol: "DOT",
      name: "Polkadot",
      amount: 100,
      value: 3000,
      change24h: 1.7,
      allocation: 4,
    },
  ]);

  const totalValue = portfolioData.reduce((sum, asset) => sum + asset.value, 0);
  const totalChange24h = portfolioData.reduce(
    (sum, asset) => sum + (asset.value * asset.change24h) / 100,
    0
  );

  return (
    <div className="portfolio">
      <div className="portfolio-header">
        <h1>My Portfolio</h1>
        <p>Track your cryptocurrency investments</p>
      </div>

      <div className="portfolio-overview">
        <div className="portfolio-card total-value">
          <h3>Total Portfolio Value</h3>
          <div className="value">${totalValue.toLocaleString()}</div>
          <div
            className={`change ${
              totalChange24h >= 0 ? "positive" : "negative"
            }`}
          >
            {totalChange24h >= 0 ? "+" : ""}
            {totalChange24h.toFixed(2)}% (24h)
          </div>
        </div>

        <div className="portfolio-card total-assets">
          <h3>Total Assets</h3>
          <div className="value">{portfolioData.length}</div>
          <div className="subtitle">Cryptocurrencies</div>
        </div>

        <div className="portfolio-card best-performer">
          <h3>Best Performer</h3>
          <div className="value">ADA</div>
          <div className="change positive">+5.8%</div>
        </div>
      </div>

      <div className="portfolio-assets">
        <h2>Your Assets</h2>
        <div className="assets-table">
          <div className="table-header">
            <div className="header-cell">Asset</div>
            <div className="header-cell">Amount</div>
            <div className="header-cell">Value</div>
            <div className="header-cell">24h Change</div>
            <div className="header-cell">Allocation</div>
          </div>

          {portfolioData.map((asset) => (
            <div key={asset.id} className="table-row">
              <div className="cell asset-info">
                <div className="asset-symbol">{asset.symbol}</div>
                <div className="asset-name">{asset.name}</div>
              </div>
              <div className="cell amount">{asset.amount.toLocaleString()}</div>
              <div className="cell value">${asset.value.toLocaleString()}</div>
              <div
                className={`cell change ${
                  asset.change24h >= 0 ? "positive" : "negative"
                }`}
              >
                {asset.change24h >= 0 ? "+" : ""}
                {asset.change24h}%
              </div>
              <div className="cell allocation">
                <div className="allocation-bar">
                  <div
                    className="allocation-fill"
                    style={{ width: `${asset.allocation}%` }}
                  ></div>
                </div>
                <span>{asset.allocation}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="portfolio-actions">
        <button className="btn btn-primary">Add Asset</button>
        <button className="btn btn-secondary">Export Portfolio</button>
        <button className="btn btn-outline">View History</button>
      </div>
    </div>
  );
};

export default Portfolio;
