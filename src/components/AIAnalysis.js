import React, { useState, useEffect } from 'react';
import { useTradingMode } from '../contexts/TradingModeContext';
import './AIAnalysis.css';

const AIAnalysis = ({ isConnected, sendMessage, data, startBot, stopBot, getBotStatus, updateBotConfig }) => {

  // Get global trading mode
  const { isLiveMode } = useTradingMode();

  // State for all sections
  const [activeTab, setActiveTab] = useState('overview');
  const [botStatus, setBotStatus] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [mockTradeHistory, setMockTradeHistory] = useState([]);
  const [realTradeHistory, setRealTradeHistory] = useState([]);
  const [analysisLogs, setAnalysisLogs] = useState([]);
  const [tradeLogs, setTradeLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Tab definitions with required sections
  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'active-trades', label: 'Active Trades', icon: '⚡' },
    { id: 'pair-status', label: 'Pair Status', icon: '🔄' },
    { id: 'trade-history', label: 'Trade History', icon: '📜' },
    { id: 'analysis-logs', label: 'Analysis Logs', icon: '' },
    { id: 'trade-logs', label: 'Trade Logs', icon: '📋' }
  ];

  // Request data on component mount and periodically
  useEffect(() => {
    if (isConnected) {
      requestAllData();
      const interval = setInterval(requestAllData, 10000); // Update every 10 seconds
      return () => clearInterval(interval);
    }
  }, [isConnected, isLiveMode]);

  // Request all required data
  const requestAllData = async () => {
    if (!isConnected) return;

    try {
      // Request bot status (includes pair status and stats)
      if (getBotStatus) {
        await getBotStatus();
      }

      // Request positions (active trades)
      sendMessage({ type: 'get_positions' });

      // Request trade history from MongoDB - with mode parameter
      sendMessage({ type: 'get_trade_history', limit: 100, mode: isLiveMode ? 'live' : 'mock' });

      // Request analysis logs
      sendMessage({ type: 'get_analysis_logs', limit: 50 });

      // Request trade logs with confidence scores
      sendMessage({ type: 'get_trade_logs', limit: 50 });

      setLastUpdate(new Date());
    } catch (error) {
      // Error requesting data - handle silently
    }
  };

  // Update displayed trade history when global trading mode changes
  useEffect(() => {
    setTradeHistory(!isLiveMode ? mockTradeHistory : realTradeHistory);
  }, [isLiveMode, mockTradeHistory, realTradeHistory]);

  // Listen for WebSocket messages
  useEffect(() => {
    const handleBotResponse = (messageData) => {
      if (messageData.type === 'bot_status_response') {
        setBotStatus(messageData.data);
      }
    };

    const handleTradeHistoryResponse = (messageData) => {
      if (messageData.type === 'trade_history_response') {
        const trades = messageData.data.trades || [];
        const mode = messageData.data.mode || 'unknown';
        
        // Update trade history based on current mode
        if (mode === (isLiveMode ? 'live' : 'mock')) {
          setTradeHistory(trades);
        }
      }
    };

    const handleAnalysisLogsResponse = (messageData) => {
      if (messageData.type === 'analysis_logs_response') {
        setAnalysisLogs(messageData.data.logs || []);
      }
    };

    const handleTradeLogsResponse = (messageData) => {
      if (messageData.type === 'trade_logs_response') {
        setTradeLogs(messageData.data.logs || []);
      }
    };

    // Set up global message handlers
    window.handleBotResponse = handleBotResponse;
    window.handleTradeHistoryResponse = handleTradeHistoryResponse;
    window.handleAnalysisLogsResponse = handleAnalysisLogsResponse;
    window.handleTradeLogsResponse = handleTradeLogsResponse;

    return () => {
      // Clean up handlers
      if (window.handleBotResponse === handleBotResponse) {
        delete window.handleBotResponse;
      }
      if (window.handleTradeHistoryResponse === handleTradeHistoryResponse) {
        delete window.handleTradeHistoryResponse;
      }
      if (window.handleAnalysisLogsResponse === handleAnalysisLogsResponse) {
        delete window.handleAnalysisLogsResponse;
      }
      if (window.handleTradeLogsResponse === handleTradeLogsResponse) {
        delete window.handleTradeLogsResponse;
      }
    };
  }, []);

  // Format time ago
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

  // Format currency
  const formatCurrency = (value) => {
    if (typeof value !== 'number') return '$0.00';
    return `$${value.toFixed(2)}`;
  };

  // Format percentage
  const formatPercentage = (value) => {
    if (typeof value !== 'number') return '0.00%';
    return `${value.toFixed(2)}%`;
  };

  // Render Overview Section
  const renderOverview = () => {
    const positions = data?.positions || {};
    const { paper_balance = 0, trading_balance = null } = data || {};
    
    // Use correct balance based on trading mode
    const balance = (() => {
      if (isLiveMode && trading_balance) {
        if (typeof trading_balance.total === 'number' && trading_balance.total >= 0) {
          return trading_balance.total;
        }
        return 0;
      }
      return paper_balance || 100000;
    })();
    
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
    const activeTrades = botStats.active_trades || 0;
    const totalProfit = botStats.total_profit || 0;

    return (
      <div className="overview-section">
        <div className="overview-header">
          <h3>📊 Trading Overview</h3>
          <div className="last-update">
            Last Updated: {lastUpdate ? lastUpdate.toLocaleTimeString() : 'Never'}
          </div>
        </div>
        
        {/* Real-time Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-value">{formatCurrency(balance)}</div>
            <div className="stat-label">💰 Current Balance</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{activeTrades}</div>
            <div className="stat-label">⚡ Active Trades</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{formatCurrency(totalPnL)}</div>
            <div className="stat-label">📈 Total PnL</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{formatCurrency(totalProfit)}</div>
            <div className="stat-label">💎 Total Profit</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{totalTrades}</div>
            <div className="stat-label">📊 Total Trades</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{formatPercentage(winRate)}</div>
            <div className="stat-label">🎯 Win Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{tradestoday}</div>
            <div className="stat-label">📅 Trades Today</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{formatCurrency(totalValue)}</div>
            <div className="stat-label">💼 Position Value</div>
          </div>
        </div>

        {/* Bot Status */}
        <div className="bot-status-section">
          <div className="bot-status-header">
            <h4>🤖 Bot Status</h4>
            <div className={`bot-status-indicator ${botStats.enabled ? 'active' : 'inactive'}`}>
              {botStats.enabled ? '🟢 Active' : '🔴 Inactive'}
            </div>
          </div>
          
          {botStats.enabled && (
            <div className="bot-runtime-info">
              <div className="runtime-stat">
                <span>⏱️ Running Time:</span>
                <span>{Math.floor((botStats.running_duration || 0) / 60)} minutes</span>
              </div>
              <div className="runtime-stat">
                <span>🎯 Confidence Threshold:</span>
                <span>{((botStats.config?.ai_confidence_threshold || 0) * 100).toFixed(0)}%</span>
              </div>
              <div className="runtime-stat">
                <span>💰 Trade Amount:</span>
                <span>${botStats.config?.trade_amount_usdt || 0}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render Active Trades Section
  const renderActiveTrades = () => {
    const positions = data?.positions || {};
    const positionEntries = Object.entries(positions);

    return (
      <div className="active-trades-section">
        <div className="section-header">
          <h3>⚡ Active Trades</h3>
          <div className="section-stats">
            {positionEntries.length} Open Position{positionEntries.length !== 1 ? 's' : ''}
          </div>
        </div>

        {positionEntries.length > 0 ? (
          <div className="positions-grid">
            {positionEntries.map(([symbol, position]) => (
              <div key={symbol} className="position-card">
                <div className="position-header">
                  <div className="symbol">{symbol}</div>
                  <div className={`direction ${position.direction}`}>
                    {position.direction === 'long' ? '📈' : '📉'} {position.direction.toUpperCase()}
                  </div>
                </div>
                
                <div className="position-details">
                  <div className="detail-row">
                    <span>Amount:</span>
                    <span>{position.amount}</span>
                  </div>
                  <div className="detail-row">
                    <span>Entry Price:</span>
                    <span>{formatCurrency(position.entry_price)}</span>
                  </div>
                  <div className="detail-row">
                    <span>Current Price:</span>
                    <span>{formatCurrency(position.current_price)}</span>
                  </div>
                  <div className="detail-row">
                    <span>Unrealized PnL:</span>
                    <span className={position.unrealized_pnl >= 0 ? 'profit' : 'loss'}>
                      {formatCurrency(position.unrealized_pnl)}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span>Margin Used:</span>
                    <span>{formatCurrency(position.margin_used)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-data">
            <div className="no-data-icon">💤</div>
            <p>No active trades at the moment</p>
            <p>Start the bot to begin automated trading</p>
          </div>
        )}
      </div>
    );
  };

  // Render Pair Status Section
  const renderPairStatus = () => {
    const pairStatus = botStatus?.pair_status || {};
    const allowedPairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT'];

    return (
      <div className="pair-status-section">
        <div className="section-header">
          <h3>🔄 Pair Status</h3>
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
                <div className="pair-symbol">{symbol}</div>
                <div className="pair-status">
                  <div className="status-indicator">
                    {statusEmoji[status]} {statusLabel[status]}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render Trade History Section
  const renderTradeHistory = () => {
    return (
      <div className="trade-history-section">
        <div className="section-header">
          <h3>📜 Trade History</h3>
          <div className="section-stats">
            <span className="mode-indicator">
              {!isLiveMode ? '🧪 Mock' : '📈 Live'} Trading Mode
            </span>
            <span className="trade-count">
              {tradeHistory.length} Trade{tradeHistory.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {tradeHistory.length > 0 ? (
          <div className="trade-history-table">
            <div className="table-header">
              <div>Symbol</div>
              <div>Type</div>
              <div>Direction</div>
              <div>Amount</div>
              <div>Price</div>
              <div>PnL</div>
              <div>Time</div>
            </div>
            {tradeHistory.map((trade, index) => (
              <div key={index} className="table-row">
                <div>{trade.symbol}</div>
                <div className="trade-type">
                  {trade.bot_trade || trade.trade_type === 'bot' ? 
                    <span className="ai-tag">🤖 AI</span> : 
                    <span className="manual-tag">👤 Manual</span>
                  }
                  {trade.failed && trade.reason && (
                    <span className="failed-tag" title={trade.reason}>❌ Failed</span>
                  )}
                </div>
                <div className={`direction ${trade.direction?.toLowerCase()}`}>
                  {trade.direction}
                </div>
                <div>{trade.amount}</div>
                <div>{formatCurrency(trade.price)}</div>
                <div className={trade.pnl >= 0 ? 'profit' : 'loss'}>
                  {formatCurrency(trade.pnl)}
                </div>
                <div>{formatTimeAgo(trade.timestamp)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-data">
            <div className="no-data-icon">📊</div>
            <p>No trade history available</p>
            <p>Execute some trades to see history here</p>
          </div>
        )}
      </div>
    );
  };

  // Render Analysis Logs Section
  const renderAnalysisLogs = () => {
    return (
      <div className="analysis-logs-section">
        <div className="section-header">
          <h3> Analysis Logs</h3>
          <div className="section-stats">
            {analysisLogs.length} Log{analysisLogs.length !== 1 ? 's' : ''}
          </div>
        </div>

        <div className="logs-container">
          {analysisLogs.length > 0 ? (
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
          ) : (
            <div className="no-data">
              <div className="no-data-icon">📝</div>
              <p>No analysis logs available</p>
              <p>Analysis logs will appear here as AI analysis runs</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render Trade Logs Section
  const renderTradeLogs = () => {
    return (
      <div className="trade-logs-section">
        <div className="section-header">
          <h3>📋 Trade Logs</h3>
          <div className="section-stats">
            {tradeLogs.length} Log{tradeLogs.length !== 1 ? 's' : ''}
          </div>
        </div>

        <div className="trade-logs-container">
          {tradeLogs.length > 0 ? (
            tradeLogs.map((log, index) => (
              <div key={index} className={`trade-log-entry ${log.trade_decision?.toLowerCase()}`}>
                <div className="log-header">
                  <div className="log-symbol">{log.symbol}</div>
                  <div className="log-time">{formatTimeAgo(log.timestamp)}</div>
                </div>
                <div className="log-details">
                  <div className="confidence-info">
                    <span className="confidence-label">Confidence:</span>
                    <span className="confidence-value">{formatPercentage(log.final_confidence_score * 100)}</span>
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
          ) : (
            <div className="no-data">
              <div className="no-data-icon">📊</div>
              <p>No trade logs available</p>
              <p>Trade decision logs will appear here as analysis runs</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="ai-analysis-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-info">
          <h2>🤖 AI Analysis Dashboard</h2>
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>
        <div className="header-actions">
          <button className="refresh-btn" onClick={requestAllData} disabled={!isConnected}>
            🔄 Refresh All
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'active-trades' && renderActiveTrades()}
        {activeTab === 'pair-status' && renderPairStatus()}
        {activeTab === 'trade-history' && renderTradeHistory()}
        {activeTab === 'analysis-logs' && renderAnalysisLogs()}
        {activeTab === 'trade-logs' && renderTradeLogs()}
      </div>
    </div>
  );
};

export default AIAnalysis;