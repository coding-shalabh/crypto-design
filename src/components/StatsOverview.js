import React from "react";
import "./StatsOverview.css";

const StatsOverview = ({ stats }) => {
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

  return (
    <section className="stats-overview">
      <div className="stat-card">
        <h3>Total Market Cap</h3>
        <p>{formatMarketCap(stats.totalMarketCap)}</p>
      </div>
      <div className="stat-card">
        <h3>24h Volume</h3>
        <p>{formatVolume(stats.totalVolume)}</p>
      </div>
      <div className="stat-card">
        <h3>Active Coins</h3>
        <p>{stats.activeCoins}</p>
      </div>
      <div className="stat-card">
        <h3>BTC Dominance</h3>
        <p>{stats.btcDominance.toFixed(2)}%</p>
      </div>
    </section>
  );
};

export default StatsOverview;
