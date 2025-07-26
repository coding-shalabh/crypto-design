import React, { useState } from 'react';
import './AuthPage.css';

const AuthPage = ({ onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Frontend validation
    if (!formData.username.trim()) {
      setError('Username is required');
      setLoading(false);
      return;
    }
    
    if (!formData.password.trim()) {
      setError('Password is required');
      setLoading(false);
      return;
    }
    
    if (!isLogin && !formData.email.trim()) {
      setError('Email is required for signup');
      setLoading(false);
      return;
    }

    // Attempting authentication

    try {
      // Create WebSocket connection if it doesn't exist
      if (!window.ws || window.ws.readyState !== WebSocket.OPEN) {
        // Creating WebSocket connection
        window.ws = new WebSocket('ws://localhost:8767');
        await new Promise((resolve, reject) => {
          window.ws.onopen = () => {
            // WebSocket connected
            resolve();
          };
          window.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            reject(error);
          };
          setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
        });
      }

      const messageType = isLogin ? 'login' : 'register';
      const payload = isLogin 
        ? { username: formData.username.trim(), password: formData.password }
        : { username: formData.username.trim(), email: formData.email.trim(), password: formData.password };

      // Sending authentication request

      // Send authentication request
      window.ws.send(JSON.stringify({
        type: messageType,
        data: payload
      }));

      // Wait for response
      const response = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Request timeout')), 10000);
        
        window.ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          // Received authentication response
          
          if (message.type === 'login_success' || message.type === 'register_success') {
            clearTimeout(timeout);
            resolve(message);
          } else if (message.type === 'auth_error') {
            clearTimeout(timeout);
            reject(new Error(message.data.message));
          }
        };
      });

      // Store auth data and call success callback
      if (response.data.token) {
        localStorage.setItem('auth_token', response.data.token);
        localStorage.setItem('user_data', JSON.stringify(response.data.user));
        onAuthSuccess(response.data.user, response.data.token);
      }

    } catch (err) {
      console.error('Auth error:', err);
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          {/* <h1>Crypto Trading Bot</h1> */}
          <p>{isLogin ? 'Login to your account' : 'Create a new account'}</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              required
              placeholder="Enter your username"
            />
          </div>

          {!isLogin && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                placeholder="Enter your email"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              placeholder="Enter your password"
              minLength="6"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>

        <div className="auth-switch">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              className="switch-button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setFormData({ username: '', email: '', password: '' });
              }}
            >
              {isLogin ? 'Sign Up' : 'Login'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;