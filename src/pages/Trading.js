import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  FiBarChart2,
  FiInfo, 
  FiTrendingUp, 
  FiTrendingDown,
  FiDollarSign,
  FiActivity,
  FiTarget,
  FiShield,
  FiZap,
  FiClock,
  FiVolume2,
  FiHome
} from 'react-icons/fi';
import { useWebSocket } from "../contexts/WebSocketContext";
import { useCryptoDataBackend } from "../hooks/useCryptoDataBackend";

import TradingViewChart from "../components/TradingViewChart";
import TradingPanel from "../components/TradingPanel";
import PositionsSidebar from "../components/PositionsSidebar";
import TradingBot from "../components/TradingBot";
import AIAnalysis from "../components/AIAnalysis";
import "./Trading.css";
import { useNavigate } from "react-router-dom";

const Trading = () => {
  console.log('🔍 Trading: Page component initialized');
  const navigate = useNavigate();
  const chartRef = useRef(null);
  const [selectedSymbol, setSelectedSymbol] = useState("BTCUSDT");
  console.log('🔍 Trading: Initial selectedSymbol:', selectedSymbol);
  const [currentPrice, setCurrentPrice] = useState(null);
  console.log('🔍 Trading: Initial currentPrice:', currentPrice);
  const [priceChange, setPriceChange] = useState(0);
  console.log('🔍 Trading: Initial priceChange:', priceChange);
  const [currentTimeframe, setCurrentTimeframe] = useState('1');
  console.log('🔍 Trading: Initial currentTimeframe:', currentTimeframe);
  const [activeTab, setActiveTab] = useState('chart'); // 'chart', 'info', 'trading-data', 'ai'
  console.log('🔍 Trading: Initial activeTab:', activeTab);
  const [showAIChat, setShowAIChat] = useState(false);
  console.log('🔍 Trading: Initial showAIChat:', showAIChat);
  const [isChangingSymbol, setIsChangingSymbol] = useState(false);
  console.log('🔍 Trading: Initial isChangingSymbol:', isChangingSymbol);
  const [isChangingTimeframe, setIsChangingTimeframe] = useState(false);
  console.log('🔍 Trading: Initial isChangingTimeframe:', isChangingTimeframe);

  // Use shared WebSocket connection for trading operations
  const {
    isConnected,
    data,
    executePaperTrade,
    startBot,
    stopBot,
    getBotStatus,
    updateBotConfig,
    getPositions,
    closePosition,
    sendMessage
  } = useWebSocket();
  console.log('🔍 Trading: WebSocket context initialized:', { 
    isConnected, 
    dataKeys: Object.keys(data || {}),
    executePaperTrade: !!executePaperTrade,
    startBot: !!startBot,
    stopBot: !!stopBot,
    getBotStatus: !!getBotStatus,
    updateBotConfig: !!updateBotConfig,
    getPositions: !!getPositions,
    closePosition: !!closePosition,
    sendMessage: !!sendMessage
  });

  // Backend crypto data
  const {
    cryptoData
  } = useCryptoDataBackend();
  console.log('🔍 Trading: Crypto data hook initialized:', { 
    cryptoDataSize: cryptoData ? cryptoData.size : 0
  });

  // Request crypto data when component mounts
  useEffect(() => {
    console.log('🔍 Trading: useEffect triggered - requesting crypto data');
    if (isConnected) {
      console.log('🔍 Trading: Requesting crypto data from backend...');
      // The useCryptoDataBackend hook should handle this, but let's make sure
      setTimeout(() => {
        if (isConnected) {
          console.log('🔍 Trading: Ensuring crypto data is loaded...');
        }
      }, 2000);
    } else {
      console.log('🔍 Trading: Not connected, skipping crypto data request');
    }
  }, [isConnected]);


  // Update current price from WebSocket data or crypto data
  useEffect(() => {
    console.log('🔍 Trading: useEffect triggered - updating current price from WebSocket data or crypto data');
    // First try to get from WebSocket price cache
    if (data.price_cache && data.price_cache[selectedSymbol]) {
      const priceData = data.price_cache[selectedSymbol];
      console.log(`🔍 Trading: Updating price from WebSocket for ${selectedSymbol}: ${priceData.price}`);
      setCurrentPrice(priceData.price);
      setPriceChange(priceData.change_24h);
    } else {
      console.log(`🔍 Trading: No WebSocket price data for ${selectedSymbol}, trying crypto data`);
      // Fallback to crypto data - try both full symbol and base symbol
      let crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === selectedSymbol
      );
      
      // If not found, try base symbol (BTC for BTCUSDT)
      if (!crypto) {
        const baseSymbol = selectedSymbol.replace('USDT', '');
        console.log(`🔍 Trading: Trying base symbol ${baseSymbol} for ${selectedSymbol}`);
        crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === baseSymbol
        );
      }
      
      if (crypto) {
        console.log(`🔍 Trading: Updating price from crypto data for ${selectedSymbol}: ${crypto.current_price}`);
        setCurrentPrice(crypto.current_price);
        setPriceChange(crypto.price_change_percentage_24h);
      } else {
        console.log(`🔍 Trading: No price data available for ${selectedSymbol} from WebSocket or crypto data`);
        console.log(`🔍 Trading: Available crypto symbols:`, Array.from(cryptoData.values()).map(c => c.symbol).slice(0, 10));
      }
    }
  }, [data.price_cache, cryptoData, selectedSymbol]);

  // Real-time price updates from WebSocket
  useEffect(() => {
    console.log('🔍 Trading: useEffect triggered - real-time price updates from WebSocket');
    if (data.price_cache && data.price_cache[selectedSymbol]) {
      const priceData = data.price_cache[selectedSymbol];
      // Only update if the price has actually changed
      if (priceData.price !== currentPrice) {
        console.log(`🔍 Trading: Real-time price update for ${selectedSymbol}: ${priceData.price} (was: ${currentPrice})`);
        setCurrentPrice(priceData.price);
        setPriceChange(priceData.change_24h);
      } else {
        console.log(`🔍 Trading: Price unchanged for ${selectedSymbol}: ${priceData.price}`);
      }
    } else {
      console.log(`🔍 Trading: No WebSocket price data available for ${selectedSymbol}`);
    }
  }, [data.price_cache, selectedSymbol, currentPrice]);

  const handlePriceUpdate = (priceData) => {
    console.log('🔍 Trading: handlePriceUpdate called with:', priceData);
    // Update current price from chart
    if (priceData && priceData.currentPrice) {
      console.log(`🔍 Trading: Price update from chart: ${priceData.currentPrice}`);
      setCurrentPrice(priceData.currentPrice);
    }
    if (priceData && typeof priceData.priceChange === 'number') {
      console.log(`🔍 Trading: Price change update from chart: ${priceData.priceChange}%`);
      setPriceChange(priceData.priceChange);
    }
  };

  // Update position markers when positions data changes
  useEffect(() => {
    if (chartRef.current && data.positions) {
      console.log('🔍 Trading: Positions updated, calling updatePositionMarkers on chart');
      chartRef.current.updatePositionMarkers(data.positions);
    }
  }, [data.positions]);

  const handleBotControl = useCallback(async (action, config = {}) => {
    console.log('🔍 Trading: handleBotControl called with action:', action, 'config:', config);
    if (isConnected) {
      console.log('🔍 Trading: Bot control - connected, executing action');
      try {
        switch (action) {
          case 'start':
            console.log('🔍 Trading: Starting bot with config:', config);
            await startBot(config);
            break;
          case 'stop':
            console.log('🔍 Trading: Stopping bot');
            await stopBot();
            break;
          case 'status':
            console.log('🔍 Trading: Getting bot status');
            await getBotStatus();
            break;
          case 'config':
            console.log('🔍 Trading: Updating bot config:', config);
            await updateBotConfig(config);
            break;
          default:
            console.error("🔍 Trading: Unknown bot action:", action);
        }
      } catch (error) {
        console.error("🔍 Trading: Error with bot control:", error);
      }
    } else {
      console.log('🔍 Trading: Bot control - not connected, skipping action');
    }
  }, [isConnected, startBot, stopBot, getBotStatus, updateBotConfig]);

  const handleChartReady = (chart) => {
    console.log("🔍 Trading: TradingView chart ready");
  };

  const handleSymbolChange = (newSymbol) => {
    console.log('🔍 Trading: handleSymbolChange called with:', newSymbol);
    if (newSymbol === selectedSymbol) {
      console.log('🔍 Trading: Symbol unchanged, skipping update');
      return; // Don't change if same symbol
    }
    
    console.log(`🔍 Trading: Symbol changed from ${selectedSymbol} to ${newSymbol}`);
    setIsChangingSymbol(true);
    console.log('🔍 Trading: Set isChangingSymbol to true');
    setSelectedSymbol(newSymbol);
    console.log('🔍 Trading: Updated selectedSymbol to:', newSymbol);
    
    // Reset loading state after a short delay
    setTimeout(() => {
      console.log('🔍 Trading: Resetting isChangingSymbol to false');
      setIsChangingSymbol(false);
    }, 1000);
    
    // Remove automatic AI analysis - only do it when user clicks the button
  };

  const handleTimeframeChange = (timeframe) => {
    console.log('🔍 Trading: handleTimeframeChange called with:', timeframe);
    if (timeframe === currentTimeframe) {
      console.log('🔍 Trading: Timeframe unchanged, skipping update');
      return; // Don't change if same timeframe
    }
    
    console.log(`🔍 Trading: Timeframe changed from ${currentTimeframe} to ${timeframe}`);
    setIsChangingTimeframe(true);
    console.log('🔍 Trading: Set isChangingTimeframe to true');
    setCurrentTimeframe(timeframe);
    console.log('🔍 Trading: Updated currentTimeframe to:', timeframe);
    
    // Reset loading state after a short delay
    setTimeout(() => {
      console.log('🔍 Trading: Resetting isChangingTimeframe to false');
      setIsChangingTimeframe(false);
    }, 500);
    
    // The chart will automatically update due to the key prop change
    // and the useEffect in TradingViewChart component
  };



  // Popular trading pairs for top navigation
  const popularPairs = [
    { symbol: "BTCUSDT", change: 2.44 },
    { symbol: "ETHUSDT", change: 3.55 },
    { symbol: "BNBUSDT", change: 1.29 },
    { symbol: "ADAUSDT", change: 7.08 },
    { symbol: "SOLUSDT", change: 4.11 },
    { symbol: "XRPUSDT", change: 2.41 }
  ];

  // Get real price data for popular pairs
  const getPopularPairsWithRealData = () => {
    return popularPairs.map(pair => {
      // Try to get from WebSocket price cache first
      if (data.price_cache && data.price_cache[pair.symbol]) {
        return {
          ...pair,
          change: data.price_cache[pair.symbol].change_24h || pair.change
        };
      }
      
      // Fallback to crypto data
      const crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === pair.symbol
      );
      if (crypto) {
        return {
          ...pair,
          change: crypto.price_change_percentage_24h || pair.change
        };
      }
      
      return pair;
    });
  };

  const popularPairsWithRealData = getPopularPairsWithRealData();

  return (
    <div className="trading-container">
      {/* Top Navigation Bar */}
      <div className="top-nav">
        <div className="nav-left">
          <div className="logo">
            <span className="logo-icon"><FiTrendingUp size={20} /></span>
            <span className="logo-text">CRYPTO FUTURES</span>
          </div>
          <div className="nav-home" onClick={() => navigate('/')}>
            <span className="home-icon"><FiHome size={18} /></span>
          </div>
        </div>
        
        <div className="nav-center">
          <div className="popular-pairs">
            {popularPairsWithRealData.map((pair) => (
              <div 
                key={pair.symbol} 
                className={`pair-item ${selectedSymbol === pair.symbol ? 'active' : ''}`}
                onClick={() => handleSymbolChange(pair.symbol)}
              >
                <span className="pair-symbol">{pair.symbol}</span>
                <span className={`pair-change ${pair.change >= 0 ? 'positive' : 'negative'}`}>
                  {pair.change >= 0 ? '+' : ''}{pair.change}%
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="nav-right">
          <div className="nav-actions">
            <button className="nav-btn"><FiZap size={16} /></button>
            <button className="nav-btn"><FiVolume2 size={16} /></button>
            <button className="nav-btn back-live">Back to Live</button>
          </div>
        </div>
      </div>

      {/* Trading Pair Details */}
      <div className="pair-details">
        <div className="pair-info">
          <div className="pair-name">
            <span className="pair-symbol">{selectedSymbol} Perp</span>
            <span className="star-icon"><FiShield size={16} /></span>
          </div>
          <div className="price-info">
            <div className="mark-price">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice.toLocaleString() : '0.00'}</div>
            <div className={`price-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
              {priceChange && typeof priceChange === 'number' && !isNaN(priceChange) ? `${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%` : '0.00%'}
            </div>
          </div>
        </div>
        <div className="pair-stats">
          <div className="stat-item">
            <span className="stat-label">Index Price:</span>
            <span className="stat-value">
              ${(() => {
                // Get real index price from WebSocket data
                if (data.price_cache && data.price_cache[selectedSymbol]) {
                  return (parseFloat(data.price_cache[selectedSymbol].price) * 0.999).toFixed(2);
                }
                // Fallback to crypto data
                const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                if (crypto) {
                  return (crypto.current_price * 0.999).toFixed(2);
                }
                return currentPrice ? (currentPrice * 0.999).toFixed(2) : '0.00';
              })()}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Funding/Countdown:</span>
            <span className="stat-value">0.3000% / 02:31:04</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">24h High:</span>
            <span className="stat-value">
              ${(() => {
                // Get real 24h high from WebSocket data
                if (data.price_cache && data.price_cache[selectedSymbol]) {
                  const price = data.price_cache[selectedSymbol].price;
                  return (price * 1.05).toFixed(2);
                }
                // Fallback to crypto data
                const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                if (crypto) {
                  return (crypto.current_price * 1.05).toFixed(2);
                }
                return currentPrice ? (currentPrice * 1.05).toFixed(2) : '0.00';
              })()}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">24h Low:</span>
            <span className="stat-value">
              ${(() => {
                // Get real 24h low from WebSocket data
                if (data.price_cache && data.price_cache[selectedSymbol]) {
                  const price = data.price_cache[selectedSymbol].price;
                  return (price * 0.95).toFixed(2);
                }
                // Fallback to crypto data
                const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                if (crypto) {
                  return (crypto.current_price * 0.95).toFixed(2);
                }
                return currentPrice ? (currentPrice * 0.95).toFixed(2) : '0.00';
              })()}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">24h Volume:</span>
            <span className="stat-value">
              {(() => {
                // Get real volume from WebSocket data
                if (data.price_cache && data.price_cache[selectedSymbol]) {
                  const volume = data.price_cache[selectedSymbol].volume || 0;
                  return volume.toFixed(2);
                }
                // Fallback to crypto data
                const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                if (crypto) {
                  return (crypto.volume_24h || 0).toFixed(2);
                }
                return currentPrice ? (currentPrice * 0.1).toFixed(2) : '0.00';
              })()} {selectedSymbol.replace('USDT', '')}
            </span>
          </div>
        </div>
      </div>

      {/* Main Trading Area - Three Panels */}
      <div className="trading-main">
        {/* Panel 1: Chart Panel */}
        <div className="chart-panel">
          <div className="chart-header">
            <div className="chart-tabs">
              <button 
                className={`tab ${activeTab === 'chart' ? 'active' : ''}`}
                onClick={() => setActiveTab('chart')}
              >
                Chart
              </button>
              <button 
                className={`tab ${activeTab === 'info' ? 'active' : ''}`}
                onClick={() => setActiveTab('info')}
              >
                Info
              </button>
              <button 
                className={`tab ${activeTab === 'trading-data' ? 'active' : ''}`}
                onClick={() => setActiveTab('trading-data')}
              >
                Trading Data
              </button>
              <button 
                className={`tab ${activeTab === 'ai' ? 'active' : ''}`}
                onClick={() => setActiveTab('ai')}
              >
                AI Analysis
              </button>
            </div>
            <div className="timeframe-selector">
              <button 
                className={`timeframe-btn ${currentTimeframe === '1' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('1')}
                disabled={isChangingTimeframe}
              >
                1m
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '5' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('5')}
                disabled={isChangingTimeframe}
              >
                5m
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '15' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('15')}
                disabled={isChangingTimeframe}
              >
                15m
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '60' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('60')}
                disabled={isChangingTimeframe}
              >
                1H
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '240' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('240')}
                disabled={isChangingTimeframe}
              >
                4H
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '1D' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('1D')}
                disabled={isChangingTimeframe}
              >
                1D
              </button>
              <button 
                className={`timeframe-btn ${currentTimeframe === '1W' ? 'active' : ''} ${isChangingTimeframe ? 'updating' : ''}`}
                onClick={() => handleTimeframeChange('1W')}
                disabled={isChangingTimeframe}
              >
                1W
              </button>
            </div>
          </div>
          <div className="chart-container">
            {isChangingSymbol && (
              <div className="chart-loading-overlay">
                <div className="loading-spinner"></div>
                <div className="loading-text">Loading {selectedSymbol}...</div>
              </div>
            )}
            
            {/* Chart Tab Content */}
            {activeTab === 'chart' && (
              <TradingViewChart
                ref={chartRef}
                key={`${selectedSymbol}-${currentTimeframe}`}
                symbol={selectedSymbol}
                onPriceUpdate={handlePriceUpdate}
                onChartReady={handleChartReady}
                timeframe={currentTimeframe}
              />
            )}
            
            {/* Info Tab Content */}
            {activeTab === 'info' && (
              <div className="info-tab-content">
                <div className="info-section">
                  <h3><FiBarChart2 size={18} /> Market Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">Symbol:</span>
                      <span className="info-value">{selectedSymbol}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Current Price:</span>
                      <span className="info-value">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice.toLocaleString() : '0.00'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">24h Change:</span>
                      <span className={`info-value ${priceChange >= 0 ? 'positive' : 'negative'}`}>
                        {priceChange && typeof priceChange === 'number' && !isNaN(priceChange) ? `${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%` : '0.00%'}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Market Cap:</span>
                      <span className="info-value">
                        {(() => {
                          const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                          return crypto ? `$${(crypto.market_cap / 1e9).toFixed(2)}B` : 'N/A';
                        })()}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">24h Volume:</span>
                      <span className="info-value">
                        {(() => {
                          const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                          return crypto ? `$${(crypto.total_volume / 1e6).toFixed(2)}M` : 'N/A';
                        })()}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Circulating Supply:</span>
                      <span className="info-value">
                        {(() => {
                          const crypto = Array.from(cryptoData.values()).find(c => c.symbol === selectedSymbol);
                          return crypto ? `${(crypto.circulating_supply / 1e6).toFixed(2)}M` : 'N/A';
                        })()}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="info-section">
                  <h3><FiActivity size={18} /> Technical Indicators</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="info-label">RSI (14):</span>
                      <span className="info-value">65.4</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">MACD:</span>
                      <span className="info-value">Bullish</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Moving Average (50):</span>
                      <span className="info-value">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * 0.98).toFixed(2) : '0.00'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Moving Average (200):</span>
                      <span className="info-value">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * 0.95).toFixed(2) : '0.00'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Support Level:</span>
                      <span className="info-value">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * 0.92).toFixed(2) : '0.00'}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Resistance Level:</span>
                      <span className="info-value">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * 1.08).toFixed(2) : '0.00'}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Trading Data Tab Content */}
            {activeTab === 'trading-data' && (
              <div className="trading-data-tab-content">
                <div className="data-section">
                  <h3><FiBarChart2 size={18} /> Order Book</h3>
                  <div className="order-book">
                    <div className="order-book-header">
                      <span>Price (USDT)</span>
                      <span>Amount ({selectedSymbol.replace('USDT', '')})</span>
                      <span>Total</span>
                    </div>
                    <div className="order-book-body">
                      {/* Current Price */}
                      <div className="current-price-row">
                        <span className="price">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice.toFixed(2) : '0.00'}</span>
                        <span className="amount">{(Math.random() * 50).toFixed(4)}</span>
                        <span className="total">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * (Math.random() * 50)).toFixed(2) : '0.00'}</span>
                      </div>
                    
                      {/* Sell Orders (Red) */}
                      <div className="sell-orders">
                        {Array.from({length: 10}, (_, i) => (
                          <div key={`sell-${i}`} className="order-row sell">
                            <span className="price">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * (1 + (i + 1) * 0.001)).toFixed(2) : '0.00'}</span>
                            <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                            <span className="total">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? ((currentPrice * (1 + (i + 1) * 0.001)) * (Math.random() * 10)).toFixed(2) : '0.00'}</span>
                          </div>
                        ))}
                      </div>
                      
                      {/* Current Price */}
                      <div className="current-price-row">
                        <span className="price">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice.toFixed(2) : '0.00'}</span>
                        <span className="amount">{(Math.random() * 50).toFixed(4)}</span>
                        <span className="total">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * (Math.random() * 50)).toFixed(2) : '0.00'}</span>
                      </div>
                      
                      {/* Buy Orders (Green) */}
                      <div className="buy-orders">
                        {Array.from({length: 10}, (_, i) => (
                          <div key={`buy-${i}`} className="order-row buy">
                            <span className="price">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? (currentPrice * (1 - (i + 1) * 0.001)).toFixed(2) : '0.00'}</span>
                            <span className="amount">{(Math.random() * 10).toFixed(4)}</span>
                            <span className="total">${currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) ? ((currentPrice * (1 - (i + 1) * 0.001)) * (Math.random() * 10)).toFixed(2) : '0.00'}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Replace mock trades with real trades from data.recent_trades */}
                <div className="data-section">
                  <h3><FiClock size={18} /> Recent Trades</h3>
                  <div className="recent-trades">
                    <div className="trades-header">
                      <span>Price</span>
                      <span>Amount</span>
                      <span>Time</span>
                    </div>
                    <div className="trades-body">
                      {(data.recent_trades || []).filter(trade => trade.symbol === selectedSymbol).slice(0, 20).map((trade, i) => {
                        const isBuy = trade.direction === 'BUY' || trade.direction === 'LONG' || trade.side === 'buy';
                        const price = trade.price;
                        const amount = Math.abs(trade.amount);
                        const time = new Date(trade.timestamp * 1000).toLocaleTimeString();
                        return (
                          <div key={i} className={`trade-row ${isBuy ? 'buy' : 'sell'}`}>
                            <span className="price">${price.toFixed(2)}</span>
                            <span className="amount">{amount}</span>
                            <span className="time">{time}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {/* AI Analysis Tab Content */}
            {activeTab === 'ai' && (
              <div className="ai-analysis-tab-content">
                <div className="ai-analysis-header">
                  <h3>AI Analysis for {selectedSymbol}</h3>
                  <button 
                    className="refresh-ai-btn"
                    onClick={() => sendMessage({ type: 'get_ai_analysis', symbol: selectedSymbol })}
                    disabled={!isConnected}
                  >
                    Refresh Analysis
                  </button>
                </div>
                
                {/* Current Analysis */}
                {data.ai_analysis && data.ai_analysis[selectedSymbol] ? (
                  <div className="ai-analysis-results">
                    <div className="analysis-section">
                      <h4>Current Analysis</h4>
                      <div className="analysis-data">
                        <p><strong>Symbol:</strong> {data.ai_analysis[selectedSymbol].symbol}</p>
                        <p><strong>Confidence:</strong> {data.ai_analysis[selectedSymbol].confidence || 'N/A'}</p>
                        <p><strong>Action:</strong> {data.ai_analysis[selectedSymbol].action || 'N/A'}</p>
                        <p><strong>Timestamp:</strong> {data.ai_analysis[selectedSymbol].timestamp ? new Date(data.ai_analysis[selectedSymbol].timestamp * 1000).toLocaleString() : 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="no-ai-analysis">
                    <p>No AI analysis available for {selectedSymbol}</p>
                    <p>Click "Refresh Analysis" to get the latest analysis</p>
                  </div>
                )}
                
                {/* Opportunities */}
                {data.ai_opportunities && Object.keys(data.ai_opportunities).length > 0 && (
                  <div className="ai-opportunities-section">
                    <h4>AI Opportunities</h4>
                    <div className="opportunities-grid">
                      {Object.entries(data.ai_opportunities).map(([symbol, opportunity]) => (
                        <div key={symbol} className="opportunity-card">
                          <h5>{symbol}</h5>
                          <p><strong>Action:</strong> {opportunity.action}</p>
                          <p><strong>Confidence:</strong> {opportunity.confidence}</p>
                          <p><strong>Time:</strong> {new Date(opportunity.timestamp * 1000).toLocaleString()}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Panel 2: Order Placement */}
        <div className="order-panel">
          <TradingPanel
            isConnected={isConnected}
            data={data}
            executePaperTrade={executePaperTrade}
            closePosition={closePosition}
            getPositions={getPositions}
            currentSymbol={selectedSymbol}
            currentPrice={currentPrice}
            cryptoData={cryptoData}
          />
        </div>

        {/* Panel 3: Positions */}

      </div>
      <div className="positions-panel">
          <PositionsSidebar
            positions={data.positions || {}}
            currentPrices={data.price_cache || {}}
            onClosePosition={closePosition}
            isConnected={isConnected}
            cryptoData={cryptoData}
          />
        </div>
      {/* AI Analysis Panel */}
      {showAIChat && (
        <div className="ai-analysis-overlay">
          <div className="ai-analysis-modal">
            <div className="ai-analysis-header">
              <h2><FiZap size={20} /> Trading Bot</h2>
              <button 
                className="close-ai-btn"
                onClick={() => setShowAIChat(false)}
              >
                ×
              </button>
            </div>
            <TradingBot
              isConnected={isConnected}
              startBot={startBot}
              stopBot={stopBot}
              getBotStatus={getBotStatus}
              updateBotConfig={updateBotConfig}
              sendMessage={sendMessage}
              data={data}
            />
          </div>
        </div>
      )}

      {/* Floating Trading Bot Button */}
      <div className="floating-ai-chat">
        <button 
          className="ai-chat-btn"
          onClick={() => setShowAIChat(!showAIChat)}
          title="Trading Bot"
        >
          <FiZap size={24} />
        </button>
      </div>

      {/* Bottom Status Bar */}
      <div className="bottom-status">
        <div className="status-left">
          <span className="notifications">9+ 30°C</span>
        </div>
        <div className="status-right">
          <span className="current-time">{new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default Trading;
