class TradingService {
  constructor() {
    this.websocket = null;
    this.tradingMode = 'mock';
    this.callbacks = new Map();
  }

  setWebSocket(websocket) {
    this.websocket = websocket;
  }

  setTradingMode(mode) {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      // Set up callback for response
      this.callbacks.set('trading_mode_set_handler', (response) => {
        this.callbacks.delete('trading_mode_set_handler');
        if (response.type === 'trading_mode_set') {
          this.tradingMode = mode;
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      // Send trading mode change request
      this.websocket.send(JSON.stringify({
        type: 'set_trading_mode',
        data: { mode }
      }));

      // Set timeout
      setTimeout(() => {
        if (this.callbacks.has('trading_mode_set_handler')) {
          this.callbacks.delete('trading_mode_set_handler');
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  getTradingBalance(asset = 'USDT') {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      this.callbacks.set('trading_balance_handler', (response) => {
        this.callbacks.delete('trading_balance_handler');
        if (response.type === 'trading_balance') {
          resolve(response.data.balance);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_trading_balance',
        data: { asset }
      }));

      setTimeout(() => {
        if (this.callbacks.has('trading_balance_handler')) {
          this.callbacks.delete('trading_balance_handler');
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  getAllTradingBalances() {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `get_all_balances_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'all_trading_balances') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_all_trading_balances',
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  placeTradingOrder(orderData) {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `place_order_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'trading_order_placed') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'place_trading_order',
        data: orderData,
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 15000); // Longer timeout for order placement
    });
  }

  getPortfolioSummary() {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `portfolio_summary_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'portfolio_summary') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_portfolio_summary',
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  testTradingConnection() {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `test_connection_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'trading_connection_test') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'test_trading_connection',
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  // Handle incoming WebSocket messages
  handleMessage(message) {
    const messageId = message.messageId;
    if (messageId && this.callbacks.has(messageId)) {
      const callback = this.callbacks.get(messageId);
      callback(message);
      return;
    }
    
    // Handle response messages by type
    const messageType = message.type;
    const handlerKey = `${messageType}_handler`;
    
    if (this.callbacks.has(handlerKey)) {
      const callback = this.callbacks.get(handlerKey);
      callback(message);
    }
  }

  // Convenience methods for common trading operations
  async buyMarket(symbol, quantity) {
    return this.placeTradingOrder({
      symbol,
      side: 'BUY',
      type: 'MARKET',
      quantity
    });
  }

  async sellMarket(symbol, quantity) {
    return this.placeTradingOrder({
      symbol,
      side: 'SELL',
      type: 'MARKET',
      quantity
    });
  }

  async buyLimit(symbol, quantity, price) {
    return this.placeTradingOrder({
      symbol,
      side: 'BUY',
      type: 'LIMIT',
      quantity,
      price
    });
  }

  async sellLimit(symbol, quantity, price) {
    return this.placeTradingOrder({
      symbol,
      side: 'SELL',
      type: 'LIMIT',
      quantity,
      price
    });
  }

  getCurrentMode() {
    return this.tradingMode;
  }

  isLiveMode() {
    return this.tradingMode === 'live';
  }

  isMockMode() {
    return this.tradingMode === 'mock';
  }

  getCategorizedBalances() {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `categorized_balances_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'categorized_balances') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_categorized_balances',
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  getWalletBalances(walletType) {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `wallet_balances_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'wallet_balances') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_wallet_balances',
        data: { wallet_type: walletType },
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }

  transferBetweenWallets(asset, amount, fromWallet, toWallet) {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `transfer_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'wallet_transfer_result') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'transfer_between_wallets',
        data: {
          asset,
          amount,
          from_wallet: fromWallet,
          to_wallet: toWallet
        },
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 15000);
    });
  }

  getTransferHistory(limit = 50) {
    if (!this.websocket) {
      throw new Error('WebSocket not connected');
    }

    return new Promise((resolve, reject) => {
      const messageId = `transfer_history_${Date.now()}`;
      
      this.callbacks.set(messageId, (response) => {
        this.callbacks.delete(messageId);
        if (response.type === 'transfer_history') {
          resolve(response.data);
        } else if (response.type === 'error') {
          reject(new Error(response.data.message));
        }
      });

      this.websocket.send(JSON.stringify({
        type: 'get_transfer_history',
        data: { limit },
        messageId
      }));

      setTimeout(() => {
        if (this.callbacks.has(messageId)) {
          this.callbacks.delete(messageId);
          reject(new Error('Request timeout'));
        }
      }, 10000);
    });
  }
}

// Create singleton instance
const tradingService = new TradingService();

export default tradingService;