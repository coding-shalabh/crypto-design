import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import apiService from '../services/apiService';
import tradingService from '../services/tradingService';
import { toast } from 'react-toastify';

// Redux actions
import { setBotStatus, setBotEnabled, setActiveTrades, addAnalysisLog, addTradeLog } from '../store/slices/botSlice';
import { setPaperBalance, setPositions, setRecentTrades, addTrade } from '../store/slices/tradingSlice';
import { updateCryptoData } from '../store/slices/marketDataSlice';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const dispatch = useDispatch();
  
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [data, setData] = useState({ 
    crypto_data: {}, 
    price_cache: {}, 
    positions: {}, 
    paper_balance: 0, 
    recent_trades: [], 
    ai_analysis: {}, 
    ai_opportunities: {},
    bot_status: {
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
    }
  });
  const [error, setError] = useState(null);
  const [lastConnectionCheck, setLastConnectionCheck] = useState(null);
  const [connectionErrorDetails, setConnectionErrorDetails] = useState(null);
  
  // Use centralized API service
  const apiServiceRef = useRef(apiService);
  
  // 🔧 FIXED: Use refs to prevent infinite re-renders
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5; // Reduced from 10
  const baseReconnectDelay = 10000; // Reduced from 20 seconds to 10 seconds
  const maxReconnectDelay = 30000; // Reduced from 60 seconds
  const isReconnectingRef = useRef(false);
  const messageQueueRef = useRef([]);
  const isManualCloseRef = useRef(false);
  const botOperationInProgressRef = useRef(false); // NEW: Track bot operations
  
  // 🔧 FIXED: Heartbeat mechanism
  const heartbeatIntervalRef = useRef(null);
  const lastHeartbeatRef = useRef(null);
  const missedHeartbeatsRef = useRef(0);
  const maxMissedHeartbeats = 3;

  const connect = useCallback(() => {
    
    // Don't connect if already connected or connecting
    if (socketRef.current && 
        (socketRef.current.readyState === WebSocket.CONNECTING || 
         socketRef.current.readyState === WebSocket.OPEN)) {
      return;
    }
    
    try {
      setConnectionStatus('connecting');
      
      // 🔧 FIXED: Create WebSocket with proper URL
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8767';
      
      const newSocket = new WebSocket(wsUrl);
      socketRef.current = newSocket;
      setSocket(newSocket);
      
      // 🔧 FIXED: Set connection timeout
      const connectionTimeout = setTimeout(() => {
        if (newSocket.readyState === WebSocket.CONNECTING) {
          // Connection timeout
          newSocket.close();
        }
      }, 10000); // 10 second timeout
      
      newSocket.onopen = (event) => {
        // Connection opened successfully
        clearTimeout(connectionTimeout);
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null); // Clear any previous errors
        setConnectionErrorDetails(null); // Clear error details
        reconnectAttemptsRef.current = 0;
        isReconnectingRef.current = false;
        
        // 🔥 NEW: Clear any existing error toasts
        toast.dismiss('connection-error');
        toast.dismiss('reconnecting');
        toast.dismiss('connection-failed');
        
        // Show success toast on connection restoration
        if (reconnectAttemptsRef.current > 0) {
          toast.success(
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>✅ Connection Restored</div>
              <div>Successfully connected to backend server</div>
            </div>,
            {
              position: "top-center",
              autoClose: 3000,
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
            }
          );
        }
        
        // 🔧 FIXED: Start heartbeat
        startHeartbeat();
        
        // 🔧 FIXED: Send queued messages
        sendQueuedMessages();
      };
      
      newSocket.onmessage = (event) => {
        let message;
        try {
          message = JSON.parse(event.data);
        } catch (e) {
          return;
        }
        // Remove debug logging to prevent spam
        // console.log('[WebSocketContext] Received message:', message);
          // Message received
          
          // 🔧 FIXED: Handle heartbeat responses
          if (message.type === 'pong') {
            handleHeartbeatResponse();
            return;
          }
          
          setLastMessage(message);
          
          // 🔧 FIXED: Update data state based on message type + Redux
          if (message.type === 'initial_data' && message.data) {
            setData(prevData => ({
              ...prevData,
              ...message.data,
              positions: message.data.positions || {},
              paper_balance: message.data.paper_balance || prevData.paper_balance || 0,
              ai_analysis: prevData.ai_analysis || {},
              ai_opportunities: prevData.ai_opportunities || {}
            }));
            
            // 🔥 NEW: Update Redux store
            if (message.data.positions) {
              dispatch(setPositions(message.data.positions));
            }
            if (message.data.paper_balance !== undefined) {
              dispatch(setPaperBalance(message.data.paper_balance));
            }
          } else if (message.type === 'crypto_data_response' && message.data) {
            setData(prevData => ({
              ...prevData,
              crypto_data: message.data
            }));
          } else if (message.type === 'price_updates_batch' && message.data) {
            const updates = message.data.updates || [];
            const newPriceCache = updates.reduce((acc, update) => {
              acc[update.symbol] = update;
              return acc;
            }, {});
            
            setData(prevData => ({
              ...prevData,
              price_cache: {
                ...prevData.price_cache,
                ...newPriceCache
              }
            }));
          } else if (message.type === 'position_update' && message.data) {
            setData(prevData => ({
              ...prevData,
              positions: message.data.positions || {},
              paper_balance: message.data.balance || prevData.paper_balance
            }));
          } else if (message.type === 'positions_response' && message.data) {
            setData(prevData => ({
              ...prevData,
              positions: message.data.positions || {},
              paper_balance: message.data.balance || prevData.paper_balance
            }));
          } else if (message.type === 'trade_executed' && message.data) {
            setData(prevData => ({
              ...prevData,
              positions: message.data.positions || prevData.positions,
              paper_balance: message.data.new_balance || prevData.paper_balance
            }));
          } else if (message.type === 'recent_trades_update' && message.data) {
            const recentTrades = message.data.recent_trades || [];
            setData(prevData => ({
              ...prevData,
              recent_trades: recentTrades
            }));
          } else if (message.type === 'ai_analysis_response' && message.data) {
            const symbol = message.data.symbol || 'unknown';
            setData(prevData => ({
              ...prevData,
              ai_analysis: {
                ...prevData.ai_analysis,
                [symbol]: message.data
              }
            }));
          } else if (message.type === 'ai_opportunity_alert' && message.data) {
            const symbol = message.data.symbol || 'unknown';
            setData(prevData => ({
              ...prevData,
              ai_opportunities: {
                ...prevData.ai_opportunities,
                [symbol]: message.data
              }
            }));
          } else if (message.type === 'bot_status_response' && message.data) {
            setData(prevData => ({
              ...prevData,
              bot_status: {
                ...prevData.bot_status,
                ...message.data
              }
            }));
            
            // 🔥 NEW: Update Redux store
            dispatch(setBotStatus(message.data));
            
          } else if (message.type === 'start_bot_response' && message.data) {
            // 🔥 NEW: Mark bot operation as in progress
            botOperationInProgressRef.current = true;
            
            if (message.data.success) {
              setData(prevData => ({
                ...prevData,
                bot_status: {
                  ...prevData.bot_status,
                  enabled: true
                }
              }));
              
              // 🔥 NEW: Update Redux store
              dispatch(setBotEnabled(true));
            }
            
            // Clear bot operation flag after a short delay
            setTimeout(() => {
              botOperationInProgressRef.current = false;
            }, 5000);
            
          } else if (message.type === 'stop_bot_response' && message.data) {
            // 🔥 NEW: Mark bot operation as in progress
            botOperationInProgressRef.current = true;
            
            if (message.data.success) {
              setData(prevData => ({
                ...prevData,
                bot_status: {
                  ...prevData.bot_status,
                  enabled: false
                }
              }));
              
              // 🔥 NEW: Update Redux store
              dispatch(setBotEnabled(false));
            }
            
            // Clear bot operation flag after a short delay
            setTimeout(() => {
              botOperationInProgressRef.current = false;
            }, 2000);
          } else if (message.type === 'trading_balance' && message.data) {
            setData(prevData => ({
              ...prevData,
              trading_balance: message.data.balance,
              trading_mode: message.data.mode,
              // Update paper_balance for mock mode compatibility
              paper_balance: message.data.mode === 'mock' ? message.data.balance.total : prevData.paper_balance
            }));
          } else if (message.type === 'all_trading_balances' && message.data) {
            setData(prevData => ({
              ...prevData,
              all_trading_balances: message.data.balances,
              trading_mode: message.data.mode
            }));
          } else if (message.type === 'order_placed' && message.data) {
            // 🔥 NEW: Handle live order placement response
            if (message.data.success) {
              // Show success message
              if (window.showToast) {
                window.showToast('success', `Live order placed successfully: ${message.data.message}`);
              }
              // Trigger balance refresh
              if (sendMessage) {
                sendMessage({ type: 'get_trading_balance' });
              }
            } else {
              // Show error message
              if (window.showToast) {
                window.showToast('error', `Order placement failed: ${message.data.message}`);
              }
            }
          } else if (message.type === 'trading_mode_updated' && message.data) {
            // 🔥 NEW: Handle trading mode update response
            if (window.showToast) {
              window.showToast('info', message.data.message);
            }
          }
          
          // 🔧 DEPRECATED: AI analysis messages are now handled directly in the main context
          // Keep this for backward compatibility with existing AI analysis component
          if (window.handleAIAnalysisResponse && 
              ['ai_analysis_response', 'all_ai_analysis_response', 'ai_opportunities_response', 
               'ai_opportunity_alert', 'analysis_status', 'analysis_status_response', 
               'pending_trades_response', 'trade_accepted', 'trade_ready_alert', 'analysis_log'].includes(message.type)) {
            try {
              window.handleAIAnalysisResponse(message);
            } catch (error) {
            }
          }
          
          // 🔧 FIXED: Route bot messages to bot handler
          if (window.handleBotResponse && 
              ['bot_start_response', 'bot_stop_response', 'bot_status_response', 'bot_status_update', 
               'bot_config_update_response', 'bot_trade_executed', 'bot_error'].includes(message.type)) {
            try {
              window.handleBotResponse(message);
            } catch (error) {
            }
          }
          
          // Route trading messages to trading service
          if (['trading_mode_set', 'all_trading_balances', 'trading_order_placed', 
               'portfolio_summary', 'trading_connection_test', 'categorized_balances', 'wallet_balances',
               'wallet_transfer_result', 'transfer_history'].includes(message.type)) {
            try {
              tradingService.handleMessage(message);
            } catch (error) {
            }
          }
        };
      
      newSocket.onerror = (error) => {
        clearTimeout(connectionTimeout);
        setConnectionStatus('error');
        
        // 🔥 NEW: Enhanced error handling with detailed information
        const errorMessage = 'Backend connection failed';
        const errorDetails = {
          message: errorMessage,
          timestamp: new Date().toISOString(),
          error: error,
          reconnectAttempts: reconnectAttemptsRef.current,
          maxAttempts: maxReconnectAttempts
        };
        
        setError(errorMessage);
        setConnectionErrorDetails(errorDetails);
        setLastConnectionCheck(new Date());
        
        // Show user-friendly error popup
        toast.error(
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🔴 Connection Error</div>
            <div>Backend server connection failed</div>
            <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.8 }}>
              Attempting to reconnect in 20 seconds...
            </div>
          </div>, 
          {
            position: "top-center",
            autoClose: false, // Keep open until connection is restored
            hideProgressBar: false,
            closeOnClick: false,
            pauseOnHover: true,
            draggable: true,
            toastId: 'connection-error', // Prevent multiple toasts
          }
        );
      };
      
      newSocket.onclose = (event) => {
        // Connection closed
        clearTimeout(connectionTimeout);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
        
        // 🔥 NEW: Enhanced close handling with detailed information
        const closeDetails = {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          timestamp: new Date().toISOString()
        };
        
        
        // 🔧 FIXED: Only reconnect if not manually closed and within attempt limits
        // 🔥 NEW: Be less aggressive during bot operations
        if (!isManualCloseRef.current && 
            reconnectAttemptsRef.current < maxReconnectAttempts && 
            !isReconnectingRef.current &&
            !botOperationInProgressRef.current) {
          
          // Update error message based on close reason
          let errorMessage = 'Backend connection lost';
          if (event.code === 1006) {
            errorMessage = 'Backend server is not responding';
          } else if (event.code === 1015) {
            errorMessage = 'Backend server certificate error';
          }
          
          setError(errorMessage);
          setConnectionErrorDetails({
            ...closeDetails,
            message: errorMessage,
            reconnectAttempts: reconnectAttemptsRef.current,
            maxAttempts: maxReconnectAttempts
          });
          setLastConnectionCheck(new Date());
          
          // Show reconnection message
          toast.info(
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🔄 Reconnecting...</div>
              <div>Attempt {reconnectAttemptsRef.current + 1} of {maxReconnectAttempts}</div>
              <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.8 }}>
                Next attempt in 20 seconds
              </div>
            </div>,
            {
              position: "top-center",
              autoClose: false,
              hideProgressBar: false,
              closeOnClick: false,
              pauseOnHover: true,
              draggable: true,
              toastId: 'reconnecting',
            }
          );
          
          scheduleReconnect();
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          // Max reconnection attempts reached
          setConnectionStatus('failed');
          setError('Maximum reconnection attempts reached. Please refresh the page.');
          
          toast.error(
            <div>
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>❌ Connection Failed</div>
              <div>Unable to connect to backend server</div>
              <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.8 }}>
                Please check if the server is running and refresh the page
              </div>
            </div>,
            {
              position: "top-center",
              autoClose: false,
              hideProgressBar: false,
              closeOnClick: true,
              pauseOnHover: true,
              draggable: true,
              toastId: 'connection-failed',
            }
          );
        }
        
        // Reset manual close flag
        isManualCloseRef.current = false;
      };
      
    } catch (error) {
      setConnectionStatus('error');
      scheduleReconnect();
    }
  }, []);
  
  // 🔧 FIXED: Improved reconnection logic with 20-second intervals
  const scheduleReconnect = useCallback(() => {
    if (isReconnectingRef.current) {
      return;
    }
    
    isReconnectingRef.current = true;
    reconnectAttemptsRef.current += 1;
    
    // 🔥 NEW: Use 20-second intervals as requested
    const delay = baseReconnectDelay; // Always 20 seconds
    
    setConnectionStatus('reconnecting');
    
    // Update the reconnection toast with countdown
    const updateReconnectionToast = () => {
      const remainingTime = Math.max(0, Math.ceil((delay - (Date.now() - startTime)) / 1000));
      if (remainingTime > 0) {
        toast.info(
          <div>
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🔄 Reconnecting...</div>
            <div>Attempt {reconnectAttemptsRef.current} of {maxReconnectAttempts}</div>
            <div style={{ fontSize: '12px', marginTop: '5px', opacity: 0.8 }}>
              Next attempt in {remainingTime} seconds
            </div>
          </div>,
          {
            position: "top-center",
            autoClose: false,
            hideProgressBar: false,
            closeOnClick: false,
            pauseOnHover: true,
            draggable: true,
            toastId: 'reconnecting',
          }
        );
      }
    };
    
    const startTime = Date.now();
    const countdownInterval = setInterval(updateReconnectionToast, 1000);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      clearInterval(countdownInterval);
      connect();
    }, delay);
  }, [connect]);
  
  // 🔧 FIXED: Heartbeat mechanism to detect dead connections
  const startHeartbeat = useCallback(() => {
    // Debug: Starting heartbeat');
    stopHeartbeat(); // Clear any existing heartbeat
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        try {
          // Only send ping if we haven't sent one recently
          const now = Date.now();
          if (!lastHeartbeatRef.current || now - lastHeartbeatRef.current > 25000) {
            socketRef.current.send(JSON.stringify({ type: 'ping', timestamp: now }));
            lastHeartbeatRef.current = now;
            
            // Check for missed heartbeats
            if (missedHeartbeatsRef.current >= maxMissedHeartbeats) {
              // Debug: Too many missed heartbeats, closing connection');
              socketRef.current.close();
              return;
            }
            
            missedHeartbeatsRef.current += 1;
          }
        } catch (error) {
        }
      }
    }, 30000); // Send heartbeat every 30 seconds
  }, []);
  
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    missedHeartbeatsRef.current = 0;
  }, []);
  
  const handleHeartbeatResponse = useCallback(() => {
    // Debug: Heartbeat response received');
    missedHeartbeatsRef.current = 0;
    lastHeartbeatRef.current = Date.now();
  }, []);
  
  // 🔧 FIXED: Queue messages when disconnected
  const sendMessage = useCallback((message) => {
    // Debug: sendMessage called with:', message);
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      // Debug: Socket not ready, queueing message');
      messageQueueRef.current.push(message);
      
      // Try to reconnect if not already trying
      if (!isReconnectingRef.current && connectionStatus !== 'connecting') {
        connect();
      }
      return false;
    }
    
    try {
      const messageStr = JSON.stringify(message);
      // Debug: Sending message:', messageStr);
      socketRef.current.send(messageStr);
      return true;
    } catch (error) {
      // Queue the message for retry
      messageQueueRef.current.push(message);
      return false;
    }
  }, [connectionStatus, connect]);
  
  // 🔧 FIXED: Send queued messages when connection is restored
  const sendQueuedMessages = useCallback(() => {
    
    const queue = [...messageQueueRef.current];
    messageQueueRef.current = [];
    
    queue.forEach(message => {
      try {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify(message));
        } else {
          // Re-queue if connection lost again
          messageQueueRef.current.push(message);
        }
      } catch (error) {
        messageQueueRef.current.push(message);
      }
    });
  }, []);
  
  // 🔧 FIXED: Graceful disconnect
  const disconnect = useCallback(() => {
    // Debug: Manual disconnect called');
    isManualCloseRef.current = true;
    
    // Clear reconnection timer
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Stop heartbeat
    stopHeartbeat();
    
    // Close socket
    if (socketRef.current) {
      socketRef.current.close(1000, 'Manual disconnect');
      socketRef.current = null;
    }
    
    setSocket(null);
    setIsConnected(false);
    setConnectionStatus('disconnected');
    isReconnectingRef.current = false;
  }, [stopHeartbeat]);
  
  // 🔧 FIXED: Initialize connection on mount
  useEffect(() => {
    // Debug: Component mounted, connecting...');
    connect();
    
    // Cleanup on unmount
    return () => {
      // Debug: Component unmounting, cleaning up...');
      disconnect();
    };
  }, [connect, disconnect]);
  
  // 🔧 FIXED: Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Debug: Page became visible, checking connection');
        // Check connection health when page becomes visible
        if (!isConnected && !isReconnectingRef.current) {
          connect();
        }
      } else {
        // Debug: Page became hidden');
        // Don't disconnect on hidden, but stop trying to reconnect aggressively
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isConnected, connect]);
  
  // 🔧 FIXED: Handle network status changes
  useEffect(() => {
    const handleOnline = () => {
      // Debug: Network came online, reconnecting...');
      if (!isConnected && !isReconnectingRef.current) {
        reconnectAttemptsRef.current = 0; // Reset attempts on network recovery
        connect();
      }
    };
    
    const handleOffline = () => {
      // Debug: Network went offline');
      setConnectionStatus('offline');
    };
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isConnected, connect]);
  
  // 🔧 FIXED: Monitor connection health
  useEffect(() => {
    const healthCheckInterval = setInterval(() => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        // Connection is healthy
        if (connectionStatus !== 'connected') {
          setConnectionStatus('connected');
        }
      } else if (socketRef.current && socketRef.current.readyState === WebSocket.CONNECTING) {
        // Still connecting
        if (connectionStatus !== 'connecting') {
          setConnectionStatus('connecting');
        }
      } else if (!isManualCloseRef.current && !isReconnectingRef.current) {
        // Connection lost unexpectedly
        // Debug: Health check detected connection loss');
        if (connectionStatus !== 'disconnected') {
          setConnectionStatus('disconnected');
          setIsConnected(false);
        }
        
        // Try to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          scheduleReconnect();
        }
      }
    }, 5000); // Check every 5 seconds
    
    return () => clearInterval(healthCheckInterval);
  }, [connectionStatus, scheduleReconnect]);
  
  // 🔧 FIXED: Debug logging for connection state changes
  useEffect(() => {
    // Debug: Connection status changed to:', connectionStatus);
  }, [connectionStatus]);
  
  useEffect(() => {
    // Debug: Connected status changed to:', isConnected);
  }, [isConnected]);
  
  // 🔧 FIXED: Memoized context value to prevent unnecessary re-renders
  const contextValue = React.useMemo(() => ({
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    data,
    error,
    lastConnectionCheck,
    connectionErrorDetails,
    sendMessage,
    connect,
    disconnect,
    reconnectAttempts: reconnectAttemptsRef.current,
    queuedMessages: messageQueueRef.current.length,
    getCryptoData: () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'get_crypto_data' });
      }
    },
    getPositions: () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'get_positions' });
      }
    },
    getBotStatus: () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'get_bot_status' });
      } else {
      }
    },
    executePaperTrade: async (tradeData) => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'execute_trade', trade_data: tradeData });
        return { success: true, message: 'Trade request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    },
    startBot: async (config = {}) => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        // 🔥 NEW: Include current trading mode in bot config
        const tradingMode = localStorage.getItem('tradingMode') || 'mock';
        const enhancedConfig = {
          ...config,
          trading_mode: tradingMode === 'live' ? 'live' : 'mock'
        };
        
        sendMessage({ type: 'start_bot', config: enhancedConfig });
        return { success: true, message: 'Bot start request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    },
    stopBot: async () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'stop_bot' });
        return { success: true, message: 'Bot stop request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    },
    updateBotConfig: async (config) => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'update_bot_config', config });
        return { success: true, message: 'Bot config update request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    },
    getBotConfig: async () => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'get_bot_config' });
        return { success: true, message: 'Bot config request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    },
    closePosition: async (symbol) => {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'close_position', symbol });
        return { success: true, message: 'Position close request sent' };
      } else {
        throw new Error('WebSocket not connected');
      }
    }
  }), [
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    data,
    error,
    lastConnectionCheck,
    connectionErrorDetails,
    sendMessage,
    connect,
    disconnect
  ]);
  
  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};