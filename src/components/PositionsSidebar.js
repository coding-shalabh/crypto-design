import React from 'react';
import './PositionsSidebar.css';

const PositionsSidebar = ({ 
  positions = {}, 
  currentPrices = {}, 
  onClosePosition, 
  isConnected = false,
  cryptoData = new Map()
}) => {
  const formatNumber = (num) => {
    if (num === null || num === undefined) return '0.00';
    return parseFloat(num).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const calculatePnL = (position, currentPrice) => {
    const entryPrice = position.avg_price || position.entry_price;
    if (!currentPrice || !entryPrice) return { pnl: 0, pnlPercentage: 0 };
    
    let pnl, pnlPercentage;
    
    if (position.direction === 'long') {
      // For long positions: profit when price goes up
      pnl = (currentPrice - entryPrice) * position.amount;
      pnlPercentage = ((currentPrice - entryPrice) / entryPrice) * 100;
    } else {
      // For short positions: profit when price goes down
      pnl = (entryPrice - currentPrice) * position.amount;
      pnlPercentage = ((entryPrice - currentPrice) / entryPrice) * 100;
    }
    
    return { pnl, pnlPercentage };
  };

  const getCurrentPrice = (symbol) => {
    // First try to get from WebSocket price cache
    if (currentPrices[symbol]) {
      return currentPrices[symbol].price;
    }
    
    // Fallback to crypto data
    for (let [id, crypto] of cryptoData) {
      if (crypto.symbol === symbol) {
        return crypto.current_price;
      }
    }
    
    return null;
  };

  const positionsList = Object.entries(positions);

  if (positionsList.length === 0) {
    return (
      <div className="positions-panel">
        <div className="positions-header">
          <h3>Positions</h3>
          <span className="positions-count">No open positions</span>
        </div>
        <div className="positions-content">
          <div className="no-positions">
            <span>No active positions</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="positions-panel">
      <div className="positions-header">
        <h3>Positions</h3>
        <span className="positions-count">{positionsList.length} position{positionsList.length !== 1 ? 's' : ''}</span>
      </div>
      
      <div className="positions-content">
        <div className="positions-grid">
          {positionsList.map(([symbol, position]) => {
            const currentPrice = getCurrentPrice(symbol);
            const { pnl, pnlPercentage } = calculatePnL(position, currentPrice);
            const isLong = position.direction === 'long';
            
            return (
              <div key={symbol} className="position-card">
                <div className="position-header">
                  <div className="position-symbol">
                    <span className="symbol-name">{symbol}</span>
                    <span className={`position-type ${isLong ? 'long' : 'short'}`}>
                      {isLong ? 'LONG' : 'SHORT'}
                    </span>
                  </div>
                  <button
                    className="close-position-btn"
                    onClick={() => onClosePosition(symbol)}
                    disabled={!isConnected}
                    title="Close Position"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="position-details">
                  <div className="position-row">
                    <span className="label">Size:</span>
                    <span className="value">{Math.abs(parseFloat(position.amount) || 0).toFixed(6)}</span>
                  </div>
                  
                  <div className="position-row">
                    <span className="label">Entry Price:</span>
                    <span className="value">${formatNumber(position.avg_price || position.entry_price)}</span>
                  </div>
                  
                  <div className="position-row">
                    <span className="label">Mark Price:</span>
                    <span className="value">${formatNumber(currentPrice)}</span>
                  </div>
                  
                  <div className="position-row">
                    <span className="label">P&L:</span>
                    <span className={`value pnl ${pnl >= 0 ? 'positive' : 'negative'}`}>
                      ${formatNumber(pnl)} ({pnlPercentage >= 0 ? '+' : ''}{(parseFloat(pnlPercentage) || 0).toFixed(2)}%)
                    </span>
                  </div>
                  
                  <div className="position-row">
                    <span className="label">Value:</span>
                    <span className="value">${formatNumber(Math.abs(position.amount * (currentPrice || (position.avg_price || position.entry_price))))}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default PositionsSidebar; 