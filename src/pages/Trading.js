import React, { useState } from "react";
import "./Trading.css";

const Trading = () => {
  const [activeTab, setActiveTab] = useState("buy");
  const [selectedCrypto, setSelectedCrypto] = useState("BTC");
  const [amount, setAmount] = useState("");
  const [orderType, setOrderType] = useState("market");

  const cryptoOptions = [
    { symbol: "BTC", name: "Bitcoin", price: 50000 },
    { symbol: "ETH", name: "Ethereum", price: 3000 },
    { symbol: "ADA", name: "Cardano", price: 1.6 },
    { symbol: "SOL", name: "Solana", price: 480 },
    { symbol: "DOT", name: "Polkadot", price: 30 },
  ];

  const selectedCryptoData = cryptoOptions.find(
    (crypto) => crypto.symbol === selectedCrypto
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    // Handle trading logic here
    console.log(`${activeTab} ${amount} ${selectedCrypto}`);
  };

  return (
    <div className="trading">
      <div className="trading-header">
        <h1>Trading</h1>
        <p>Buy and sell cryptocurrencies</p>
      </div>

      <div className="trading-container">
        <div className="trading-card">
          <div className="trading-tabs">
            <button
              className={`tab ${activeTab === "buy" ? "active" : ""}`}
              onClick={() => setActiveTab("buy")}
            >
              Buy
            </button>
            <button
              className={`tab ${activeTab === "sell" ? "active" : ""}`}
              onClick={() => setActiveTab("sell")}
            >
              Sell
            </button>
          </div>

          <form onSubmit={handleSubmit} className="trading-form">
            <div className="form-group">
              <label htmlFor="crypto">Cryptocurrency</label>
              <select
                id="crypto"
                value={selectedCrypto}
                onChange={(e) => setSelectedCrypto(e.target.value)}
                className="form-control"
              >
                {cryptoOptions.map((crypto) => (
                  <option key={crypto.symbol} value={crypto.symbol}>
                    {crypto.symbol} - {crypto.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="orderType">Order Type</label>
              <select
                id="orderType"
                value={orderType}
                onChange={(e) => setOrderType(e.target.value)}
                className="form-control"
              >
                <option value="market">Market Order</option>
                <option value="limit">Limit Order</option>
                <option value="stop">Stop Order</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="amount">Amount (USD)</label>
              <input
                type="number"
                id="amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="Enter amount in USD"
                className="form-control"
                min="0"
                step="0.01"
              />
            </div>

            {selectedCryptoData && (
              <div className="price-info">
                <div className="current-price">
                  <span>Current Price:</span>
                  <span className="price">
                    ${selectedCryptoData.price.toLocaleString()}
                  </span>
                </div>
                {amount && (
                  <div className="estimated-amount">
                    <span>Estimated {selectedCryptoData.symbol}:</span>
                    <span className="amount">
                      {(parseFloat(amount) / selectedCryptoData.price).toFixed(
                        6
                      )}
                    </span>
                  </div>
                )}
              </div>
            )}

            <button type="submit" className={`btn btn-${activeTab}`}>
              {activeTab === "buy" ? "Buy" : "Sell"} {selectedCrypto}
            </button>
          </form>
        </div>

        <div className="trading-info">
          <div className="info-card">
            <h3>Market Overview</h3>
            <div className="market-stats">
              <div className="stat">
                <span className="label">24h Volume</span>
                <span className="value">$45.2B</span>
              </div>
              <div className="stat">
                <span className="label">Market Cap</span>
                <span className="value">$2.1T</span>
              </div>
              <div className="stat">
                <span className="label">Active Pairs</span>
                <span className="value">1,234</span>
              </div>
            </div>
          </div>

          <div className="info-card">
            <h3>Recent Trades</h3>
            <div className="recent-trades">
              <div className="trade">
                <span className="trade-type buy">BUY</span>
                <span className="trade-amount">0.5 BTC</span>
                <span className="trade-price">$25,000</span>
              </div>
              <div className="trade">
                <span className="trade-type sell">SELL</span>
                <span className="trade-amount">2.1 ETH</span>
                <span className="trade-price">$6,300</span>
              </div>
              <div className="trade">
                <span className="trade-type buy">BUY</span>
                <span className="trade-amount">1000 ADA</span>
                <span className="trade-price">$1,600</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trading;
