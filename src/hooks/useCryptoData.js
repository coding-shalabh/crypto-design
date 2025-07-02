import { useState, useEffect, useCallback, useMemo } from "react";

export const useCryptoData = () => {
  const [cryptoData, setCryptoData] = useState(new Map());
  const [searchTerm, setSearchTerm] = useState("");
  const [currentView, setCurrentView] = useState("grid");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ws, setWs] = useState(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState("connecting");

  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

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

  // Load initial data
  const loadInitialData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch initial data");
      }

      const data = await response.json();

      const newCryptoData = new Map();
      data.forEach((coin) => {
        newCryptoData.set(coin.id, {
          id: coin.id,
          symbol: coin.symbol.toUpperCase(),
          name: coin.name,
          current_price: coin.current_price,
          market_cap: coin.market_cap,
          volume_24h: coin.total_volume,
          price_change_24h: coin.price_change_24h,
          price_change_percentage_24h: coin.price_change_percentage_24h,
          market_cap_rank: coin.market_cap_rank,
          last_updated: new Date(coin.last_updated),
        });
      });

      setCryptoData(newCryptoData);
      setLoading(false);
    } catch (err) {
      console.error("Error loading initial data:", err);
      setError(err.message);
      setLoading(false);
    }
  }, []);

  // Connect WebSocket
  const connectWebSocket = useCallback(() => {
    try {
      const websocket = new WebSocket(
        "wss://stream.binance.com:9443/ws/!ticker@arr"
      );

      websocket.onopen = () => {
        setConnectionStatus("connected");
        setReconnectAttempts(0);
        console.log("WebSocket connected");
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          processWebSocketData(data);
        } catch (err) {
          console.error("Error parsing WebSocket data:", err);
        }
      };

      websocket.onclose = () => {
        setConnectionStatus("disconnected");
        console.log("WebSocket disconnected");
        scheduleReconnect();
      };

      websocket.onerror = (err) => {
        console.error("WebSocket error:", err);
        setConnectionStatus("disconnected");
      };

      setWs(websocket);
    } catch (err) {
      console.error("Error connecting to WebSocket:", err);
      setConnectionStatus("disconnected");
    }
  }, []);

  // Process WebSocket data
  const processWebSocketData = useCallback((data) => {
    if (!Array.isArray(data)) return;

    setCryptoData((prevData) => {
      const newData = new Map(prevData);

      data.forEach((ticker) => {
        const symbol = ticker.s;
        const price = parseFloat(ticker.c);
        const priceChange = parseFloat(ticker.P);
        const volume = parseFloat(ticker.v);
        const marketCap = price * parseFloat(ticker.Q);

        // Find matching crypto by symbol
        for (let [id, crypto] of newData) {
          if (crypto.symbol === symbol.replace("USDT", "")) {
            newData.set(id, {
              ...crypto,
              current_price: price,
              price_change_percentage_24h: priceChange,
              volume_24h: volume,
              market_cap: marketCap,
              last_updated: new Date(),
            });
            break;
          }
        }
      });

      return newData;
    });
  }, []);

  // Schedule reconnection
  const scheduleReconnect = useCallback(() => {
    if (reconnectAttempts < maxReconnectAttempts) {
      setReconnectAttempts((prev) => prev + 1);
      console.log(
        `Attempting to reconnect (${
          reconnectAttempts + 1
        }/${maxReconnectAttempts})...`
      );

      setTimeout(() => {
        connectWebSocket();
      }, reconnectDelay * (reconnectAttempts + 1));
    } else {
      console.error("Max reconnection attempts reached");
      setError("Connection failed. Please check your internet connection.");
    }
  }, [reconnectAttempts, connectWebSocket]);

  // Retry connection
  const retryConnection = useCallback(() => {
    setReconnectAttempts(0);
    setError(null);
    if (ws) {
      ws.close();
    }
    connectWebSocket();
    loadInitialData();
  }, [ws, connectWebSocket, loadInitialData]);

  // Initialize on mount
  useEffect(() => {
    loadInitialData();
    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log("Page hidden - reducing update frequency");
      } else {
        console.log("Page visible - resuming normal updates");
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

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
    connectionStatus,
    retryConnection,
  };
};
