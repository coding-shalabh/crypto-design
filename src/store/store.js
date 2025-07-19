import { configureStore } from '@reduxjs/toolkit';
import tradingReducer from './slices/tradingSlice';
import botReducer from './slices/botSlice';
import marketDataReducer from './slices/marketDataSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    trading: tradingReducer,
    bot: botReducer,
    marketData: marketDataReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;