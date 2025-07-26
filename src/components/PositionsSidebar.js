import React from 'react';
import './PositionsSidebar.css';
import { FiCircle } from 'react-icons/fi';

// Import Redux hooks for real-time prices
import { 
  usePriceBySymbol, 
  useMultipleSymbolPrices,
  useBinanceConnectionStatus 
} from '../store/hooks';

const PositionsSidebar = ({ 
  positions = {}, 
  currentPrices = {}, 
  onClosePosition, 
  isConnected = false,
  cryptoData = new Map()
}) => {
  // 🔥 NEW: Get real-time prices from Redux store for all position symbols
  const positionSymbols = Object.keys(positions);
  const reduxPrices = useMultipleSymbolPrices(positionSymbols);
  const binanceConnectionStatus = useBinanceConnectionStatus();
  
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

    const pnl = (currentPrice - entryPrice) * position.amount;
    const pnlPercentage = (pnl / (entryPrice * Math.abs(position.amount))) * 100;

    return { pnl, pnlPercentage };
  };

  // 🔥 UPDATED: Get current price using Redux store (with fallbacks)
  const getCurrentPrice = (symbol, position) => {
    // First try Redux real-time price
    if (reduxPrices[symbol] && reduxPrices[symbol].price) {
      return reduxPrices[symbol].price;
    }
    
    // Fallback to currentPrices prop
    if (currentPrices[symbol]) {
      return currentPrices[symbol].price;
    }

    // Fallback to cryptoData
    for (let [id, crypto] of cryptoData) {
      if (crypto.symbol === symbol) {
        return crypto.current_price;
      }
    }

    // Last fallback to entry price
    return position.avg_price || position.entry_price;
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
            const currentPrice = getCurrentPrice(symbol, position);
            const { pnl, pnlPercentage } = calculatePnL(position, currentPrice);
            const isLong = position.direction === 'long';
            
            return (
              <div key={symbol} className="position-card">
                <div className="position-header">
                  <div className="position-symbol">
                    <span className="symbol-name">{symbol}</span>
                    <div className="position-tags">
                      <span className={`position-type ${isLong ? 'long' : 'short'}`}>
                        {isLong ? 'LONG' : 'SHORT'}
                      </span>
                      {(position.bot_trade || position.trade_type === 'bot') && (
                        <span className="ai-tag" title="AI Bot Trade">
                          🤖 AI
                        </span>
                      )}
                    </div>
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
                    <span className="value">
                      ${formatNumber(currentPrice)}
                      {reduxPrices[symbol] && reduxPrices[symbol].price && (
                        <span className="real-time-indicator" title="Real-time price from Binance">
                          <FiCircle style={{color: '#ff4757', fill: '#ff4757'}} size={8} />
                        </span>
                      )}
                    </span>
                  </div>
                  
                  {(position.bot_trade || position.trade_type === 'bot') && (
                    <>
                      {position.leverage && (
                        <div className="position-row">
                          <span className="label">Leverage:</span>
                          <span className="value">{position.leverage}x</span>
                        </div>
                      )}
                      
                      {position.margin_used && (
                        <div className="position-row">
                          <span className="label">Margin Used:</span>
                          <span className="value">${formatNumber(position.margin_used)}</span>
                        </div>
                      )}
                      
                      {(position.stop_loss || position.take_profit) && (
                        <div className="position-row tp-sl-row">
                          <span className="label">TP/SL:</span>
                          <div className="tp-sl-values">
                            {position.take_profit && (
                              <span className="tp-value" title="Take Profit">
                                TP: ${formatNumber(position.take_profit)}
                                {position.old_take_profit && position.old_take_profit !== position.take_profit && (
                                  <span className="old-value" title="Previous TP">
                                    (was ${formatNumber(position.old_take_profit)})
                                  </span>
                                )}
                              </span>
                            )}
                            {position.stop_loss && (
                              <span className="sl-value" title="Stop Loss">
                                SL: ${formatNumber(position.stop_loss)}
                                {position.old_stop_loss && position.old_stop_loss !== position.stop_loss && (
                                  <span className="old-value" title="Previous SL">
                                    (was ${formatNumber(position.old_stop_loss)})
                                  </span>
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </>
                  )}
                  
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