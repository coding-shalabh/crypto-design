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
} = marketDataSlice.actions;

export default marketDataSlice.reducer;