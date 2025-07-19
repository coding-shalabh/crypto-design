class BinanceWebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectTimeout = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseReconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.subscribers = new Set();
    this.symbols = new Set();
    this.isConnected = false;
    this.isConnecting = false;
  }

  // Subscribe to price updates
  subscribe(callback) {
    this.subscribers.add(callback);
    console.log('🔍 BinanceWS: Added subscriber, total:', this.subscribers.size);
    
    // Connect if not already connected
    if (!this.isConnected && !this.isConnecting) {
      this.connect();
    }
  }

  // Unsubscribe from price updates
  unsubscribe(callback) {
    this.subscribers.delete(callback);
    console.log('🔍 BinanceWS: Removed subscriber, total:', this.subscribers.size);
    
    // Disconnect if no more subscribers
    if (this.subscribers.size === 0 && this.ws) {
      this.disconnect();
    }
  }

  // Add symbols to watch
  addSymbols(symbolList) {
    const newSymbols = symbolList.filter(symbol => !this.symbols.has(symbol.toLowerCase()));
    newSymbols.forEach(symbol => this.symbols.add(symbol.toLowerCase()));
    
    console.log('🔍 BinanceWS: Added symbols:', newSymbols);
    console.log('🔍 BinanceWS: Total symbols watching:', this.symbols.size);
    
    // Reconnect with new symbols if already connected
    if (this.isConnected && newSymbols.length > 0) {
      this.reconnect();
    }
  }

  // Remove symbols from watch list
  removeSymbols(symbolList) {
    symbolList.forEach(symbol => this.symbols.delete(symbol.toLowerCase()));
    console.log('🔍 BinanceWS: Removed symbols:', symbolList);
    console.log('🔍 BinanceWS: Remaining symbols:', this.symbols.size);
    
    // Reconnect with updated symbols if connected
    if (this.isConnected) {
      this.reconnect();
    }
  }

  // Connect to Binance WebSocket
  connect() {
    if (this.isConnecting || this.isConnected) {
      console.log('🔍 BinanceWS: Already connecting or connected');
      return;
    }

    if (this.symbols.size === 0) {
      // Add default major trading pairs
      this.addSymbols([
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
        'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
      ]);
    }

    this.isConnecting = true;
    console.log('🔍 BinanceWS: Connecting to Binance WebSocket...');

    try {
      // Create stream names for all symbols
      const streams = Array.from(this.symbols).map(symbol => `${symbol}@ticker`);
      const streamUrl = `wss://stream.binance.com:9443/ws/${streams.join('/')}`;
      
      console.log('🔍 BinanceWS: Connecting to:', streamUrl);
      console.log('🔍 BinanceWS: Watching symbols:', Array.from(this.symbols));

      this.ws = new WebSocket(streamUrl);

      this.ws.onopen = () => {
        console.log('🔍 BinanceWS: Connected successfully');
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.clearReconnectTimeout();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('🔍 BinanceWS: Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('🔍 BinanceWS: WebSocket error:', error);
        this.isConnected = false;
        this.isConnecting = false;
      };

      this.ws.onclose = (event) => {
        console.log('🔍 BinanceWS: Connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.isConnecting = false;
        
        // Reconnect if not manually closed and have subscribers
        if (event.code !== 1000 && this.subscribers.size > 0) {
          this.scheduleReconnect();
        }
      };

    } catch (error) {
      console.error('🔍 BinanceWS: Error creating WebSocket:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  // Handle incoming messages
  handleMessage(data) {
    if (!data || !data.s) return;

    // Parse Binance ticker data
    const priceUpdate = {
      symbol: data.s, // Symbol
      price: parseFloat(data.c), // Current price
      priceChange: parseFloat(data.p), // Price change
      priceChangePercent: parseFloat(data.P), // Price change percent
      volume: parseFloat(data.v), // Volume
      quoteVolume: parseFloat(data.q), // Quote volume
      openPrice: parseFloat(data.o), // Open price
      highPrice: parseFloat(data.h), // High price
      lowPrice: parseFloat(data.l), // Low price
      timestamp: data.E, // Event time
      count: parseInt(data.c), // Trade count
    };

    // Notify all subscribers
    this.subscribers.forEach(callback => {
      try {
        callback(priceUpdate);
      } catch (error) {
        console.error('🔍 BinanceWS: Error in subscriber callback:', error);
      }
    });
  }

  // Schedule reconnection
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🔍 BinanceWS: Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(`🔍 BinanceWS: Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  // Clear reconnection timeout
  clearReconnectTimeout() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  // Reconnect with current symbols
  reconnect() {
    console.log('🔍 BinanceWS: Reconnecting...');
    this.disconnect();
    setTimeout(() => this.connect(), 1000);
  }

  // Disconnect
  disconnect() {
    console.log('🔍 BinanceWS: Disconnecting...');
    this.isConnected = false;
    this.isConnecting = false;
    this.clearReconnectTimeout();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  // Get connection status
  getStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      subscriberCount: this.subscribers.size,
      symbolCount: this.symbols.size,
      symbols: Array.from(this.symbols),
    };
  }
}

// Create singleton instance
const binanceWebSocketService = new BinanceWebSocketService();

export default binanceWebSocketService;