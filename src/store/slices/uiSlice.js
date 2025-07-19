import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  isConnected: false,
  activeTab: 'overview',
  showConfigModal: false,
  showTradeModal: false,
  sidebarCollapsed: false,
  theme: 'dark',
  notifications: [],
  loading: {
    bot: false,
    trading: false,
    market: false,
  },
  errors: {
    bot: null,
    trading: null,
    market: null,
    connection: null,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setConnectionStatus: (state, action) => {
      state.isConnected = action.payload;
      if (!action.payload) {
        state.errors.connection = 'WebSocket connection lost';
      } else {
        state.errors.connection = null;
      }
    },
    setActiveTab: (state, action) => {
      state.activeTab = action.payload;
    },
    setShowConfigModal: (state, action) => {
      state.showConfigModal = action.payload;
    },
    setShowTradeModal: (state, action) => {
      state.showTradeModal = action.payload;
    },
    setSidebarCollapsed: (state, action) => {
      state.sidebarCollapsed = action.payload;
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
    addNotification: (state, action) => {
      const notification = {
        id: Date.now(),
        timestamp: Date.now(),
        ...action.payload,
      };
      state.notifications.unshift(notification);
      // Keep only the last 20 notifications
      if (state.notifications.length > 20) {
        state.notifications = state.notifications.slice(0, 20);
      }
    },
    removeNotification: (state, action) => {
      const id = action.payload;
      state.notifications = state.notifications.filter(n => n.id !== id);
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setLoading: (state, action) => {
      const { component, loading } = action.payload;
      state.loading[component] = loading;
    },
    setError: (state, action) => {
      const { component, error } = action.payload;
      state.errors[component] = error;
    },
    clearError: (state, action) => {
      const component = action.payload;
      state.errors[component] = null;
    },
    clearAllErrors: (state) => {
      state.errors = {
        bot: null,
        trading: null,
        market: null,
        connection: null,
      };
    },
  },
});

export const {
  setConnectionStatus,
  setActiveTab,
  setShowConfigModal,
  setShowTradeModal,
  setSidebarCollapsed,
  setTheme,
  addNotification,
  removeNotification,
  clearNotifications,
  setLoading,
  setError,
  clearError,
  clearAllErrors,
} = uiSlice.actions;

export default uiSlice.reducer;