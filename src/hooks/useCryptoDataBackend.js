import { useState, useEffect, useCallback, useMemo } from "react";
import { useWebSocketContext } from "../contexts/WebSocketContext";

export const useCryptoDataBackend = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [currentView, setCurrentView] = useState("grid");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Use the shared WebSocket context instead of creating a new connection
  const {
    isConnected,
    error: wsError,
    data: wsData,
    getCryptoData,
    connect,
    disconnect
  } = useWebSocketContext();

  // Extract crypto data from WebSocket data
  const cryptoData = useMemo(() => {
    const data = new Map(Object.entries(wsData.crypto_data || {}));
    console.log('Crypto data from WebSocket:', wsData.crypto_data);
    console.log('Processed crypto data:', data);
    console.log('Sample crypto entries:', Array.from(data.entries()).slice(0, 3));
    return data;
  }, [wsData.crypto_data]);

  // Filtered data based on search term
  const filteredData = useMemo(() => {
    return Array.from(cryptoData.values())
      .filter(
        (crypto) =>
          crypto.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          crypto.symbol.toLowerCase().includes(searchTerm.toLowerCase())
      )
      .sort((a, b) => a.market_cap_rank - b.market_cap_rank);
  }, [cryptoData, searchTerm]);

  // Global stats calculation
  const globalStats = useMemo(() => {
    const totalMarketCap = Array.from(cryptoData.values()).reduce(
      (sum, crypto) => sum + crypto.market_cap,
      0
    );

    const totalVolume = Array.from(cryptoData.values()).reduce(
      (sum, crypto) => sum + crypto.volume_24h,
      0
    );

    const btcData = cryptoData.get("bitcoin");
    const btcDominance = btcData
      ? (btcData.market_cap / totalMarketCap) * 100
      : 0;

    return {
      totalMarketCap,
      totalVolume,
      activeCoins: cryptoData.size,
      btcDominance,
    };
  }, [cryptoData]);

  // Load initial data when connected
  const loadInitialData = useCallback(async () => {
    if (isConnected) {
      try {
        setLoading(true);
        setError(null);
        
        // Request all crypto data from backend
        getCryptoData();
        
        setLoading(false);
      } catch (err) {
        console.error("Error loading initial data:", err);
        setError(err.message);
        setLoading(false);
      }
    }
  }, [isConnected, getCryptoData]);

  // Retry connection
  const retryConnection = useCallback(() => {
    setError(null);
    connect();
  }, [connect]);

  // Initialize on mount
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      setError(wsError);
    }
  }, [wsError]);

  // Handle connection status
  useEffect(() => {
    if (isConnected) {
      setError(null);
      // Load data when connected
      loadInitialData();
    }
  }, [isConnected, loadInitialData]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log("Page hidden - reducing update frequency");
      } else {
        console.log("Page visible - resuming normal updates");
        // Refresh data when page becomes visible
        if (isConnected) {
          loadInitialData();
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isConnected, loadInitialData]);

  return {
    cryptoData,
    filteredData,
    globalStats,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    currentView,
    setCurrentView,
    connectionStatus: isConnected ? "connected" : "disconnected",
    retryConnection,
    // Also expose WebSocket data for trading components
    wsData,
    isConnected,
  };
}; 