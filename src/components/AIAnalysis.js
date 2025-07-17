import React, { useState, useEffect } from 'react';
import './AIAnalysis.css';

const AIAnalysis = ({ isConnected, sendMessage }) => {
  console.log('🔍 AIAnalysis: Component initialized with props:', { isConnected, sendMessage: !!sendMessage });
  
  const [analysisData, setAnalysisData] = useState({});
  console.log('🔍 AIAnalysis: Initial analysisData:', analysisData);
  
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  console.log('🔍 AIAnalysis: Initial selectedSymbol:', selectedSymbol);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  console.log('🔍 AIAnalysis: Initial isAnalyzing:', isAnalyzing);
  
  const [analysisStatus, setAnalysisStatus] = useState({});
  console.log('🔍 AIAnalysis: Initial analysisStatus:', analysisStatus);
  
  const [pendingTrades, setPendingTrades] = useState([]);
  console.log('🔍 AIAnalysis: Initial pendingTrades length:', pendingTrades.length);
  
  const [analysisLogs, setAnalysisLogs] = useState([]);
  console.log('🔍 AIAnalysis: Initial analysisLogs length:', analysisLogs.length);
  
  // Additional state variables needed for the UI
  const [analysisEnabled, setAnalysisEnabled] = useState(false);
  console.log('🔍 AIAnalysis: Initial analysisEnabled:', analysisEnabled);
  
  const [analysisStartTime, setAnalysisStartTime] = useState(null);
  console.log('🔍 AIAnalysis: Initial analysisStartTime:', analysisStartTime);
  
  const [analysisLoading, setAnalysisLoading] = useState(false);
  console.log('🔍 AIAnalysis: Initial analysisLoading:', analysisLoading);
  
  const [activeTab, setActiveTab] = useState('current');
  console.log('🔍 AIAnalysis: Initial activeTab:', activeTab);
  
  const [opportunities, setOpportunities] = useState({});
  console.log('🔍 AIAnalysis: Initial opportunities:', opportunities);
  
  const [lastAlert, setLastAlert] = useState(null);
  console.log('🔍 AIAnalysis: Initial lastAlert:', lastAlert);
  
  const [showTradePopup, setShowTradePopup] = useState(null);
  console.log('🔍 AIAnalysis: Initial showTradePopup:', showTradePopup);
  
  const [usdtInputs, setUsdtInputs] = useState({});
  console.log('🔍 AIAnalysis: Initial usdtInputs:', usdtInputs);
  
  const [loading, setLoading] = useState(false);
  console.log('🔍 AIAnalysis: Initial loading:', loading);
  
  const [currentSymbol, setCurrentSymbol] = useState('BTCUSDT');
  console.log('🔍 AIAnalysis: Initial currentSymbol:', currentSymbol);
  
  const [analysis, setAnalysis] = useState(null);
  console.log('🔍 AIAnalysis: Initial analysis:', analysis);
  
  const [allAnalysis, setAllAnalysis] = useState({});
  console.log('🔍 AIAnalysis: Initial allAnalysis:', allAnalysis);
  
  const [targetPairs] = useState([
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 
    'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT'
  ]);
  console.log('🔍 AIAnalysis: Initial targetPairs:', targetPairs);

  const availableSymbols = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT', 
    'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT'
  ];

  // Global message handler for AI analysis responses
  const handleAIAnalysisResponse = (message) => {
    console.log('🔍 AIAnalysis: handleAIAnalysisResponse called with:', message);
    const { type, data } = message;
    console.log('🔍 AIAnalysis: Message type:', type, 'Data:', data);
    
    switch (type) {
      case 'ai_analysis_response':
        console.log('🔍 AIAnalysis: Processing ai_analysis_response for symbol:', data.symbol);
        setAnalysisData(prev => {
          const newData = { ...prev, [data.symbol]: data };
          console.log('🔍 AIAnalysis: Updated analysisData for', data.symbol, 'New data:', data);
          return newData;
        });
        setIsAnalyzing(false);
        console.log('🔍 AIAnalysis: Set isAnalyzing to false');
        setAnalysisStatus('completed');
        console.log('🔍 AIAnalysis: Set analysisStatus to completed');
        break;

      case 'all_ai_analysis_response':
        console.log('🔍 AIAnalysis: Processing all_ai_analysis_response');
        setAnalysisData(prev => {
          const newData = { ...prev, ...data.analyses };
          console.log('🔍 AIAnalysis: Updated analysisData with all analyses. New symbols:', Object.keys(data.analyses));
          return newData;
        });
        setIsAnalyzing(false);
        console.log('🔍 AIAnalysis: Set isAnalyzing to false');
        setAnalysisStatus('completed');
        console.log('🔍 AIAnalysis: Set analysisStatus to completed');
        break;

      case 'ai_opportunities_response':
        console.log('🔍 AIAnalysis: Processing ai_opportunities_response');
        setAnalysisData(prev => {
          const newData = { ...prev, ...data.opportunities };
          console.log('🔍 AIAnalysis: Updated analysisData with opportunities. New opportunities:', Object.keys(data.opportunities));
          return newData;
        });
        break;

      case 'ai_opportunity_alert':
        console.log('🔍 AIAnalysis: Processing ai_opportunity_alert for symbol:', data.symbol);
        setAnalysisData(prev => {
          const newData = { ...prev, [data.symbol]: data };
          console.log('🔍 AIAnalysis: Updated analysisData with opportunity alert for', data.symbol);
          return newData;
        });
        break;

      case 'analysis_status':
        console.log('🔍 AIAnalysis: Processing analysis_status:', data);
        setAnalysisStatus(data.status);
        console.log('🔍 AIAnalysis: Updated analysisStatus to:', data.status);
        if (data.progress) {
          console.log('🔍 AIAnalysis: Analysis progress:', data.progress);
        }
        break;

      case 'analysis_status_response':
        console.log('🔍 AIAnalysis: Processing analysis_status_response:', data);
        setAnalysisStatus(data.status);
        console.log('🔍 AIAnalysis: Updated analysisStatus to:', data.status);
        setIsAnalyzing(data.status === 'analyzing');
        console.log('🔍 AIAnalysis: Set isAnalyzing to:', data.status === 'analyzing');
        break;

      case 'pending_trades_response':
        console.log('🔍 AIAnalysis: Processing pending_trades_response');
        setPendingTrades(data.trades || []);
        console.log('🔍 AIAnalysis: Updated pendingTrades. Count:', data.trades ? data.trades.length : 0);
        break;

      case 'trade_accepted':
        console.log('🔍 AIAnalysis: Processing trade_accepted for symbol:', data.symbol);
        setPendingTrades(prev => {
          const newTrades = prev.filter(trade => trade.symbol !== data.symbol);
          console.log('🔍 AIAnalysis: Removed accepted trade for', data.symbol, 'from pendingTrades. Remaining:', newTrades.length);
          return newTrades;
        });
        break;

      case 'trade_ready_alert':
        console.log('🔍 AIAnalysis: Processing trade_ready_alert for symbol:', data.symbol);
        setPendingTrades(prev => {
          const newTrades = [...prev, data];
          console.log('🔍 AIAnalysis: Added trade ready alert for', data.symbol, 'to pendingTrades. New count:', newTrades.length);
          return newTrades;
        });
        break;

      case 'analysis_log':
        console.log('🔍 AIAnalysis: Processing analysis_log');
        setAnalysisLogs(prev => {
          const newLogs = [data, ...prev.slice(0, 49)];
          console.log('🔍 AIAnalysis: Added analysis log. New logs length:', newLogs.length);
          return newLogs;
        });
        break;

      default:
        console.log('🔍 AIAnalysis: Unknown message type:', type);
    }
  };

  // Expose handler for WebSocket messages
  useEffect(() => {
    console.log('🔍 AIAnalysis: Setting up global handleAIAnalysisResponse');
    window.handleAIAnalysisResponse = handleAIAnalysisResponse;
    
    return () => {
      console.log('🔍 AIAnalysis: Cleaning up global handleAIAnalysisResponse');
      if (window.handleAIAnalysisResponse === handleAIAnalysisResponse) {
        delete window.handleAIAnalysisResponse;
      }
    };
  }, []);

  const handleAnalyzeSymbol = async (symbol) => {
    console.log('🔍 AIAnalysis: handleAnalyzeSymbol called with symbol:', symbol);
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot analyze symbol - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Starting analysis for symbol:', symbol);
    setIsAnalyzing(true);
    console.log('🔍 AIAnalysis: Set isAnalyzing to true');
    setAnalysisStatus('analyzing');
    console.log('🔍 AIAnalysis: Set analysisStatus to analyzing');
    
    try {
      const message = {
        type: 'get_ai_analysis',
        symbol: symbol
      };
      console.log('🔍 AIAnalysis: Sending analysis request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error requesting analysis:', error);
      setIsAnalyzing(false);
      console.log('🔍 AIAnalysis: Set isAnalyzing to false due to error');
      setAnalysisStatus('error');
      console.log('🔍 AIAnalysis: Set analysisStatus to error');
    }
  };

  const handleAnalyzeAll = async () => {
    console.log('🔍 AIAnalysis: handleAnalyzeAll called');
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot analyze all - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Starting analysis for all symbols');
    setIsAnalyzing(true);
    console.log('🔍 AIAnalysis: Set isAnalyzing to true');
    setAnalysisStatus('analyzing');
    console.log('🔍 AIAnalysis: Set analysisStatus to analyzing');
    
    try {
      const message = {
        type: 'get_all_ai_analysis',
        symbols: availableSymbols
      };
      console.log('🔍 AIAnalysis: Sending all analysis request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error requesting all analysis:', error);
      setIsAnalyzing(false);
      console.log('🔍 AIAnalysis: Set isAnalyzing to false due to error');
      setAnalysisStatus('error');
      console.log('🔍 AIAnalysis: Set analysisStatus to error');
    }
  };

  const handleGetOpportunities = async () => {
    console.log('🔍 AIAnalysis: handleGetOpportunities called');
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot get opportunities - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Requesting high-confidence opportunities');
    try {
      const message = {
        type: 'get_ai_opportunities',
        min_confidence: 0.8
      };
      console.log('🔍 AIAnalysis: Sending opportunities request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error requesting opportunities:', error);
    }
  };

  const handleGetPendingTrades = async () => {
    console.log('🔍 AIAnalysis: handleGetPendingTrades called');
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot get pending trades - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Requesting pending trades');
    try {
      const message = {
        type: 'get_pending_trades'
      };
      console.log('🔍 AIAnalysis: Sending pending trades request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error requesting pending trades:', error);
    }
  };

  const handleAcceptTrade = async (symbol) => {
    console.log('🔍 AIAnalysis: handleAcceptTrade called for symbol:', symbol);
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot accept trade - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Accepting trade for symbol:', symbol);
    try {
      const message = {
        type: 'accept_trade',
        symbol: symbol
      };
      console.log('🔍 AIAnalysis: Sending accept trade request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error accepting trade:', error);
    }
  };

  const handleRejectTrade = async (symbol) => {
    console.log('🔍 AIAnalysis: handleRejectTrade called for symbol:', symbol);
    if (!isConnected) {
      console.log('🔍 AIAnalysis: Cannot reject trade - not connected');
      return;
    }
    
    console.log('🔍 AIAnalysis: Rejecting trade for symbol:', symbol);
    try {
      const message = {
        type: 'reject_trade',
        symbol: symbol
      };
      console.log('🔍 AIAnalysis: Sending reject trade request:', message);
      sendMessage(message);
    } catch (error) {
      console.error('🔍 AIAnalysis: Error rejecting trade:', error);
    }
  };

  // Additional functions needed for the UI
  const startAnalysis = async () => {
    console.log('🔍 AIAnalysis: startAnalysis called');
    setAnalysisLoading(true);
    setAnalysisEnabled(true);
    setAnalysisStartTime(Date.now() / 1000);
    // Implementation would go here
  };

  const stopAnalysis = async () => {
    console.log('🔍 AIAnalysis: stopAnalysis called');
    setAnalysisLoading(true);
    setAnalysisEnabled(false);
    setAnalysisStartTime(null);
    // Implementation would go here
  };

  const getOpportunities = async () => {
    console.log('🔍 AIAnalysis: getOpportunities called');
    await handleGetOpportunities();
  };

  const getPendingTrades = async () => {
    console.log('🔍 AIAnalysis: getPendingTrades called');
    await handleGetPendingTrades();
  };

  const getAllAnalysis = async () => {
    console.log('🔍 AIAnalysis: getAllAnalysis called');
    await handleAnalyzeAll();
  };

  const triggerManualAnalysis = async () => {
    console.log('🔍 AIAnalysis: triggerManualAnalysis called');
    await handleAnalyzeAll();
  };

  const getAnalysisStatus = async () => {
    console.log('🔍 AIAnalysis: getAnalysisStatus called');
    // Implementation would go here
  };

  const getAnalysisForSymbol = async (symbol) => {
    console.log('🔍 AIAnalysis: getAnalysisForSymbol called for:', symbol);
    await handleAnalyzeSymbol(symbol);
  };

  const acceptTrade = async (symbol) => {
    console.log('🔍 AIAnalysis: acceptTrade called for:', symbol);
    await handleAcceptTrade(symbol);
  };

  // Render functions
  const renderMarketData = (marketData) => {
    console.log('🔍 AIAnalysis: renderMarketData called with:', marketData);
    return <div>Market Data: {JSON.stringify(marketData)}</div>;
  };

  const renderClaudeAnalysis = (claudeAnalysis) => {
    console.log('🔍 AIAnalysis: renderClaudeAnalysis called with:', claudeAnalysis);
    return <div>Claude Analysis: {JSON.stringify(claudeAnalysis)}</div>;
  };

  const renderGPTAnalysis = (gptAnalysis) => {
    console.log('🔍 AIAnalysis: renderGPTAnalysis called with:', gptAnalysis);
    return <div>GPT Analysis: {JSON.stringify(gptAnalysis)}</div>;
  };

  const renderOpportunityCard = (symbol, analysis) => {
    console.log('🔍 AIAnalysis: renderOpportunityCard called for:', symbol);
    return <div key={symbol}>Opportunity: {symbol}</div>;
  };

  const renderPendingTrade = (symbol, tradeData) => {
    console.log('🔍 AIAnalysis: renderPendingTrade called for:', symbol);
    return <div key={symbol}>Pending Trade: {symbol}</div>;
  };

  const renderSearchText = (symbol) => {
    console.log('🔍 AIAnalysis: renderSearchText called for:', symbol);
    return <div>Searching: {symbol}</div>;
  };

  // Debug logging for state changes
  useEffect(() => {
    console.log('🔍 AIAnalysis: State updated:', {
      analysisData: Object.keys(analysisData).length,
      selectedSymbol,
      isAnalyzing,
      analysisStatus,
      pendingTrades: pendingTrades.length,
      analysisLogs: analysisLogs.length,
      isConnected
    });
  }, [analysisData, selectedSymbol, isAnalyzing, analysisStatus, pendingTrades, analysisLogs, isConnected]);

  return (
    <div className="ai-analysis-container">
      {/* Analysis Control Header */}
      <div className="analysis-control-header">
        <div className="control-status">
          <span className={`status-indicator ${analysisEnabled ? 'running' : 'stopped'}`}>
            {analysisEnabled ? '🟢' : '🔴'}
          </span>
          <span className="status-text">
            {analysisEnabled ? 'Analysis Running' : 'Analysis Stopped'}
          </span>
          {analysisStartTime && (
            <span className="running-time">
              Running for {Math.floor((Date.now() / 1000 - analysisStartTime) / 60)}m
            </span>
          )}
        </div>
        <div className="control-buttons">
          {!analysisEnabled ? (
            <button 
              className="start-analysis-btn"
              onClick={startAnalysis}
              disabled={!isConnected || analysisLoading}
            >
              {analysisLoading ? (
                <>
                  <div className="spinner"></div>
                  Starting...
                </>
              ) : (
                '🚀 Start Analysis'
              )}
            </button>
          ) : (
            <button 
              className="stop-analysis-btn"
              onClick={stopAnalysis}
              disabled={!isConnected || analysisLoading}
            >
              {analysisLoading ? (
                <>
                  <div className="spinner"></div>
                  Stopping...
                </>
              ) : (
                '⏹️ Stop Analysis'
              )}
            </button>
          )}
        </div>
      </div>

      <div className="ai-header">
        <div className="ai-controls">
          <button 
            className={`tab-btn ${activeTab === 'current' ? 'active' : ''}`}
            onClick={() => setActiveTab('current')}
          >
            Current Analysis
          </button>
          <button 
            className={`tab-btn ${activeTab === 'opportunities' ? 'active' : ''}`}
            onClick={() => setActiveTab('opportunities')}
          >
            Opportunities ({Object.keys(opportunities).length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'pending' ? 'active' : ''}`}
            onClick={() => setActiveTab('pending')}
          >
            Pending Trades ({Object.keys(pendingTrades).length})
          </button>
          <button 
            className={`tab-btn ${activeTab === 'monitoring' ? 'active' : ''}`}
            onClick={() => setActiveTab('monitoring')}
          >
            All Pairs
          </button>
        </div>
      </div>

      {/* AI Opportunity Alert */}
      {lastAlert && (
        <div className="ai-alert">
          <div className="alert-header">
            <span className="alert-icon">🚨</span>
            <span className="alert-title">High Confidence Opportunity</span>
            <button 
              className="alert-close"
              onClick={() => setLastAlert(null)}
            >
              ×
            </button>
          </div>
          <div className="alert-content">
            <strong>{lastAlert.symbol}</strong> - Confidence Score: {lastAlert.analysis.gpt_analysis.confidence_score}/10
          </div>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'current' && (
        <div className="current-analysis">
          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Analyzing {currentSymbol}...</p>
            </div>
          ) : analysis && !analysis.error ? (
            <div className="analysis-pipeline">
              {renderMarketData(analysis.market_data)}
              {renderClaudeAnalysis(analysis.claude_analysis)}
              {renderGPTAnalysis(analysis.gpt_analysis)}
            </div>
          ) : (
            <div className="no-analysis">
              <p>No analysis available for {currentSymbol}</p>
              <button 
                className="refresh-btn"
                onClick={() => getAnalysisForSymbol(currentSymbol)}
              >
                Refresh Analysis
              </button>
              <button 
                className="refresh-btn"
                onClick={() => {
                  console.log('Current analysis state:', analysis);
                  console.log('All analysis state:', allAnalysis);
                }}
              >
                Debug State
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'opportunities' && (
        <div className="opportunities-view">
          <div className="opportunities-header">
            <h3>All AI Analysis Results</h3>
            <button 
              className="refresh-btn"
              onClick={getOpportunities}
            >
              Refresh
            </button>
          </div>
          {Object.keys(opportunities).length > 0 ? (
            <div className="opportunities-grid">
              {Object.entries(opportunities).map(([symbol, analysis]) => 
                renderOpportunityCard(symbol, analysis)
              )}
            </div>
          ) : (
            <div className="no-opportunities">
              <p>No analysis results available at this time.</p>
              <p>The AI is continuously monitoring all pairs for trading opportunities.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'pending' && (
        <div className="pending-trades-view">
          <div className="pending-trades-header">
            <h3>Pending Trades</h3>
            <button 
              className="refresh-btn"
              onClick={getPendingTrades}
            >
              Refresh
            </button>
          </div>
          {Object.keys(pendingTrades).length > 0 ? (
            <div className="pending-trades-grid">
              {Object.entries(pendingTrades).map(([symbol, tradeData]) => 
                renderPendingTrade(symbol, tradeData)
              )}
            </div>
          ) : (
            <div className="no-pending-trades">
              <p>No pending trades at this time.</p>
              <p>The AI is continuously monitoring for new opportunities.</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div className="monitoring-view">
          <div className="monitoring-header">
            <h3>All Pairs Monitoring</h3>
            <button 
              className="refresh-btn"
              onClick={getAllAnalysis}
              disabled={Object.values(analysisStatus).some(status => status !== 'idle' && status !== 'completed')}
            >
              Refresh All
            </button>
            <button 
              className="refresh-btn"
              onClick={triggerManualAnalysis}
              disabled={Object.values(analysisStatus).some(status => status !== 'idle' && status !== 'completed')}
            >
              Manual Refresh
            </button>
            <button 
              className="refresh-btn"
              onClick={getAnalysisStatus}
            >
              Update Status
            </button>
          </div>
          
          {/* Debug info */}
          <div className="debug-info" style={{ padding: '10px', background: '#2a2a2a', marginBottom: '10px', borderRadius: '4px', fontSize: '12px' }}>
            <div>Total pairs: {targetPairs.length}</div>
            <div>Analysis data received: {Object.keys(allAnalysis).length}</div>
            <div>Available symbols: {Object.keys(allAnalysis).join(', ')}</div>
            <div>Active analysis: {Object.values(analysisStatus).filter(s => s !== 'idle' && s !== 'completed').length}</div>
          </div>
          
          <div className="pairs-grid">
            {targetPairs.map(symbol => {
              const pairAnalysis = allAnalysis[symbol];
              const status = analysisStatus[symbol];
              const isAnalyzing = status && status !== 'idle' && status !== 'completed';
              
              return (
                <div key={symbol} className="pair-card">
                  <div className="pair-header">
                    <h4>{symbol}</h4>
                    {pairAnalysis && pairAnalysis.gpt_analysis && (
                      <span className={`confidence-badge ${(pairAnalysis.gpt_analysis.confidence_score || 0) >= 0.8 ? 'high' : (pairAnalysis.gpt_analysis.confidence_score || 0) >= 0.7 ? 'medium' : 'low'}`}>
                        {Math.round((pairAnalysis.gpt_analysis.confidence_score || 0) * 100)}%
                      </span>
                    )}
                  </div>
                  
                  {/* Real-time search text */}
                  {isAnalyzing && renderSearchText(symbol)}
                  
                  {pairAnalysis ? (
                    <div className="pair-summary">
                      <div className="summary-row">
                        <span>Price:</span>
                        <span>${pairAnalysis.market_data?.price || 'N/A'}</span>
                      </div>
                      <div className="summary-row">
                        <span>Bias:</span>
                        <span className={`bias-badge ${pairAnalysis.claude_analysis?.bias || 'neutral'}`}>
                          {pairAnalysis.claude_analysis?.bias || 'neutral'}
                        </span>
                      </div>
                      <div className="summary-row">
                        <span>RSI:</span>
                        <span>{pairAnalysis.market_data?.indicators?.RSI_14 || 'N/A'}</span>
                      </div>
                      <div className="summary-row">
                        <span>Direction:</span>
                        <span className={`direction-badge ${(pairAnalysis.gpt_analysis?.direction || 'NO_TRADE').toLowerCase()}`}>
                          {pairAnalysis.gpt_analysis?.direction || 'NO_TRADE'}
                        </span>
                      </div>
                      {pairAnalysis.gpt_analysis?.direction !== 'NO_TRADE' && (
                        <div className="summary-row">
                          <span>Entry:</span>
                          <span>${pairAnalysis.gpt_analysis?.entry_price || 'N/A'}</span>
                        </div>
                      )}
                      
                      {/* Show Accept Trade button for opportunities */}
                      {pairAnalysis.gpt_analysis?.direction !== 'NO_TRADE' && pairAnalysis.gpt_analysis?.confidence_score >= 0.7 && (
                        <div className="opportunity-actions">
                          <button 
                            className="accept-opportunity-btn"
                            onClick={() => {
                              setUsdtInputs(prev => ({
                                ...prev,
                                [symbol]: ''
                              }));
                              setShowTradePopup(symbol);
                            }}
                          >
                            Accept Trade
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="pair-loading">
                      {isAnalyzing ? (
                        <>
                          <div className="mini-spinner"></div>
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <div className="mini-spinner"></div>
                          <span>Waiting for analysis...</span>
                          {!pairAnalysis && (
                            <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
                              No data yet
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {/* Trade Acceptance Popup */}
      {showTradePopup && (
        <div className="trade-popup-overlay" onClick={() => setShowTradePopup(null)}>
          <div className="trade-popup" onClick={(e) => e.stopPropagation()}>
            <div className="trade-popup-header">
              <h3>Accept Trade - {showTradePopup}</h3>
              <button 
                className="popup-close-btn"
                onClick={() => setShowTradePopup(null)}
              >
                ×
              </button>
            </div>
            
            <div className="trade-popup-content">
              <div className="trade-info-summary">
                <div className="info-row">
                  <span>Direction:</span>
                  <span className={`direction-badge ${opportunities[showTradePopup]?.gpt_analysis?.direction?.toLowerCase() || 'unknown'}`}>
                    {opportunities[showTradePopup]?.gpt_analysis?.direction || 'N/A'}
                  </span>
                </div>
                <div className="info-row">
                  <span>Confidence:</span>
                  <span className="confidence-score">
                    {Math.round((opportunities[showTradePopup]?.gpt_analysis?.confidence_score || 0) * 100)}%
                  </span>
                </div>
                <div className="info-row">
                  <span>Entry Price:</span>
                  <span>${opportunities[showTradePopup]?.gpt_analysis?.entry_price?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="info-row">
                  <span>Stop Loss:</span>
                  <span>${opportunities[showTradePopup]?.gpt_analysis?.stop_loss?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="info-row">
                  <span>Take Profit:</span>
                  <span>${opportunities[showTradePopup]?.gpt_analysis?.take_profit?.toFixed(2) || 'N/A'}</span>
                </div>
              </div>
              
              <div className="trade-amount-input">
                <label htmlFor="usdt-amount">USDT Amount to Invest:</label>
                <input
                  id="usdt-amount"
                  type="number"
                  min="1"
                  step="any"
                  placeholder="Enter USDT amount"
                  value={usdtInputs[showTradePopup] || ''}
                  onChange={(e) => setUsdtInputs(prev => ({
                    ...prev,
                    [showTradePopup]: e.target.value
                  }))}
                  className="usdt-input"
                />
                <small className="input-hint">
                  Minimum: $1 | Recommended: $100 - $1000
                </small>
              </div>
              
              <div className="trade-popup-actions">
                <button 
                  className="btn-cancel"
                  onClick={() => setShowTradePopup(null)}
                >
                  Cancel
                </button>
                <button 
                  className="btn-accept"
                  onClick={() => {
                    acceptTrade(showTradePopup);
                    setShowTradePopup(null);
                  }}
                  disabled={!usdtInputs[showTradePopup] || parseFloat(usdtInputs[showTradePopup]) < 1}
                >
                  Accept & Execute Trade
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAnalysis; 