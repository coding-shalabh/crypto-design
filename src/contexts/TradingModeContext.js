import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWebSocket } from './WebSocketContext';

const TradingModeContext = createContext();

export const useTradingMode = () => {
  const context = useContext(TradingModeContext);
  if (!context) {
    throw new Error('useTradingMode must be used within a TradingModeProvider');
  }
  return context;
};

export const TradingModeProvider = ({ children }) => {
  const { sendMessage, isConnected } = useWebSocket();
  
  // Load saved trading mode from localStorage or default to mock
  const [isLiveMode, setIsLiveMode] = useState(() => {
    const saved = localStorage.getItem('tradingMode');
    return saved === 'live';
  });

  // Save trading mode to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('tradingMode', isLiveMode ? 'live' : 'mock');
  }, [isLiveMode]);

  // 🔥 NEW: Send trading mode to backend when it changes
  useEffect(() => {
    if (isConnected && sendMessage) {
      const mode = isLiveMode ? 'live' : 'mock';
      sendMessage({
        type: 'set_trading_mode',
        data: { mode }
      });
      console.log('TradingModeContext: Sent trading mode to backend:', mode);
      
      // 🔥 NEW: Request fresh balance after mode change
      setTimeout(() => {
        if (isConnected && sendMessage) {
          sendMessage({
            type: 'get_trading_balance',
            data: { asset: 'USDT', mode }
          });
          console.log('TradingModeContext: Requested fresh balance for mode:', mode);
        }
      }, 1000); // Wait 1 second for mode to be set
    }
  }, [isLiveMode, isConnected, sendMessage]);

  const toggleTradingMode = () => {
    setIsLiveMode(prev => !prev);
  };

  const value = {
    isLiveMode,
    tradingMode: isLiveMode ? 'live' : 'mock',
    setIsLiveMode,
    toggleTradingMode
  };

  return (
    <TradingModeContext.Provider value={value}>
      {children}
    </TradingModeContext.Provider>
  );
};

export default TradingModeContext;