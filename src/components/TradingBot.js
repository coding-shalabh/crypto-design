import { 
  FiPlay, 
  FiSquare, 
  FiSettings, 
  FiTrendingUp, 
  FiTrendingDown,
  FiDollarSign,
  FiClock,
  FiTarget,
  FiShield,
  FiZap,
  FiActivity,
  FiBarChart2,
  FiCheck,
  FiX
} from 'react-icons/fi';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useTradingMode } from '../contexts/TradingModeContext';
import './TradingBot.css';
import { BiChart, BiDollar, BiTargetLock, BiUpvote } from 'react-icons/bi';
import { CiAlignBottom, CiBadgeDollar, CiBag1, CiCalendar, CiChartLine, CiChat1, CiDollar, CiFlag1, CiRepeat, CiSaveUp1, CiWavePulse1 } from 'react-icons/ci';
import { CiWallet } from 'react-icons/ci';
import { MdCandlestickChart } from 'react-icons/md';
import { toast } from 'react-toastify';
import tradingService from '../services/tradingService';
import { GrTarget } from 'react-icons/gr';
import { useState, useEffect } from 'react';

const TradingBot = ({ isConnected, startBot, stopBot, getBotStatus, updateBotConfig, getBotConfig, sendMessage, data, lastConnectionCheck, connectionErrorDetails }) => {
  
  // Get WebSocket context for real-time updates
  const { lastMessage } = useWebSocket();
  
  // Get trading mode context
  const { isLiveMode, tradingMode } = useTradingMode();

  
  const [botEnabled, setBotEnabled] = useState(false);
  
  const [botConfig, setBotConfig] = useState({
    max_trades_per_day: 10,
    trade_amount_usdt: 50,
    max_amount_per_trade_usdt: 500,
    leverage_per_trade: 5,
    profit_target_min: 3,  // Aligned with backend: 3% take profit
    profit_target_max: 5,
    stop_loss_percent: 1.5,  // Aligned with backend: 1.5% stop loss
    trailing_enabled: true,
    trailing_trigger_usd: 1,
    trailing_distance_usd: 0.5,
    trade_interval_secs: 600,
    max_concurrent_trades: 20,  // Aligned with backend: 20 max concurrent trades
    cooldown_secs: 300,
    allowed_pairs: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    ai_confidence_threshold: 0.65,
    run_time_minutes: 180,
    test_mode: false,
    risk_per_trade_percent: 5.0,  // Aligned with backend: 5% max position per trade
    monitor_open_trades: true,
    loss_check_interval_percent: 1,
    rollback_enabled: true,
    reanalysis_cooldown_seconds: 300,
    reconfirm_before_entry: true,
    slippage_tolerance_percent: 0.1,
    signal_sources: ['gpt', 'claude'],
    manual_approval_mode: false
  });
  
  const [botStatus, setBotStatus] = useState({
    enabled: false,
    start_time: null,
    active_trades: 0,
    trades_today: 0,
    total_profit: 0,
    total_trades: 0,
    winning_trades: 0,
    win_rate: 0,
    pair_status: {},
    running_duration: 0
  });
  
  const [activeTrades, setActiveTrades] = useState({});
  
  const [tradeHistory, setTradeHistory] = useState([]);
  
  const [analysisLogs, setAnalysisLogs] = useState([]);
  
  const [tradeLogs, setTradeLogs] = useState([]);
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configLoading, setConfigLoading] = useState(false);
  
  // Wallet management state
  const [showWalletModal, setShowWalletModal] = useState(false);
  const [categorizedBalances, setCategorizedBalances] = useState({});
  const [selectedWallet, setSelectedWallet] = useState('FUTURES');
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferData, setTransferData] = useState({
    asset: 'USDT',
    amount: '',
    fromWallet: 'SPOT',
    toWallet: 'FUTURES'
  });
  const [showInsufficientBalanceModal, setShowInsufficientBalanceModal] = useState(false);
  const [insufficientBalanceData, setInsufficientBalanceData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Available trading pairs
  const availablePairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'];

  // Track whether config has been loaded to prevent overriding user changes
  const [configLoaded, setConfigLoaded] = useState(false);

  useEffect(() => {
    if (isConnected) {
      getBotStatus();
      
      // Only load config on first connection to prevent overriding user changes
      if (!configLoaded) {
        getBotConfig(); 
        setConfigLoaded(true);
      }
      
      // Request additional data for all sections
      requestAllData();
      
      // Fetch categorized balances when connected
      fetchCategorizedBalances();
    } else {
    }
  }, [isConnected, getBotStatus, getBotConfig, configLoaded]);

  // 🔥 NEW: Sync bot status from global WebSocket data
  useEffect(() => {
    if (data.bot_status) {
      setBotStatus(prevStatus => ({
        ...prevStatus,
        ...data.bot_status
      }));
      setBotEnabled(data.bot_status.enabled || false);
    }
  }, [data.bot_status]);

  // 🔥 NEW: Handle trading mode changes
  useEffect(() => {
    if (isConnected) {
      // Refresh all data when trading mode changes
      requestAllData();
    }
  }, [tradingMode, isLiveMode, isConnected]);

  // Request all required data for the trading bot dashboard
  const requestAllData = () => {
    if (!isConnected || !sendMessage) return;

    try {
      // Request bot status first
      sendMessage({ type: 'get_bot_status' });

      // Request positions (active trades)
      sendMessage({ type: 'get_positions' });

      // Request trade history from MongoDB with mode parameter
      sendMessage({ type: 'get_trade_history', limit: 100, mode: isLiveMode ? 'live' : 'mock' });

      // Request analysis logs
      sendMessage({ type: 'get_analysis_logs', limit: 50 });

      // Request trade logs with confidence scores
      sendMessage({ type: 'get_trade_logs', limit: 50 });

    } catch (error) {
    }
  };

  // Real-time data refresh every 2 seconds
  useEffect(() => {
    if (!isConnected) return;
    
    const interval = setInterval(() => {
      if (isConnected && sendMessage) {
        // Request updated bot status and positions
        sendMessage({ type: 'get_bot_status' });
        sendMessage({ type: 'get_positions' });
        // Request trade history with current mode
        sendMessage({ type: 'get_trade_history', limit: 100, mode: isLiveMode ? 'live' : 'mock' });
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isConnected, sendMessage, isLiveMode]);

  // Global message handler for bot responses
  const handleBotResponse = (message) => {
    const { type, data } = message;
    
    if (type === 'bot_status_response') {
      setBotStatus(data);
      setBotEnabled(data.enabled);
      
      // 🔥 NEW: Extract trading balance and update data state if available
      if (data.trading_balance) {
        // Note: The data prop is managed by the parent component, so we just log the balance
        // The parent component should handle updating the global data state
      }
      
      // Convert active_trades array to object with symbol keys
      if (data.active_trades && Array.isArray(data.active_trades)) {
        const activeTradesObject = {};
        data.active_trades.forEach(trade => {
          if (trade.symbol) {
            activeTradesObject[trade.symbol] = {
              symbol: trade.symbol,
              amount: trade.amount || 0,
              entry_price: trade.entry_price || 0,
              current_price: trade.entry_price || 0, // Use entry_price as current_price if not provided
              unrealized_pnl: 0, // Will be calculated from positions data
              direction: trade.action === 'BUY' ? 'long' : 'short',
              margin_used: trade.amount || 0,
              trade_value: trade.amount || 0,
              confidence_score: trade.confidence || 0
            };
          }
        });
        setActiveTrades(activeTradesObject);
      }
      
    } else if (type === 'categorized_balances_response') {
      setCategorizedBalances(data);
    } else if (type === 'wallet_transfer_result') {
      if (data.success) {
        toast.success(data.message || 'Transfer completed successfully');
        fetchCategorizedBalances(); // Refresh balances
      } else {
        toast.error(data.message || 'Transfer failed');
      }
    } else if (type === 'insufficient_balance_error') {
      setInsufficientBalanceData(data.error_details);
      setShowInsufficientBalanceModal(true);
      toast.error(data.message || 'Insufficient balance for trade');
    } else if (type === 'start_bot_response') {
      if (data.success) {
        setBotEnabled(true);
        // Get updated bot status immediately after starting
        setTimeout(() => {
          getBotStatus();
        }, 1000);
      } else {
      }
    } else if (type === 'stop_bot_response') {
      if (data.success) {
        setBotEnabled(false);
        getBotStatus();
      } else {
      }
    } else if (type === 'update_bot_config_response') {
      if (data.success) {
        setShowConfigModal(false);
        getBotStatus();
      } else {
      }
    } else if (type === 'bot_config_response') {
      if (data.success && data.config) {
        setBotConfig(prevConfig => {
          // Only update if significantly different from current config
          // This prevents overriding user changes with default values
          const hasSignificantChanges = Object.keys(data.config).some(key => 
            JSON.stringify(prevConfig[key]) !== JSON.stringify(data.config[key])
          );
          
          if (hasSignificantChanges || !configLoaded) {
            return data.config;
          } else {
            return prevConfig;
          }
        });
      }
    } else if (type === 'bot_status_update') {
      setBotStatus(prev => {
        const newStatus = { ...prev, ...data };
        return newStatus;
      });
      setBotEnabled(data.enabled);
    } else if (type === 'bot_trade_executed') {
      // Add/update active trade for this symbol
      setActiveTrades(prev => {
        const newTrades = { ...prev, [data.symbol]: data.trade_data };
        return newTrades;
      });
      getBotStatus();
    } else if (type === 'trade_executed') {
      // If this is a bot trade, add to activeTrades
      if (data.trade && data.trade.bot_trade) {
        setActiveTrades(prev => {
          const newTrades = { ...prev, [data.trade.symbol]: data.trade };
          return newTrades;
        });
      }
      // Optionally update positions/trade history here if needed
    } else if (type === 'bot_trade_closed' || type === 'position_closed') {
      // Remove from activeTrades if present
      const symbol = data.symbol || (data.trade && data.trade.symbol);
      if (symbol) {
        setActiveTrades(prev => {
          const newTrades = { ...prev };
          delete newTrades[symbol];
          return newTrades;
        });
      }
      // Add to trade history if trade_record present
      if (data.trade_record) {
        setTradeHistory(prev => [data.trade_record, ...prev]);
      } else if (data.trade) {
        setTradeHistory(prev => [data.trade, ...prev]);
      }
      getBotStatus();
    } else if (type === 'ai_analysis_response') {
      
      // Create analysis log entry
      const analysisLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: 'info',
        message: `AI Analysis completed for ${data.symbol}`,
        grok_sentiment: data.analysis?.grok_analysis?.sentiment || 'N/A',
        claude_confidence: data.analysis?.claude_analysis?.recommendation?.confidence || 0,
        final_action: data.analysis?.final_recommendation?.action || 'HOLD',
        combined_confidence: data.analysis?.combined_confidence || 0,
        source: 'AI Analysis'
      };
      
      setAnalysisLogs(prev => {
        const newLogs = [analysisLog, ...prev.slice(0, 49)];
        return newLogs;
      });
    } else if (type === 'ai_opportunity_alert') {
      
      // Create trade opportunity log entry
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: 'success',
        message: `${data.action} opportunity detected for ${data.symbol}`,
        action: data.action,
        confidence: data.confidence,
        source: 'Trade Opportunity'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
    } else if (type === 'automated_trade_executed') {
      
      // Create successful trade log entry
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: 'success',
        message: ` Automated ${data.action} trade executed for ${data.symbol} at $${data.price}`,
        action: data.action,
        price: data.price,
        source: 'Automated Trade'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
      
      // Add/update active trade for this symbol
      if (data.trade_result && data.trade_result.trade_data) {
        setActiveTrades(prev => {
          const newTrades = { ...prev, [data.symbol]: data.trade_result.trade_data };
          return newTrades;
        });
      }
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'auto_close_notification') {
      
      // Create auto-close notification log entry
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: data.type === 'stop_loss' ? 'error' : 'success',
        message: data.message,
        pnl_usd: data.pnl_usd,
        type: data.type,
        auto_close: true,
        source: 'Auto-Close System'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
      
      // Show prominent auto-close notification
      
    } else if (type === 'automated_trade_failed') {
      
      // Create failed trade log entry
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: 'error',
        message: `❌ Automated ${data.action} trade failed for ${data.symbol}: ${data.error}`,
        action: data.action,
        error: data.error,
        source: 'Automated Trade'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
    } else if (type === 'trade_closed') {
      
      // Remove from active trades
      setActiveTrades(prev => {
        const newTrades = { ...prev };
        delete newTrades[data.symbol];
        return newTrades;
      });
      
      // Create trade closure log entry with enhanced auto-close messaging
      const isAutoClose = data.auto_close || data.reason === 'stop_loss' || data.reason === 'take_profit';
      const emoji = data.reason === 'stop_loss' ? '🛑' : data.reason === 'take_profit' ? '💰' : '📊';
      const message = isAutoClose 
        ? `${emoji} AUTO-CLOSE: ${data.symbol} ${data.reason.replace('_', ' ')} - ${data.pnl_usd >= 0 ? '+' : ''}$${data.pnl_usd.toFixed(2)}`
        : `${emoji} ${data.symbol} closed (${data.reason}): ${data.pnl_usd >= 0 ? '+' : ''}$${data.pnl_usd.toFixed(2)}`;
      
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: data.reason === 'stop_loss' ? 'error' : 'success',
        message: message,
        pnl_usd: data.pnl_usd,
        reason: data.reason,
        auto_close: isAutoClose,
        source: 'Auto-Close System'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
      
      // Show auto-close notification if applicable
      if (isAutoClose) {
        // You can add a toast notification here if you have a notification system
      }
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'rollback_trade_executed') {
      
      // Create rollback trade log entry
      const tradeLog = {
        timestamp: data.timestamp * 1000 || Date.now(),
        symbol: data.symbol,
        level: 'warning',
        message: `🔄 Rollback: ${data.action} ${data.symbol} at $${data.price} (${(data.confidence * 100).toFixed(1)}% confidence)`,
        action: data.action,
        confidence: data.confidence,
        source: 'Rollback Strategy'
      };
      
      setTradeLogs(prev => {
        const newLogs = [tradeLog, ...prev.slice(0, 49)];
        return newLogs;
      });
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'analysis_log') {
      // Ensure the data has the required log structure
      const logEntry = {
        timestamp: data.timestamp || Date.now() / 1000,
        symbol: data.symbol || 'Unknown',
        level: data.level || 'INFO',
        message: data.message || `Analysis for ${data.symbol}`,
        source: data.source || 'Analysis Log'
      };
      
      setAnalysisLogs(prev => {
        const newLogs = [logEntry, ...prev.slice(0, 49)];
        return newLogs;
      });
    } else if (type === 'trade_log') {
      // Ensure the data has the required log structure
      const logEntry = {
        timestamp: data.timestamp || Date.now() / 1000,
        symbol: data.symbol || 'Unknown',
        level: data.level || 'info',
        message: data.message || `Trade action: ${data.action} for ${data.symbol}`,
        action: data.action,
        confidence: data.confidence,
        trade_decision: data.trade_decision || 'N/A',
        final_confidence_score: data.confidence,
        analysis_source: data.source || 'Trade Log',
        confidence_above_threshold: data.confidence_above_threshold || false,
        source: 'Trade Log'
      };
      
      setTradeLogs(prev => {
        const newLogs = [logEntry, ...prev.slice(0, 49)];
        return newLogs;
      });
    } else if (type === 'trade_history_response') {
      if (data.trades) {
        setTradeHistory(data.trades);
      }
    } else if (type === 'analysis_logs_response') {
      if (data.logs) {
        setAnalysisLogs(data.logs);
      }
    } else if (type === 'trade_logs_response') {
      if (data.logs) {
        setTradeLogs(data.logs);
      }
    } else if (type === 'positions_response') {
      // Update active trades from positions data
      if (data.positions) {
        setActiveTrades(data.positions);
      }
    } else {
    }
  };

  // Set up WebSocket message handler
  useEffect(() => {
    
    // Set global bot response handler for WebSocket context
    window.handleBotResponse = handleBotResponse;
    
    // Clean up on unmount
    return () => {
      if (window.handleBotResponse === handleBotResponse) {
        delete window.handleBotResponse;
      }
    };
  }, []);

  // Handle incoming WebSocket messages  
  useEffect(() => {
    if (lastMessage) {
      handleBotResponse(lastMessage);
    }
  }, [lastMessage]);

  // Real-time timer update for running duration
  useEffect(() => {
    let timerInterval;
    
    if (botEnabled && botStatus.start_time) {
      timerInterval = setInterval(() => {
        const currentTime = Math.floor(Date.now() / 1000);
        const startTime = Math.floor(botStatus.start_time);
        const runningDuration = currentTime - startTime;
        
        
        setBotStatus(prev => {
          const newStatus = { ...prev, running_duration: runningDuration };
          return newStatus;
        });
      }, 1000); // Update every second
    }
    
    return () => {
      if (timerInterval) {
        clearInterval(timerInterval);
      }
    };
  }, [botEnabled, botStatus.start_time]);

  const handleStartBot = async () => {
    if (!isConnected) {
      toast.error('Cannot start bot - WebSocket not connected');
      return;
    }
    
    // Check futures balance if in live mode
    if (isLiveMode) {
      try {
        const futuresBalance = await tradingService.getTradingBalance('USDT');
        
        // Handle API credential errors
        if (futuresBalance && futuresBalance.error === 'API credentials not configured') {
          toast.error('Cannot start bot: Binance API credentials are not configured. Please set up your API keys first.');
          return;
        }
        
        // Check if futures balance is zero or very low
        if (futuresBalance && (futuresBalance.total === 0 || futuresBalance.total < 5)) {
          // Get spot balance for transfer suggestions
          try {
            const allBalances = await tradingService.getAllTradingBalances();
            const spotUSDT = allBalances?.balances?.spot?.USDT;
            
            let availableForTransfer = 0;
            if (spotUSDT && spotUSDT.free > 0) {
              availableForTransfer = spotUSDT.free;
            }
            
            // Show insufficient balance modal with transfer suggestions
            setInsufficientBalanceData({
              required_amount: Math.max(50, futuresBalance.total === 0 ? 100 : 50), // Minimum suggested amount
              available_amount: futuresBalance.total || 0,
              asset: 'USDT',
              current_wallet: 'FUTURES',
              transfer_suggestions: availableForTransfer > 0 ? [{
                from_wallet: 'SPOT',
                to_wallet: 'FUTURES',
                available_amount: availableForTransfer
              }] : [],
              message: futuresBalance.total === 0 
                ? 'Your Futures wallet is empty. You need USDT in your Futures wallet to start live trading.'
                : `Your Futures wallet balance is very low (${futuresBalance.total} USDT). We recommend having at least 50 USDT for effective trading.`
            });
            setShowInsufficientBalanceModal(true);
            return;
          } catch (balanceError) {
            toast.error('Cannot start bot: Futures wallet balance is insufficient and unable to check transfer options.');
            return;
          }
        }
        
        if (futuresBalance && futuresBalance.total < 20) {
          const proceed = window.confirm(
            `Warning: Your futures wallet balance is low (${futuresBalance.total} USDT). ` +
            'We recommend having at least 20 USDT for effective trading. Do you want to proceed anyway?'
          );
          if (!proceed) {
            return;
          }
        }
      } catch (error) {
        toast.error('Cannot start bot: Failed to verify futures balance. Please check your connection and API credentials.');
        return;
      }
    }
    
    const confirmed = window.confirm(
      'Are you sure you want to start the trading bot? This will begin automatic trading based on your configuration.'
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      // Include trading mode in the config
      const configWithMode = {
        ...botConfig,
        trading_mode: tradingMode,
        is_live_mode: isLiveMode
      };
      await startBot(configWithMode);
    } catch (error) {
      toast.error('Failed to start bot: ' + error.message);
    }
  };

  const handleStopBot = async () => {
    if (!isConnected) {
      return;
    }
    
    const confirmed = window.confirm(
      'Are you sure you want to stop the trading bot? This will close all active trades.'
    );
    
    if (!confirmed) {
      return;
    }
    
    try {
      await stopBot();
    } catch (error) {
    }
  };

  const handleUpdateConfig = async (newConfig) => {
    if (!isConnected) {
      toast.error('Cannot update configuration - not connected to server');
      return;
    }
    
    setConfigLoading(true);
    try {
      // Include trading mode in the config
      const configWithMode = {
        ...newConfig,
        trading_mode: tradingMode,
        is_live_mode: isLiveMode
      };
      await updateBotConfig(configWithMode);
      toast.success('Configuration saved successfully!');
    } catch (error) {
      toast.error('Failed to save configuration. Please try again.');
    } finally {
      setConfigLoading(false);
    }
  };

  // Wallet management functions
  const fetchCategorizedBalances = async () => {
    try {
      if (sendMessage) {
        sendMessage({
          type: 'get_categorized_balances'
        });
      }
    } catch (error) {
      toast.error('Failed to fetch wallet balances');
    }
  };

  const executeTransfer = async () => {
    try {
      if (!transferData.asset || !transferData.amount || !transferData.fromWallet || !transferData.toWallet) {
        toast.error('Please fill in all transfer details');
        return;
      }

      if (parseFloat(transferData.amount) <= 0) {
        toast.error('Transfer amount must be greater than 0');
        return;
      }

      if (transferData.fromWallet === transferData.toWallet) {
        toast.error('Source and destination wallets cannot be the same');
        return;
      }

      if (sendMessage) {
        sendMessage({
          type: 'transfer_between_wallets',
          data: {
            asset: transferData.asset,
            amount: parseFloat(transferData.amount),
            from_wallet: transferData.fromWallet,
            to_wallet: transferData.toWallet
          }
        });
        
        toast.info('Transfer initiated...');
        setShowTransferModal(false);
        
        // Refresh balances after transfer
        setTimeout(() => {
          fetchCategorizedBalances();
        }, 2000);
      }
    } catch (error) {
      toast.error('Failed to execute transfer');
    }
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const renderOverview = () => {
    // Calculate real-time statistics from available data
    const positions = data?.positions || {};
    // Use live balance when in live mode, otherwise use paper balance
    const balance = isLiveMode ? (data?.trading_balance?.total || 0) : (data?.paper_balance || 0);
    const recentTrades = data?.recent_trades || [];
    
    // Calculate stats from available data
    const totalPositions = Object.keys(positions).length;
    const totalValue = Object.values(positions).reduce((sum, pos) => sum + (pos.trade_value || 0), 0);
    const totalPnL = Object.values(positions).reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
    
    // 🔥 UPDATED: Use mode-specific bot statistics
    const botStats = botStatus || {};
    
    // Use mode-specific statistics based on current trading mode
    const modePrefix = isLiveMode ? 'live_' : 'mock_';
    const totalTrades = botStats[`${modePrefix}total_trades`] || botStats.total_trades || 0;
    const winningTrades = botStats[`${modePrefix}winning_trades`] || botStats.winning_trades || 0;
    const tradestoday = botStats[`${modePrefix}trades_today`] || botStats.trades_today || 0;
    const totalProfit = botStats[`${modePrefix}total_profit`] || botStats.total_profit || 0;
    
    // If in live mode and no live data exists, show zeros instead of mock data
    const safeTotalTrades = isLiveMode && !botStats[`${modePrefix}total_trades`] ? 0 : totalTrades;
    const safeWinningTrades = isLiveMode && !botStats[`${modePrefix}winning_trades`] ? 0 : winningTrades;
    const safeTradesToday = isLiveMode && !botStats[`${modePrefix}trades_today`] ? 0 : tradestoday;
    const safeTotalProfit = isLiveMode && !botStats[`${modePrefix}total_profit`] ? 0 : totalProfit;
    
    const winRate = safeTotalTrades > 0 ? (safeWinningTrades / safeTotalTrades * 100) : 0;
    const activeTrades = botStats.active_trades || totalPositions;

    const formatCurrency = (value) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    };

    const formatPercentage = (value) => {
      return `${value.toFixed(2)}%`;
    };

    return (
      <div className="overview-section">
        <div className="section-header">
          <h3>Trading Overview</h3>
          {/* 🔥 NEW: Connection Status Display */}
          <div className="connection-status">
            <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              <span className="status-text">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {!isConnected && (
              <div className="connection-info">
                <small>Last check: {lastConnectionCheck ? new Date(lastConnectionCheck).toLocaleTimeString() : 'Never'}</small>
              </div>
            )}
          </div>
        </div>

        {/* Real-time Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card wallet-card" onClick={() => setShowWalletModal(true)}>
            <div className="stat-icon"><CiDollar/></div>
            <div className="stat-label">
              Current Balance 
              <span className="wallet-type">
                ({data?.trading_balance?.wallet_type || 'UNKNOWN'})
              </span>
            </div>
            <div className="stat-value">{formatCurrency(balance)}</div>
            <div className="wallet-hint">Click to manage wallets</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiWavePulse1/></div>
            <div className="stat-label">Active Trades</div>
            <div className="stat-value">{Object.keys(activeTrades).length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiBadgeDollar /></div>
            <div className="stat-label">Total PnL</div>
            <div className="stat-value">{formatCurrency(totalPnL)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiBag1/></div>
            <div className="stat-label">Total Profit</div>
            <div className="stat-value">{formatCurrency(safeTotalProfit)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiAlignBottom/></div>
            <div className="stat-label">Total Trades</div>
            <div className="stat-value">{safeTotalTrades}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiFlag1/></div>
            <div className="stat-label">Win Rate</div>
            <div className="stat-value">{formatPercentage(winRate)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiCalendar/></div>
            <div className="stat-label">Trades Today</div>
            <div className="stat-value">{safeTradesToday}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiWallet/></div>
            <div className="stat-label">Position Value</div>
            <div className="stat-value">{formatCurrency(totalValue)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiSaveUp1/> </div>
            <div className="stat-label">Auto-Close</div>
            <div className="stat-value"> Active (30s)</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><GrTarget/> </div>
            <div className="stat-label">Targets</div>
            <div className="stat-value">TP: ${botConfig.profit_target_min} | SL: {botConfig.stop_loss_percent}%</div>
            
          </div>
        </div>

        {/* Bot Status */}
        <div className="bot-status-section">

          
          {botStats.enabled && (
            <div className="bot-runtime-info">
              <div className="runtime-stat">
                <span>⏱️ Running Time:</span>
                <span>{Math.floor((botStatus.running_duration || 0) / 60)} minutes</span>
              </div>
              <div className="runtime-stat">
                <span>🎯 Confidence Threshold:</span>
                <span>{((botConfig?.ai_confidence_threshold || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="runtime-stat">
                <span>💰 Trade Amount:</span>
                <span>${botConfig?.trade_amount_usdt || 0}</span>
              </div>
              <div className="runtime-stat">
                <span>Auto-Close Monitoring:</span>
                <span>Active (30s intervals)</span>
              </div>
              <div className="runtime-stat">
                <span> Profit Target:</span>
                <span>${botConfig?.profit_target_min || 0}</span>
              </div>
              <div className="runtime-stat">
                <span>Stop Loss:</span>
                <span>{botConfig?.stop_loss_percent || 0}%</span>
              </div>
            </div>
          )}
        </div>

        {/* Bot Controls */}
        <div className="bot-controls">
          {!botEnabled ? (
            <button 
              className="start-bot-btn"
              onClick={handleStartBot}
              disabled={!isConnected}
            >
              <FiPlay size={16} />
              Start Bot
            </button>
          ) : (
            <button 
              className="stop-bot-btn"
              onClick={handleStopBot}
              disabled={!isConnected}
            >
              <FiSquare size={16} />
              Stop Bot
            </button>
          )}
          
          <button 
            className="config-btn"
            onClick={() => setShowConfigModal(true)}
            disabled={!isConnected}
          >
            <FiSettings size={16} />
            Configure
          </button>
          
          <button 
            className="refresh-btn" 
            onClick={requestAllData} 
            disabled={!isConnected}
          >
            <CiRepeat size={16} />
          </button>
        </div>
      </div>
    );
  };

  const renderActiveTrades = () => {
    // Use positions data from WebSocket context if available, otherwise use local state
    const positions = data?.positions || activeTrades;
    const positionEntries = Object.entries(positions);

    return (
      <div className="active-trades">
        <div className="section-header">
          <h3>Active Trades</h3>
          <div className="section-stats">
            {positionEntries.length} Open Position{positionEntries.length !== 1 ? 's' : ''}
          </div>
        </div>

        {positionEntries.length > 0 ? (
          <div className="trades-grid">
            {positionEntries.map(([symbol, position]) => {
              // Ensure position is an object and extract values safely
              if (!position || typeof position !== 'object') {
                return null;
              }

              // Safely extract values with proper type checking
              const entryPrice = typeof position.entry_price === 'number' ? position.entry_price : 
                                typeof position.price === 'number' ? position.price : 0;
              const currentPrice = typeof position.current_price === 'number' ? position.current_price : 
                                  typeof position.price === 'number' ? position.price : 0;
              const amount = typeof position.amount === 'number' ? position.amount : 0;
              const unrealizedPnl = typeof position.unrealized_pnl === 'number' ? position.unrealized_pnl : 0;
              const marginUsed = typeof position.margin_used === 'number' ? position.margin_used : 0;
              const confidenceScore = typeof position.confidence_score === 'number' ? position.confidence_score : null;
              const direction = typeof position.direction === 'string' ? position.direction : 'long';

              return (
                <div key={symbol} className="trade-card">
                  <div className="trade-header">
                    <h4>{symbol}</h4>
                    <span className={`direction-badge ${direction.toLowerCase()}`}>
                      {direction === 'long' ? '📈' : '📉'} {direction.toUpperCase()}
                    </span>
                  </div>
                  <div className="trade-details">
                    <div className="detail-row">
                      <span>Entry Price:</span>
                      <span>${entryPrice.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Current Price:</span>
                      <span>${currentPrice.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Amount:</span>
                      <span>{amount.toFixed(2)}</span>
                    </div>
                    <div className="detail-row">
                      <span>Unrealized PnL:</span>
                      <span className={unrealizedPnl >= 0 ? 'profit' : 'loss'}>
                        ${unrealizedPnl.toFixed(2)}
                      </span>
                    </div>
                    <div className="detail-row">
                      <span>Margin Used:</span>
                      <span>${marginUsed.toFixed(2)}</span>
                    </div>
                    {confidenceScore !== null && (
                      <div className="detail-row">
                        <span>Confidence:</span>
                        <span>{(confidenceScore * 100).toFixed(1)}%</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="no-trades">
            <div className="no-data-icon">💤</div>
            <p>No active trades at the moment</p>
            <p>Start the bot to begin automated trading</p>
          </div>
        )}
      </div>
    );
  };

  const renderPairStatus = () => {
    const pairStatus = botStatus?.pair_status || {};
    const allowedPairs = botConfig?.allowed_pairs || ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];

    return (
      <div className="pair-status">
        <div className="section-header">
          <h3>Pair Status</h3>
          <div className="section-stats">
            {Object.keys(pairStatus).length} Pairs Monitored
          </div>
        </div>

        <div className="pairs-grid">
          {allowedPairs.map(symbol => {
            const status = pairStatus[symbol] || 'no_selected';
            const statusEmoji = {
              'idle': '⏳',
              'in_trade': '🔥',
              'cooldown': '❄️',
              'analyzing': '',
              'no_selected': '⚫'
            };

            const statusLabel = {
              'idle': 'Idle',
              'in_trade': 'In Trade',
              'cooldown': 'Cooldown',
              'analyzing': 'Analyzing',
              'no_selected': 'Not Selected'
            };

            return (
              <div key={symbol} className={`pair-card ${status}`}>
                <div className="pair-header">
                  <h4>{symbol}</h4>
                  <span className={`status-badge ${status}`}>
                    {statusEmoji[status]} {statusLabel[status]}
                  </span>
                </div>
                <div className="pair-info">
                  {status === 'cooldown' && (
                    <div className="cooldown-info">
                      <FiClock size={12} />
                      <span>Cooldown active</span>
                    </div>
                  )}
                  {status === 'in_trade' && (
                    <div className="trade-info">
                      <FiActivity size={12} />
                      <span>Trade active</span>
                    </div>
                  )}
                  {status === 'idle' && (
                    <div className="idle-info">
                      <FiTarget size={12} />
                      <span>Ready for signals</span>
                    </div>
                  )}
                  {status === 'analyzing' && (
                    <div className="analyzing-info">
                      <FiZap size={12} />
                      <span>AI analyzing...</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderTradeHistory = () => {
    const formatTimeAgo = (timestamp) => {
      const now = Date.now();
      const diff = now - (timestamp * 1000);
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 0) return `${days}d ago`;
      if (hours > 0) return `${hours}h ago`;
      if (minutes > 0) return `${minutes}m ago`;
      return 'Just now';
    };

    return (
      <div className="trade-history">
        <div className="section-header">
          <h3>📜 Trade History</h3>
          <div className="section-stats">
            {tradeHistory.length} Trade{tradeHistory.length !== 1 ? 's' : ''}
          </div>
        </div>

        {tradeHistory.length > 0 ? (
          <div className="history-table">
            <div className="table-header">
              <span>Symbol</span>
              <span>Direction</span>
              <span>Amount</span>
              <span>Price</span>
              <span>PnL</span>
              <span>Time</span>
            </div>
            <div className="table-body">
            {tradeHistory.map((trade, index) => (
              <div key={index} className="table-row">
                <span>{trade.symbol}</span>
                <span className={`direction-badge ${trade.direction?.toLowerCase()}`}>
                  {trade.direction}
                </span>
                <span>{trade.amount}</span>
                <span>${(trade.price || 0).toFixed(2)}</span>
                <span className={`pnl ${(trade.pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                  ${(trade.pnl || 0).toFixed(2)}
                </span>
                <span>{formatTimeAgo(trade.timestamp)}</span>
              </div>
            ))}
            </div>
          </div>
        ) : (
          <div className="no-history">
            <div className="no-data-icon">📊</div>
            <p>No trade history available</p>
            <p>Execute some trades to see history here</p>
          </div>
        )}
      </div>
    );
  };

  const renderLogs = () => {
    const formatTimeAgo = (timestamp) => {
      const now = Date.now();
      const diff = now - (timestamp * 1000);
      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(minutes / 60);
      const days = Math.floor(hours / 24);

      if (days > 0) return `${days}d ago`;
      if (hours > 0) return `${hours}h ago`;
      if (minutes > 0) return `${minutes}m ago`;
      return 'Just now';
    };

    return (
      <div className="bot-logs">
        <div className="section-header">
          <h3>📋 Analysis & Trade Logs</h3>
          <div className="log-filters">
            <span className="log-count">
              Total: {analysisLogs.length + tradeLogs.length} logs
            </span>
          </div>
        </div>
        
        <div className="logs-container">
          {/* Analysis Logs Section */}
          <div className="log-section">
            <h4> Analysis Logs ({analysisLogs.length})</h4>
            <div className="log-list">
              {analysisLogs.length === 0 ? (
                <div className="empty-state">
                  <div className="no-data-icon">📝</div>
                  <p>No analysis logs available</p>
                  <p>Analysis logs will appear here as AI analysis runs</p>
                </div>
              ) : (
                analysisLogs.map((log, index) => (
                  <div key={index} className="log-entry">
                    <div className="log-timestamp">{formatTimeAgo(log.timestamp)}</div>
                    <div className="log-message">
                      {log.level === 'INFO' && '📘'}
                      {log.level === 'WARNING' && '⚠️'}
                      {log.level === 'ERROR' && '❌'}
                      {log.level === 'DEBUG' && '🔧'}
                      <span className="log-text">{log.message}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Trade Logs Section */}
          <div className="log-section">
            <h4>📊 Trade Logs ({tradeLogs.length})</h4>
            <div className="log-list">
              {tradeLogs.length === 0 ? (
                <div className="empty-state">
                  <div className="no-data-icon">📊</div>
                  <p>No trade logs available</p>
                  <p>Trade decision logs will appear here as analysis runs</p>
                </div>
              ) : (
                tradeLogs.map((log, index) => (
                  <div key={index} className={`trade-log-entry ${log.trade_decision?.toLowerCase()}`}>
                    <div className="log-header">
                      <div className="log-symbol">{log.symbol}</div>
                      <div className="log-time">{formatTimeAgo(log.timestamp)}</div>
                    </div>
                    <div className="log-details">
                      <div className="confidence-info">
                        <span className="confidence-label">Confidence:</span>
                        <span className="confidence-value">
                          {log.final_confidence_score ? (log.final_confidence_score * 100).toFixed(2) : 
                           log.confidence ? (log.confidence * 100).toFixed(2) : '0'}%
                        </span>
                      </div>
                      <div className="decision-info">
                        <span className="decision-label">Decision:</span>
                        <span className={`decision-value ${log.trade_decision?.toLowerCase()}`}>
                          {log.trade_decision === 'ACCEPTED' ? '' : '❌'} {log.trade_decision}
                        </span>
                      </div>
                    </div>
                    <div className="log-reason">
                      Source: {log.analysis_source} | Threshold: {log.confidence_above_threshold ? 'Met' : 'Not Met'}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderConfigModal = () => (
    <div className="config-modal-overlay" onClick={() => setShowConfigModal(false)}>
      <div className="config-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Bot Configuration</h3>
          <button 
            className="close-btn"
            onClick={() => setShowConfigModal(false)}
          >
            <FiX size={20} />
          </button>
        </div>
        
        <div className="config-form">
          <div className="config-section">
            <h4>Trade Limits</h4>
            <div className="form-row">
              <label>Max Trades Per Day:</label>
              <input
                type="number"
                value={botConfig.max_trades_per_day}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  max_trades_per_day: parseInt(e.target.value)
                }))}
                min="1"
                max="50"
              />
            </div>
            <div className="form-row">
              <label>Max Concurrent Trades:</label>
              <input
                type="number"
                value={botConfig.max_concurrent_trades}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  max_concurrent_trades: parseInt(e.target.value)
                }))}
                min="1"
                max="10"
              />
            </div>
          </div>

          <div className="config-section">
            <h4>Trade Amounts</h4>
            <div className="form-row">
              <label>Trade Amount (USDT):</label>
              <input
                type="number"
                value={botConfig.trade_amount_usdt}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  trade_amount_usdt: parseFloat(e.target.value)
                }))}
                min="1"
                step="0.01"
              />
            </div>
            <div className="form-row">
              <label>Max Amount Per Trade (USDT):</label>
              <input
                type="number"
                value={botConfig.max_amount_per_trade_usdt}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  max_amount_per_trade_usdt: parseFloat(e.target.value)
                }))}
                min="1"
                step="0.01"
              />
            </div>
            <div className="form-row">
              <label>Leverage Per Trade:</label>
              <input
                type="number"
                value={botConfig.leverage_per_trade}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  leverage_per_trade: parseInt(e.target.value)
                }))}
                min="1"
                max="125"
              />
            </div>
            <div className="form-row">
              <label>Risk Per Trade (%):</label>
              <input
                type="number"
                value={botConfig.risk_per_trade_percent}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  risk_per_trade_percent: parseFloat(e.target.value)
                }))}
                min="0.1"
                max="10"
                step="0.1"
              />
            </div>
            <div className="form-row">
              <label>Min Profit Target ($):</label>
              <input
                type="number"
                value={botConfig.profit_target_min}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  profit_target_min: parseFloat(e.target.value)
                }))}
                min="0.1"
                step="0.1"
              />
            </div>
            <div className="form-row">
              <label>Max Profit Target ($):</label>
              <input
                type="number"
                value={botConfig.profit_target_max}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  profit_target_max: parseFloat(e.target.value)
                }))}
                min="0.1"
                step="0.1"
              />
            </div>
            <div className="form-row">
              <label>Stop Loss (%):</label>
              <input
                type="number"
                value={botConfig.stop_loss_percent}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  stop_loss_percent: parseFloat(e.target.value)
                }))}
                min="0.1"
                max="10"
                step="0.1"
              />
            </div>
          </div>

          <div className="config-section">
            <h4>Trade Monitoring</h4>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.monitor_open_trades}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    monitor_open_trades: e.target.checked
                  }))}
                />
                Monitor Open Trades
              </label>
            </div>
            <div className="form-row">
              <label>Loss Check Interval (%):</label>
              <input
                type="number"
                value={botConfig.loss_check_interval_percent}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  loss_check_interval_percent: parseFloat(e.target.value)
                }))}
                min="0.5"
                max="5"
                step="0.5"
              />
            </div>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.rollback_enabled}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    rollback_enabled: e.target.checked
                  }))}
                />
                Enable Rollback Strategy
              </label>
            </div>
            <div className="form-row">
              <label>Reanalysis Cooldown (seconds):</label>
              <input
                type="number"
                value={botConfig.reanalysis_cooldown_seconds}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  reanalysis_cooldown_seconds: parseInt(e.target.value)
                }))}
                min="60"
                max="1800"
                step="60"
              />
            </div>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.reconfirm_before_entry}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    reconfirm_before_entry: e.target.checked
                  }))}
                />
                Reconfirm Before Entry
              </label>
            </div>
          </div>

          <div className="config-section">
            <h4>Trailing Stop</h4>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.trailing_enabled}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    trailing_enabled: e.target.checked
                  }))}
                />
                Enable Trailing Stop
              </label>
            </div>
            {botConfig.trailing_enabled && (
              <>
                <div className="form-row">
                  <label>Trailing Trigger (USD):</label>
                  <input
                    type="number"
                    value={botConfig.trailing_trigger_usd}
                    onChange={(e) => setBotConfig(prev => ({
                      ...prev,
                      trailing_trigger_usd: parseFloat(e.target.value)
                    }))}
                    min="0.1"
                    step="0.01"
                  />
                </div>
                <div className="form-row">
                  <label>Trailing Distance (USD):</label>
                  <input
                    type="number"
                    value={botConfig.trailing_distance_usd}
                    onChange={(e) => setBotConfig(prev => ({
                      ...prev,
                      trailing_distance_usd: parseFloat(e.target.value)
                    }))}
                    min="0.1"
                    step="0.01"
                  />
                </div>
              </>
            )}
          </div>

          <div className="config-section">
            <h4>Timing</h4>
            <div className="form-row">
              <label>Trade Interval (seconds):</label>
              <input
                type="number"
                value={botConfig.trade_interval_secs}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  trade_interval_secs: parseInt(e.target.value)
                }))}
                min="30"
                max="300"
              />
            </div>
            <div className="form-row">
              <label>Cooldown (seconds):</label>
              <input
                type="number"
                value={botConfig.cooldown_secs}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  cooldown_secs: parseInt(e.target.value)
                }))}
                min="60"
                max="3600"
              />
            </div>
            <div className="form-row">
              <label>Run Time (minutes):</label>
              <input
                type="number"
                value={botConfig.run_time_minutes}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  run_time_minutes: parseInt(e.target.value)
                }))}
                min="0"
                max="1440"
              />
            </div>
          </div>

          <div className="config-section">
            <h4>AI Settings</h4>
            <div className="form-row">
              <label>Confidence Threshold:</label>
              <input
                type="number"
                value={botConfig.ai_confidence_threshold}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  ai_confidence_threshold: parseFloat(e.target.value)
                }))}
                min="0.1"
                max="1.0"
                step="0.05"
              />
            </div>
            <div className="form-row">
              <label>Allowed Pairs:</label>
              <div className="pairs-selector">
                {availablePairs.map(pair => (
                  <label key={pair} className="pair-checkbox">
                    <input
                      type="checkbox"
                      checked={botConfig.allowed_pairs.includes(pair)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setBotConfig(prev => ({
                            ...prev,
                            allowed_pairs: [...prev.allowed_pairs, pair]
                          }));
                        } else {
                          setBotConfig(prev => ({
                            ...prev,
                            allowed_pairs: prev.allowed_pairs.filter(p => p !== pair)
                          }));
                        }
                      }}
                    />
                    {pair}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="config-section">
            <h4>Other Settings</h4>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.test_mode}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    test_mode: e.target.checked
                  }))}
                />
                Test Mode (Simulate trades)
              </label>
            </div>
            <div className="form-row">
              <label>
                <input
                  type="checkbox"
                  checked={botConfig.manual_approval_mode}
                  onChange={(e) => setBotConfig(prev => ({
                    ...prev,
                    manual_approval_mode: e.target.checked
                  }))}
                />
                Manual Approval Mode
              </label>
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button 
            className="save-btn"
            onClick={() => handleUpdateConfig(botConfig)}
            disabled={configLoading}
          >
            {configLoading ? 'Saving...' : 'Save Configuration'}
          </button>
          <button 
            className="cancel-btn"
            onClick={() => setShowConfigModal(false)}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );

  const renderWalletModal = () => {
    const formatCurrency = (value) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 6
      }).format(value);
    };

    return (
      <div className="modal-overlay" onClick={() => setShowWalletModal(false)}>
        <div className="modal-content wallet-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Wallet Management</h3>
            <button className="close-btn" onClick={() => setShowWalletModal(false)}>×</button>
          </div>
          
          <div className="wallet-modal-body">
            <div className="wallet-tabs">
              {Object.keys(categorizedBalances).map(walletType => (
                <button
                  key={walletType}
                  className={`wallet-tab ${selectedWallet === walletType ? 'active' : ''}`}
                  onClick={() => setSelectedWallet(walletType)}
                >
                  {walletType}
                </button>
              ))}
            </div>
            
            <div className="wallet-content">
              {categorizedBalances[selectedWallet] && (
                <div className="wallet-section">
                  <h4>{categorizedBalances[selectedWallet].name}</h4>
                  <div className="balance-list">
                    {categorizedBalances[selectedWallet].balances
                      .filter(balance => parseFloat(balance.total) > 0.001)
                      .map(balance => (
                        <div key={balance.asset} className="balance-item">
                          <div className="balance-asset">{balance.asset}</div>
                          <div className="balance-amounts">
                            <div className="balance-total">
                              Total: {parseFloat(balance.total).toFixed(6)}
                            </div>
                            <div className="balance-free">
                              Free: {parseFloat(balance.free).toFixed(6)}
                            </div>
                            {parseFloat(balance.locked) > 0 && (
                              <div className="balance-locked">
                                Locked: {parseFloat(balance.locked).toFixed(6)}
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    }
                    {(!categorizedBalances[selectedWallet].balances || 
                      categorizedBalances[selectedWallet].balances.filter(b => parseFloat(b.total) > 0.001).length === 0) && (
                      <div className="no-balances">No significant balances found</div>
                    )}
                  </div>
                  
                  <div className="total-value">
                    Total USDT Value: {formatCurrency(categorizedBalances[selectedWallet].total_usdt || 0)}
                  </div>
                </div>
              )}
            </div>
            
            <div className="wallet-actions">
              <button 
                className="btn-primary"
                onClick={() => setShowTransferModal(true)}
              >
                Transfer Funds
              </button>
              <button 
                className="btn-primary"
                onClick={fetchCategorizedBalances}
              >
                Refresh Balances
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowWalletModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderTransferModal = () => {
    const getAvailableAssets = () => {
      const assets = new Set();
      Object.values(categorizedBalances).forEach(wallet => {
        if (wallet.balances) {
          wallet.balances.forEach(balance => {
            if (parseFloat(balance.total) > 0.001) {
              assets.add(balance.asset);
            }
          });
        }
      });
      return Array.from(assets).sort();
    };

    const getMaxTransferAmount = () => {
      const fromWalletData = categorizedBalances[transferData.fromWallet];
      if (!fromWalletData || !fromWalletData.balances) return 0;
      
      const assetBalance = fromWalletData.balances.find(b => b.asset === transferData.asset);
      return assetBalance ? parseFloat(assetBalance.free) : 0;
    };

    return (
      <div className="modal-overlay" onClick={() => setShowTransferModal(false)}>
        <div className="modal-content transfer-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Transfer Funds Between Wallets</h3>
            <button className="close-btn" onClick={() => setShowTransferModal(false)}>×</button>
          </div>
          
          <div className="transfer-modal-body">
            <div className="transfer-form">
              <div className="form-row">
                <label>Asset</label>
                <select 
                  value={transferData.asset} 
                  onChange={(e) => setTransferData(prev => ({ ...prev, asset: e.target.value }))}
                >
                  {getAvailableAssets().map(asset => (
                    <option key={asset} value={asset}>{asset}</option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <label>From Wallet</label>
                <select 
                  value={transferData.fromWallet} 
                  onChange={(e) => setTransferData(prev => ({ ...prev, fromWallet: e.target.value }))}
                >
                  {Object.keys(categorizedBalances).map(walletType => (
                    <option key={walletType} value={walletType}>{walletType}</option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <label>To Wallet</label>
                <select 
                  value={transferData.toWallet} 
                  onChange={(e) => setTransferData(prev => ({ ...prev, toWallet: e.target.value }))}
                >
                  {Object.keys(categorizedBalances).filter(w => w !== transferData.fromWallet).map(walletType => (
                    <option key={walletType} value={walletType}>{walletType}</option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <label>
                  Amount 
                  <span className="balance-info">
                    (Available: {getMaxTransferAmount().toFixed(6)} {transferData.asset})
                  </span>
                </label>
                <div className="amount-input-container">
                  <input 
                    type="number" 
                    step="0.000001"
                    min="0"
                    max={getMaxTransferAmount()}
                    value={transferData.amount} 
                    onChange={(e) => setTransferData(prev => ({ ...prev, amount: e.target.value }))}
                    placeholder="Enter amount"
                  />
                  <button 
                    className="max-btn"
                    onClick={() => setTransferData(prev => ({ ...prev, amount: getMaxTransferAmount().toString() }))}
                  >
                    MAX
                  </button>
                </div>
              </div>
            </div>
            
            <div className="transfer-actions">
              <button 
                className="btn-primary"
                onClick={executeTransfer}
                disabled={!transferData.amount || parseFloat(transferData.amount) <= 0}
              >
                Execute Transfer
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowTransferModal(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderInsufficientBalanceModal = () => {
    if (!insufficientBalanceData) return null;

    const {
      required_amount,
      available_amount,
      asset,
      current_wallet,
      transfer_suggestions,
      message
    } = insufficientBalanceData;

    const handleQuickTransfer = (suggestion) => {
      const transferAmount = Math.min(
        suggestion.available_amount,
        Math.max(required_amount - available_amount, 50) // Transfer at least 50 USDT or the shortage
      );
      
      setTransferData({
        asset: asset,
        amount: transferAmount.toFixed(2),
        fromWallet: suggestion.from_wallet,
        toWallet: suggestion.to_wallet
      });
      setShowInsufficientBalanceModal(false);
      setShowTransferModal(true);
    };

    return (
      <div className="modal-overlay" onClick={() => setShowInsufficientBalanceModal(false)}>
        <div className="modal-content insufficient-balance-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Insufficient Balance</h3>
            <button className="close-btn" onClick={() => setShowInsufficientBalanceModal(false)}>×</button>
          </div>
          
          <div className="insufficient-balance-body">
            {message && (
              <div className="balance-message">
                <p>{message}</p>
              </div>
            )}
            
            <div className="balance-summary">
              <h4>Balance Information</h4>
              <div className="balance-info-grid">
                <div className="balance-info-item">
                  <span className="label">Recommended:</span>
                  <span className="value">{required_amount?.toFixed(2)} {asset}</span>
                </div>
                <div className="balance-info-item">
                  <span className="label">Available in {current_wallet}:</span>
                  <span className="value">{available_amount?.toFixed(2)} {asset}</span>
                </div>
                {available_amount < required_amount && (
                  <div className="balance-info-item">
                    <span className="label">Need to Transfer:</span>
                    <span className="value shortage">{(required_amount - available_amount)?.toFixed(2)} {asset}</span>
                  </div>
                )}
              </div>
            </div>

            {transfer_suggestions && transfer_suggestions.length > 0 && (
              <div className="transfer-suggestions">
                <h4>Transfer Options</h4>
                <p>You have sufficient balance in other wallets. Quick transfer options:</p>
                <div className="suggestions-list">
                  {transfer_suggestions.map((suggestion, index) => {
                    const transferAmount = Math.min(
                      suggestion.available_amount,
                      Math.max(required_amount - available_amount, 50)
                    );
                    
                    return (
                      <div key={index} className="suggestion-item">
                        <div className="suggestion-info">
                          <div className="suggestion-title">
                            Transfer from {suggestion.from_wallet} Wallet
                          </div>
                          <div className="suggestion-details">
                            Available: {suggestion.available_amount?.toFixed(2)} {asset}
                          </div>
                        </div>
                        <button 
                          className="btn-primary suggestion-btn"
                          onClick={() => handleQuickTransfer(suggestion)}
                        >
                          Transfer {transferAmount.toFixed(2)} {asset}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {(!transfer_suggestions || transfer_suggestions.length === 0) && (
              <div className="no-options">
                <h4>No Transfer Options Available</h4>
                <p>You don't have sufficient {asset} balance in your Spot wallet to transfer to Futures.</p>
                <p>Please deposit {asset} to your Binance account first, then you can transfer to your Futures wallet.</p>
                <div className="deposit-info">
                  <small>💡 Tip: You can deposit {asset} directly to your Spot wallet on Binance, then use the transfer feature to move it to Futures for trading.</small>
                </div>
              </div>
            )}
            
            <div className="modal-actions">
              <button 
                className="btn-primary"
                onClick={() => {
                  setShowInsufficientBalanceModal(false);
                  setShowWalletModal(true);
                }}
              >
                View All Wallets
              </button>
              <button 
                className="btn-secondary"
                onClick={() => setShowInsufficientBalanceModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="trading-bot-container">
      <div className="bot-header">
        <h2> Trading Bot</h2>
        <div className="bot-controls">
          <button 
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`tab-btn ${activeTab === 'active-trades' ? 'active' : ''}`}
            onClick={() => setActiveTab('active-trades')}
          >
            Active Trades ({Object.keys(activeTrades).length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pair-status' ? 'active' : ''}`}
            onClick={() => setActiveTab('pair-status')}
          >
            Pair Status
          </button>
          <button 
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Trade History
          </button>
          <button 
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            Logs ({analysisLogs.length + tradeLogs.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'active-trades' && renderActiveTrades()}
      {activeTab === 'pair-status' && renderPairStatus()}
      {activeTab === 'history' && renderTradeHistory()}
      {activeTab === 'logs' && renderLogs()}

      {/* Configuration Modal */}
      {showConfigModal && renderConfigModal()}
      
      {/* Wallet Management Modal */}
      {showWalletModal && renderWalletModal()}
      
      {/* Transfer Modal */}
      {showTransferModal && renderTransferModal()}
      
      {/* Insufficient Balance Modal */}
      {showInsufficientBalanceModal && renderInsufficientBalanceModal()}
    </div>
  );
};

export default TradingBot; 