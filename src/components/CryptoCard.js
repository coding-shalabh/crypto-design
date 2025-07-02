import React from "react";
import "./CryptoCard.css";

const CryptoCard = ({ crypto, currentView }) => {
  const formatPrice = (price) => {
    if (price >= 1) {
      return `$${price.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    } else {
      return `$${price.toLocaleString("en-US", {
        minimumFractionDigits: 6,
        maximumFractionDigits: 6,
      })}`;
    }
  };

  const formatMarketCap = (marketCap) => {
    if (marketCap >= 1e12) {
      return `$${(marketCap / 1e12).toFixed(2)}T`;
    } else if (marketCap >= 1e9) {
      return `$${(marketCap / 1e9).toFixed(2)}B`;
    } else if (marketCap >= 1e6) {
      return `$${(marketCap / 1e6).toFixed(2)}M`;
    } else {
      return `$${marketCap.toLocaleString()}`;
    }
  };

  const formatVolume = (volume) => {
    if (volume >= 1e12) {
      return `$${(volume / 1e12).toFixed(2)}T`;
    } else if (volume >= 1e9) {
      return `$${(volume / 1e9).toFixed(2)}B`;
    } else if (volume >= 1e6) {
      return `$${(volume / 1e6).toFixed(2)}M`;
    } else {
      return `$${volume.toLocaleString()}`;
    }
  };

  const changeClass =
    crypto.price_change_percentage_24h >= 0 ? "positive" : "negative";
  const changeIcon =
    crypto.price_change_percentage_24h >= 0 ? "fa-arrow-up" : "fa-arrow-down";

  return (
    <div
      className={`crypto-card ${currentView === "list" ? "list-view" : ""}`}
      data-crypto-id={crypto.id}
    >
      <div className="crypto-header">
        <div className="crypto-name">
          <div className="crypto-icon">{crypto.symbol.charAt(0)}</div>
          <div>
            <div className="crypto-symbol">{crypto.symbol}</div>
            <div className="crypto-full-name">{crypto.name}</div>
          </div>
        </div>
        <div className="crypto-rank">#{crypto.market_cap_rank}</div>
      </div>

      <div className="crypto-price">{formatPrice(crypto.current_price)}</div>

      <div className={`price-change ${changeClass}`}>
        <i className={`fas ${changeIcon}`}></i>
        {Math.abs(crypto.price_change_percentage_24h).toFixed(2)}%
      </div>

      <div className="crypto-stats">
        <div className="stat-item">
          <span className="stat-label">Market Cap</span>
          <span className="stat-value" data-stat="market-cap">
            {formatMarketCap(crypto.market_cap)}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Volume (24h)</span>
          <span className="stat-value" data-stat="volume">
            {formatVolume(crypto.volume_24h)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default CryptoCard;
