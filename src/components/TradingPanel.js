import React, { useState, useEffect } from 'react';
import { 
  FiLock, 
  FiLink, 
  FiDollarSign, 
  FiTrendingUp, 
  FiTrendingDown,
  FiShield,
  FiZap,
  FiPercent,
  FiClock
} from 'react-icons/fi';
import TradingBalanceDisplay from './TradingBalanceDisplay';
import { useTradingMode } from '../contexts/TradingModeContext';
import './TradingPanel.css';

// 🔥 NEW: Import Redux hooks for real-time prices
import { 
  usePriceBySymbol, 
  useEnhancedPrice,
  useBinanceConnectionStatus,
  usePriceUpdateStats 
} from '../store/hooks';

const TradingPanel = ({ 
  isConnected, 
  data, 
  sendMessage,
  executePaperTrade, 
  closePosition, 
  getPositions,
  currentSymbol = 'BTCUSDT',
  currentPrice = null,
  cryptoData = new Map()
}) => {
  console.log(' TradingPanel: Component initialized with props:', { 
    currentSymbol, 
    currentPrice, 
    isConnected, 
    sendMessage: !!sendMessage,
    data: Object.keys(data || {}).length,
    cryptoData: cryptoData ? cryptoData.size : 0
  });

  // 🔥 NEW: Use Redux hooks for real-time prices
  const reduxPrice = usePriceBySymbol(currentSymbol);
  const enhancedPrice = useEnhancedPrice(currentSymbol);
  const binanceConnectionStatus = useBinanceConnectionStatus();
  const priceUpdateStats = usePriceUpdateStats();
  
  console.log(' TradingPanel: Redux price data:', { 
    reduxPrice, 
    enhancedPrice, 
    binanceConnectionStatus, 
    priceUpdateStats 
  });

  const [activeTab, setActiveTab] = useState('buy');
  console.log(' TradingPanel: Initial activeTab:', activeTab);
  const [amount, setAmount] = useState('');
  console.log(' TradingPanel: Initial amount:', amount);
  const [orderType, setOrderType] = useState('limit');
  console.log(' TradingPanel: Initial orderType:', orderType);
  const [leverage, setLeverage] = useState(10);
  console.log(' TradingPanel: Initial leverage:', leverage);
  const [marginMode, setMarginMode] = useState('isolated');
  console.log(' TradingPanel: Initial marginMode:', marginMode);
  const [price, setPrice] = useState('');
  console.log(' TradingPanel: Initial price:', price);
  const [size, setSize] = useState('');
  console.log(' TradingPanel: Initial size:', size);
  const [sizeUnit, setSizeUnit] = useState('USDT'); // Add size unit state
  console.log(' TradingPanel: Initial sizeUnit:', sizeUnit);
  const [sizeSliderValue, setSizeSliderValue] = useState(0); // Add slider value state
  console.log(' TradingPanel: Initial sizeSliderValue:', sizeSliderValue);
  const [useTpSl, setUseTpSl] = useState(false);
  console.log(' TradingPanel: Initial useTpSl:', useTpSl);
  const [reduceOnly, setReduceOnly] = useState(false);
  console.log(' TradingPanel: Initial reduceOnly:', reduceOnly);
  const [isExecuting, setIsExecuting] = useState(false);
  console.log(' TradingPanel: Initial isExecuting:', isExecuting);
  const [lastTrade, setLastTrade] = useState(null);
  console.log(' TradingPanel: Initial lastTrade:', lastTrade);
  const [lastTradeId, setLastTradeId] = useState(null); // Track last trade to prevent duplicates
  console.log(' TradingPanel: Initial lastTradeId:', lastTradeId);
  
  // Get trading mode from global context
  const { isLiveMode, tradingMode } = useTradingMode();
  console.log(' TradingPanel: Current trading mode:', { isLiveMode, tradingMode });

  // Safely destructure data with defaults
  const { paper_balance = 0, trading_balance = null, positions = {}, recent_trades = [] } = data || {};
  
  // 🔥 NEW: Use live balance when in live mode, fallback to paper balance
  const effectiveBalance = isLiveMode && trading_balance ? trading_balance.total : paper_balance;
  
  console.log(' TradingPanel: Current data structure:', { 
    paper_balance, 
    trading_balance, 
    effectiveBalance,
    isLiveMode,
    positions: Object.keys(positions).length, 
    recent_trades: recent_trades.length 
  });
  console.log(' TradingPanel: Data from props:', { 
    paper_balance, 
    trading_balance,
    effectiveBalance,
    positions: Object.keys(positions).length, 
    recent_trades: recent_trades.length 
  });

  // Calculate position info
  const currentPosition = positions[currentSymbol];
  console.log(' TradingPanel: Current position for', currentSymbol, ':', currentPosition);

  useEffect(() => {
    if (isConnected) {
      getPositions();
      console.log(' TradingPanel: getPositions called, isConnected:', isConnected);
    }
  }, [isConnected, getPositions]);

  // Request crypto data if not available
  useEffect(() => {
    if (isConnected && (!cryptoData || cryptoData.size === 0)) {
      console.log(' TradingPanel: No crypto data available, requesting from backend...');
      // We need to access the getCryptoData function from the parent
      // This will be handled by the useCryptoDataBackend hook
    }
  }, [isConnected, cryptoData]);

  // 🔥 UPDATED: Price effect using Redux real-time prices
  useEffect(() => {
    let foundPrice = null;

    if (orderType === 'market') {
      // Use Redux real-time price first
      if (reduxPrice && reduxPrice.price) {
        foundPrice = reduxPrice.price;
        console.log(' TradingPanel: Setting market price from Redux:', foundPrice);
      } else if (currentPrice) {
        foundPrice = currentPrice;
        console.log(' TradingPanel: Setting market price from props:', foundPrice);
      } else if (data && data.price_cache && data.price_cache[currentSymbol]) {
        foundPrice = data.price_cache[currentSymbol].price;
        console.log(' TradingPanel: Setting market price from cache:', foundPrice);
      } else if (cryptoData && cryptoData.size > 0) {
        const crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === currentSymbol
        );
        if (crypto && crypto.current_price) {
          foundPrice = crypto.current_price;
          console.log(' TradingPanel: Setting market price from cryptoData:', foundPrice);
        }
      }
    } else {
      foundPrice = price ? parseFloat(price) : null;
    }

    if (foundPrice && typeof foundPrice === 'number' && !isNaN(foundPrice)) {
      setPrice(foundPrice.toFixed(2));
    }
  }, [currentSymbol, currentPrice, cryptoData, data, orderType, price, reduxPrice]);

  // 🔥 UPDATED: Update slider value when size is manually entered (using Redux price)
  useEffect(() => {
    if (size && parseFloat(size) > 0) {
      const currentPrice = getCurrentPrice();
      const availableBalance = effectiveBalance || 100000;
      
      if (currentPrice && availableBalance > 0) {
        let percentage;
        
        if (sizeUnit === 'USDT') {
          percentage = (parseFloat(size) / availableBalance) * 100;
        } else {
          const maxCryptoAmount = availableBalance / currentPrice;
          percentage = (parseFloat(size) / maxCryptoAmount) * 100;
        }
        
        // Clamp percentage between 0 and 100
        percentage = Math.min(100, Math.max(0, percentage));
        setSizeSliderValue(Math.round(percentage));
      }
    } else if (!size) {
      setSizeSliderValue(0);
    }
  }, [size, sizeUnit, paper_balance, currentPrice, cryptoData, data, currentSymbol, reduxPrice]);

  // Reset slider and size when symbol changes
  useEffect(() => {
    setSizeSliderValue(0);
    setSize('');
    setSizeUnit('USDT'); // Reset to USDT when symbol changes
  }, [currentSymbol]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!isConnected || !size || isExecuting) {
      return;
    }

    const tradeAmount = parseFloat(size);
    if (tradeAmount <= 0) {
      window.alert('Trade amount must be greater than 0');
      return;
    }

    let effectivePrice = null;
    if (orderType === 'market') {
      effectivePrice = getCurrentPrice();
    } else {
      effectivePrice = parseFloat(price);
    }

    if (!effectivePrice) {
      window.alert('Could not determine price for trade.');
      return;
    }

    let tradeValue;
    let finalTradeAmount;

    if (sizeUnit === 'USDT') {
      tradeValue = tradeAmount;
      finalTradeAmount = tradeValue / effectivePrice;
    } else {
      finalTradeAmount = tradeAmount;
      tradeValue = finalTradeAmount * effectivePrice;
    }

    const availableBalance = effectiveBalance || 100000;

    if (activeTab === 'buy' && tradeValue > availableBalance) {
      window.alert('Insufficient balance!');
      return;
    }

    setIsExecuting(true);

    try {
      const tradeData = {
        symbol: currentSymbol,
        direction: activeTab,
        amount: finalTradeAmount,
        order_type: orderType,
        price: effectivePrice,
        strategy: 'manual',
        ai_confidence: 0.0,
        trade_id: `${currentSymbol}-${orderType}-${Date.now()}`,
        trade_type: activeTab === 'buy' ? 'LONG' : 'SHORT',
        margin_mode: marginMode,
        leverage: leverage,
        trading_mode: tradingMode, // 🔥 NEW: Include trading mode
      };

      // 🔥 NEW: Use live trading when in live mode
      if (isLiveMode && sendMessage) {
        // Send live trading message
        sendMessage({
          type: 'place_order',
          data: {
            ...tradeData,
            mode: 'live'
          }
        });
        
        // Note: Response will be handled by WebSocket context
        // The order_placed response will trigger balance updates
      } else {
        // Use paper trading
        await executePaperTrade(tradeData);
      }

      setTimeout(() => {
        if (isConnected) {
          getPositions();
        }
      }, 1000);

      setSize('');
      setPrice('');

      setLastTrade({
        symbol: currentSymbol,
        direction: activeTab,
        amount: finalTradeAmount,
        price: effectivePrice,
        timestamp: new Date(),
      });

      setTimeout(() => {
        setLastTrade(null);
      }, 5000);
    } catch (error) {
      console.error('Trade execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClosePosition = async (symbol) => {
    if (!isConnected) return;
    
    try {
      await closePosition(symbol);
    } catch (error) {
      console.error(' TradingPanel: Failed to close position:', error);
    }
  };

  // 🔥 UPDATED: Calculate cost using Redux real-time prices
  const calculateCost = () => {
    if (!size) return 0;
    
    // For market orders, use current price; for limit orders, use entered price
    let effectivePrice = null;
    
    if (orderType === 'market') {
      // Use Redux real-time price first
      if (reduxPrice && reduxPrice.price) {
        effectivePrice = reduxPrice.price;
      } else if (currentPrice) {
        effectivePrice = currentPrice;
      } else if (price && parseFloat(price) > 0) {
        effectivePrice = parseFloat(price);
      } else if (cryptoData && cryptoData.size > 0) {
        const crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === currentSymbol
        );
        if (crypto && crypto.current_price) {
          effectivePrice = crypto.current_price;
        }
      } else if (data && data.price_cache && data.price_cache[currentSymbol]) {
        effectivePrice = data.price_cache[currentSymbol].price;
      } else if (data && data.price_cache) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        if (data.price_cache[baseSymbol]) {
          effectivePrice = data.price_cache[baseSymbol].price;
        }
      }
    } else {
      effectivePrice = parseFloat(price);
    }
    
    if (!effectivePrice) return 0;
    
    const sizeValue = parseFloat(size);
    if (sizeUnit === 'USDT') {
      // If size is in USDT, return the size directly
      return sizeValue.toFixed(2);
    } else {
      // If size is in crypto (e.g., BTC), calculate USDT value
      return (sizeValue * effectivePrice).toFixed(2);
    }
  };

  // Handle size unit change
  const handleSizeUnitChange = (newUnit) => {
    setSizeUnit(newUnit);
    
    // Convert the current size value to the new unit
    if (size && parseFloat(size) > 0) {
      const currentPrice = getCurrentPrice();
      if (currentPrice) {
        const currentSize = parseFloat(size);
        let newSize;
        
        if (sizeUnit === 'USDT' && newUnit === currentSymbol.replace('USDT', '')) {
          // Convert from USDT to crypto amount
          newSize = currentSize / currentPrice;
        } else if (sizeUnit === currentSymbol.replace('USDT', '') && newUnit === 'USDT') {
          // Convert from crypto amount to USDT
          newSize = currentSize * currentPrice;
        } else {
          // Keep the same value if converting between same types
          newSize = currentSize;
        }
        
        setSize(newSize.toFixed(2));
        
        // Update slider value after conversion
        const availableBalance = paper_balance || 100000;
        if (availableBalance > 0) {
          let percentage;
          
          if (newUnit === 'USDT') {
            percentage = (newSize / availableBalance) * 100;
          } else {
            const maxCryptoAmount = availableBalance / currentPrice;
            percentage = (newSize / maxCryptoAmount) * 100;
          }
          
          // Clamp percentage between 0 and 100
          percentage = Math.min(100, Math.max(0, percentage));
          setSizeSliderValue(Math.round(percentage));
        }
      }
    }
  };

  // Handle slider change
  const handleSliderChange = (value) => {
    setSizeSliderValue(value);
    
    const currentPrice = getCurrentPrice();
    const availableBalance = paper_balance || 100000;
    
    if (currentPrice && availableBalance > 0) {
      let newSize;
      
      if (sizeUnit === 'USDT') {
        // Calculate USDT amount based on percentage
        newSize = (availableBalance * value) / 100;
      } else {
        // Calculate crypto amount based on percentage
        const maxCryptoAmount = availableBalance / currentPrice;
        newSize = (maxCryptoAmount * value) / 100;
      }
      
      setSize(newSize.toFixed(2));
    }
  };

  // 🔥 UPDATED: Get current price using Redux store (with fallbacks)
  const getCurrentPrice = () => {
    // First try Redux real-time price
    if (reduxPrice && reduxPrice.price) {
      console.log(' TradingPanel: Using Redux real-time price:', reduxPrice.price);
      return reduxPrice.price;
    }
    
    // Fallback to prop-based currentPrice
    if (currentPrice) {
      console.log(' TradingPanel: Using prop currentPrice:', currentPrice);
      return currentPrice;
    }
    
    // Fallback to data price cache
    if (data && data.price_cache && data.price_cache[currentSymbol]) {
      console.log(' TradingPanel: Using data price cache:', data.price_cache[currentSymbol].price);
      return data.price_cache[currentSymbol].price;
    }
    
    // Try base symbol in price cache
    if (data && data.price_cache) {
      const baseSymbol = currentSymbol.replace('USDT', '');
      if (data.price_cache[baseSymbol]) {
        console.log(' TradingPanel: Using base symbol price cache:', data.price_cache[baseSymbol].price);
        return data.price_cache[baseSymbol].price;
      }
    }
    
    // Last fallback to cryptoData
    if (cryptoData && cryptoData.size > 0) {
      const crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === currentSymbol
      );
      if (crypto && crypto.current_price) {
        console.log(' TradingPanel: Using cryptoData price:', crypto.current_price);
        return crypto.current_price;
      }
    }
    
    console.log(' TradingPanel: No price found for symbol:', currentSymbol);
    return null;
  };

  // Get max available amount for current unit
  const getMaxAmount = () => {
    const currentPrice = getCurrentPrice();
    const availableBalance = effectiveBalance || 100000;
    
    if (!currentPrice || availableBalance <= 0) return 0;
    
    // Apply margin mode logic
    let maxBalance = availableBalance;
    
    if (marginMode === 'isolated') {
      // In isolated mode, we can use the full balance for this position
      maxBalance = availableBalance;
    } else {
      // In cross mode, we need to consider existing positions
      const totalPositionValue = Object.values(positions).reduce((total, pos) => {
        return total + Math.abs(pos.amount * pos.avg_price);
      }, 0);
      
      // Reserve some balance for other positions in cross mode
      maxBalance = availableBalance - (totalPositionValue * 0.1); // Reserve 10% for safety
    }
    
    if (sizeUnit === 'USDT') {
      return Math.max(0, maxBalance);
    } else {
      return Math.max(0, maxBalance / currentPrice);
    }
  };

  const getPositionForSymbol = (symbol) => {
    return (positions || {})[symbol] || null;
  };

  // Calculate margin requirements based on margin mode
  const calculateMarginRequirement = () => {
    if (!size || !getCurrentPrice()) return 0;
    
    const tradeValue = sizeUnit === 'USDT' ? parseFloat(size) : parseFloat(size) * getCurrentPrice();
    const marginRequirement = tradeValue / leverage;
    
    if (marginMode === 'isolated') {
      return marginRequirement;
    } else {
      // In cross mode, margin is shared across all positions
      const totalPositionValue = Object.values(positions || {}).reduce((total, pos) => {
        return total + Math.abs(pos.amount * pos.avg_price);
      }, 0);
      return Math.max(marginRequirement, totalPositionValue / leverage);
    }
  };

  // Debug logging for state changes
  useEffect(() => {
    const tradeValue = currentPrice && size ? currentPrice * parseFloat(size) : 0;
    console.log(' TradingPanel: State updated:', {
      activeTab,
      amount,
      orderType,
      leverage,
      marginMode,
      price,
      size,
      sizeUnit,
      sizeSliderValue,
      useTpSl,
      reduceOnly,
      isExecuting,
      currentPrice,
      currentSymbol,
      paper_balance,
      trading_balance,
      effectiveBalance,
      isLiveMode,
      positions: Object.keys(positions || {}).length,
      currentPosition,
      tradeValue,
      hasEnoughBalance: currentPrice && size ? currentPrice * parseFloat(size) <= effectiveBalance : false,
      hasPosition: currentPosition ? Math.abs(currentPosition.amount) > 0 : false,
      lastTrade,
      lastTradeId
    });
  }, [activeTab, amount, orderType, leverage, marginMode, price, size, sizeUnit, sizeSliderValue, useTpSl, reduceOnly, isExecuting, currentPrice, currentSymbol, paper_balance, trading_balance, effectiveBalance, isLiveMode, positions, currentPosition]);

  // Handle order type change
  const handleOrderTypeChange = (newOrderType) => {
    setOrderType(newOrderType);
    // For market orders, set price to current price or crypto data
    if (newOrderType === 'market') {
      if (currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice)) {
        setPrice(currentPrice.toFixed(2));
        console.log(' TradingPanel: Setting market price from currentPrice:', currentPrice.toFixed(2));
      } else if (cryptoData && cryptoData.size > 0) {
        const crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === currentSymbol
        );
        if (crypto && crypto.current_price && typeof crypto.current_price === 'number' && !isNaN(crypto.current_price)) {
          setPrice(crypto.current_price.toFixed(2));
          console.log(' TradingPanel: Setting market price from crypto data:', crypto.current_price.toFixed(2));
        }
      } else if (data && data.price_cache && data.price_cache[currentSymbol]) {
        const price = data.price_cache[currentSymbol].price;
        if (typeof price === 'number' && !isNaN(price)) {
          setPrice(price.toFixed(2));
          console.log(' TradingPanel: Setting market price from WebSocket price cache:', price.toFixed(2));
        }
      } else if (data && data.price_cache) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        if (data.price_cache[baseSymbol]) {
          const price = data.price_cache[baseSymbol].price;
          if (typeof price === 'number' && !isNaN(price)) {
            setPrice(price.toFixed(2));
            console.log(' TradingPanel: Setting market price from base symbol price cache:', baseSymbol, price.toFixed(2));
          }
        }
      }
    }
  };

  return (
    <div className="trading-panel">
      {/* Leverage and Margin Mode */}
      <div className="leverage-section">
        <div className="margin-mode">
          <button 
            className={`mode-btn ${marginMode === 'isolated' ? 'active' : ''}`}
            data-mode="isolated"
            data-tooltip="Isolated Margin: Risk is limited to allocated balance"
            onClick={() => setMarginMode('isolated')}
          >
                            <FiLock size={14} /> Isolated
          </button>
          <button 
            className={`mode-btn ${marginMode === 'cross' ? 'active' : ''}`}
            data-mode="cross"
            data-tooltip="Cross Margin: Risk is shared across all positions"
            onClick={() => setMarginMode('cross')}
          >
                            <FiLink size={14} /> Cross
          </button>
        </div>
        <div className="leverage-selector">
          <span className="leverage-label">Leverage</span>
          <select 
            value={leverage} 
            onChange={(e) => setLeverage(parseInt(e.target.value))}
            className="leverage-select"
          >
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={5}>5x</option>
            <option value={10}>10x</option>
            <option value={20}>20x</option>
            <option value={50}>50x</option>
            <option value={100}>100x</option>
          </select>
        </div>
      </div>

      {/* Available Balance and Margin Info */}
      <TradingBalanceDisplay 
        mode={tradingMode} 
        isConnected={isConnected}
        sendMessage={sendMessage}
        data={data}
      />
      <div className="margin-info">
        <span className="margin-mode-indicator">
          {marginMode === 'isolated' ? <FiLock size={12} /> : <FiLink size={12} />} {marginMode.charAt(0).toUpperCase() + marginMode.slice(1)} Margin
        </span>
        <span className="leverage-indicator">
          <FiZap size={12} /> {leverage}x Leverage
        </span>
      </div>

      {/* Order Type */}
      <div className="order-type-section">
        <div className="order-type-tabs">
          <button 
            className={`order-type-btn ${orderType === 'limit' ? 'active' : ''}`}
            onClick={() => handleOrderTypeChange('limit')}
          >
            Limit
          </button>
          <button 
            className={`order-type-btn ${orderType === 'market' ? 'active' : ''}`}
            onClick={() => handleOrderTypeChange('market')}
          >
            Market
          </button>
          <button 
            className={`order-type-btn ${orderType === 'stop' ? 'active' : ''}`}
            onClick={() => handleOrderTypeChange('stop')}
          >
            Stop Limit
          </button>
        </div>
      </div>

      {/* Trading Form */}
      <form onSubmit={handleSubmit} className="trading-form">
        {/* Price Input - Hidden for market orders */}
        {orderType !== 'market' && (
          <div className="form-group">
            <label className="form-label">
              Price
            </label>
            <div className="input-group">
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="0.00"
                className="form-input"
                step="0.01"
                min="0"
              />
              <span className="input-suffix">USDT</span>
            </div>
          </div>
        )}

        {/* Market Price Display - Only for market orders */}
        {orderType === 'market' && (
          <div className="form-group">
            <label className="form-label">
              <span className="market-indicator">Market Price</span>
            </label>
            <div className="market-price-display">
              <span className="current-price-value">
                ${(() => {
                  // Use Redux real-time price first
                  if (reduxPrice && reduxPrice.price && typeof reduxPrice.price === 'number' && !isNaN(reduxPrice.price)) {
                    return reduxPrice.price.toFixed(2);
                  }
                  
                  // Fallback to prop-based price
                  if (currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice)) {
                    return currentPrice.toFixed(2);
                  }
                  
                  if (data && data.price_cache && data.price_cache[currentSymbol]) {
                    const price = data.price_cache[currentSymbol].price;
                    if (typeof price === 'number' && !isNaN(price)) {
                      return price.toFixed(2);
                    }
                  }
                  
                  if (data && data.price_cache) {
                    const baseSymbol = currentSymbol.replace('USDT', '');
                    if (data.price_cache[baseSymbol]) {
                      const price = data.price_cache[baseSymbol].price;
                      if (typeof price === 'number' && !isNaN(price)) {
                        return price.toFixed(2);
                      }
                    }
                  }
                  
                  if (cryptoData && cryptoData.size > 0) {
                    const crypto = Array.from(cryptoData.values()).find(
                      c => c.symbol === currentSymbol
                    );
                    if (crypto && crypto.current_price && typeof crypto.current_price === 'number' && !isNaN(crypto.current_price)) {
                      return crypto.current_price.toFixed(2);
                    }
                  }
                  
                  return binanceConnectionStatus === 'connected' ? 'Loading...' : 'Connecting...';
                })()}
              </span>
              <span className="market-price-label">USDT</span>
            </div>
          </div>
        )}

        {/* Size Input */}
        <div className="form-group">
          <label className="form-label">Size</label>
          <div className="input-group">
            <input
              type="number"
              value={size}
              onChange={(e) => setSize(e.target.value)}
              placeholder="0.00"
              className="form-input"
              step="0.01"
              min="0"
            />
            <select 
              className="size-unit-select"
              value={sizeUnit}
              onChange={(e) => handleSizeUnitChange(e.target.value)}
            >
              <option value="USDT">USDT</option>
              <option value={currentSymbol.replace('USDT', '')}>{currentSymbol.replace('USDT', '')}</option>
            </select>
          </div>
          
          {/* Size Slider */}
          <div className="size-slider-container">
            <div className="slider-header">
              <span className="slider-label">Size: {sizeSliderValue}%</span>
              <span className="max-amount">
                Max: {getMaxAmount().toFixed(4)} {sizeUnit}
              </span>
            </div>
            <div className="slider-wrapper">
              <input
                type="range"
                min="0"
                max="100"
                value={sizeSliderValue}
                onChange={(e) => handleSliderChange(parseInt(e.target.value))}
                className="size-slider"
              />
              <div className="slider-markers">
                <span className="marker">0%</span>
                <span className="marker">25%</span>
                <span className="marker">50%</span>
                <span className="marker">75%</span>
                <span className="marker">100%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Options */}
        <div className="options-section">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useTpSl}
              onChange={(e) => setUseTpSl(e.target.checked)}
            />
            <span className="checkmark"></span>
            TP/SL
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={reduceOnly}
              onChange={(e) => setReduceOnly(e.target.checked)}
            />
            <span className="checkmark"></span>
            Reduce-Only
          </label>
        </div>

        {/* Cost and Margin Display */}
        <div className="cost-section">
          <div className="cost-row">
            <span className="cost-label">Cost</span>
            <span className="cost-amount">{calculateCost()} USDT</span>
          </div>
          {size && (
            <div className="margin-row">
              <span className="margin-label">Margin Required</span>
              <span className="margin-amount">
                <FiDollarSign size={12} /> {calculateMarginRequirement().toFixed(2)} USDT
                <span className="margin-mode-badge">
                                      {marginMode === 'isolated' ? <FiLock size={10} /> : <FiLink size={10} />}
                </span>
              </span>
            </div>
          )}
        </div>

        {/* Trade Buttons */}
        <div className="trade-buttons">
          <button 
            type="submit" 
            className={`trade-btn buy-btn ${activeTab === 'buy' ? 'active' : ''}`}
            onClick={() => setActiveTab('buy')}
            disabled={!isConnected || !size || (orderType !== 'market' && !price) || isExecuting}
          >
            {isExecuting ? 'Executing...' : 'Buy/Long'}
          </button>
          <button 
            type="submit" 
            className={`trade-btn sell-btn ${activeTab === 'sell' ? 'active' : ''}`}
            onClick={() => setActiveTab('sell')}
            disabled={!isConnected || !size || (orderType !== 'market' && !price) || isExecuting}
          >
            {isExecuting ? 'Executing...' : 'Sell/Short'}
          </button>
        </div>
        {/* Submit Button */}
        {/* <div className="form-group"> */}
          {/* <button 
            type="submit" 
            className={`submit-btn ${activeTab}`}
            disabled={isExecuting || !isConnected}
          >
            {isExecuting ? 'Executing...' : `${activeTab.toUpperCase()} ${currentSymbol}`}
          </button> */}
        {/* </div> */}
      </form>

      {/* Promotional Banners */}
      {/* <div className="promo-banners">
        <div className="promo-banner">
          Trade Futures with USDT Flexible Assets
        </div>
        <div className="promo-banner">
          0 Fee on USDC-M Contracts
        </div>
      </div> */}

      {/* Last Trade Success */}
      {lastTrade && (
        <div className="trade-success">
          <div className="success-icon"> </div>
          <div className="success-message">
            Successfully {lastTrade.direction === 'buy' ? 'bought' : 'sold'} {lastTrade.amount} USDT of {lastTrade.symbol} at ${lastTrade.price}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingPanel; 