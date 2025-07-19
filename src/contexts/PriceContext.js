import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWebSocket } from './WebSocketContext';

const PriceContext = createContext();

export const usePrices = () => {
  const context = useContext(PriceContext);
  if (!context) {
    throw new Error('usePrices must be used within a PriceProvider');
  }
  return context;
};

export const PriceProvider = ({ children }) => {
  const { data } = useWebSocket();
  const [prices, setPrices] = useState(new Map());
  const [priceChanges, setPriceChanges] = useState(new Map());
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');

  // Initialize with some default data to prevent loading issues
  useEffect(() => {
    if (prices.size === 0) {
      const defaultPrices = new Map();
      const defaultSymbols = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT'];
      
      defaultSymbols.forEach(symbol => {
        defaultPrices.set(symbol, {
          price: 0,
          volume_24h: 0,
          price_change_24h: 0,
          high_24h: 0,
          low_24h: 0,
          timestamp: Date.now()
        });
      });
      
      setPrices(defaultPrices);
    }
  }, []);

  // Update prices from WebSocket data
  useEffect(() => {
    if (data && data.crypto_data && Array.isArray(data.crypto_data) && data.crypto_data.length > 0) {
      const newPrices = new Map();
      const newChanges = new Map();
      
      data.crypto_data.forEach(item => {
        if (item.symbol && item.price) {
          const previousPrice = prices.get(item.symbol);
          newPrices.set(item.symbol, {
            price: item.price,
            volume_24h: item.volume_24h || 0,
            price_change_24h: item.price_change_24h || 0,
            high_24h: item.high_24h || item.price,
            low_24h: item.low_24h || item.price,
            timestamp: Date.now()
          });
          
          // Track price changes for animations
          if (previousPrice && previousPrice.price !== item.price) {
            newChanges.set(item.symbol, {
              direction: item.price > previousPrice.price ? 'up' : 'down',
              timestamp: Date.now()
            });
          }
        }
      });
      
      if (newPrices.size > 0) {
        setPrices(newPrices);
        setPriceChanges(newChanges);
        
        // Clear price change indicators after 2 seconds
        setTimeout(() => {
          setPriceChanges(new Map());
        }, 2000);
      }
    }
  }, [data]);

  // Update from price cache if available
  useEffect(() => {
    if (data && data.price_cache) {
      const newPrices = new Map(prices);
      
      Object.entries(data.price_cache).forEach(([symbol, priceData]) => {
        if (priceData && priceData.price) {
          newPrices.set(symbol, {
            price: priceData.price,
            volume_24h: priceData.volume_24h || 0,
            price_change_24h: priceData.price_change_24h || 0,
            high_24h: priceData.high_24h || priceData.price,
            low_24h: priceData.low_24h || priceData.price,
            timestamp: Date.now()
          });
        }
      });
      
      setPrices(newPrices);
    }
  }, [data?.price_cache]);

  const getPrice = (symbol) => {
    const priceData = prices.get(symbol);
    return priceData ? priceData.price : 0;
  };

  const getPriceData = (symbol) => {
    return prices.get(symbol) || {
      price: 0,
      volume_24h: 0,
      price_change_24h: 0,
      high_24h: 0,
      low_24h: 0,
      timestamp: 0
    };
  };

  const getPriceChange = (symbol) => {
    return priceChanges.get(symbol);
  };

  const getFormattedPrice = (symbol, decimals = 2) => {
    const price = getPrice(symbol);
    return price.toFixed(decimals);
  };

  const getTopMovers = (limit = 10) => {
    const symbols = Array.from(prices.values())
      .sort((a, b) => Math.abs(b.price_change_24h) - Math.abs(a.price_change_24h))
      .slice(0, limit);
    return symbols;
  };

  const contextValue = {
    prices,
    priceChanges,
    selectedSymbol,
    setSelectedSymbol,
    getPrice,
    getPriceData,
    getPriceChange,
    getFormattedPrice,
    getTopMovers
  };

  return (
    <PriceContext.Provider value={contextValue}>
      {children}
    </PriceContext.Provider>
  );
};