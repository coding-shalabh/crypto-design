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

function App() {
  console.log('🔍 App: Application component initialized');
  
  // Check if user is authenticated (you can implement your own auth logic)
  const isAuthenticated = true; // For now, always authenticated
  console.log('🔍 App: Authentication status:', isAuthenticated);

  // Debug logging for component lifecycle
  React.useEffect(() => {
    console.log('🔍 App: Component mounted');
    console.log('🔍 App: Current authentication status:', isAuthenticated);
    console.log('🔍 App: Available routes:', ['/', '/trading', '/analytics', '/settings', '/login']);
    
    // 🔥 Initialize real-time price service with Redux store
    if (isAuthenticated) {
      console.log('🔍 App: Initializing real-time price service...');
      realTimePriceService.init(store);
    }
    
    return () => {
      console.log('🔍 App: Component unmounting');
      // Cleanup real-time price service
      realTimePriceService.cleanup();
    };
  }, [isAuthenticated]);

  // Debug logging for route changes
  const handleRouteChange = (pathname) => {
    console.log('🔍 App: Route changed to:', pathname);
  };

  if (!isAuthenticated) {
    console.log('🔍 App: User not authenticated, redirecting to login');
    return (
      <Provider store={store}>
        <WebSocketProvider>
          <Router>
            <div className="App">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="*" element={<Navigate to="/login" replace />} />
              </Routes>
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
            </div>
          </Router>
        </WebSocketProvider>
      </Provider>
    );
  }

  console.log('🔍 App: User authenticated, rendering main application');
  
  return (
    <Provider store={store}>
      <WebSocketProvider>
        <ErrorBoundary>
          <Router>
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
                  <Route 
                    path="/" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Dashboard route')}
                        <Dashboard />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/trading" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Trading route')}
                        <Trading />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/portfolio" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Portfolio route')}
                        <Portfolio />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/charts" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Charts route (redirecting to Trading)')}
                        <Trading />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/analytics" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Analytics route')}
                        <Analytics />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/news" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering News route')}
                        <News />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="/settings" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering Settings route')}
                        <Settings />
                      </React.Fragment>
                    } 
                  />
                  <Route 
                    path="*" 
                    element={
                      <React.Fragment>
                        {console.log('🔍 App: Rendering default redirect to Dashboard')}
                        <Navigate to="/" replace />
                      </React.Fragment>
                    } 
                  />
                </Routes>
              </ErrorBoundary>
            </div>
          </div>
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
        </ErrorBoundary>
      </WebSocketProvider>
    </Provider>
  );
}

export default App;
