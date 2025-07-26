/**
 * Centralized API Service for Frontend
 * Handles all API calls with environment-based switching
 */

class ApiService {
  constructor() {
    // Get API URLs from environment variables
    this.baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8767';
    this.websocketUrl = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8767';
    this.analysisApiUrl = process.env.REACT_APP_ANALYSIS_API_URL || 'http://localhost:5001';
    
    // WebSocket connection
    this.websocket = null;
    this.websocketCallbacks = new Map();
    this.reconnectInterval = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    
    // API Service initialized
  }

  /**
   * Initialize WebSocket connection
   */
  async initializeWebSocket() {
    try {
      // Connecting to WebSocket
      
      this.websocket = new WebSocket(this.websocketUrl);
      
      this.websocket.onopen = () => {
        // WebSocket connected
        this.reconnectAttempts = 0;
        if (this.reconnectInterval) {
          clearInterval(this.reconnectInterval);
          this.reconnectInterval = null;
        }
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // WebSocket message received
          
          // Call registered callbacks
          this.websocketCallbacks.forEach((callback, key) => {
            try {
              callback(data);
            } catch (error) {
              console.error(`❌ Error in callback ${key}:`, error);
            }
          });
        } catch (error) {
          console.error('❌ Error parsing WebSocket message:', error);
        }
      };
      
      this.websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };
      
      this.websocket.onclose = () => {
        // WebSocket disconnected
        this.attemptReconnect();
      };
      
    } catch (error) {
      console.error('❌ Failed to initialize WebSocket:', error);
      this.attemptReconnect();
    }
  }

  /**
   * Attempt to reconnect WebSocket
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      return;
    }
    
    if (this.reconnectInterval) return;
    
    this.reconnectAttempts++;
    // Attempting to reconnect
    
    this.reconnectInterval = setTimeout(() => {
      this.reconnectInterval = null;
      this.initializeWebSocket();
    }, 3000 * this.reconnectAttempts);
  }

  /**
   * Register callback for WebSocket messages
   */
  onWebSocketMessage(key, callback) {
    this.websocketCallbacks.set(key, callback);
  }

  /**
   * Unregister callback for WebSocket messages
   */
  offWebSocketMessage(key) {
    this.websocketCallbacks.delete(key);
  }

  /**
   * Send WebSocket message
   */
  sendWebSocketMessage(message) {
    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      this.websocket.send(JSON.stringify(message));
      // WebSocket message sent
      return true;
    } else {
      console.error('❌ WebSocket not connected');
      return false;
    }
  }

  /**
   * HTTP API call with error handling
   */
  async apiCall(endpoint, options = {}) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const config = {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      };

      // API Call
      
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      // API response received
      return data;
      
    } catch (error) {
      console.error('❌ API call failed:', error);
      throw error;
    }
  }

  /**
   * Analysis API call (can be real or fake)
   */
  async getAnalysis(symbol) {
    try {
      const url = `${this.analysisApiUrl}/api/analysis/${symbol}`;
      // Getting analysis
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Analysis API error! status: ${response.status}`);
      }
      
      const data = await response.json();
      // Analysis received
      return data;
      
    } catch (error) {
      console.error('❌ Analysis API call failed:', error);
      throw error;
    }
  }

  // ===========================================
  // TRADING API METHODS
  // ===========================================

  /**
   * Get bot configuration
   */
  async getBotConfig() {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`config_${messageId}`, (data) => {
        if (data.type === 'bot_config') {
          this.offWebSocketMessage(`config_${messageId}`);
          resolve(data.data.config);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`config_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_bot_config',
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Update bot configuration
   */
  async updateBotConfig(config) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`update_config_${messageId}`, (data) => {
        if (data.type === 'config_updated') {
          this.offWebSocketMessage(`update_config_${messageId}`);
          resolve(data.data);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`update_config_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'update_bot_config',
        config,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Start trading bot
   */
  async startBot(duration = 180) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`start_bot_${messageId}`, (data) => {
        if (data.type === 'bot_started') {
          this.offWebSocketMessage(`start_bot_${messageId}`);
          resolve(data.data);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`start_bot_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'start_bot',
        duration,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Stop trading bot
   */
  async stopBot() {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`stop_bot_${messageId}`, (data) => {
        if (data.type === 'bot_stopped') {
          this.offWebSocketMessage(`stop_bot_${messageId}`);
          resolve(data.data);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`stop_bot_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'stop_bot',
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Execute manual trade
   */
  async executeTrade(symbol, side, amount, price, type = 'market') {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`trade_${messageId}`, (data) => {
        if (data.type === 'trade_executed') {
          this.offWebSocketMessage(`trade_${messageId}`);
          resolve(data.data);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`trade_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'execute_trade',
        symbol,
        side,
        amount,
        price,
        type,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  // ===========================================
  // DATA RETRIEVAL METHODS
  // ===========================================

  /**
   * Get market data
   */
  async getMarketData(symbol = null) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`market_${messageId}`, (data) => {
        if (data.type === 'market_data') {
          this.offWebSocketMessage(`market_${messageId}`);
          resolve(data.data.market_data);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`market_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_market_data',
        symbol,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Get trading positions
   */
  async getPositions() {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`positions_${messageId}`, (data) => {
        if (data.type === 'positions') {
          this.offWebSocketMessage(`positions_${messageId}`);
          resolve(data.data.positions);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`positions_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_positions',
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Get trading history
   */
  async getTradingHistory(limit = 50) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`history_${messageId}`, (data) => {
        if (data.type === 'trading_history') {
          this.offWebSocketMessage(`history_${messageId}`);
          resolve(data.data.trades);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`history_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_trading_history',
        limit,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Get AI analysis
   */
  async getAIAnalysis(symbol) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`ai_analysis_${messageId}`, (data) => {
        if (data.type === 'ai_analysis') {
          this.offWebSocketMessage(`ai_analysis_${messageId}`);
          resolve(data.data.analysis);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`ai_analysis_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_ai_analysis',
        symbol,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Get system logs
   */
  async getLogs(limit = 50) {
    return new Promise((resolve, reject) => {
      const messageId = Date.now().toString();
      
      // Register callback for response
      this.onWebSocketMessage(`logs_${messageId}`, (data) => {
        if (data.type === 'logs') {
          this.offWebSocketMessage(`logs_${messageId}`);
          resolve(data.data.logs);
        } else if (data.type === 'error') {
          this.offWebSocketMessage(`logs_${messageId}`);
          reject(new Error(data.data.message));
        }
      });

      // Send request
      if (!this.sendWebSocketMessage({
        action: 'get_logs',
        limit,
        messageId
      })) {
        reject(new Error('WebSocket not connected'));
      }
    });
  }

  /**
   * Cleanup connections
   */
  cleanup() {
    if (this.websocket) {
      this.websocket.close();
    }
    if (this.reconnectInterval) {
      clearInterval(this.reconnectInterval);
    }
    this.websocketCallbacks.clear();
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;