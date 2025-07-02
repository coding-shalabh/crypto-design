import React from "react";
import "./App.css";
import Header from "./components/Header";
import Controls from "./components/Controls";
import StatsOverview from "./components/StatsOverview";
import CryptoGrid from "./components/CryptoGrid";
import Loading from "./components/Loading";
import ErrorMessage from "./components/ErrorMessage";
import { useCryptoData } from "./hooks/useCryptoData";

function App() {
  const {
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
  } = useCryptoData();

  return (
    <div className="App">
      <Header connectionStatus={connectionStatus} />

      <main className="main">
        <div className="container">
          <Controls
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            currentView={currentView}
            setCurrentView={setCurrentView}
          />

          <StatsOverview stats={globalStats} />

          {loading && <Loading />}

          {error && <ErrorMessage onRetry={retryConnection} />}

          {!loading && !error && (
            <CryptoGrid cryptoData={filteredData} currentView={currentView} />
          )}
        </div>
      </main>

      <footer className="footer">
        <div className="container">
          <p>
            &copy; 2024 Crypto Trading Dashboard. Real-time data powered by
            WebSocket.
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
