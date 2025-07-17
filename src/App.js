import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Import WebSocket context
import { WebSocketProvider } from './contexts/WebSocketContext';

// Import pages
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Login from './pages/Login';

// Import components
import Sidebar from './components/Sidebar';
import Header from './components/Header';

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
    
    return () => {
      console.log('🔍 App: Component unmounting');
    };
  }, [isAuthenticated]);

  // Debug logging for route changes
  const handleRouteChange = (pathname) => {
    console.log('🔍 App: Route changed to:', pathname);
  };

  if (!isAuthenticated) {
    console.log('🔍 App: User not authenticated, redirecting to login');
    return (
      <WebSocketProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </div>
        </Router>
      </WebSocketProvider>
    );
  }

  console.log('🔍 App: User authenticated, rendering main application');
  
  return (
    <WebSocketProvider>
      <Router>
        <div className="App">
          <Sidebar />
          <div className="main-content">
            <Header />
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
                path="/analytics" 
                element={
                  <React.Fragment>
                    {console.log('🔍 App: Rendering Analytics route')}
                    <Analytics />
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
          </div>
        </div>
      </Router>
    </WebSocketProvider>
  );
}

export default App;
