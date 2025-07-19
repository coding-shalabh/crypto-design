import { useDispatch, useSelector } from 'react-redux';

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