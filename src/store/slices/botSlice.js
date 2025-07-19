import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  enabled: false,
  status: {
    enabled: false,
    start_time: null,
    active_trades: 0,
    trades_today: 0,
    total_profit: 0,
    total_trades: 0,
    winning_trades: 0,
    win_rate: 0,
    pair_status: {},
    running_duration: 0,
  },
  config: {
    max_trades_per_day: 10,
    trade_amount_usdt: 50,
    profit_target_min: 3,
    profit_target_max: 5,
    stop_loss_percent: 1.5,
    trailing_enabled: true,
    trailing_trigger_usd: 1,
    trailing_distance_usd: 0.5,
    trade_interval_secs: 600,
    max_concurrent_trades: 20,
    cooldown_secs: 300,
    allowed_pairs: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    ai_confidence_threshold: 0.65,
    run_time_minutes: 180,
    test_mode: false,
    risk_per_trade_percent: 5.0,
    monitor_open_trades: true,
    loss_check_interval_percent: 1,
    rollback_enabled: true,
    reanalysis_cooldown_seconds: 300,
    reconfirm_before_entry: true,
    slippage_tolerance_percent: 0.1,
    signal_sources: ['gpt', 'claude'],
    manual_approval_mode: false,
  },
  activeTrades: {},
  tradeHistory: [],
  analysisLogs: [],
  tradeLogs: [],
  loading: false,
  error: null,
};

const botSlice = createSlice({
  name: 'bot',
  initialState,
  reducers: {
    setBotEnabled: (state, action) => {
      state.enabled = action.payload;
      state.status.enabled = action.payload;
    },
    setBotStatus: (state, action) => {
      state.status = { ...state.status, ...action.payload };
      state.enabled = action.payload.enabled !== undefined ? action.payload.enabled : state.enabled;
    },
    setBotConfig: (state, action) => {
      state.config = { ...state.config, ...action.payload };
    },
    setActiveTrades: (state, action) => {
      state.activeTrades = action.payload;
    },
    addActiveTrade: (state, action) => {
      const { symbol, trade } = action.payload;
      state.activeTrades[symbol] = trade;
    },
    removeActiveTrade: (state, action) => {
      const symbol = action.payload;
      delete state.activeTrades[symbol];
    },
    updateActiveTrade: (state, action) => {
      const { symbol, updates } = action.payload;
      if (state.activeTrades[symbol]) {
        state.activeTrades[symbol] = { ...state.activeTrades[symbol], ...updates };
      }
    },
    setBotTradeHistory: (state, action) => {
      state.tradeHistory = action.payload;
    },
    addBotTrade: (state, action) => {
      state.tradeHistory.unshift(action.payload);
      // Keep only the last 100 trades
      if (state.tradeHistory.length > 100) {
        state.tradeHistory = state.tradeHistory.slice(0, 100);
      }
    },
    setAnalysisLogs: (state, action) => {
      state.analysisLogs = action.payload;
    },
    addAnalysisLog: (state, action) => {
      state.analysisLogs.unshift(action.payload);
      // Keep only the last 50 logs
      if (state.analysisLogs.length > 50) {
        state.analysisLogs = state.analysisLogs.slice(0, 50);
      }
    },
    setTradeLogs: (state, action) => {
      state.tradeLogs = action.payload;
    },
    addTradeLog: (state, action) => {
      state.tradeLogs.unshift(action.payload);
      // Keep only the last 50 logs
      if (state.tradeLogs.length > 50) {
        state.tradeLogs = state.tradeLogs.slice(0, 50);
      }
    },
    updateRunningDuration: (state, action) => {
      state.status.running_duration = action.payload;
    },
    setBotLoading: (state, action) => {
      state.loading = action.payload;
    },
    setBotError: (state, action) => {
      state.error = action.payload;
    },
    clearBotError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setBotEnabled,
  setBotStatus,
  setBotConfig,
  setActiveTrades,
  addActiveTrade,
  removeActiveTrade,
  updateActiveTrade,
  setBotTradeHistory,
  addBotTrade,
  setAnalysisLogs,
  addAnalysisLog,
  setTradeLogs,
  addTradeLog,
  updateRunningDuration,
  setBotLoading,
  setBotError,
  clearBotError,
} = botSlice.actions;

export default botSlice.reducer;