import React, { useState, useEffect } from 'react';
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
import './TradingBot.css';

const TradingBot = ({ isConnected, startBot, stopBot, getBotStatus, updateBotConfig }) => {
  console.log('🔍 TradingBot: Component initialized with props:', { isConnected, startBot: !!startBot, stopBot: !!stopBot, getBotStatus: !!getBotStatus, updateBotConfig: !!updateBotConfig });
  
  const [botEnabled, setBotEnabled] = useState(false);
  console.log('🔍 TradingBot: Initial botEnabled state:', botEnabled);
  
  const [botConfig, setBotConfig] = useState({
    max_trades_per_day: 10,
    trade_amount_usdt: 50,
    profit_target_usd: 2,
    stop_loss_usd: 1,
    trailing_enabled: true,
    trailing_trigger_usd: 1,
    trailing_distance_usd: 0.5,
    trade_interval_secs: 60,
    max_concurrent_trades: 3,
    cooldown_secs: 300,
    allowed_pairs: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    ai_confidence_threshold: 0.5,
    run_time_minutes: 180,
    test_mode: false,
    risk_per_trade_percent: 1.0,
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
      console.log('🔍 TradingBot: Connection detected, calling getBotStatus');
      getBotStatus();
    } else {
      console.log('🔍 TradingBot: No connection detected');
    }
  }, [isConnected, getBotStatus]);

  // Global message handler for bot responses
  const handleBotResponse = (message) => {
    console.log('🔍 TradingBot: handleBotResponse called with message:', message);
    const { type, data } = message;
    console.log('🔍 TradingBot: Message type:', type, 'Data:', data);
    
    if (type === 'bot_status_response') {
      console.log('🔍 TradingBot: Processing bot_status_response:', data);
      setBotStatus(data);
      setBotEnabled(data.enabled);
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
    } else {
      console.log('🔍 TradingBot: Unknown message type:', type);
    }
  };

  // Expose handler for WebSocket messages
  useEffect(() => {
    console.log('🔍 TradingBot: Setting up global handleBotResponse');
    window.handleBotResponse = handleBotResponse;
    
    return () => {
      console.log('🔍 TradingBot: Cleaning up global handleBotResponse');
      if (window.handleBotResponse === handleBotResponse) {
        delete window.handleBotResponse;
      }
    };
  }, []);

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
      return;
    }
    
    setConfigLoading(true);
    console.log('🔍 TradingBot: Set configLoading to true');
    try {
      await updateBotConfig(newConfig);
      console.log('🔍 TradingBot: updateBotConfig call completed');
    } catch (error) {
      console.error('🔍 TradingBot: Error updating bot config:', error);
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

  const renderOverview = () => (
    <div className="bot-overview">
      <div className="bot-status-card">
        <div className="status-header">
          <span className={`status-indicator ${botEnabled ? 'running' : 'stopped'}`}>
            {botEnabled ? <FiPlay size={16} /> : <FiSquare size={16} />}
          </span>
          <span className="status-text">
            {botEnabled ? 'Bot Running' : 'Bot Stopped'}
          </span>
          {botStatus.start_time && (
            <span className="running-time">
              Running for {formatDuration(botStatus.running_duration)}
            </span>
          )}
        </div>
        
        <div className="bot-stats">
          <div className="stat-item">
            <FiTrendingUp size={16} />
            <span>Total Profit: ${(botStatus.total_profit || 0).toFixed(2)}</span>
          </div>
          <div className="stat-item">
            <FiActivity size={16} />
            <span>Total Trades: {botStatus.total_trades}</span>
          </div>
          <div className="stat-item">
            <FiTarget size={16} />
            <span>Win Rate: {(botStatus.win_rate || 0).toFixed(1)}%</span>
          </div>
          <div className="stat-item">
            <FiClock size={16} />
            <span>Trades Today: {botStatus.trades_today}/{botConfig.max_trades_per_day}</span>
          </div>
          <div className="stat-item">
            <FiZap size={16} />
            <span>Active Trades: {botStatus.active_trades}/{botConfig.max_concurrent_trades}</span>
          </div>
        </div>
      </div>

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
      </div>
    </div>
  );

  const renderActiveTrades = () => (
    <div className="active-trades">
      <h3>Active Trades</h3>
      {Object.keys(activeTrades).length > 0 ? (
        <div className="trades-grid">
          {Object.entries(activeTrades).map(([symbol, trade]) => (
            <div key={symbol} className="trade-card">
              <div className="trade-header">
                <h4>{symbol}</h4>
                <span className={`direction-badge ${trade.direction.toLowerCase()}`}>
                  {trade.direction}
                </span>
              </div>
              <div className="trade-details">
                <div className="detail-row">
                  <span>Entry Price:</span>
                  <span>${(parseFloat(trade.price) || 0).toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span>Take Profit:</span>
                  <span>${(parseFloat(trade.take_profit) || 0).toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span>Stop Loss:</span>
                  <span>${(parseFloat(trade.stop_loss) || 0).toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span>Amount:</span>
                  <span>${((parseFloat(trade.amount) || 0) * (parseFloat(trade.price) || 0)).toFixed(2)}</span>
                </div>
                <div className="detail-row">
                  <span>Confidence:</span>
                  <span>{((parseFloat(trade.confidence_score) || 0) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-trades">
          <p>No active trades</p>
        </div>
      )}
    </div>
  );

  const renderPairStatus = () => (
    <div className="pair-status">
      <h3>Pair Status</h3>
      <div className="pairs-grid">
        {botConfig.allowed_pairs.map(pair => {
          const status = botStatus.pair_status[pair] || 'idle';
          return (
            <div key={pair} className={`pair-card ${status}`}>
              <div className="pair-header">
                <h4>{pair}</h4>
                <span className={`status-badge ${status}`}>
                  {status.toUpperCase()}
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
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  const renderTradeHistory = () => (
    <div className="trade-history">
      <h3>Recent Trades</h3>
      {tradeHistory.length > 0 ? (
        <div className="history-table">
          <div className="table-header">
            <span>Symbol</span>
            <span>Direction</span>
            <span>Entry</span>
            <span>Exit</span>
            <span>P&L</span>
            <span>Reason</span>
          </div>
          {tradeHistory.slice(0, 20).map((trade, index) => (
            <div key={index} className="table-row">
              <span>{trade.symbol}</span>
              <span className={`direction-badge ${trade.direction.toLowerCase()}`}>
                {trade.direction}
              </span>
              <span>${(parseFloat(trade.entry_price) || 0).toFixed(2)}</span>
              <span>${(parseFloat(trade.exit_price) || 0).toFixed(2)}</span>
              <span className={`pnl ${(parseFloat(trade.profit_loss) || 0) >= 0 ? 'positive' : 'negative'}`}>
                ${(parseFloat(trade.profit_loss) || 0).toFixed(2)}
              </span>
              <span className="exit-reason">{trade.exit_reason}</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-history">
          <p>No trade history available</p>
        </div>
      )}
    </div>
  );

  const renderLogs = () => (
    <div className="bot-logs">
      <div className="section-header">
        <h3>Real-time Logs</h3>
        <div className="log-filters">
          <span className="log-count">
            Total: {analysisLogs.length + tradeLogs.length} logs
          </span>
        </div>
      </div>
      
      <div className="logs-container">
        <div className="log-section">
          <h4>Analysis Logs ({analysisLogs.length})</h4>
          <div className="log-list">
            {analysisLogs.length === 0 ? (
              <div className="empty-state">
                <FiActivity size={24} />
                <p>No analysis logs yet</p>
              </div>
            ) : (
              analysisLogs.map((log, index) => (
                <div key={index} className={`log-item analysis-log ${log.level}`}>
                  <div className="log-header">
                    <span className="log-timestamp">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`log-level ${log.level}`}>
                      {log.level === 'high' ? '🚨' : '📊'}
                    </span>
                  </div>
                  <div className="log-message">{log.message}</div>
                  <div className="log-details">
                    {log.confidence_score && (
                      <span>Confidence: {((parseFloat(log.confidence_score) || 0) * 100).toFixed(1)}%</span>
                    )}
                    {log.entry_price && <span>Entry: ${(parseFloat(log.entry_price) || 0).toFixed(2)}</span>}
                    {log.action && log.action !== 'HOLD' && (
                      <span className={`action-badge ${log.action.toLowerCase()}`}>
                        {log.action}
                      </span>
                    )}
                  </div>
                  {log.reasoning && (
                    <div className="log-reasoning">
                      <strong>Reasoning:</strong> {log.reasoning}
                    </div>
                  )}
                  {(log.grok_sentiment || log.claude_confidence) && (
                    <div className="log-analysis-details">
                      {log.grok_sentiment && <span>Grok: {log.grok_sentiment}</span>}
                      {log.claude_confidence && <span>Claude: {((parseFloat(log.claude_confidence) || 0) * 100).toFixed(1)}%</span>}
                      {log.source && <span>Source: {log.source}</span>}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
        
        <div className="log-section">
          <h4>Trade Logs ({tradeLogs.length})</h4>
          <div className="log-list">
            {tradeLogs.length === 0 ? (
              <div className="empty-state">
                <FiDollarSign size={24} />
                <p>No trade logs yet</p>
              </div>
            ) : (
              tradeLogs.map((log, index) => (
                <div key={index} className={`log-item trade-log ${log.level}`}>
                  <div className="log-header">
                    <span className="log-timestamp">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    <span className={`log-level ${log.level}`}>
                      {log.level === 'success' ? '💰' : '⚠️'}
                    </span>
                  </div>
                  <div className="log-message">{log.message}</div>
                  {log.profit && (
                    <div className="log-details">
                      <span className={log.profit >= 0 ? 'positive' : 'negative'}>
                        Profit: ${(parseFloat(log.profit) || 0).toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );

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
          </div>

          <div className="config-section">
            <h4>Profit & Loss</h4>
            <div className="form-row">
              <label>Profit Target (USD):</label>
              <input
                type="number"
                value={botConfig.profit_target_usd}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  profit_target_usd: parseFloat(e.target.value)
                }))}
                min="0.1"
                step="0.01"
              />
            </div>
            <div className="form-row">
              <label>Stop Loss (USD):</label>
              <input
                type="number"
                value={botConfig.stop_loss_usd}
                onChange={(e) => setBotConfig(prev => ({
                  ...prev,
                  stop_loss_usd: parseFloat(e.target.value)
                }))}
                min="0.1"
                step="0.01"
              />
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
        <h2>🤖 Trading Bot</h2>
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