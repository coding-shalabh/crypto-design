import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import apiService from '../services/apiService';
import { toast } from 'react-toastify';

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
  console.log('🔍 WebSocketProvider: Component initialized');
  
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
  
  // Use centralized API service
  const apiServiceRef = useRef(apiService);
  
  // 🔧 FIXED: Use refs to prevent infinite re-renders
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10;
  const baseReconnectDelay = 1000; // 1 second
  const maxReconnectDelay = 30000; // 30 seconds
  const isReconnectingRef = useRef(false);
  const messageQueueRef = useRef([]);
  const isManualCloseRef = useRef(false);
  
  // 🔧 FIXED: Heartbeat mechanism
  const heartbeatIntervalRef = useRef(null);
  const lastHeartbeatRef = useRef(null);
  const missedHeartbeatsRef = useRef(0);
  const maxMissedHeartbeats = 3;

  const connect = useCallback(() => {
    console.log('🔍 WebSocketProvider: connect() called');
    
    // Don't connect if already connected or connecting
    if (socketRef.current && 
        (socketRef.current.readyState === WebSocket.CONNECTING || 
         socketRef.current.readyState === WebSocket.OPEN)) {
      console.log('🔍 WebSocketProvider: Already connected or connecting, skipping');
      return;
    }
    
    try {
      console.log('🔍 WebSocketProvider: Creating new WebSocket connection');
      setConnectionStatus('connecting');
      
      // 🔧 FIXED: Create WebSocket with proper URL
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8767';
      console.log('🔍 WebSocketProvider: Connecting to:', wsUrl);
      
      const newSocket = new WebSocket(wsUrl);
      socketRef.current = newSocket;
      setSocket(newSocket);
      
      // 🔧 FIXED: Set connection timeout
      const connectionTimeout = setTimeout(() => {
        if (newSocket.readyState === WebSocket.CONNECTING) {
          console.log('🔍 WebSocketProvider: Connection timeout');
          newSocket.close();
        }
      }, 10000); // 10 second timeout
      
      newSocket.onopen = (event) => {
        console.log('🔍 WebSocketProvider: Connection opened', event);
        clearTimeout(connectionTimeout);
        setIsConnected(true);
        setConnectionStatus('connected');
        setError(null); // Clear any previous errors
        reconnectAttemptsRef.current = 0;
        isReconnectingRef.current = false;
        
        // Show success toast on connection
        if (reconnectAttemptsRef.current > 0) {
          toast.success('Connection restored successfully!', {
            position: "top-right",
            autoClose: 2000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
          });
        }
        
        // 🔧 FIXED: Start heartbeat
        startHeartbeat();
        
        // 🔧 FIXED: Send queued messages
        sendQueuedMessages();
      };
      
      newSocket.onmessage = (event) => {
        try {
          const messageData = JSON.parse(event.data);
          console.log('🔍 WebSocketProvider: Message received:', messageData.type);
          
          // 🔧 FIXED: Handle heartbeat responses
          if (messageData.type === 'pong') {
            handleHeartbeatResponse();
            return;
          }
          
          setLastMessage(messageData);
          
          // 🔧 FIXED: Update data state based on message type
          if (messageData.type === 'initial_data' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              ...messageData.data,
              positions: messageData.data.positions || {},
              paper_balance: messageData.data.paper_balance || prevData.paper_balance || 0,
              ai_analysis: prevData.ai_analysis || {},
              ai_opportunities: prevData.ai_opportunities || {}
            }));
          } else if (messageData.type === 'crypto_data_response' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              crypto_data: messageData.data
            }));
          } else if (messageData.type === 'price_updates_batch' && messageData.data) {
            const newPriceCache = messageData.data.updates.reduce((acc, update) => {
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
          } else if (messageData.type === 'position_update' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              positions: messageData.data.positions || {},
              paper_balance: messageData.data.balance || prevData.paper_balance
            }));
          } else if (messageData.type === 'positions_response' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              positions: messageData.data.positions || {},
              paper_balance: messageData.data.balance || prevData.paper_balance
            }));
          } else if (messageData.type === 'trade_executed' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              positions: messageData.data.positions || prevData.positions,
              paper_balance: messageData.data.new_balance || prevData.paper_balance
            }));
          } else if (messageData.type === 'recent_trades_update' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              recent_trades: messageData.data.recent_trades || prevData.recent_trades
            }));
          } else if (messageData.type === 'ai_analysis_response' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              ai_analysis: {
                ...prevData.ai_analysis,
                [messageData.data.symbol]: messageData.data
              }
            }));
          } else if (messageData.type === 'ai_opportunity_alert' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              ai_opportunities: {
                ...prevData.ai_opportunities,
                [messageData.data.symbol]: messageData.data
              }
            }));
          } else if (messageData.type === 'bot_status_response' && messageData.data) {
            setData(prevData => ({
              ...prevData,
              bot_status: {
                ...prevData.bot_status,
                ...messageData.data
              }
            }));
          } else if (messageData.type === 'start_bot_response' && messageData.data) {
            if (messageData.data.success) {
              setData(prevData => ({
                ...prevData,
                bot_status: {
                  ...prevData.bot_status,
                  enabled: true
                }
              }));
            }
          } else if (messageData.type === 'stop_bot_response' && messageData.data) {
            if (messageData.data.success) {
              setData(prevData => ({
                ...prevData,
                bot_status: {
                  ...prevData.bot_status,
                  enabled: false
                }
              }));
            }
          }
          
          // 🔧 DEPRECATED: AI analysis messages are now handled directly in the main context
          // Keep this for backward compatibility with existing AI analysis component
          if (window.handleAIAnalysisResponse && 
              ['ai_analysis_response', 'all_ai_analysis_response', 'ai_opportunities_response', 
               'ai_opportunity_alert', 'analysis_status', 'analysis_status_response', 
               'pending_trades_response', 'trade_accepted', 'trade_ready_alert', 'analysis_log'].includes(messageData.type)) {
            try {
              window.handleAIAnalysisResponse(messageData);
            } catch (error) {
              console.error('🔍 WebSocketProvider: Error in AI analysis handler:', error);
            }
          }
          
          // 🔧 FIXED: Route bot messages to bot handler
          if (window.handleBotResponse && 
              ['bot_start_response', 'bot_stop_response', 'bot_status_response', 'bot_status_update', 
               'bot_config_update_response', 'bot_trade_executed', 'bot_error'].includes(messageData.type)) {
            try {
              window.handleBotResponse(messageData);
            } catch (error) {
              console.error('🔍 WebSocketProvider: Error in bot handler:', error);
            }
          }
        } catch (error) {
          console.error('🔍 WebSocketProvider: Error parsing message:', error);
        }
      };
      
      newSocket.onerror = (error) => {
        console.error('🔍 WebSocketProvider: WebSocket error:', error);
        clearTimeout(connectionTimeout);
        setConnectionStatus('error');
        setError('WebSocket connection error');
        
        // Show user-friendly toast notification instead of breaking the page
        toast.error('Connection issue detected. Attempting to reconnect...', {
          position: "top-right",
          autoClose: 3000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
      };
      
      newSocket.onclose = (event) => {
        console.log('🔍 WebSocketProvider: Connection closed:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });
        
        clearTimeout(connectionTimeout);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        setError(null); // Clear any previous errors
        stopHeartbeat();
        
        // 🔧 FIXED: Only reconnect if not manually closed and within attempt limits
        if (!isManualCloseRef.current && 
            reconnectAttemptsRef.current < maxReconnectAttempts && 
            !isReconnectingRef.current) {
          scheduleReconnect();
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.log('🔍 WebSocketProvider: Max reconnection attempts reached');
          setConnectionStatus('failed');
        }
        
        // Reset manual close flag
        isManualCloseRef.current = false;
      };
      
    } catch (error) {
      console.error('🔍 WebSocketProvider: Error creating WebSocket:', error);
      setConnectionStatus('error');
      scheduleReconnect();
    }
  }, []);
  
  // 🔧 FIXED: Improved reconnection logic with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (isReconnectingRef.current) {
      console.log('🔍 WebSocketProvider: Already reconnecting, skipping');
      return;
    }
    
    isReconnectingRef.current = true;
    reconnectAttemptsRef.current += 1;
    
    // 🔧 FIXED: Exponential backoff with jitter
    const delay = Math.min(
      baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current - 1) + 
      Math.random() * 1000, // Add jitter
      maxReconnectDelay
    );
    
    console.log(`🔍 WebSocketProvider: Scheduling reconnect attempt ${reconnectAttemptsRef.current} in ${delay}ms`);
    setConnectionStatus('reconnecting');
    
    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`🔍 WebSocketProvider: Reconnection attempt ${reconnectAttemptsRef.current}`);
      connect();
    }, delay);
  }, [connect]);
  
  // 🔧 FIXED: Heartbeat mechanism to detect dead connections
  const startHeartbeat = useCallback(() => {
    console.log('🔍 WebSocketProvider: Starting heartbeat');
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
              console.log('🔍 WebSocketProvider: Too many missed heartbeats, closing connection');
              socketRef.current.close();
              return;
            }
            
            missedHeartbeatsRef.current += 1;
          }
        } catch (error) {
          console.error('🔍 WebSocketProvider: Error sending heartbeat:', error);
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
    console.log('🔍 WebSocketProvider: Heartbeat response received');
    missedHeartbeatsRef.current = 0;
    lastHeartbeatRef.current = Date.now();
  }, []);
  
  // 🔧 FIXED: Queue messages when disconnected
  const sendMessage = useCallback((message) => {
    console.log('🔍 WebSocketProvider: sendMessage called with:', message);
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.log('🔍 WebSocketProvider: Socket not ready, queueing message');
      messageQueueRef.current.push(message);
      
      // Try to reconnect if not already trying
      if (!isReconnectingRef.current && connectionStatus !== 'connecting') {
        connect();
      }
      return false;
    }
    
    try {
      const messageStr = JSON.stringify(message);
      console.log('🔍 WebSocketProvider: Sending message:', messageStr);
      socketRef.current.send(messageStr);
      return true;
    } catch (error) {
      console.error('🔍 WebSocketProvider: Error sending message:', error);
      // Queue the message for retry
      messageQueueRef.current.push(message);
      return false;
    }
  }, [connectionStatus, connect]);
  
  // 🔧 FIXED: Send queued messages when connection is restored
  const sendQueuedMessages = useCallback(() => {
    console.log(`🔍 WebSocketProvider: Sending ${messageQueueRef.current.length} queued messages`);
    
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
        console.error('🔍 WebSocketProvider: Error sending queued message:', error);
        messageQueueRef.current.push(message);
      }
    });
  }, []);
  
  // 🔧 FIXED: Graceful disconnect
  const disconnect = useCallback(() => {
    console.log('🔍 WebSocketProvider: Manual disconnect called');
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
    console.log('🔍 WebSocketProvider: Component mounted, connecting...');
    connect();
    
    // Cleanup on unmount
    return () => {
      console.log('🔍 WebSocketProvider: Component unmounting, cleaning up...');
      disconnect();
    };
  }, [connect, disconnect]);
  
  // 🔧 FIXED: Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        console.log('🔍 WebSocketProvider: Page became visible, checking connection');
        // Check connection health when page becomes visible
        if (!isConnected && !isReconnectingRef.current) {
          connect();
        }
      } else {
        console.log('🔍 WebSocketProvider: Page became hidden');
        // Don't disconnect on hidden, but stop trying to reconnect aggressively
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isConnected, connect]);
  
  // 🔧 FIXED: Handle network status changes
  useEffect(() => {
    const handleOnline = () => {
      console.log('🔍 WebSocketProvider: Network came online, reconnecting...');
      if (!isConnected && !isReconnectingRef.current) {
        reconnectAttemptsRef.current = 0; // Reset attempts on network recovery
        connect();
      }
    };
    
    const handleOffline = () => {
      console.log('🔍 WebSocketProvider: Network went offline');
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
        console.log('🔍 WebSocketProvider: Health check detected connection loss');
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
    console.log('🔍 WebSocketProvider: Connection status changed to:', connectionStatus);
  }, [connectionStatus]);
  
  useEffect(() => {
    console.log('🔍 WebSocketProvider: Connected status changed to:', isConnected);
  }, [isConnected]);
  
  // 🔧 FIXED: Memoized context value to prevent unnecessary re-renders
  const contextValue = React.useMemo(() => ({
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    data,
    error,
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
        console.warn('WebSocket not connected: cannot get bot status');
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
        sendMessage({ type: 'start_bot', config });
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