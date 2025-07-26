import React, { useState, useEffect } from 'react';
import { FiInfo, FiDollarSign } from 'react-icons/fi';
import { useTradingMode } from '../contexts/TradingModeContext';
import './TradingBalanceDisplay.css';

const TradingBalanceDisplay = ({ isConnected, sendMessage, data, mode }) => {
  const { isLiveMode, tradingMode } = useTradingMode();
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Use mode prop if provided, otherwise use context
  const currentMode = mode || tradingMode;
  const currentIsLiveMode = mode ? mode === 'live' : isLiveMode;


  // Load balance when component mounts or mode changes (with debouncing)
  useEffect(() => {
    if (isConnected) {
      // Debounce balance requests to prevent rapid API calls
      const timeoutId = setTimeout(() => {
        sendMessage({ type: 'get_trading_balance', mode: currentMode });
      }, 100); // 100ms debounce
      
      return () => clearTimeout(timeoutId);
    }
  }, [isConnected, sendMessage, currentMode]);

  // Listen for balance updates from websocket data
  useEffect(() => {
    if (data) {
      
      // Check for trading balance response (new direct handling)
      if (data.trading_balance) {
        setBalance(data.trading_balance);
        setLoading(false);
        setLastUpdate(new Date());
      }
      // Check for trading balance response (legacy format)
      else if (data.type === 'trading_balance' && data.data && data.data.balance) {
        setBalance(data.data.balance);
        setLoading(false);
        setLastUpdate(new Date());
      }
      // Also check if balance is directly in data (for ongoing updates)
      else if (data.trading_balance) {
        setBalance(data.trading_balance);
        setLoading(false);
        setLastUpdate(new Date());
      }
      // Check for paper balance (fallback for mock mode)
      else if (data.paper_balance !== undefined && currentMode === 'mock') {
        const mockBalance = {
          asset: 'USDT',
          free: data.paper_balance,
          locked: 0,
          total: data.paper_balance,
          wallet_type: 'MOCK',
          mode: currentMode
        };
        setBalance(mockBalance);
        setLoading(false);
        setLastUpdate(new Date());
      }
    }
  }, [data, currentMode]);

  const loadTradingBalance = async () => {
    if (!isConnected || !sendMessage) {
      return;
    }

    setLoading(true);
    
    try {
      // Request trading balance via websocket
      sendMessage({
        type: 'get_trading_balance',
        data: { asset: 'USDT' },
        mode: currentMode
      });

      // Set timeout to stop loading if no response
      setTimeout(() => {
        if (loading) {
          setLoading(false);
        }
      }, 15000); // Increased timeout
    } catch (error) {
      setLoading(false);
    }
  };

  const formatBalance = (amount) => {
    if (!amount && amount !== 0) return '0';
    return parseFloat(amount).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const getWalletTypeDisplay = (walletType) => {
    const walletIcons = {
      'SPOT': '💰',
      'FUTURES': '📈',
      'MARGIN': '⚖️',
      'FUNDING': '💳',
      'MOCK': '🎯',
      'MOCK_FALLBACK': '⚠️'
    };
    
    const walletNames = {
      'SPOT': 'Spot Wallet',
      'FUTURES': 'Futures Wallet',
      'MARGIN': 'Margin Wallet',
      'FUNDING': 'Funding Wallet',
      'MOCK': 'Mock Trading',
      'MOCK_FALLBACK': 'Mock (Fallback)'
    };
    
    return {
      icon: walletIcons[walletType] || '💰',
      name: walletNames[walletType] || walletType
    };
  };

  const getBalanceStatus = () => {
    if (!balance) return { status: 'unknown', message: 'No balance data' };
    
    if (balance.available_for_trading) {
      return { 
        status: 'ready', 
        message: 'Ready for trading',
        color: '#10b981'
      };
    } else if (balance.total > 0 && balance.free === 0) {
      return { 
        status: 'locked', 
        message: 'Balance locked in orders',
        color: '#f59e0b'
      };
    } else if (balance.total === 0) {
      return { 
        status: 'empty', 
        message: 'No balance available',
        color: '#ef4444'
      };
    } else {
      return { 
        status: 'unknown', 
        message: 'Status unknown',
        color: '#6b7280'
      };
    }
  };

  const getBalanceInfo = () => {
    if (!balance) return { text: 'Unknown', icon: '❓' };
    
    if (balance.wallet_type === 'FUTURES') {
      return {
        text: 'Futures Wallet - Used for live trading',
        icon: '📈',
        detail: 'This balance is from your Binance Futures wallet and will be used for actual trading.'
      };
    } else if (balance.wallet_type === 'MOCK' || balance.wallet_type === 'MOCK_FALLBACK') {
      return {
        text: 'Virtual Balance - Paper trading only',
        icon: '🧪',
        detail: 'This is a virtual balance for paper trading simulation. No real money is involved.'
      };
    } else if (balance.wallet_type === 'SPOT') {
      return {
        text: 'Spot Wallet',
        icon: '💰',
        detail: 'This balance is from your Binance Spot wallet.'
      };
    } else {
      return {
        text: 'Trading Balance',
        icon: '💰',
        detail: `Balance for ${currentMode} trading mode.`
      };
    }
  };

  const balanceInfo = getBalanceInfo();

  // Get effective balance based on mode
  const getEffectiveBalance = () => {
    if (!balance) {
      // If no balance data but we have paper_balance in data, use it for mock mode
      if (data && data.paper_balance !== undefined && currentMode === 'mock') {
        return {
          total: data.paper_balance,
          free: data.paper_balance,
          locked: 0,
          wallet_type: 'MOCK'
        };
      }
      return null;
    }
    return balance;
  };

  const effectiveBalance = getEffectiveBalance();

  return (
    <div className="trading-balance-display">
      <div className="balance-header">
        <FiDollarSign className="balance-icon" />
        <span className="balance-label">Trading Balance</span>
        <div 
          className="info-tooltip-container"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <FiInfo className="info-icon" />
          {showTooltip && (
            <div className="tooltip">
              <div className="tooltip-header">
                <span className="tooltip-icon">{balanceInfo.icon}</span>
                <span className="tooltip-title">{balanceInfo.text}</span>
              </div>
              <div className="tooltip-body">
                {balanceInfo.detail}
              </div>
              {effectiveBalance && (
                <div className="tooltip-details">
                  <div className="detail-row">
                    <span>Free:</span>
                    <span>{formatBalance(effectiveBalance.free)} USDT</span>
                  </div>
                  <div className="detail-row">
                    <span>Locked:</span>
                    <span>{formatBalance(effectiveBalance.locked)} USDT</span>
                  </div>
                  <div className="detail-row">
                    <span>Mode:</span>
                    <span className={`mode-indicator ${currentMode}`}>{currentMode.toUpperCase()}</span>
                  </div>
                  {lastUpdate && (
                    <div className="detail-row">
                      <span>Updated:</span>
                      <span>{lastUpdate.toLocaleTimeString()}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="balance-amount">
        {loading ? (
          <div className="loading-balance">
            <div className="loading-spinner"></div>
            <span>Loading...</span>
          </div>
        ) : (
          <>
            <div className="balance-main">
              <span className="amount">{formatBalance(effectiveBalance?.total || 0)}</span>
              <span className="currency">USDT</span>
            </div>
            
            <div className="balance-details">
              <div className="wallet-info">
                <span className="wallet-icon">
                  {getWalletTypeDisplay(effectiveBalance?.wallet_type).icon}
                </span>
                <span className="wallet-name">
                  {getWalletTypeDisplay(effectiveBalance?.wallet_type).name}
                </span>
              </div>
              
              {effectiveBalance && (
                <div className="balance-status" style={{ color: getBalanceStatus().color }}>
                  <span className="status-indicator">●</span>
                  <span className="status-text">{getBalanceStatus().message}</span>
                </div>
              )}
              
              {effectiveBalance?.free !== effectiveBalance?.total && effectiveBalance?.total > 0 && (
                <div className="free-balance">
                  Free: {formatBalance(effectiveBalance?.free || 0)} USDT
                </div>
              )}
            </div>
          </>
        )}
      </div>
      
      <button 
        className="refresh-balance" 
        onClick={loadTradingBalance} 
        disabled={loading || !isConnected}
        title="Refresh balance"
      >
        <span className={`refresh-icon ${loading ? 'spinning' : ''}`}>↻</span>
      </button>
    </div>
  );
};

export default TradingBalanceDisplay;