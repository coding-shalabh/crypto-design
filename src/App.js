import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Import Redux store and provider
import { Provider } from 'react-redux';
import { store } from './store/store';

// Import WebSocket context
import { WebSocketProvider } from './contexts/WebSocketContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { TradingModeProvider } from './contexts/TradingModeContext';

// Import real-time price service
import realTimePriceService from './services/realTimePriceService';

// Import pages
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Analytics from './pages/Analytics';
import Portfolio from './pages/Portfolio';
import News from './pages/News';
import Settings from './pages/Settings';
import Login from './pages/Login';

// Import components
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import AuthPage from './components/AuthPage';
import TradingModeToggle from './components/TradingModeToggle';

// Create main app component that uses authentication
const MainApp = () => {
  const { isAuthenticated, user, loading, login } = useAuth();
  const [tradingMode, setTradingMode] = React.useState('mock');

  // Initialize real-time price service when authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      realTimePriceService.init(store);
    }
    
    return () => {
      realTimePriceService.cleanup();
    };
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: '#1a1a1a',
        color: 'white'
      }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthPage onAuthSuccess={login} />;
  }

  return (
    <ErrorBoundary>
      <div className="App">
        <ErrorBoundary>
          <Sidebar />
        </ErrorBoundary>
        <div className="main-content">
          <ErrorBoundary>
            <Header />
          </ErrorBoundary>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trading" element={<Trading />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/charts" element={<Trading />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/news" element={<News />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </div>
        <TradingModeToggle onModeChange={setTradingMode} />
      </div>
    </ErrorBoundary>
  );
};

function App() {
  return (
    <Provider store={store}>
      <AuthProvider>
        <WebSocketProvider>
          <TradingModeProvider>
            <Router>
              <MainApp />
              <ToastContainer 
                position="top-right"
                autoClose={3000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
              />
            </Router>
          </TradingModeProvider>
        </WebSocketProvider>
      </AuthProvider>
    </Provider>
  );
}

export default App;
