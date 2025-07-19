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
import './TradingBot.css';
import { BiChart, BiDollar, BiTargetLock, BiUpvote } from 'react-icons/bi';
import { CiAlignBottom, CiBadgeDollar, CiBag1, CiCalendar, CiChartLine, CiChat1, CiDollar, CiFlag1, CiRepeat, CiSaveUp1, CiWavePulse1 } from 'react-icons/ci';
import { CiWallet } from 'react-icons/ci';
import { MdCandlestickChart } from 'react-icons/md';
import { toast } from 'react-toastify';
import { GrTarget } from 'react-icons/gr';
import { useState, useEffect } from 'react';

const TradingBot = ({ isConnected, startBot, stopBot, getBotStatus, updateBotConfig, getBotConfig, sendMessage, data }) => {
  console.log('🔍 TradingBot: Component initialized with props:', { isConnected, startBot: !!startBot, stopBot: !!stopBot, getBotStatus: !!getBotStatus, updateBotConfig: !!updateBotConfig, getBotConfig: !!getBotConfig });
  
  // Get WebSocket context for real-time updates
  const { lastMessage } = useWebSocket();

  
  const [botEnabled, setBotEnabled] = useState(false);
  console.log('🔍 TradingBot: Initial botEnabled state:', botEnabled);
  
  const [botConfig, setBotConfig] = useState({
    max_trades_per_day: 10,
    trade_amount_usdt: 50,
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
  console.log('🔍 TradingBot: Initial botConfig:', botConfig);
  
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
  console.log('🔍 TradingBot: Initial botStatus:', botStatus);
  
  const [activeTrades, setActiveTrades] = useState({});
  console.log('🔍 TradingBot: Initial activeTrades:', activeTrades);
  
  const [tradeHistory, setTradeHistory] = useState([]);
  console.log('🔍 TradingBot: Initial tradeHistory length:', tradeHistory.length);
  
  const [analysisLogs, setAnalysisLogs] = useState([]);
  console.log('🔍 TradingBot: Initial analysisLogs length:', analysisLogs.length);
  
  const [tradeLogs, setTradeLogs] = useState([]);
  console.log('🔍 TradingBot: Initial tradeLogs length:', tradeLogs.length);
  
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configLoading, setConfigLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Available trading pairs
  const availablePairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'];

  useEffect(() => {
    console.log('🔍 TradingBot: useEffect triggered - isConnected:', isConnected);
    if (isConnected) {
      console.log('🔍 TradingBot: Connection detected, calling getBotStatus and getBotConfig');
      getBotStatus();
      getBotConfig(); // Load saved configuration
      // Request additional data for all sections
      requestAllData();
    } else {
      console.log('🔍 TradingBot: No connection detected');
    }
  }, [isConnected, getBotStatus, getBotConfig]);

  // Request all required data for the trading bot dashboard
  const requestAllData = () => {
    if (!isConnected || !sendMessage) return;

    try {
      // Request positions (active trades)
      sendMessage({ type: 'get_positions' });

      // Request trade history from MongoDB
      sendMessage({ type: 'get_trade_history', limit: 100 });

      // Request analysis logs
      sendMessage({ type: 'get_analysis_logs', limit: 50 });

      // Request trade logs with confidence scores
      sendMessage({ type: 'get_trade_logs', limit: 50 });

      console.log('🔍 TradingBot: All data requests sent');
    } catch (error) {
      console.error('🔍 TradingBot: Error requesting data:', error);
    }
  };

  // Global message handler for bot responses
  const handleBotResponse = (message) => {
    console.log('🔍 TradingBot: handleBotResponse called with message:', message);
    const { type, data } = message;
    console.log('🔍 TradingBot: Message type:', type, 'Data:', data);
    console.log('🔍 TradingBot: Full message object:', JSON.stringify(message, null, 2));
    
    if (type === 'bot_status_response') {
      console.log('🔍 TradingBot: Processing bot_status_response:', data);
      setBotStatus(data);
      setBotEnabled(data.enabled);
      
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
        console.log('🔍 TradingBot: Converted active_trades array to object:', activeTradesObject);
      }
      
      console.log('🔍 TradingBot: Updated botStatus to:', data);
      console.log('🔍 TradingBot: Updated botEnabled to:', data.enabled);
    } else if (type === 'start_bot_response') {
      console.log('🔍 TradingBot: Processing start_bot_response:', data);
      if (data.success) {
        console.log('🔍 TradingBot: Bot start successful, setting botEnabled to true');
        setBotEnabled(true);
        // Get updated bot status immediately after starting
        setTimeout(() => {
          console.log('🔍 TradingBot: Getting updated bot status after start');
          getBotStatus();
        }, 1000);
      } else {
        console.log('🔍 TradingBot: Bot start failed:', data.error);
      }
    } else if (type === 'stop_bot_response') {
      console.log('🔍 TradingBot: Processing stop_bot_response:', data);
      if (data.success) {
        console.log('🔍 TradingBot: Bot stop successful, setting botEnabled to false');
        setBotEnabled(false);
        getBotStatus();
      } else {
        console.log('🔍 TradingBot: Bot stop failed:', data.error);
      }
    } else if (type === 'update_bot_config_response') {
      console.log('🔍 TradingBot: Processing update_bot_config_response:', data);
      if (data.success) {
        console.log('🔍 TradingBot: Config update successful, closing modal');
        setShowConfigModal(false);
        getBotStatus();
      } else {
        console.log('🔍 TradingBot: Config update failed:', data.error);
      }
    } else if (type === 'bot_config_response') {
      console.log('🔍 TradingBot: Processing bot_config_response:', data);
      if (data.success && data.config) {
        console.log('🔍 TradingBot: Loading saved bot configuration:', data.config);
        setBotConfig(data.config);
      }
    } else if (type === 'bot_status_update') {
      console.log('🔍 TradingBot: Processing bot_status_update:', data);
      setBotStatus(prev => {
        const newStatus = { ...prev, ...data };
        console.log('🔍 TradingBot: Updated botStatus from', prev, 'to', newStatus);
        return newStatus;
      });
      setBotEnabled(data.enabled);
      console.log('🔍 TradingBot: Updated botEnabled to:', data.enabled);
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
      console.log('🔍 TradingBot: Processing ai_analysis_response:', data);
      
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
        console.log('🔍 TradingBot: Added analysis log. New logs length:', newLogs.length);
        return newLogs;
      });
    } else if (type === 'ai_opportunity_alert') {
      console.log('🔍 TradingBot: Processing ai_opportunity_alert:', data);
      
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
        console.log('🔍 TradingBot: Added trade opportunity log. New logs length:', newLogs.length);
        return newLogs;
      });
    } else if (type === 'automated_trade_executed') {
      console.log('🔍 TradingBot: Processing automated_trade_executed:', data);
      
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
        console.log('🔍 TradingBot: Added automated trade log. New logs length:', newLogs.length);
        return newLogs;
      });
      
      // Add/update active trade for this symbol
      if (data.trade_result && data.trade_result.trade_data) {
        setActiveTrades(prev => {
          const newTrades = { ...prev, [data.symbol]: data.trade_result.trade_data };
          console.log('🔍 TradingBot: Updated activeTrades:', newTrades);
          return newTrades;
        });
      }
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'auto_close_notification') {
      console.log('🎯 TradingBot: Processing auto_close_notification:', data);
      
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
        console.log('🔍 TradingBot: Added auto-close notification log. New logs length:', newLogs.length);
        return newLogs;
      });
      
      // Show prominent auto-close notification
      console.log('🎯 AUTO-CLOSE NOTIFICATION:', data.message);
      
    } else if (type === 'automated_trade_failed') {
      console.log('🔍 TradingBot: Processing automated_trade_failed:', data);
      
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
        console.log('🔍 TradingBot: Added failed trade log. New logs length:', newLogs.length);
        return newLogs;
      });
    } else if (type === 'trade_closed') {
      console.log('🔍 TradingBot: Processing trade_closed:', data);
      
      // Remove from active trades
      setActiveTrades(prev => {
        const newTrades = { ...prev };
        delete newTrades[data.symbol];
        console.log('🔍 TradingBot: Removed closed trade from activeTrades:', newTrades);
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
        console.log('🔍 TradingBot: Added trade closure log. New logs length:', newLogs.length);
        return newLogs;
      });
      
      // Show auto-close notification if applicable
      if (isAutoClose) {
        // You can add a toast notification here if you have a notification system
        console.log('🎯 AUTO-CLOSE TRIGGERED:', data.notification || message);
      }
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'rollback_trade_executed') {
      console.log('🔍 TradingBot: Processing rollback_trade_executed:', data);
      
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
        console.log('🔍 TradingBot: Added rollback trade log. New logs length:', newLogs.length);
        return newLogs;
      });
      
      // Refresh bot status
      getBotStatus();
    } else if (type === 'analysis_log') {
      setAnalysisLogs(prev => {
        const newLogs = [data, ...prev.slice(0, 49)];
        console.log('🔍 TradingBot: Added analysis log. New logs length:', newLogs.length);
        return newLogs;
      });
    } else if (type === 'trade_log') {
      setTradeLogs(prev => {
        const newLogs = [data, ...prev.slice(0, 49)];
        console.log('🔍 TradingBot: Added trade log. New logs length:', newLogs.length);
        return newLogs;
      });
    } else if (type === 'trade_history_response') {
      console.log('🔍 TradingBot: Processing trade_history_response:', data);
      if (data.trades) {
        setTradeHistory(data.trades);
      }
    } else if (type === 'analysis_logs_response') {
      console.log('🔍 TradingBot: Processing analysis_logs_response:', data);
      if (data.logs) {
        setAnalysisLogs(data.logs);
      }
    } else if (type === 'trade_logs_response') {
      console.log('🔍 TradingBot: Processing trade_logs_response:', data);
      if (data.logs) {
        setTradeLogs(data.logs);
      }
    } else if (type === 'positions_response') {
      console.log('🔍 TradingBot: Processing positions_response:', data);
      // Update active trades from positions data
      if (data.positions) {
        setActiveTrades(data.positions);
      }
    } else {
      console.log('🔍 TradingBot: Unknown message type:', type);
    }
  };

  // Set up WebSocket message handler
  useEffect(() => {
    console.log('🔍 TradingBot: Setting up WebSocket message handler');
    
    if (lastMessage) {
      console.log('🔍 TradingBot: Received lastMessage:', lastMessage);
      handleBotResponse(lastMessage);
    }
  }, [lastMessage]);

  // Real-time timer update for running duration
  useEffect(() => {
    console.log('🔍 TradingBot: Setting up timer effect - botEnabled:', botEnabled, 'start_time:', botStatus.start_time);
    let timerInterval;
    
    if (botEnabled && botStatus.start_time) {
      console.log('🔍 TradingBot: Starting timer interval');
      timerInterval = setInterval(() => {
        const currentTime = Math.floor(Date.now() / 1000);
        const startTime = Math.floor(botStatus.start_time);
        const runningDuration = currentTime - startTime;
        
        console.log('🔍 TradingBot: Timer update - currentTime:', currentTime, 'startTime:', startTime, 'runningDuration:', runningDuration);
        
        setBotStatus(prev => {
          const newStatus = { ...prev, running_duration: runningDuration };
          console.log('🔍 TradingBot: Updated running_duration to:', runningDuration);
          return newStatus;
        });
      }, 1000); // Update every second
    }
    
    return () => {
      if (timerInterval) {
        console.log('🔍 TradingBot: Clearing timer interval');
        clearInterval(timerInterval);
      }
    };
  }, [botEnabled, botStatus.start_time]);

  const handleStartBot = async () => {
    console.log('🔍 TradingBot: handleStartBot called');
    if (!isConnected) {
      console.log('🔍 TradingBot: Cannot start bot - not connected');
      return;
    }
    
    const confirmed = window.confirm(
      'Are you sure you want to start the trading bot? This will begin automatic trading based on your configuration.'
    );
    
    if (!confirmed) {
      console.log('🔍 TradingBot: User cancelled bot start');
      return;
    }
    
    console.log('🔍 TradingBot: Starting bot with config:', botConfig);
    try {
      await startBot(botConfig);
      console.log('🔍 TradingBot: startBot call completed');
    } catch (error) {
      console.error('🔍 TradingBot: Error starting bot:', error);
    }
  };

  const handleStopBot = async () => {
    console.log('🔍 TradingBot: handleStopBot called');
    if (!isConnected) {
      console.log('🔍 TradingBot: Cannot stop bot - not connected');
      return;
    }
    
    const confirmed = window.confirm(
      'Are you sure you want to stop the trading bot? This will close all active trades.'
    );
    
    if (!confirmed) {
      console.log('🔍 TradingBot: User cancelled bot stop');
      return;
    }
    
    console.log('🔍 TradingBot: Stopping bot');
    try {
      await stopBot();
      console.log('🔍 TradingBot: stopBot call completed');
    } catch (error) {
      console.error('🔍 TradingBot: Error stopping bot:', error);
    }
  };

  const handleUpdateConfig = async (newConfig) => {
    console.log('🔍 TradingBot: handleUpdateConfig called with:', newConfig);
    if (!isConnected) {
      console.log('🔍 TradingBot: Cannot update config - not connected');
      toast.error('Cannot update configuration - not connected to server');
      return;
    }
    
    setConfigLoading(true);
    console.log('🔍 TradingBot: Set configLoading to true');
    try {
      await updateBotConfig(newConfig);
      console.log('🔍 TradingBot: updateBotConfig call completed');
      toast.success('Configuration saved successfully!');
    } catch (error) {
      console.error('🔍 TradingBot: Error updating bot config:', error);
      toast.error('Failed to save configuration. Please try again.');
    } finally {
      setConfigLoading(false);
      console.log('🔍 TradingBot: Set configLoading to false');
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
    const balance = data?.paper_balance || 0;
    const recentTrades = data?.recent_trades || [];
    
    // Calculate stats from available data
    const totalPositions = Object.keys(positions).length;
    const totalValue = Object.values(positions).reduce((sum, pos) => sum + (pos.trade_value || 0), 0);
    const totalPnL = Object.values(positions).reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
    
    // Bot statistics from bot status
    const botStats = botStatus || {};
    const totalTrades = botStats.total_trades || 0;
    const winningTrades = botStats.winning_trades || 0;
    const tradestoday = botStats.trades_today || 0;
    const winRate = totalTrades > 0 ? (winningTrades / totalTrades * 100) : 0;
    const activeTrades = botStats.active_trades || totalPositions;
    const totalProfit = botStats.total_profit || 0;

    const formatCurrency = (value) => {
      if (typeof value !== 'number') return '$0.00';
      return `$${value.toFixed(2)}`;
    };

    const formatPercentage = (value) => {
      if (typeof value !== 'number') return '0.00%';
      return `${value.toFixed(2)}%`;
    };

    return (
      <div className="bot-overview">
        <div className="overview-header">
          <div className="overview-header-left">
          <h3>Trading Overview</h3>
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          </div>
       
          <div className="bot-status-header">
            <h4>Bot Status</h4>
            <div className="bot-status-indicator" aria-live="polite">
              <span
                className="status-dot"
                style={{
                  display: 'inline-block',
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  marginRight: '8px',
                  backgroundColor: botStats.enabled ? '#28c76f' : '#ea5455',
                  verticalAlign: 'middle',
                }}
                aria-label={botStats.enabled ? 'Online' : 'Offline'}
                title={botStats.enabled ? 'Online' : 'Offline'}
              ></span>
            </div>
          </div>
        </div>

        {/* Real-time Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon"><CiDollar/></div>
            <div className="stat-label">Current Balance</div>
            <div className="stat-value">{formatCurrency(balance)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiWavePulse1/></div>
            <div className="stat-label">Active Trades</div>
            <div className="stat-value">{activeTrades}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiBadgeDollar /></div>
            <div className="stat-label">Total PnL</div>
            <div className="stat-value">{formatCurrency(totalPnL)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiBag1/></div>
            <div className="stat-label">Total Profit</div>
            <div className="stat-value">{formatCurrency(totalProfit)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiAlignBottom/></div>
            <div className="stat-label">Total Trades</div>
            <div className="stat-value">{totalTrades}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiFlag1/></div>
            <div className="stat-label">Win Rate</div>
            <div className="stat-value">{formatPercentage(winRate)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon"><CiCalendar/></div>
            <div className="stat-label">Trades Today</div>
            <div className="stat-value">{tradestoday}</div>
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
                console.warn('Invalid position data for symbol:', symbol, position);
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
              'analyzing': '🔍',
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
            <h4>🔍 Analysis Logs ({analysisLogs.length})</h4>
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
                        <span className="confidence-value">{(log.final_confidence_score * 100).toFixed(2)}%</span>
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
    </div>
  );
};

export default TradingBot; 