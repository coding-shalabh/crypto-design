import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  cryptoData: {},
  priceCache: {},
  selectedCrypto: null,
  isLoading: false,
  lastUpdate: null,
  error: null,
  candleData: {},
  newsData: [],
  aiAnalysis: {},
  aiOpportunities: {},
  // 🔥 NEW: Real-time price management
  realTimePrices: {},
  priceHistory: {},
  binanceConnectionStatus: 'disconnected',
  priceUpdateStats: {
    totalUpdates: 0,
    lastUpdateTime: null,
    updatesPerSecond: 0,
  },
  watchedSymbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'SOLUSDT'],
};

const marketDataSlice = createSlice({
  name: 'marketData',
  initialState,
  reducers: {
    setCryptoData: (state, action) => {
      state.cryptoData = action.payload;
      state.lastUpdate = Date.now();
    },
    updateCryptoData: (state, action) => {
      state.cryptoData = { ...state.cryptoData, ...action.payload };
      state.lastUpdate = Date.now();
    },
    setPriceCache: (state, action) => {
      state.priceCache = action.payload;
    },
    updatePriceCache: (state, action) => {
      state.priceCache = { ...state.priceCache, ...action.payload };
    },
    batchUpdatePrices: (state, action) => {
      const updates = action.payload;
      updates.forEach(update => {
        state.priceCache[update.symbol] = update;
      });
    },
    setSelectedCrypto: (state, action) => {
      state.selectedCrypto = action.payload;
    },
    setMarketLoading: (state, action) => {
      state.isLoading = action.payload;
    },
    setMarketError: (state, action) => {
      state.error = action.payload;
    },
    clearMarketError: (state) => {
      state.error = null;
    },
    setCandleData: (state, action) => {
      const { symbol, data } = action.payload;
      state.candleData[symbol] = data;
    },
    setNewsData: (state, action) => {
      state.newsData = action.payload;
    },
    addNews: (state, action) => {
      state.newsData.unshift(action.payload);
      // Keep only the last 100 news items
      if (state.newsData.length > 100) {
        state.newsData = state.newsData.slice(0, 100);
      }
    },
    setAiAnalysis: (state, action) => {
      const { symbol, analysis } = action.payload;
      state.aiAnalysis[symbol] = analysis;
    },
    setAiOpportunities: (state, action) => {
      state.aiOpportunities = action.payload;
    },
    addAiOpportunity: (state, action) => {
      const { symbol, opportunity } = action.payload;
      if (!state.aiOpportunities[symbol]) {
        state.aiOpportunities[symbol] = [];
      }
      state.aiOpportunities[symbol].unshift(opportunity);
      // Keep only the last 10 opportunities per symbol
      if (state.aiOpportunities[symbol].length > 10) {
        state.aiOpportunities[symbol] = state.aiOpportunities[symbol].slice(0, 10);
      }
    },
    // 🔥 NEW: Real-time price management actions
    updateRealTimePrice: (state, action) => {
      const priceData = action.payload;
      const { symbol } = priceData;
      
      // Update real-time prices
      state.realTimePrices[symbol] = {
        ...priceData,
        lastUpdate: Date.now(),
      };
      
      // Update price cache for backward compatibility
      state.priceCache[symbol] = {
        price: priceData.price,
        change_24h: priceData.priceChangePercent,
        volume: priceData.volume,
        high_24h: priceData.highPrice,
        low_24h: priceData.lowPrice,
        timestamp: priceData.timestamp,
      };
      
      // Update statistics
      state.priceUpdateStats.totalUpdates += 1;
      state.priceUpdateStats.lastUpdateTime = Date.now();
      
      // Store price history (keep last 100 updates per symbol)
      if (!state.priceHistory[symbol]) {
        state.priceHistory[symbol] = [];
      }
      state.priceHistory[symbol].unshift({
        price: priceData.price,
        timestamp: priceData.timestamp,
      });
      if (state.priceHistory[symbol].length > 100) {
        state.priceHistory[symbol] = state.priceHistory[symbol].slice(0, 100);
      }
      
      state.lastUpdate = Date.now();
    },
    batchUpdateRealTimePrices: (state, action) => {
      const priceUpdates = action.payload;
      const updateTime = Date.now();
      
      priceUpdates.forEach(priceData => {
        const { symbol } = priceData;
        
        // Update real-time prices
        state.realTimePrices[symbol] = {
          ...priceData,
          lastUpdate: updateTime,
        };
        
        // Update price cache for backward compatibility
        state.priceCache[symbol] = {
          price: priceData.price,
          change_24h: priceData.priceChangePercent,
          volume: priceData.volume,
          high_24h: priceData.highPrice,
          low_24h: priceData.lowPrice,
          timestamp: priceData.timestamp,
        };
        
        // Store price history
        if (!state.priceHistory[symbol]) {
          state.priceHistory[symbol] = [];
        }
        state.priceHistory[symbol].unshift({
          price: priceData.price,
          timestamp: priceData.timestamp,
        });
        if (state.priceHistory[symbol].length > 100) {
          state.priceHistory[symbol] = state.priceHistory[symbol].slice(0, 100);
        }
      });
      
      // Update statistics
      state.priceUpdateStats.totalUpdates += priceUpdates.length;
      state.priceUpdateStats.lastUpdateTime = updateTime;
      state.lastUpdate = updateTime;
    },
    setBinanceConnectionStatus: (state, action) => {
      state.binanceConnectionStatus = action.payload;
    },
    addWatchedSymbol: (state, action) => {
      const symbol = action.payload;
      if (!state.watchedSymbols.includes(symbol)) {
        state.watchedSymbols.push(symbol);
      }
    },
    removeWatchedSymbol: (state, action) => {
      const symbol = action.payload;
      state.watchedSymbols = state.watchedSymbols.filter(s => s !== symbol);
    },
    setWatchedSymbols: (state, action) => {
      state.watchedSymbols = action.payload;
    },
    updatePriceUpdateStats: (state, action) => {
      state.priceUpdateStats = { ...state.priceUpdateStats, ...action.payload };
    },
    clearPriceHistory: (state, action) => {
      const symbol = action.payload;
      if (symbol) {
        delete state.priceHistory[symbol];
      } else {
        state.priceHistory = {};
      }
    },
  },
});

export const {
  setCryptoData,
  updateCryptoData,
  setPriceCache,
  updatePriceCache,
  batchUpdatePrices,
  setSelectedCrypto,
  setMarketLoading,
  setMarketError,
  clearMarketError,
  setCandleData,
  setNewsData,
  addNews,
  setAiAnalysis,
  setAiOpportunities,
  addAiOpportunity,
  // 🔥 NEW: Real-time price actions
  updateRealTimePrice,
  batchUpdateRealTimePrices,
  setBinanceConnectionStatus,
  addWatchedSymbol,
  removeWatchedSymbol,
  setWatchedSymbols,
  updatePriceUpdateStats,
  clearPriceHistory,
} = marketDataSlice.actions;

export default marketDataSlice.reducer;