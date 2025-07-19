import binanceWebSocketService from './binanceWebSocketService';
import { 
  updateRealTimePrice, 
  batchUpdateRealTimePrices, 
  setBinanceConnectionStatus,
  updatePriceUpdateStats 
} from '../store/slices/marketDataSlice';

class RealTimePriceService {
  constructor() {
    this.store = null;
    this.isInitialized = false;
    this.priceBuffer = [];
    this.bufferTimeout = null;
    this.bufferSize = 50; // Batch updates every 50 prices
    this.bufferTimeMs = 1000; // Or every 1000ms (1 second)
    this.updateCounter = 0;
    this.lastStatsUpdate = Date.now();
  }

  // Initialize with Redux store
  init(store) {
    if (this.isInitialized) {
      console.log('🔍 RealTimePriceService: Already initialized');
      return;
    }

    this.store = store;
    this.isInitialized = true;

    console.log('🔍 RealTimePriceService: Initializing real-time price service');

    // Subscribe to Binance price updates
    binanceWebSocketService.subscribe(this.handlePriceUpdate.bind(this));

    // Monitor connection status
    this.monitorConnection();

    // Get watched symbols from store and add them to Binance service
    const state = store.getState();
    const watchedSymbols = state.marketData.watchedSymbols || [];
    
    if (watchedSymbols.length > 0) {
      binanceWebSocketService.addSymbols(watchedSymbols);
    }

    console.log('🔍 RealTimePriceService: Initialized with symbols:', watchedSymbols);
  }

  // Handle price updates from Binance
  handlePriceUpdate(priceData) {
    if (!this.store) return;

    this.updateCounter++;

    // Add to buffer for batch processing
    this.priceBuffer.push(priceData);

    // Process buffer if it reaches size limit or timeout
    if (this.priceBuffer.length >= this.bufferSize) {
      this.flushBuffer();
    } else if (!this.bufferTimeout) {
      this.bufferTimeout = setTimeout(() => {
        this.flushBuffer();
      }, this.bufferTimeMs);
    }

    // Update statistics every second
    const now = Date.now();
    if (now - this.lastStatsUpdate > 1000) {
      this.updateStats();
      this.lastStatsUpdate = now;
    }
  }

  // Flush price buffer to Redux store
  flushBuffer() {
    if (!this.store || this.priceBuffer.length === 0) return;

    const updates = [...this.priceBuffer];
    this.priceBuffer = [];

    if (this.bufferTimeout) {
      clearTimeout(this.bufferTimeout);
      this.bufferTimeout = null;
    }

    // Dispatch batch update to Redux store
    this.store.dispatch(batchUpdateRealTimePrices(updates));

    console.log(`🔍 RealTimePriceService: Batch updated ${updates.length} prices`);
  }

  // Update performance statistics
  updateStats() {
    if (!this.store) return;

    const updatesPerSecond = this.updateCounter;
    this.updateCounter = 0;

    this.store.dispatch(updatePriceUpdateStats({
      updatesPerSecond,
      lastUpdateTime: Date.now(),
    }));

    console.log(`🔍 RealTimePriceService: ${updatesPerSecond} updates/sec`);
  }

  // Monitor Binance connection status
  monitorConnection() {
    const checkConnection = () => {
      if (!this.store) return;

      const status = binanceWebSocketService.getStatus();
      let connectionStatus = 'disconnected';

      if (status.isConnected) {
        connectionStatus = 'connected';
      } else if (status.isConnecting) {
        connectionStatus = 'connecting';
      } else if (status.reconnectAttempts > 0) {
        connectionStatus = 'reconnecting';
      }

      // Update Redux store with connection status
      this.store.dispatch(setBinanceConnectionStatus(connectionStatus));

      console.log('🔍 RealTimePriceService: Connection status:', connectionStatus, status);
    };

    // Check every 5 seconds
    setInterval(checkConnection, 5000);
    checkConnection(); // Initial check
  }

  // Add symbols to watch
  addWatchedSymbols(symbols) {
    console.log('🔍 RealTimePriceService: Adding watched symbols:', symbols);
    binanceWebSocketService.addSymbols(symbols);
  }

  // Remove symbols from watch
  removeWatchedSymbols(symbols) {
    console.log('🔍 RealTimePriceService: Removing watched symbols:', symbols);
    binanceWebSocketService.removeSymbols(symbols);
  }

  // Get current status
  getStatus() {
    return {
      ...binanceWebSocketService.getStatus(),
      isInitialized: this.isInitialized,
      bufferSize: this.priceBuffer.length,
      updateCounter: this.updateCounter,
    };
  }

  // Manually trigger connection
  connect() {
    console.log('🔍 RealTimePriceService: Manually triggering connection');
    binanceWebSocketService.connect();
  }

  // Disconnect
  disconnect() {
    console.log('🔍 RealTimePriceService: Disconnecting');
    binanceWebSocketService.disconnect();
    
    // Clear buffer
    this.flushBuffer();
  }

  // Cleanup
  cleanup() {
    console.log('🔍 RealTimePriceService: Cleaning up');
    this.disconnect();
    
    if (this.bufferTimeout) {
      clearTimeout(this.bufferTimeout);
      this.bufferTimeout = null;
    }
    
    this.isInitialized = false;
    this.store = null;
  }
}

// Create singleton instance
const realTimePriceService = new RealTimePriceService();

export default realTimePriceService;