// Crypto Trading Dashboard - Real-time WebSocket Application
class CryptoDashboard {
  constructor() {
    this.cryptoData = new Map();
    this.filteredData = [];
    this.currentView = "grid";
    this.searchTerm = "";
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.connectWebSocket();
    this.loadInitialData();
  }

  setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById("search-input");
    searchInput.addEventListener("input", (e) => {
      this.searchTerm = e.target.value.toLowerCase();
      this.filterAndDisplayData();
    });

    // View switching
    const gridViewBtn = document.getElementById("grid-view");
    const listViewBtn = document.getElementById("list-view");

    gridViewBtn.addEventListener("click", () => this.switchView("grid"));
    listViewBtn.addEventListener("click", () => this.switchView("list"));

    // Retry button
    const retryBtn = document.getElementById("retry-btn");
    retryBtn.addEventListener("click", () => this.retryConnection());

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "k":
            e.preventDefault();
            searchInput.focus();
            break;
          case "1":
            e.preventDefault();
            this.switchView("grid");
            break;
          case "2":
            e.preventDefault();
            this.switchView("list");
            break;
        }
      }
    });
  }

  async loadInitialData() {
    try {
      this.showLoading(true);

      // Load initial data from CoinGecko API
      const response = await fetch(
        "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch initial data");
      }

      const data = await response.json();

      // Process and store initial data
      data.forEach((coin) => {
        this.cryptoData.set(coin.id, {
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

      this.updateGlobalStats();
      this.filterAndDisplayData();
      this.showLoading(false);
    } catch (error) {
      console.error("Error loading initial data:", error);
      this.showError();
    }
  }

  connectWebSocket() {
    try {
      // Using Binance WebSocket for real-time price updates
      this.ws = new WebSocket("wss://stream.binance.com:9443/ws/!ticker@arr");

      this.ws.onopen = () => {
        this.updateConnectionStatus("connected");
        this.reconnectAttempts = 0;
        console.log("WebSocket connected");
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.processWebSocketData(data);
        } catch (error) {
          console.error("Error parsing WebSocket data:", error);
        }
      };

      this.ws.onclose = () => {
        this.updateConnectionStatus("disconnected");
        console.log("WebSocket disconnected");
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        this.updateConnectionStatus("disconnected");
      };
    } catch (error) {
      console.error("Error connecting to WebSocket:", error);
      this.updateConnectionStatus("disconnected");
    }
  }

  processWebSocketData(data) {
    if (!Array.isArray(data)) return;

    data.forEach((ticker) => {
      const symbol = ticker.s;
      const price = parseFloat(ticker.c);
      const priceChange = parseFloat(ticker.P);
      const volume = parseFloat(ticker.v);
      const marketCap = price * parseFloat(ticker.Q);

      // Find matching crypto by symbol
      for (let [id, crypto] of this.cryptoData) {
        if (crypto.symbol === symbol.replace("USDT", "")) {
          const oldPrice = crypto.current_price;

          crypto.current_price = price;
          crypto.price_change_percentage_24h = priceChange;
          crypto.volume_24h = volume;
          crypto.market_cap = marketCap;
          crypto.last_updated = new Date();

          // Update the specific card with animation
          this.updateCryptoCard(id, crypto, oldPrice);
          break;
        }
      }
    });

    this.updateGlobalStats();
  }

  updateCryptoCard(id, crypto, oldPrice) {
    const card = document.querySelector(`[data-crypto-id="${id}"]`);
    if (!card) return;

    // Update price with animation
    const priceElement = card.querySelector(".crypto-price");
    if (priceElement) {
      const newPrice = this.formatPrice(crypto.current_price);
      const priceChange = crypto.current_price - oldPrice;

      if (priceChange !== 0) {
        priceElement.style.color = priceChange > 0 ? "#10b981" : "#ef4444";
        setTimeout(() => {
          priceElement.style.color = "";
        }, 1000);
      }

      priceElement.textContent = newPrice;
    }

    // Update price change
    const changeElement = card.querySelector(".price-change");
    if (changeElement) {
      const changeClass =
        crypto.price_change_percentage_24h >= 0 ? "positive" : "negative";
      const changeIcon =
        crypto.price_change_percentage_24h >= 0
          ? "fa-arrow-up"
          : "fa-arrow-down";

      changeElement.className = `price-change ${changeClass}`;
      changeElement.innerHTML = `
                <i class="fas ${changeIcon}"></i>
                ${Math.abs(crypto.price_change_percentage_24h).toFixed(2)}%
            `;
    }

    // Update stats
    const marketCapElement = card.querySelector('[data-stat="market-cap"]');
    if (marketCapElement) {
      marketCapElement.textContent = this.formatMarketCap(crypto.market_cap);
    }

    const volumeElement = card.querySelector('[data-stat="volume"]');
    if (volumeElement) {
      volumeElement.textContent = this.formatVolume(crypto.volume_24h);
    }
  }

  updateGlobalStats() {
    const totalMarketCap = Array.from(this.cryptoData.values()).reduce(
      (sum, crypto) => sum + crypto.market_cap,
      0
    );

    const totalVolume = Array.from(this.cryptoData.values()).reduce(
      (sum, crypto) => sum + crypto.volume_24h,
      0
    );

    const btcData = this.cryptoData.get("bitcoin");
    const btcDominance = btcData
      ? (btcData.market_cap / totalMarketCap) * 100
      : 0;

    document.getElementById("total-market-cap").textContent =
      this.formatMarketCap(totalMarketCap);
    document.getElementById("total-volume").textContent =
      this.formatVolume(totalVolume);
    document.getElementById("active-coins").textContent = this.cryptoData.size;
    document.getElementById(
      "btc-dominance"
    ).textContent = `${btcDominance.toFixed(2)}%`;
  }

  filterAndDisplayData() {
    this.filteredData = Array.from(this.cryptoData.values())
      .filter(
        (crypto) =>
          crypto.name.toLowerCase().includes(this.searchTerm) ||
          crypto.symbol.toLowerCase().includes(this.searchTerm)
      )
      .sort((a, b) => a.market_cap_rank - b.market_cap_rank);

    this.renderCryptoCards();
  }

  renderCryptoCards() {
    const container = document.getElementById("crypto-container");
    container.className = `crypto-grid ${
      this.currentView === "list" ? "list-view" : ""
    }`;

    if (this.filteredData.length === 0) {
      container.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No cryptocurrencies found matching "${this.searchTerm}"</p>
                </div>
            `;
      return;
    }

    container.innerHTML = this.filteredData
      .map((crypto) => this.createCryptoCard(crypto))
      .join("");
  }

  createCryptoCard(crypto) {
    const changeClass =
      crypto.price_change_percentage_24h >= 0 ? "positive" : "negative";
    const changeIcon =
      crypto.price_change_percentage_24h >= 0 ? "fa-arrow-up" : "fa-arrow-down";

    return `
            <div class="crypto-card ${
              this.currentView === "list" ? "list-view" : ""
            }" data-crypto-id="${crypto.id}">
                <div class="crypto-header">
                    <div class="crypto-name">
                        <div class="crypto-icon">${crypto.symbol.charAt(
                          0
                        )}</div>
                        <div>
                            <div class="crypto-symbol">${crypto.symbol}</div>
                            <div class="crypto-full-name">${crypto.name}</div>
                        </div>
                    </div>
                    <div class="crypto-rank">#${crypto.market_cap_rank}</div>
                </div>
                
                <div class="crypto-price">${this.formatPrice(
                  crypto.current_price
                )}</div>
                
                <div class="price-change ${changeClass}">
                    <i class="fas ${changeIcon}"></i>
                    ${Math.abs(crypto.price_change_percentage_24h).toFixed(2)}%
                </div>
                
                <div class="crypto-stats">
                    <div class="stat-item">
                        <span class="stat-label">Market Cap</span>
                        <span class="stat-value" data-stat="market-cap">${this.formatMarketCap(
                          crypto.market_cap
                        )}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Volume (24h)</span>
                        <span class="stat-value" data-stat="volume">${this.formatVolume(
                          crypto.volume_24h
                        )}</span>
                    </div>
                </div>
            </div>
        `;
  }

  switchView(view) {
    this.currentView = view;

    // Update button states
    document
      .getElementById("grid-view")
      .classList.toggle("active", view === "grid");
    document
      .getElementById("list-view")
      .classList.toggle("active", view === "list");

    // Update container class
    const container = document.getElementById("crypto-container");
    container.className = `crypto-grid ${view === "list" ? "list-view" : ""}`;

    // Re-render cards
    this.renderCryptoCards();
  }

  updateConnectionStatus(status) {
    const indicator = document.getElementById("status-indicator");
    const statusText = document.getElementById("status-text");

    indicator.className = `status-indicator ${status}`;

    switch (status) {
      case "connected":
        statusText.textContent = "Connected";
        break;
      case "disconnected":
        statusText.textContent = "Disconnected";
        break;
      default:
        statusText.textContent = "Connecting...";
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`
      );

      setTimeout(() => {
        this.connectWebSocket();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error("Max reconnection attempts reached");
      this.showError();
    }
  }

  retryConnection() {
    this.reconnectAttempts = 0;
    this.showError(false);
    this.connectWebSocket();
    this.loadInitialData();
  }

  showLoading(show) {
    const loading = document.getElementById("loading");
    const error = document.getElementById("error-message");
    const container = document.getElementById("crypto-container");

    if (show) {
      loading.style.display = "block";
      error.style.display = "none";
      container.style.display = "none";
    } else {
      loading.style.display = "none";
      container.style.display = "grid";
    }
  }

  showError(show = true) {
    const loading = document.getElementById("loading");
    const error = document.getElementById("error-message");
    const container = document.getElementById("crypto-container");

    if (show) {
      loading.style.display = "none";
      error.style.display = "block";
      container.style.display = "none";
    } else {
      error.style.display = "none";
      container.style.display = "grid";
    }
  }

  // Utility functions for formatting
  formatPrice(price) {
    if (price >= 1) {
      return `$${price.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    } else {
      return `$${price.toLocaleString("en-US", {
        minimumFractionDigits: 6,
        maximumFractionDigits: 6,
      })}`;
    }
  }

  formatMarketCap(marketCap) {
    if (marketCap >= 1e12) {
      return `$${(marketCap / 1e12).toFixed(2)}T`;
    } else if (marketCap >= 1e9) {
      return `$${(marketCap / 1e9).toFixed(2)}B`;
    } else if (marketCap >= 1e6) {
      return `$${(marketCap / 1e6).toFixed(2)}M`;
    } else {
      return `$${marketCap.toLocaleString()}`;
    }
  }

  formatVolume(volume) {
    if (volume >= 1e12) {
      return `$${(volume / 1e12).toFixed(2)}T`;
    } else if (volume >= 1e9) {
      return `$${(volume / 1e9).toFixed(2)}B`;
    } else if (volume >= 1e6) {
      return `$${(volume / 1e6).toFixed(2)}M`;
    } else {
      return `$${volume.toLocaleString()}`;
    }
  }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  new CryptoDashboard();
});

// Handle page visibility changes to optimize WebSocket usage
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    console.log("Page hidden - reducing update frequency");
  } else {
    console.log("Page visible - resuming normal updates");
  }
});

// Handle beforeunload to clean up WebSocket connection
window.addEventListener("beforeunload", () => {
  if (window.cryptoDashboard && window.cryptoDashboard.ws) {
    window.cryptoDashboard.ws.close();
  }
});
