import React, { useState, useEffect } from 'react';
import { 
  FiTrendingUp, 
  FiTrendingDown, 
  FiDollarSign, 
  FiPercent,
  FiClock,
  FiInfo,
  FiSettings,
  FiRefreshCw,
  FiBookOpen,
  FiActivity,
  FiBarChart
} from 'react-icons/fi';
import { useWebSocket } from '../contexts/WebSocketContext';
import './BinanceTradingPanel.css';

const BinanceTradingPanel = () => {
  const { data, isConnected, sendMessage } = useWebSocket();
  const [currentSymbol, setCurrentSymbol] = useState('BTCUSDT');
  const [side, setSide] = useState('BUY');
  const [orderType, setOrderType] = useState('Limit');
  const [price, setPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [total, setTotal] = useState('');
  const [leverage, setLeverage] = useState('10');
  const [marginType, setMarginType] = useState('Cross');
  
  // Market data
  const [markPrice, setMarkPrice] = useState(0);
  const [indexPrice, setIndexPrice] = useState(0);
  const [fundingRate, setFundingRate] = useState(0.0001);
  const [volume24h, setVolume24h] = useState(0);
  const [priceChange24h, setPriceChange24h] = useState(0);
  
  // Order book data
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [] });
  const [recentTrades, setRecentTrades] = useState([]);
  
  // Account data
  const [accountBalance, setAccountBalance] = useState(0);
  const [positions, setPositions] = useState([]);
  const [openOrders, setOpenOrders] = useState([]);
  
  useEffect(() => {
    if (data && data.crypto_data && Array.isArray(data.crypto_data)) {
      const symbolData = data.crypto_data.find(item => item.symbol === currentSymbol);
      if (symbolData) {
        setMarkPrice(symbolData.price || 0);
        setIndexPrice(symbolData.price || 0);
        setPriceChange24h(symbolData.price_change_24h || 0);
        setVolume24h(symbolData.volume_24h || 0);
        // Set price in the form if not already set
        if (!price && symbolData.price) {
          setPrice(symbolData.price.toString());
        }
      }
    }
    
    if (data && data.positions) {
      setPositions(Object.entries(data.positions).map(([symbol, pos]) => ({
        symbol,
        ...pos
      })));
    }
    
    if (data && data.paper_balance) {
      setAccountBalance(data.paper_balance);
    }
  }, [data, currentSymbol]);

  // Calculate total when price or quantity changes
  useEffect(() => {
    if (price && quantity) {
      const calculatedTotal = (parseFloat(price) * parseFloat(quantity)).toFixed(2);
      setTotal(calculatedTotal);
    }
  }, [price, quantity]);

  const formatPrice = (price) => {
    return parseFloat(price || 0).toFixed(2);
  };

  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatVolume = (volume) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(2)}K`;
    return volume.toFixed(2);
  };

  const handleTrade = () => {
    if (!price || !quantity) {
      alert('Please enter both price and quantity');
      return;
    }

    const tradeData = {
      symbol: currentSymbol,
      side: side.toLowerCase(),
      type: orderType.toLowerCase(),
      quantity: parseFloat(quantity),
      price: parseFloat(price),
      leverage: parseInt(leverage)
    };

    if (sendMessage) {
      sendMessage({
        type: 'execute_trade',
        trade_data: tradeData
      });
    }
  };

  const handlePercentageClick = (percentage) => {
    const percent = parseFloat(percentage.replace('%', '')) / 100;
    const maxQuantity = accountBalance / markPrice; // Simple calculation
    const newQuantity = (maxQuantity * percent).toFixed(6);
    setQuantity(newQuantity);
  };

  const handleClosePosition = (symbol) => {
    if (sendMessage) {
      sendMessage({
        type: 'close_position',
        symbol: symbol
      });
    }
  };

  return (
    <div className="binance-trading-panel">
      {/* Symbol Header */}
      <div className="symbol-header">
        <div className="symbol-info">
          <h2 className="symbol-name">{currentSymbol}</h2>
          <div className="symbol-selector">
            <select 
              value={currentSymbol} 
              onChange={(e) => setCurrentSymbol(e.target.value)}
              className="symbol-dropdown"
            >
              <option value="BTCUSDT">BTC/USDT</option>
              <option value="ETHUSDT">ETH/USDT</option>
              <option value="XRPUSDT">XRP/USDT</option>
              <option value="BNBUSDT">BNB/USDT</option>
              <option value="SOLUSDT">SOL/USDT</option>
            </select>
          </div>
        </div>
        
        <div className="price-info">
          <div className="mark-price">
            <span className="price-value">${formatPrice(markPrice)}</span>
            <span className={`price-change ${priceChange24h >= 0 ? 'positive' : 'negative'}`}>
              {priceChange24h >= 0 ? <FiTrendingUp /> : <FiTrendingDown />}
              {formatPercentage(priceChange24h)}
            </span>
          </div>
          <div className="market-stats">
            <div className="stat-item">
              <span className="stat-label">24h Volume</span>
              <span className="stat-value">{formatVolume(volume24h)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Funding Rate</span>
              <span className="stat-value">{(fundingRate * 100).toFixed(4)}%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="trading-content">
        {/* Left Column - Order Book */}
        <div className="left-column">
          <div className="order-book-section">
            <div className="section-header">
              <h3><FiBookOpen /> Order Book</h3>
              <div className="book-controls">
                <button className="book-precision">0.01</button>
                <FiSettings className="settings-icon" />
              </div>
            </div>
            
            <div className="order-book">
              <div className="book-header">
                <span>Price (USDT)</span>
                <span>Amount (BTC)</span>
                <span>Total</span>
              </div>
              
              {/* Asks (Sell Orders) */}
              <div className="asks">
                {[...Array(8)].map((_, i) => {
                  const depth = Math.random() * 0.8 + 0.1; // Random depth between 0.1 and 0.9
                  return (
                    <div 
                      key={i} 
                      className="order-row ask"
                      style={{ '--depth': depth }}
                    >
                      <span className="price">{formatPrice(markPrice + (8-i) * 10)}</span>
                      <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                      <span className="total">{(Math.random() * 100000).toFixed(0)}</span>
                    </div>
                  );
                })}
              </div>
              
              {/* Current Price */}
              <div className="current-price">
                <span className={`price ${priceChange24h >= 0 ? 'positive' : 'negative'}`}>
                  {formatPrice(markPrice)}
                </span>
                <FiTrendingUp className="trend-icon" />
              </div>
              
              {/* Bids (Buy Orders) */}
              <div className="bids">
                {[...Array(8)].map((_, i) => {
                  const depth = Math.random() * 0.8 + 0.1; // Random depth between 0.1 and 0.9
                  return (
                    <div 
                      key={i} 
                      className="order-row bid"
                      style={{ '--depth': depth }}
                    >
                      <span className="price">{formatPrice(markPrice - (i+1) * 10)}</span>
                      <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                      <span className="total">{(Math.random() * 100000).toFixed(0)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Recent Trades */}
          <div className="recent-trades-section">
            <div className="section-header">
              <h3><FiActivity /> Recent Trades</h3>
            </div>
            <div className="trades-list">
              <div className="trades-header">
                <span>Price</span>
                <span>Amount</span>
                <span>Time</span>
              </div>
              {[...Array(10)].map((_, i) => (
                <div key={i} className={`trade-row ${Math.random() > 0.5 ? 'buy' : 'sell'}`}>
                  <span className="price">{formatPrice(markPrice + (Math.random() - 0.5) * 100)}</span>
                  <span className="amount">{(Math.random() * 5).toFixed(4)}</span>
                  <span className="time">{new Date().toLocaleTimeString().slice(0, 5)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Center Column - Trading Form */}
        <div className="center-column">
          <div className="trading-form">
            {/* Margin Settings */}
            <div className="margin-settings">
              <div className="leverage-selector">
                <label>Leverage</label>
                <div className="leverage-controls">
                  <select value={leverage} onChange={(e) => setLeverage(e.target.value)}>
                    <option value="1">1x</option>
                    <option value="5">5x</option>
                    <option value="10">10x</option>
                    <option value="20">20x</option>
                    <option value="50">50x</option>
                    <option value="100">100x</option>
                  </select>
                  <span className="leverage-display">{leverage}x</span>
                </div>
              </div>
              
              <div className="margin-type">
                <label>Margin</label>
                <div className="margin-toggle">
                  <button 
                    className={marginType === 'Cross' ? 'active' : ''}
                    onClick={() => setMarginType('Cross')}
                  >
                    Cross
                  </button>
                  <button 
                    className={marginType === 'Isolated' ? 'active' : ''}
                    onClick={() => setMarginType('Isolated')}
                  >
                    Isolated
                  </button>
                </div>
              </div>
            </div>

            {/* Order Type Tabs */}
            <div className="order-type-tabs">
              {['Limit', 'Market', 'Stop', 'Stop-Limit', 'Trailing Stop'].map(type => (
                <button 
                  key={type}
                  className={orderType === type ? 'active' : ''}
                  onClick={() => setOrderType(type)}
                >
                  {type}
                </button>
              ))}
            </div>

            {/* Buy/Sell Toggle */}
            <div className="side-toggle">
              <button 
                className={`side-btn buy ${side === 'BUY' ? 'active' : ''}`}
                onClick={() => setSide('BUY')}
              >
                Long / Buy
              </button>
              <button 
                className={`side-btn sell ${side === 'SELL' ? 'active' : ''}`}
                onClick={() => setSide('SELL')}
              >
                Short / Sell
              </button>
            </div>

            {/* Order Form */}
            <div className="order-form">
              {orderType !== 'Market' && (
                <div className="form-group">
                  <label>Price</label>
                  <div className="input-group">
                    <input 
                      type="number" 
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      placeholder="0.00"
                    />
                    <span className="input-suffix">USDT</span>
                  </div>
                </div>
              )}
              
              <div className="form-group">
                <label>Size</label>
                <div className="input-group">
                  <input 
                    type="number" 
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="0.00"
                  />
                  <span className="input-suffix">BTC</span>
                </div>
              </div>

              {/* Percentage Buttons */}
              <div className="percentage-buttons">
                {['25%', '50%', '75%', '100%'].map(percent => (
                  <button 
                    key={percent} 
                    className="percent-btn"
                    onClick={() => handlePercentageClick(percent)}
                  >
                    {percent}
                  </button>
                ))}
              </div>

              <div className="form-group">
                <label>Total</label>
                <div className="input-group">
                  <input 
                    type="number" 
                    value={total}
                    onChange={(e) => setTotal(e.target.value)}
                    placeholder="0.00"
                  />
                  <span className="input-suffix">USDT</span>
                </div>
              </div>

              {/* Advanced Options */}
              <div className="advanced-options">
                <div className="option-row">
                  <input type="checkbox" id="reduce-only" />
                  <label htmlFor="reduce-only">Reduce Only</label>
                </div>
                <div className="option-row">
                  <input type="checkbox" id="post-only" />
                  <label htmlFor="post-only">Post Only</label>
                </div>
              </div>

              {/* Submit Button */}
              <button 
                className={`submit-btn ${side.toLowerCase()}`}
                onClick={handleTrade}
                disabled={!isConnected}
              >
                {side === 'BUY' ? 'Buy/Long' : 'Sell/Short'}
              </button>

              {/* Account Info */}
              <div className="account-info">
                <div className="balance-row">
                  <span>Available Balance</span>
                  <span>{accountBalance.toFixed(2)} USDT</span>
                </div>
                <div className="balance-row">
                  <span>Max Buy/Sell</span>
                  <span>-- BTC</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Positions & Orders */}
        <div className="right-column">
          {/* Positions */}
          <div className="positions-section">
            <div className="section-header">
              <h3><FiBarChart /> Positions</h3>
              <button className="close-all-btn">Close All</button>
            </div>
            
            <div className="positions-table">
              <div className="table-header">
                <span>Symbol</span>
                <span>Size</span>
                <span>Entry Price</span>
                <span>Mark Price</span>
                <span>PNL</span>
                <span>Margin</span>
                <span>Actions</span>
              </div>
              
              {positions.length > 0 ? positions.map((position, index) => (
                <div key={index} className="position-row">
                  <span className="symbol">{position.symbol}</span>
                  <span className={`size ${position.side}`}>
                    {position.side === 'LONG' ? '+' : '-'}{position.position_size}
                  </span>
                  <span className="entry-price">${formatPrice(position.entry_price)}</span>
                  <span className="mark-price">${formatPrice(position.current_price || markPrice)}</span>
                  <span className={`pnl ${position.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                    {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl?.toFixed(2)}
                  </span>
                  <span className="margin">${position.margin_used?.toFixed(2)}</span>
                  <span className="actions">
                    <button 
                      className="close-btn"
                      onClick={() => handleClosePosition(position.symbol)}
                    >
                      Close
                    </button>
                  </span>
                </div>
              )) : (
                <div className="no-positions">
                  <p>No open positions</p>
                </div>
              )}
            </div>
          </div>

          {/* Open Orders */}
          <div className="orders-section">
            <div className="section-header">
              <h3><FiClock /> Open Orders</h3>
              <button className="cancel-all-btn">Cancel All</button>
            </div>
            
            <div className="orders-table">
              <div className="table-header">
                <span>Symbol</span>
                <span>Type</span>
                <span>Side</span>
                <span>Amount</span>
                <span>Price</span>
                <span>Actions</span>
              </div>
              
              <div className="no-orders">
                <p>No open orders</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BinanceTradingPanel;