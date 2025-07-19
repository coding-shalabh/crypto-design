import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

const Login = () => {
  console.log('🔍 Login: Page component initialized');
  
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  console.log('🔍 Login: Initial email:', email);
  
  const [password, setPassword] = useState('');
  console.log('🔍 Login: Initial password:', password);
  
  const [isLoading, setIsLoading] = useState(false);
  console.log('🔍 Login: Initial isLoading:', isLoading);
  
  const [error, setError] = useState('');
  console.log('🔍 Login: Initial error:', error);

  const handleEmailChange = (e) => {
    const value = e.target.value;
    console.log('🔍 Login: handleEmailChange called with:', value);
    setEmail(value);
    console.log('🔍 Login: Updated email to:', value);
  };

  const handlePasswordChange = (e) => {
    const value = e.target.value;
    console.log('🔍 Login: handlePasswordChange called with:', value);
    setPassword(value);
    console.log('🔍 Login: Updated password to:', value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('🔍 Login: handleSubmit called');
    
    if (!email || !password) {
      console.log('🔍 Login: Validation failed - missing email or password');
      setError('Please enter both email and password');
      return;
    }

    console.log('🔍 Login: Starting login process');
    setIsLoading(true);
    console.log('🔍 Login: Set isLoading to true');
    setError('');
    console.log('🔍 Login: Cleared error');

    try {
      // For now, just simulate a login process
      console.log('🔍 Login: Simulating login process');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('🔍 Login: Login successful, navigating to dashboard');
      navigate('/');
    } catch (error) {
      console.error('🔍 Login: Login error:', error);
      setError('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
      console.log('🔍 Login: Set isLoading to false');
    }
  };

  const handleDemoLogin = () => {
    console.log('🔍 Login: handleDemoLogin called');
    console.log('🔍 Login: Navigating to dashboard for demo');
    navigate('/');
  };

  // Debug logging for state changes
  React.useEffect(() => {
    console.log('🔍 Login: State updated:', {
      email,
      password: password ? '[HIDDEN]' : '',
      isLoading,
      error
    });
  }, [email, password, isLoading, error]);

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>🔐 Crypto Trading Dashboard</h1>
          <p>Sign in to access your trading platform</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={handleEmailChange}
              placeholder="Enter your email"
              className="form-input"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={handlePasswordChange}
              placeholder="Enter your password"
              className="form-input"
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="spinner"></div>
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="demo-section">
          <p className="demo-text">Or try the demo version:</p>
          <button
            type="button"
            className="demo-btn"
            onClick={handleDemoLogin}
            disabled={isLoading}
          >
             Launch Demo
          </button>
        </div>

        <div className="login-footer">
          <p>Demo credentials: demo@example.com / demo123</p>
          <p>This is a demo trading platform for educational purposes.</p>
        </div>
      </div>
    </div>
  );
};

export default Login; 