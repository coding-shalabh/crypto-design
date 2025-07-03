import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./App.css";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import Trading from "./pages/Trading";
import Analytics from "./pages/Analytics";
import News from "./pages/News";
import Settings from "./pages/Settings";

function App() {
  return (
    <Router>
      <div className="App">
        <Sidebar />
        <Header />

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/trading" element={<Trading />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/news" element={<News />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
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
    </Router>
  );
}

export default App;
