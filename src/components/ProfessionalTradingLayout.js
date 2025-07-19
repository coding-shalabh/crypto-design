import React, { useState, useEffect } from 'react';
import { 
  FiTrendingUp, 
  FiTrendingDown, 
  FiBookOpen, 
  FiActivity,
  FiBarChart,
  FiClock,
  FiDollarSign,
  FiTarget,
  FiX,
  FiBarChart2,
  FiMaximize2,
  FiInfo
} from 'react-icons/fi';
import { useWebSocket } from '../contexts/WebSocketContext';
import { usePrices } from '../contexts/PriceContext';
import TradingViewChart from './TradingViewChart';
import TradingBot from './TradingBot';
import './ProfessionalTradingLayout.css';

const ProfessionalTradingLayout = () => {
  const { 
    data, 
    isConnected, 
    sendMessage, 
    executePaperTrade, 
    startBot, 
    stopBot, 
    getBotStatus, 
    updateBotConfig, 
    getBotConfig 
  } = useWebSocket();
  const { 
    selectedSymbol, 
    setSelectedSymbol, 
    getPrice, 
    getPriceData, 
    getPriceChange,
    getFormattedPrice,
    getTopMovers 
  } = usePrices();

  // Trading form state
  const [side, setSide] = useState('BUY');
  const [orderType, setOrderType] = useState('Limit');
  const [price, setPrice] = useState('');
  const [quantity, setQuantity] = useState('');
  const [leverage, setLeverage] = useState('10');
  const [showBotPanel, setShowBotPanel] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);

  // Market data
  const [positions, setPositions] = useState([]);
  const [accountBalance, setAccountBalance] = useState(0);
  const [recentTrades, setRecentTrades] = useState([]);

  const currentPriceData = getPriceData(selectedSymbol);
  const currentPrice = getPrice(selectedSymbol);
  
  // Fallback pricing if no data is available yet
  const fallbackPrice = 50000; // Default BTC price for display

  useEffect(() => {
    if (data && data.positions) {
      setPositions(Object.entries(data.positions).map(([symbol, pos]) => ({
        symbol,
        ...pos
      })));
    }
    
    if (data && data.paper_balance) {
      setAccountBalance(data.paper_balance);
    }
  }, [data]);

  // Update position prices in real-time
  useEffect(() => {
    setPositions(prevPositions => 
      prevPositions.map(position => ({
        ...position,
        current_price: getPrice(position.symbol),
        unrealized_pnl: calculateUnrealizedPnL(position, getPrice(position.symbol))
      }))
    );
  }, [getPrice]);

  // 🔧 FIXED: Update price when order type changes or symbol changes
  useEffect(() => {
    if (orderType === 'Market' && currentPrice) {
      setPrice(currentPrice.toFixed(2));
    }
  }, [orderType, currentPrice, selectedSymbol]);

  const calculateUnrealizedPnL = (position, currentPrice) => {
    if (!currentPrice || !position.entry_price || !position.position_size) return 0;
    
    const priceDiff = currentPrice - position.entry_price;
    const multiplier = position.side === 'LONG' ? 1 : -1;
    return priceDiff * position.position_size * multiplier;
  };

  // 🔧 FIXED: Proper trade execution with correct field names
  const handleTrade = async () => {
    if (!isConnected || isExecuting) {
      alert('Not connected to trading server');
      return;
    }

    if (!quantity || parseFloat(quantity) <= 0) {
      alert('Please enter a valid quantity');
      return;
    }

    if (orderType === 'Limit' && (!price || parseFloat(price) <= 0)) {
      alert('Please enter a valid price for limit orders');
      return;
    }

    const tradeAmount = parseFloat(quantity);
    const tradePrice = orderType === 'Market' ? currentPrice : parseFloat(price);
    
    if (!tradePrice) {
      alert('Could not determine trade price');
      return;
    }

    const tradeValue = tradeAmount * tradePrice;
    const marginRequired = tradeValue * 0.1; // 10% margin

    if (marginRequired > accountBalance) {
      alert(`Insufficient balance! Need $${marginRequired.toFixed(2)} margin, have $${accountBalance.toFixed(2)}`);
      return;
    }

    setIsExecuting(true);

    try {
      // 🔧 FIXED: Use same format as working TradingPanel
      const tradeData = {
        symbol: selectedSymbol,
        direction: side.toLowerCase(), // 'buy' or 'sell'
        amount: tradeAmount,
        order_type: orderType.toLowerCase(), // 'limit' or 'market'
        price: tradePrice,
        strategy: 'manual',
        leverage: parseInt(leverage),
        margin_mode: 'isolated',
        time_in_force: 'GTC',
        post_only: false,
        reduce_only: false,
        hidden: false,
        slippage_tolerance: 1.0
      };

      console.log('🔍 Executing trade with tradeData:', tradeData);
      
      // Use executePaperTrade function like working TradingPanel
      const result = await executePaperTrade(tradeData);
      
      if (result.success) {
        // Reset form
        setQuantity('');
        if (orderType === 'Limit') {
          setPrice('');
        }
        
        // Show success message
        alert(`Trade executed: ${side} ${tradeAmount} ${selectedSymbol.replace('USDT', '')} @ $${tradePrice.toFixed(2)}`);
      } else {
        alert('Trade failed: ' + (result.message || 'Unknown error'));
      }
      
    } catch (error) {
      console.error('Trade execution error:', error);
      alert('Trade execution failed: ' + error.message);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClosePosition = (symbol) => {
    if (sendMessage) {
      sendMessage({
        type: 'close_position',
        symbol: symbol
      });
    }
  };

  // 🔧 FIXED: Use same percentage logic as working TradingPanel
  const handlePercentageClick = (percentage) => {
    if (currentPrice && accountBalance > 0) {
      // Use same logic as TradingPanel: simple percentage of available balance
      const maxQuantity = (accountBalance * percentage / 100) / currentPrice;
      
      console.log('🔍 Percentage button clicked:', {
        percentage,
        currentPrice,
        accountBalance,
        maxQuantity
      });
      
      setQuantity(maxQuantity.toFixed(6));
    }
  };

  // 🔧 NEW: Handle max button
  const handleMaxClick = () => {
    handlePercentageClick(100);
  };

  const formatPrice = (price) => parseFloat(price || 0).toFixed(2);
  const formatPercentage = (value) => `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value || 0);
  };

  return (
    <div className="professional-trading-layout">
      {/* Top Section - 70% height */}
      <div className="top-section">
        {/* Chart Area - 60% width */}
        <div className="chart-area">
          {/* 🔧 NEW: Enhanced chart header with price display */}
          <div className="chart-header">
            <div className="symbol-info">
              <h2>{selectedSymbol}</h2>
              <div className="price-display">
                <span className="current-price">
                  ${getFormattedPrice(selectedSymbol) || formatPrice(fallbackPrice)}
                </span>
                <span className={`price-change ${currentPriceData.price_change_24h >= 0 ? 'positive' : 'negative'}`}>
                  {currentPriceData.price_change_24h >= 0 ? <FiTrendingUp /> : <FiTrendingDown />}
                  {formatPercentage(currentPriceData.price_change_24h)}
                </span>
              </div>
            </div>
            <div className="market-stats">
              <div className="stat">
                <span className="label">24h Volume</span>
                <span className="value">{(currentPriceData.volume_24h / 1e6).toFixed(2)}M</span>
              </div>
              <div className="stat">
                <span className="label">24h High</span>
                <span className="value">${formatPrice(currentPriceData.high_24h)}</span>
              </div>
              <div className="stat">
                <span className="label">24h Low</span>
                <span className="value">${formatPrice(currentPriceData.low_24h)}</span>
              </div>
            </div>
          </div>
          <div className="chart-container">
            <TradingViewChart symbol={selectedSymbol} />
          </div>
        </div>

        {/* Market Data Area - 20% width */}
        <div className="market-data-area">
          {/* Order Book */}
          <div className="order-book-widget">
            <div className="widget-header">
              <h3><FiBookOpen /> Order Book</h3>
            </div>
            <div className="order-book-content">
              <div className="book-header">
                <span>Price (USDT)</span>
                <span>Amount</span>
              </div>
              
              {/* Asks */}
              <div className="asks">
                {[...Array(8)].map((_, i) => {
                  const basePrice = currentPriceData.price || fallbackPrice;
                  return (
                    <div key={i} className="order-row ask">
                      <span className="price">{formatPrice(basePrice + (8-i) * 10)}</span>
                      <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                    </div>
                  );
                })}
              </div>
              
              {/* Current Price */}
              <div className="current-price-row">
                <span className={`price ${currentPriceData.price_change_24h >= 0 ? 'positive' : 'negative'}`}>
                  {formatPrice(currentPriceData.price || fallbackPrice)}
                </span>
              </div>
              
              {/* Bids */}
              <div className="bids">
                {[...Array(8)].map((_, i) => {
                  const basePrice = currentPriceData.price || fallbackPrice;
                  return (
                    <div key={i} className="order-row bid">
                      <span className="price">{formatPrice(basePrice - (i+1) * 10)}</span>
                      <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Recent Trades */}
          <div className="recent-trades-widget">
            <div className="widget-header">
              <h3><FiActivity /> Recent Trades</h3>
            </div>
            <div className="trades-content">
              <div className="trades-header">
                <span>Price</span>
                <span>Amount</span>
                <span>Time</span>
              </div>
              {[...Array(10)].map((_, i) => {
                const basePrice = currentPriceData.price || fallbackPrice;
                return (
                  <div key={i} className={`trade-row ${Math.random() > 0.5 ? 'buy' : 'sell'}`}>
                    <span className="price">{formatPrice(basePrice + (Math.random() - 0.5) * 100)}</span>
                    <span className="amount">{(Math.random() * 5).toFixed(4)}</span>
                    <span className="time">{new Date().toLocaleTimeString().slice(0, 5)}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top Movers */}
          <div className="top-movers-widget">
            <div className="widget-header">
              <h3><FiTrendingUp /> Top Movers</h3>
            </div>
            <div className="movers-content">
              {getTopMovers(5).map((mover, index) => (
                <div 
                  key={index} 
                  className="mover-row"
                  onClick={() => setSelectedSymbol(mover.symbol)}
                >
                  <span className="symbol">BTC</span>
                  <span className={`change ${mover.price_change_24h >= 0 ? 'positive' : 'negative'}`}>
                    {formatPercentage(mover.price_change_24h)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Trading Form Area - 20% width */}
        <div className="trading-form-area">
          <div className="trading-form">
            <div className="form-header">
              <div className="side-toggle">
                <button 
                  className={`side-btn buy ${side === 'BUY' ? 'active' : ''}`}
                  onClick={() => setSide('BUY')}
                >
                  Buy
                </button>
                <button 
                  className={`side-btn sell ${side === 'SELL' ? 'active' : ''}`}
                  onClick={() => setSide('SELL')}
                >
                  Sell
                </button>
              </div>
            </div>

            <div className="order-type-tabs">
              {['Limit', 'Market'].map(type => (
                <button 
                  key={type}
                  className={orderType === type ? 'active' : ''}
                  onClick={() => setOrderType(type)}
                >
                  {type}
                </button>
              ))}
            </div>

            <div className="form-inputs">
              {orderType !== 'Market' && (
                <div className="input-group">
                  <label>Price</label>
                  <input 
                    type="number" 
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="0.00"
                    step="0.01"
                  />
                  <span className="suffix">USDT</span>
                </div>
              )}
              
              <div className="input-group">
                <label>Amount</label>
                <div className="amount-input-wrapper">
                  <input 
                    type="number" 
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="0.00"
                    step="0.000001"
                  />
                  <button
                    type="button"
                    className="max-btn"
                    onClick={handleMaxClick}
                    title="Use maximum available balance"
                  >
                    <FiMaximize2 />
                    Max
                  </button>
                </div>
                <span className="suffix">{selectedSymbol.replace('USDT', '')}</span>
              </div>

              <div className="input-group">
                <label>Leverage</label>
                <select value={leverage} onChange={(e) => setLeverage(e.target.value)}>
                  <option value="1">1x</option>
                  <option value="5">5x</option>
                  <option value="10">10x</option>
                  <option value="20">20x</option>
                  <option value="50">50x</option>
                </select>
              </div>

              {/* 🔧 NEW: Percentage buttons */}
              <div className="percentage-buttons">
                {[25, 50, 75, 100].map(percent => (
                  <button 
                    key={percent} 
                    className="percent-btn"
                    onClick={() => handlePercentageClick(percent)}
                  >
                    {percent}%
                  </button>
                ))}
              </div>

              {/* 🔧 NEW: Trade summary */}
              {quantity && (orderType === 'Market' || price) && (
                <div className="trade-summary">
                  <div className="summary-row">
                    <span>Notional Value:</span>
                    <span>{formatCurrency(parseFloat(quantity) * (orderType === 'Market' ? currentPrice : parseFloat(price)))}</span>
                  </div>
                  <div className="summary-row">
                    <span>Required Margin:</span>
                    <span>{formatCurrency((parseFloat(quantity) * (orderType === 'Market' ? currentPrice : parseFloat(price)) * 0.1))}</span>
                  </div>
                </div>
              )}

              <button 
                className={`trade-btn ${side.toLowerCase()}`}
                onClick={handleTrade}
                disabled={!isConnected || isExecuting || !quantity}
              >
                {isExecuting ? 'Executing...' : `${side} ${selectedSymbol.replace('USDT', '')}`}
              </button>

              <div className="account-info">
                <div className="balance-row">
                  <span>Available Balance</span>
                  <span>{formatCurrency(accountBalance)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section - Positions - 30% height */}
      <div className="bottom-section">
        <div className="positions-panel">
          <div className="panel-header">
            <h3><FiBarChart/> Positions</h3>
            <div className="panel-actions">
              <button 
                className="bot-toggle-btn"
                onClick={() => setShowBotPanel(!showBotPanel)}
              >
                Trading Bot
              </button>
              <button className="close-all-btn">Close All</button>
            </div>
          </div>
          
          <div className="positions-table">
            <div className="table-header">
              <span>Symbol</span>
              <span>Side</span>
              <span>Size</span>
              <span>Entry Price</span>
              <span>Mark Price</span>
              <span>Unrealized PNL</span>
              <span>ROE%</span>
              <span>Margin</span>
              <span>Actions</span>
            </div>
            
            {positions.length > 0 ? positions.map((position, index) => {
              const currentPrice = getPrice(position.symbol);
              const unrealizedPnL = calculateUnrealizedPnL(position, currentPrice);
              const roe = position.margin_used > 0 ? (unrealizedPnL / position.margin_used) * 100 : 0;
              
              return (
                <div key={index} className="position-row">
                  <span className="symbol">{position.symbol}</span>
                  <span className={`side ${position.side?.toLowerCase()}`}>
                    {position.side === 'LONG' ? 'Long' : 'Short'}
                  </span>
                  <span className="size">{position.position_size?.toFixed(4)}</span>
                  <span className="entry-price">${formatPrice(position.entry_price)}</span>
                  <span className="mark-price">${formatPrice(currentPrice)}</span>
                  <span className={`pnl ${unrealizedPnL >= 0 ? 'positive' : 'negative'}`}>
                    {unrealizedPnL >= 0 ? '+' : ''}${unrealizedPnL.toFixed(2)}
                  </span>
                  <span className={`roe ${roe >= 0 ? 'positive' : 'negative'}`}>
                    {roe >= 0 ? '+' : ''}{roe.toFixed(2)}%
                  </span>
                  <span className="margin">${formatPrice(position.margin_used)}</span>
                  <span className="actions">
                    <button 
                      className="close-btn"
                      onClick={() => handleClosePosition(position.symbol)}
                    >
                      <FiX />
                    </button>
                  </span>
                </div>
              );
            }) : (
              <div className="no-positions">
                <p>No open positions</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Floating Trading Bot Panel */}
      {showBotPanel && (
        <div className="floating-bot-panel">
          <div className="bot-panel-header">
            <h3>Trading Bot</h3>
            <button 
              className="close-bot-panel"
              onClick={() => setShowBotPanel(false)}
            >
              <FiX />
            </button>
          </div>
          <TradingBot 
            isConnected={isConnected}
            startBot={startBot}
            stopBot={stopBot}
            getBotStatus={getBotStatus}
            updateBotConfig={updateBotConfig}
            getBotConfig={getBotConfig}
            sendMessage={sendMessage}
            data={data}
          />
        </div>
      )}
    </div>
  );
};

export default ProfessionalTradingLayout;