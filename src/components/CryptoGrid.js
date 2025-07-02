import React from "react";
import CryptoCard from "./CryptoCard";
import "./CryptoGrid.css";

const CryptoGrid = ({ cryptoData, currentView }) => {
  if (cryptoData.length === 0) {
    return (
      <div className="no-results">
        <i className="fas fa-search"></i>
        <p>No cryptocurrencies found</p>
      </div>
    );
  }

  return (
    <section
      className={`crypto-grid ${currentView === "list" ? "list-view" : ""}`}
    >
      {cryptoData.map((crypto) => (
        <CryptoCard key={crypto.id} crypto={crypto} currentView={currentView} />
      ))}
    </section>
  );
};

export default CryptoGrid;
