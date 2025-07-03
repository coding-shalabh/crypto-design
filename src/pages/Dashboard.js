import React from "react";
import Controls from "../components/Controls";
import StatsOverview from "../components/StatsOverview";
import CryptoGrid from "../components/CryptoGrid";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import { useCryptoData } from "../hooks/useCryptoData";
import "./Dashboard.css";

const Dashboard = () => {
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
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Cryptocurrency Dashboard</h1>
        <p>Real-time market data and trading insights</p>
      </div>

      <div className="dashboard-content">
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
    </div>
  );
};

export default Dashboard;
