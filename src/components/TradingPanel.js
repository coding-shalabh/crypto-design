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
import './TradingPanel.css';

const TradingPanel = ({ 
  isConnected, 
  data, 
  executePaperTrade, 
  closePosition, 
  getPositions,
  currentSymbol = 'BTCUSDT',
  currentPrice = null,
  cryptoData = new Map()
}) => {
  console.log('🔍 TradingPanel: Component initialized with props:', { 
    currentSymbol, 
    currentPrice, 
    isConnected, 
    data: Object.keys(data || {}).length,
    cryptoData: cryptoData ? cryptoData.size : 0
  });

  const [activeTab, setActiveTab] = useState('buy');
  console.log('🔍 TradingPanel: Initial activeTab:', activeTab);
  const [amount, setAmount] = useState('');
  console.log('🔍 TradingPanel: Initial amount:', amount);
  const [orderType, setOrderType] = useState('limit');
  console.log('🔍 TradingPanel: Initial orderType:', orderType);
  const [leverage, setLeverage] = useState(10);
  console.log('🔍 TradingPanel: Initial leverage:', leverage);
  const [marginMode, setMarginMode] = useState('isolated');
  console.log('🔍 TradingPanel: Initial marginMode:', marginMode);
  const [price, setPrice] = useState('');
  console.log('🔍 TradingPanel: Initial price:', price);
  const [size, setSize] = useState('');
  console.log('🔍 TradingPanel: Initial size:', size);
  const [sizeUnit, setSizeUnit] = useState('USDT'); // Add size unit state
  console.log('🔍 TradingPanel: Initial sizeUnit:', sizeUnit);
  const [sizeSliderValue, setSizeSliderValue] = useState(0); // Add slider value state
  console.log('🔍 TradingPanel: Initial sizeSliderValue:', sizeSliderValue);
  const [useTpSl, setUseTpSl] = useState(false);
  console.log('🔍 TradingPanel: Initial useTpSl:', useTpSl);
  const [reduceOnly, setReduceOnly] = useState(false);
  console.log('🔍 TradingPanel: Initial reduceOnly:', reduceOnly);
  const [isExecuting, setIsExecuting] = useState(false);
  console.log('🔍 TradingPanel: Initial isExecuting:', isExecuting);
  const [lastTrade, setLastTrade] = useState(null);
  console.log('🔍 TradingPanel: Initial lastTrade:', lastTrade);
  const [lastTradeId, setLastTradeId] = useState(null); // Track last trade to prevent duplicates
  console.log('🔍 TradingPanel: Initial lastTradeId:', lastTradeId);

  // Safely destructure data with defaults
  const { paper_balance = 0, positions = {}, recent_trades = [] } = data || {};
  console.log('🔍 TradingPanel: Data from props:', { 
    paper_balance, 
    positions: Object.keys(positions).length, 
    recent_trades: recent_trades.length 
  });

  // Calculate position info
  const currentPosition = positions[currentSymbol];
  console.log('🔍 TradingPanel: Current position for', currentSymbol, ':', currentPosition);

  useEffect(() => {
    if (isConnected) {
      getPositions();
      console.log('🔍 TradingPanel: getPositions called, isConnected:', isConnected);
    }
  }, [isConnected, getPositions]);

  // Request crypto data if not available
  useEffect(() => {
    if (isConnected && (!cryptoData || cryptoData.size === 0)) {
      console.log('🔍 TradingPanel: No crypto data available, requesting from backend...');
      // We need to access the getCryptoData function from the parent
      // This will be handled by the useCryptoDataBackend hook
    }
  }, [isConnected, cryptoData]);

  // Debug log when currentPrice changes
  useEffect(() => {
    console.log(`🔍 TradingPanel: currentPrice updated for ${currentSymbol}:`, currentPrice);
  }, [currentPrice, currentSymbol]);

  // Debug log when crypto data changes
  useEffect(() => {
    if (cryptoData && cryptoData.size > 0) {
      // Try to find crypto data for current symbol (both formats)
      let crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === currentSymbol
      );
      
      // If not found, try base symbol (BTC for BTCUSDT)
      if (!crypto) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === baseSymbol
        );
      }
      
      console.log(`🔍 TradingPanel: Crypto data for ${currentSymbol}:`, crypto);
      console.log(`🔍 TradingPanel: Total crypto data entries:`, cryptoData.size);
      console.log(`🔍 TradingPanel: Available symbols:`, Array.from(cryptoData.values()).map(c => c.symbol).slice(0, 10));
      
      // If we found crypto data, use it to set the price
      if (crypto && crypto.current_price && !currentPrice) {
        console.log(`🔍 TradingPanel: Setting price from crypto data: ${crypto.current_price}`);
        // We can't directly set currentPrice here, but we can update the price field
        if (!price) {
          setPrice(crypto.current_price.toFixed(2));
        }
      }
    } else {
      console.log(`🔍 TradingPanel: No crypto data available for ${currentSymbol}`);
    }
  }, [cryptoData, currentSymbol, currentPrice, price]);

  // Debug log when positions change
  useEffect(() => {
    console.log('🔍 TradingPanel: Positions updated:', positions);
    console.log('🔍 TradingPanel: Current positions count:', Object.keys(positions || {}).length);
    if (positions && Object.keys(positions).length > 0) {
      console.log('🔍 TradingPanel: Available positions:', Object.keys(positions));
    }
  }, [positions]);

  // Set default price to current price when it changes
  useEffect(() => {
    if (currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice) && !price) {
      setPrice(currentPrice.toFixed(2));
      console.log('🔍 TradingPanel: Setting initial price from currentPrice:', currentPrice.toFixed(2));
    }
  }, [currentPrice, price]);

  // Update price field when currentPrice changes (for market orders)
  useEffect(() => {
    if (orderType === 'market' && currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice)) {
      setPrice(currentPrice.toFixed(2));
      console.log('🔍 TradingPanel: Updating price field for market order:', currentPrice.toFixed(2));
    }
  }, [currentPrice, orderType]);

  // Additional effect to ensure price is set when component mounts or symbol changes
  useEffect(() => {
    if (currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice)) {
      setPrice(currentPrice.toFixed(2));
      console.log('🔍 TradingPanel: Price updated due to currentPrice change:', currentPrice.toFixed(2));
    }
  }, [currentPrice]);

  // Set price from crypto data when currentPrice is null but crypto data is available
  useEffect(() => {
    if (!currentPrice && cryptoData && cryptoData.size > 0) {
      const crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === currentSymbol
      );
      if (crypto && crypto.current_price) {
        setPrice(crypto.current_price.toFixed(2));
        console.log('🔍 TradingPanel: Setting price from crypto data:', crypto.current_price.toFixed(2));
      }
    }
  }, [currentPrice, cryptoData, currentSymbol]);

  // Force set price when component mounts or symbol changes, regardless of currentPrice
  useEffect(() => {
    // Always try to set a price when the component mounts or symbol changes
    let foundPrice = null;
    
    // First try currentPrice
    if (currentPrice) {
      foundPrice = currentPrice;
      console.log('🔍 TradingPanel: Using currentPrice for initial price:', foundPrice);
    }
    // Then try crypto data
    else if (cryptoData && cryptoData.size > 0) {
      const crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === currentSymbol
      );
      if (crypto && crypto.current_price) {
        foundPrice = crypto.current_price;
        console.log('🔍 TradingPanel: Using crypto data for initial price:', foundPrice);
      }
    }
    // Then try WebSocket price cache with full symbol
    else if (data && data.price_cache && data.price_cache[currentSymbol]) {
      foundPrice = data.price_cache[currentSymbol].price;
      console.log('🔍 TradingPanel: Using WebSocket price cache for initial price:', foundPrice);
    }
    // Finally try WebSocket price cache with base symbol
    else if (data && data.price_cache) {
      const baseSymbol = currentSymbol.replace('USDT', '');
      if (data.price_cache[baseSymbol]) {
        foundPrice = data.price_cache[baseSymbol].price;
        console.log('🔍 TradingPanel: Using base symbol price cache for initial price:', baseSymbol, foundPrice);
      }
    }
    
    // Set the price if we found one
    if (foundPrice && !price && typeof foundPrice === 'number' && !isNaN(foundPrice)) {
      setPrice(foundPrice.toFixed(2));
      console.log('🔍 TradingPanel: Setting initial price from available data:', foundPrice.toFixed(2));
    }
  }, [currentSymbol, currentPrice, cryptoData, data, price]);

  // Update slider value when size is manually entered
  useEffect(() => {
    if (size && parseFloat(size) > 0) {
      const currentPrice = getCurrentPrice();
      const availableBalance = paper_balance || 100000;
      
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
  }, [size, sizeUnit, paper_balance, currentPrice, cryptoData, data, currentSymbol]);

  // Reset slider and size when symbol changes
  useEffect(() => {
    setSizeSliderValue(0);
    setSize('');
    setSizeUnit('USDT'); // Reset to USDT when symbol changes
  }, [currentSymbol]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    console.log('🔍 TradingPanel: Trade form submitted:', { isConnected, size, price, currentPrice, currentSymbol, orderType });
    
    if (!isConnected || !size) {
      console.log('🔍 TradingPanel: Trade validation failed:', { isConnected, size });
      return;
    }

    // Prevent duplicate submissions
    if (isExecuting) {
      console.log('🔍 TradingPanel: Trade already executing, ignoring duplicate submission');
      return;
    }

    // Validate trade amount
    const tradeAmount = parseFloat(size);
    if (tradeAmount <= 0) {
      window.alert('Trade amount must be greater than 0');
      return;
    }

    // Calculate trade value and validate against balance
    let effectivePrice = null;
    
    if (orderType === 'market') {
      // For market orders, try to get current price from multiple sources
      if (currentPrice) {
        effectivePrice = currentPrice;
        console.log('🔍 TradingPanel: Using currentPrice prop for market order:', effectivePrice);
      }
      // Then try WebSocket price cache with full symbol
      else if (data && data.price_cache && data.price_cache[currentSymbol]) {
        effectivePrice = data.price_cache[currentSymbol].price;
        console.log('🔍 TradingPanel: Using WebSocket price cache (full symbol) for market order:', effectivePrice);
      }
      // Then try WebSocket price cache with base symbol
      else if (data && data.price_cache) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        if (data.price_cache[baseSymbol]) {
          effectivePrice = data.price_cache[baseSymbol].price;
          console.log('🔍 TradingPanel: Using WebSocket price cache (base symbol) for market order:', baseSymbol, effectivePrice);
        }
      }
      // Then try crypto data
      else if (cryptoData && cryptoData.size > 0) {
        const crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === currentSymbol
        );
        if (crypto && crypto.current_price) {
          effectivePrice = crypto.current_price;
          console.log('🔍 TradingPanel: Using crypto data fallback for market order:', effectivePrice);
        }
      }
      
      // Final fallback: try to get from WebSocket data
      if (!effectivePrice && data && data.price_cache && data.price_cache[currentSymbol]) {
        effectivePrice = data.price_cache[currentSymbol].price;
        console.log('🔍 TradingPanel: Using WebSocket price cache fallback for market order:', effectivePrice);
      }
      
      // Additional fallback: try base symbol (BTC instead of BTCUSDT)
      if (!effectivePrice && data && data.price_cache) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        if (data.price_cache[baseSymbol]) {
          effectivePrice = data.price_cache[baseSymbol].price;
          console.log('🔍 TradingPanel: Using base symbol fallback for market order:', baseSymbol, effectivePrice);
        }
      }
      
      // Debug: show what's in the price cache
      if (data && data.price_cache) {
        console.log('🔍 TradingPanel: Price cache contents:', data.price_cache);
        console.log('🔍 TradingPanel: Looking for symbol:', currentSymbol);
        console.log('🔍 TradingPanel: Available symbols in price cache:', Object.keys(data.price_cache));
      }
      
      if (!effectivePrice) {
        console.log('🔍 TradingPanel: Market order requires current price - no price available from any source');
        console.log('🔍 TradingPanel: Available data:', { 
          currentPrice, 
          price, 
          cryptoDataSize: cryptoData ? cryptoData.size : 0,
          priceCacheKeys: data && data.price_cache ? Object.keys(data.price_cache) : [],
          currentSymbol 
        });
        return;
      }
    } else {
      // For limit orders, ensure we have price
      if (!price) {
        console.log('🔍 TradingPanel: Limit order requires price');
        return;
      }
      effectivePrice = parseFloat(price);
    }

    // Calculate trade value and validate
    let tradeValue;
    let finalTradeAmount;
    
    if (sizeUnit === 'USDT') {
      // Size is already in USDT
      tradeValue = tradeAmount;
      finalTradeAmount = tradeValue / effectivePrice; // Convert to crypto amount for backend
    } else {
      // Size is in crypto amount
      finalTradeAmount = tradeAmount; // Keep as crypto amount
      tradeValue = finalTradeAmount * effectivePrice; // Calculate USDT value
    }
    
    const availableBalance = paper_balance || 100000; // Default to $100k if not available
    
    // Check if trade value exceeds balance
    if (activeTab === 'buy' && tradeValue > availableBalance) {
      const maxAmount = availableBalance / effectivePrice;
      const maxUSDT = availableBalance;
      const maxCrypto = maxAmount;
      
      let errorMessage = `Insufficient balance!\n\nYou have $${availableBalance.toLocaleString()} available.\n`;
      
      if (sizeUnit === 'USDT') {
        errorMessage += `Maximum USDT you can spend: $${maxUSDT.toLocaleString()}\n`;
      } else {
        errorMessage += `Maximum ${currentSymbol.replace('USDT', '')} you can buy: ${maxCrypto.toFixed(4)}\n`;
      }
      
      window.alert(errorMessage);
      return;
    }

    // Warn about very large trades (more than 50% of balance)
    if (tradeValue > availableBalance * 0.5) {
      const confirmLarge = window.confirm(
        `Large trade detected!\n\n` +
        `Trade value: $${tradeValue.toLocaleString()}\n` +
        `Available balance: $${availableBalance.toLocaleString()}\n` +
        `This trade uses ${((tradeValue / availableBalance) * 100).toFixed(1)}% of your balance.\n\n` +
        `Are you sure you want to proceed?`
      );
      if (!confirmLarge) {
        return;
      }
    }

    // Generate a unique trade ID to prevent duplicates
    const tradeId = `${currentSymbol}-${orderType}-${Date.now()}-${Math.random()}`;
    
    // Check if this is a duplicate of the last trade
    if (lastTradeId === tradeId) {
      console.log('🔍 TradingPanel: Duplicate trade detected, ignoring');
      return;
    }

    setIsExecuting(true);
    setLastTradeId(tradeId);
    
    try {
      const tradeData = {
        symbol: currentSymbol,
        direction: activeTab,
        amount: finalTradeAmount,
        order_type: orderType,
        price: effectivePrice,
        strategy: 'manual',
        ai_confidence: 0.0,
        trade_id: tradeId, // Add trade ID to prevent duplicates
        trade_type: activeTab === 'buy' ? 'LONG' : 'SHORT', // Set correct trade type
        margin_mode: marginMode, // Add margin mode to trade data
        leverage: leverage // Add leverage to trade data
      };

      console.log('🔍 TradingPanel: Executing paper trade with data:', tradeData);
      await executePaperTrade(tradeData);
      
      // Refresh positions after trade execution
      setTimeout(() => {
        if (isConnected) {
          console.log('🔍 TradingPanel: Refreshing positions after trade execution');
          getPositions();
        }
      }, 1000);
      
      // Reset form
      setSize('');
      setPrice('');
      
      // Show success message
      setLastTrade({
        symbol: currentSymbol,
        direction: activeTab,
        amount: finalTradeAmount,
        price: effectivePrice,
        timestamp: new Date()
      });
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setLastTrade(null);
      }, 5000);
      
    } catch (error) {
      console.error('🔍 TradingPanel: Trade execution failed:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleClosePosition = async (symbol) => {
    if (!isConnected) return;
    
    try {
      await closePosition(symbol);
    } catch (error) {
      console.error('🔍 TradingPanel: Failed to close position:', error);
    }
  };

  const calculateCost = () => {
    if (!size) return 0;
    
    // For market orders, use current price; for limit orders, use entered price
    let effectivePrice = null;
    
    if (orderType === 'market') {
      if (currentPrice) {
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

  // Get current price from multiple sources
  const getCurrentPrice = () => {
    if (currentPrice) return currentPrice;
    if (data && data.price_cache && data.price_cache[currentSymbol]) {
      return data.price_cache[currentSymbol].price;
    }
    if (data && data.price_cache) {
      const baseSymbol = currentSymbol.replace('USDT', '');
      if (data.price_cache[baseSymbol]) {
        return data.price_cache[baseSymbol].price;
      }
    }
    if (cryptoData && cryptoData.size > 0) {
      const crypto = Array.from(cryptoData.values()).find(
        c => c.symbol === currentSymbol
      );
      if (crypto && crypto.current_price) {
        return crypto.current_price;
      }
    }
    return null;
  };

  // Get max available amount for current unit
  const getMaxAmount = () => {
    const currentPrice = getCurrentPrice();
    const availableBalance = paper_balance || 100000;
    
    if (!currentPrice || availableBalance <= 0) return 0;
    
    // Apply margin mode logic
    let effectiveBalance = availableBalance;
    
    if (marginMode === 'isolated') {
      // In isolated mode, we can use the full balance for this position
      effectiveBalance = availableBalance;
    } else {
      // In cross mode, we need to consider existing positions
      const totalPositionValue = Object.values(positions).reduce((total, pos) => {
        return total + Math.abs(pos.amount * pos.avg_price);
      }, 0);
      
      // Reserve some balance for other positions in cross mode
      effectiveBalance = availableBalance - (totalPositionValue * 0.1); // Reserve 10% for safety
    }
    
    if (sizeUnit === 'USDT') {
      return Math.max(0, effectiveBalance);
    } else {
      return Math.max(0, effectiveBalance / currentPrice);
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
    console.log('🔍 TradingPanel: State updated:', {
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
      positions: Object.keys(positions || {}).length,
      currentPosition,
      tradeValue,
      hasEnoughBalance: currentPrice && size ? currentPrice * parseFloat(size) <= paper_balance : false,
      hasPosition: currentPosition ? Math.abs(currentPosition.amount) > 0 : false,
      lastTrade,
      lastTradeId
    });
  }, [activeTab, amount, orderType, leverage, marginMode, price, size, sizeUnit, sizeSliderValue, useTpSl, reduceOnly, isExecuting, currentPrice, currentSymbol, paper_balance, positions, currentPosition]);

  // Handle order type change
  const handleOrderTypeChange = (newOrderType) => {
    setOrderType(newOrderType);
    // For market orders, set price to current price or crypto data
    if (newOrderType === 'market') {
      if (currentPrice && typeof currentPrice === 'number' && !isNaN(currentPrice)) {
        setPrice(currentPrice.toFixed(2));
        console.log('🔍 TradingPanel: Setting market price from currentPrice:', currentPrice.toFixed(2));
      } else if (cryptoData && cryptoData.size > 0) {
        const crypto = Array.from(cryptoData.values()).find(
          c => c.symbol === currentSymbol
        );
        if (crypto && crypto.current_price && typeof crypto.current_price === 'number' && !isNaN(crypto.current_price)) {
          setPrice(crypto.current_price.toFixed(2));
          console.log('🔍 TradingPanel: Setting market price from crypto data:', crypto.current_price.toFixed(2));
        }
      } else if (data && data.price_cache && data.price_cache[currentSymbol]) {
        const price = data.price_cache[currentSymbol].price;
        if (typeof price === 'number' && !isNaN(price)) {
          setPrice(price.toFixed(2));
          console.log('🔍 TradingPanel: Setting market price from WebSocket price cache:', price.toFixed(2));
        }
      } else if (data && data.price_cache) {
        const baseSymbol = currentSymbol.replace('USDT', '');
        if (data.price_cache[baseSymbol]) {
          const price = data.price_cache[baseSymbol].price;
          if (typeof price === 'number' && !isNaN(price)) {
            setPrice(price.toFixed(2));
            console.log('🔍 TradingPanel: Setting market price from base symbol price cache:', baseSymbol, price.toFixed(2));
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
      <div className="balance-section">
        <div className="balance-info">
          <span className="balance-label">Available Balance</span>
          <span className="balance-amount">{paper_balance?.toLocaleString() || '0'} USDT</span>
        </div>
        <div className="margin-info">
          <span className="margin-mode-indicator">
            {marginMode === 'isolated' ? <FiLock size={12} /> : <FiLink size={12} />} {marginMode.charAt(0).toUpperCase() + marginMode.slice(1)} Margin
          </span>
          <span className="leverage-indicator">
                          <FiZap size={12} /> {leverage}x Leverage
          </span>
        </div>
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
        {/* Price Input */}
        <div className="form-group">
          <label className="form-label">
            Price {orderType === 'market' && <span className="market-indicator">(Market Price)</span>}
          </label>
          <div className="input-group">
            <input
              type="number"
              value={orderType === 'market' ? '' : price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder={orderType === 'market' ? 'Market' : '0.00'}
              className={`form-input ${orderType === 'market' ? 'disabled' : ''}`}
              step="0.01"
              min="0"
              disabled={orderType === 'market'}
            />
            <span className="input-suffix">USDT</span>
          </div>
          {orderType === 'market' && (
            <div className="market-price-info">
              <span className="current-price-label">Current Market Price:</span>
              <span className="current-price-value">
                ${(() => {
                  // Get real-time current price from multiple sources
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
                  return 'Loading...';
                })()}
              </span>
            </div>
          )}
          {orderType === 'market' && !currentPrice && !price && (
            <div className="market-price-info loading">
              <span className="current-price-label">Loading price...</span>
            </div>
          )}
        </div>

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