import { useDispatch, useSelector } from 'react-redux';
import { useMemo } from 'react';

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = () => useDispatch();
export const useAppSelector = useSelector;

// Specific selectors for common data
export const useConnectionStatus = () => useSelector(state => state.ui.isConnected);
export const useBotStatus = () => useSelector(state => state.bot.status);
export const useBotConfig = () => useSelector(state => state.bot.config);
export const usePositions = () => useSelector(state => state.trading.positions);
export const usePriceCache = () => useSelector(state => state.marketData.priceCache);
export const useCryptoData = () => useSelector(state => state.marketData.cryptoData);
export const useActiveTab = () => useSelector(state => state.ui.activeTab);
export const useNotifications = () => useSelector(state => state.ui.notifications);
export const useBotActiveTrades = () => useSelector(state => state.bot.activeTrades);
export const useTradeHistory = () => useSelector(state => state.trading.tradeHistory);
export const useBotTradeHistory = () => useSelector(state => state.bot.tradeHistory);
export const useAnalysisLogs = () => useSelector(state => state.bot.analysisLogs);
export const useTradeLogs = () => useSelector(state => state.bot.tradeLogs);
export const usePaperBalance = () => useSelector(state => state.trading.paperBalance);
export const useSelectedSymbol = () => useSelector(state => state.trading.selectedSymbol);
export const useSelectedTimeframe = () => useSelector(state => state.trading.selectedTimeframe);
export const useLoading = (component) => useSelector(state => state.ui.loading[component]);
export const useError = (component) => useSelector(state => state.ui.errors[component]);

// 🔥 NEW: Real-time price hooks
export const useRealTimePrices = () => useSelector(state => state.marketData.realTimePrices);

export const usePriceBySymbol = (symbol) => {
  return useSelector(state => 
    state.marketData.realTimePrices[symbol] || 
    state.marketData.priceCache[symbol] || 
    null
  );
};

export const usePriceHistory = (symbol) => {
  return useSelector(state => state.marketData.priceHistory[symbol] || []);
};

export const useBinanceConnectionStatus = () => {
  return useSelector(state => state.marketData.binanceConnectionStatus);
};

export const usePriceUpdateStats = () => {
  return useSelector(state => state.marketData.priceUpdateStats);
};

export const useWatchedSymbols = () => {
  return useSelector(state => state.marketData.watchedSymbols);
};

// Enhanced price hook with computed data
export const useEnhancedPrice = (symbol) => {
  const price = usePriceBySymbol(symbol);
  const history = usePriceHistory(symbol);
  
  return useMemo(() => {
    if (!price) return null;
    
    // Calculate price trend from history
    const trend = history.length > 1 ? 
      (history[0].price > history[1].price ? 'up' : 'down') : 'neutral';
    
    // Calculate price change from history
    const priceChange = history.length > 1 ?
      ((history[0].price - history[1].price) / history[1].price) * 100 : 0;
    
    return {
      ...price,
      trend,
      priceChange,
      isRealTime: Date.now() - (price.lastUpdate || 0) < 5000, // Consider real-time if updated within 5 seconds
    };
  }, [price, history]);
};

// Hook for multiple symbols
export const useMultipleSymbolPrices = (symbols) => {
  const prices = useRealTimePrices();
  
  return useMemo(() => {
    return symbols.reduce((acc, symbol) => {
      acc[symbol] = prices[symbol] || null;
      return acc;
    }, {});
  }, [symbols, prices]);
};