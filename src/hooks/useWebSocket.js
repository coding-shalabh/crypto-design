import { useEffect, useRef, useState, useCallback } from 'react';

const useWebSocket = (url = 'ws://localhost:8765') => {
  console.log('🔍 useWebSocket: Hook initialized with URL:', url);
  
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    paper_balance: 0,
    positions: {},
    recent_trades: [],
    price_cache: {},
    crypto_data: {},
    ai_insights: null
  });

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;
  const heartbeatIntervalRef = useRef(null);
  const lastHeartbeatRef = useRef(Date.now());
  const isConnectingRef = useRef(false);
  const isMountedRef = useRef(true); // Track if component is mounted

  // ✅ Fix: Create stable handleMessage function with useCallback and minimal dependencies
  const handleMessage = useCallback((message) => {
    console.log('🔍 useWebSocket: handleMessage called with:', message);
    const { type, data: messageData } = message;
    
    // Update last heartbeat on any message
    lastHeartbeatRef.current = Date.now();

    // ✅ Use functional state updates to avoid dependencies
    setData(prevData => {
      let newData = { ...prevData };
      
      switch (type) {
        case 'initial_data':
          newData = { ...newData, ...messageData };
          break;

        case 'price_update':
          newData.price_cache = {
            ...newData.price_cache,
            [messageData.symbol]: messageData
          };
          break;

        case 'crypto_data_response':
          newData.crypto_data = {
            ...newData.crypto_data,
            ...messageData
          };
          break;

        case 'trade_executed':
          newData.paper_balance = messageData.new_balance;
          newData.positions = messageData.positions;
          newData.recent_trades = [messageData.trade, ...newData.recent_trades.slice(0, 49)];
          break;

        case 'position_closed':
          newData.paper_balance = messageData.new_balance;
          newData.positions = messageData.positions;
          newData.recent_trades = [messageData.trade, ...newData.recent_trades.slice(0, 49)];
          break;

        case 'ai_insights':
          newData.ai_insights = {
            symbol: messageData.symbol,
            claude_analysis: messageData.claude_analysis,
            gpt_refinement: messageData.gpt_refinement,
            timestamp: messageData.timestamp
          };
          break;

        case 'trade_history_response':
          newData.recent_trades = messageData.trades;
          break;

        case 'positions_response':
          newData.paper_balance = messageData.balance;
          newData.positions = messageData.positions;
          break;

        case 'position_update':
          newData.paper_balance = messageData.balance;
          newData.positions = messageData.positions;
          break;

        case 'error':
          console.error('🔍 useWebSocket: Received error message:', messageData.message);
          setError(messageData.message);
          break;

        default:
          // Handle bot messages through global handler
          if (window.handleBotResponse && [
            'bot_status_response', 'bot_trade_executed', 'bot_trade_closed', 
            'analysis_log', 'trade_log'
          ].includes(type)) {
            window.handleBotResponse(message);
          }
          console.log('🔍 useWebSocket: Unknown message type:', type);
      }
      
      return newData;
    });
  }, []); // ✅ No dependencies needed thanks to functional updates

  // ✅ Fix: Create stable heartbeat functions
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (!isMountedRef.current) return; // Don't continue if unmounted
      
      const now = Date.now();
      const timeSinceLastHeartbeat = now - lastHeartbeatRef.current;
      
      if (timeSinceLastHeartbeat > 30000 && isConnected) {
        console.warn('🔍 useWebSocket: No heartbeat for 30 seconds, reconnecting...');
        if (wsRef.current) {
          wsRef.current.close();
        }
      }
    }, 10000);
  }, []); // ✅ No dependencies needed

  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // ✅ Fix: Create stable connect function
  const connect = useCallback(() => {
    console.log('🔍 useWebSocket: connect called');
    
    // ✅ Better connection state checking
    if (!isMountedRef.current) {
      console.log('🔍 useWebSocket: Component unmounted, not connecting');
      return;
    }
    
    if (isConnectingRef.current) {
      console.log('🔍 useWebSocket: Already connecting, skipping');
      return;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('🔍 useWebSocket: Already connected, skipping');
      return;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('🔍 useWebSocket: Connection in progress, skipping');
      return;
    }
    
    isConnectingRef.current = true;
    
    try {
      console.log('🔍 useWebSocket: Creating new WebSocket connection to:', url);
      
      // ✅ Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        if (!isMountedRef.current) return; // Don't continue if unmounted
        
        console.log('🔍 useWebSocket: WebSocket connection opened');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        lastHeartbeatRef.current = Date.now();
        isConnectingRef.current = false;

        startHeartbeat();

        // ✅ Load initial data with delay
        setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && isMountedRef.current) {
            console.log('🔍 useWebSocket: Loading initial data...');
            wsRef.current.send(JSON.stringify({ type: 'get_positions' }));
            wsRef.current.send(JSON.stringify({ type: 'get_trade_history', limit: 50 }));
            wsRef.current.send(JSON.stringify({ type: 'get_crypto_data' }));
          }
        }, 1000);
      };

      wsRef.current.onmessage = (event) => {
        if (!isMountedRef.current) return; // Don't process if unmounted
        
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          console.error('🔍 useWebSocket: Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        if (!isMountedRef.current) return; // Don't reconnect if unmounted
        
        console.log('🔍 useWebSocket: WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
        setIsConnected(false);
        stopHeartbeat();
        isConnectingRef.current = false;
        wsRef.current = null;

        // ✅ Only reconnect if it wasn't a normal closure and component is still mounted
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts && isMountedRef.current) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔍 useWebSocket: Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts}) in ${delay}ms...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            if (isMountedRef.current) {
              connect();
            }
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('🔍 useWebSocket: WebSocket error:', error);
        setError('WebSocket connection error');
        isConnectingRef.current = false;
      };

    } catch (error) {
      console.error('🔍 useWebSocket: Error in connect function:', error);
      setError('Failed to create WebSocket connection');
      isConnectingRef.current = false;
    }
  }, [url, handleMessage, startHeartbeat, stopHeartbeat]); // ✅ Stable dependencies

  const disconnect = useCallback(() => {
    console.log('🔍 useWebSocket: disconnect called');
    stopHeartbeat();
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      console.log('🔍 useWebSocket: Closing WebSocket connection');
      wsRef.current.close(1000, 'Manual disconnect'); // Normal closure
      wsRef.current = null;
    }
    
    setIsConnected(false);
    isConnectingRef.current = false;
    reconnectAttempts.current = 0;
  }, [stopHeartbeat]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('🔍 useWebSocket: Sending message:', message);
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('🔍 useWebSocket: Cannot send message - WebSocket not open. ReadyState:', wsRef.current?.readyState);
    }
  }, []);

  // Trading functions
  const executePaperTrade = useCallback((tradeData) => {
    sendMessage({
      type: 'execute_trade',
      ...tradeData
    });
  }, [sendMessage]);

  const getPositions = useCallback(() => {
    sendMessage({ type: 'get_positions' });
  }, [sendMessage]);

  const closePosition = useCallback((symbol) => {
    sendMessage({ type: 'close_position', symbol });
  }, [sendMessage]);

  const getTradeHistory = useCallback((limit = 50, symbol = null) => {
    sendMessage({ type: 'get_trade_history', limit, symbol });
  }, [sendMessage]);

  const getCryptoData = useCallback((symbol = null) => {
    sendMessage({ type: 'get_crypto_data', symbol });
  }, [sendMessage]);

  // Bot control functions
  const startBot = useCallback((config = {}) => {
    sendMessage({ type: 'start_bot', config });
  }, [sendMessage]);

  const stopBot = useCallback(() => {
    sendMessage({ type: 'stop_bot' });
  }, [sendMessage]);

  const getBotStatus = useCallback(() => {
    sendMessage({ type: 'get_bot_status' });
  }, [sendMessage]);

  const updateBotConfig = useCallback((newConfig) => {
    sendMessage({ type: 'update_bot_config', config: newConfig });
  }, [sendMessage]);

  // ✅ Fix: Connect only once on mount, with proper cleanup
  useEffect(() => {
    console.log('🔍 useWebSocket: Component mounted, connecting...');
    isMountedRef.current = true;
    connect();

    return () => {
      console.log('🔍 useWebSocket: Component unmounting, cleaning up...');
      isMountedRef.current = false;
      disconnect();
    };
  }, []); // ✅ Empty dependency array - connect only once!

  // ✅ Fix: Separate effect for URL changes
  useEffect(() => {
    if (isMountedRef.current && wsRef.current) {
      console.log('🔍 useWebSocket: URL changed, reconnecting...');
      disconnect();
      setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, 100);
    }
  }, [url]); // Only reconnect when URL changes

  return {
    isConnected,
    error,
    data,
    sendMessage,
    connect,
    disconnect,
    // Trading functions
    executePaperTrade,
    getPositions,
    closePosition,
    getTradeHistory,
    getCryptoData,
    // Bot control functions
    startBot,
    stopBot,
    getBotStatus,
    updateBotConfig
  };
};

export default useWebSocket;