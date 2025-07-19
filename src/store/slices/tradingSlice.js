import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  positions: {},
  tradeHistory: [],
  paperBalance: 100000.0,
  totalPnL: 0,
  selectedSymbol: 'BTCUSDT',
  selectedTimeframe: '1h',
  isChangingTimeframe: false,
  recentTrades: [],
  loading: false,
  error: null,
};

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    setPositions: (state, action) => {
      state.positions = action.payload;
    },
    addPosition: (state, action) => {
      const { symbol, position } = action.payload;
      state.positions[symbol] = position;
    },
    removePosition: (state, action) => {
      const symbol = action.payload;
      delete state.positions[symbol];
    },
    updatePosition: (state, action) => {
      const { symbol, updates } = action.payload;
      if (state.positions[symbol]) {
        state.positions[symbol] = { ...state.positions[symbol], ...updates };
      }
    },
    setTradeHistory: (state, action) => {
      state.tradeHistory = action.payload;
    },
    addTrade: (state, action) => {
      state.tradeHistory.unshift(action.payload);
      // Keep only the last 100 trades
      if (state.tradeHistory.length > 100) {
        state.tradeHistory = state.tradeHistory.slice(0, 100);
      }
    },
    setPaperBalance: (state, action) => {
      state.paperBalance = action.payload;
    },
    updateBalance: (state, action) => {
      state.paperBalance += action.payload;
    },
    setTotalPnL: (state, action) => {
      state.totalPnL = action.payload;
    },
    setSelectedSymbol: (state, action) => {
      state.selectedSymbol = action.payload;
    },
    setSelectedTimeframe: (state, action) => {
      state.selectedTimeframe = action.payload;
    },
    setIsChangingTimeframe: (state, action) => {
      state.isChangingTimeframe = action.payload;
    },
    setRecentTrades: (state, action) => {
      state.recentTrades = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setPositions,
  addPosition,
  removePosition,
  updatePosition,
  setTradeHistory,
  addTrade,
  setPaperBalance,
  updateBalance,
  setTotalPnL,
  setSelectedSymbol,
  setSelectedTimeframe,
  setIsChangingTimeframe,
  setRecentTrades,
  setLoading,
  setError,
  clearError,
} = tradingSlice.actions;

export default tradingSlice.reducer;