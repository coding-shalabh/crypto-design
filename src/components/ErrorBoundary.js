import React from 'react';
import { FiAlertTriangle, FiRefreshCw } from 'react-icons/fi';
import { toast } from 'react-toastify';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Show toast notification instead of breaking the page
    toast.error('Something went wrong. Please refresh the page if the issue persists.', {
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          padding: '20px',
          textAlign: 'center',
          backgroundColor: '#1a1a1a',
          color: '#white',
          borderRadius: '8px',
          border: '1px solid #333'
        }}>
          <FiAlertTriangle size={48} color="#ff6b6b" style={{ marginBottom: '16px' }} />
          <h2 style={{ margin: '0 0 8px 0', color: '#ff6b6b' }}>Something went wrong</h2>
          <p style={{ margin: '0 0 16px 0', color: '#999' }}>
            An unexpected error occurred in this component.
          </p>
          <button
            onClick={this.handleRetry}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = '#0056b3'}
            onMouseOut={(e) => e.target.style.backgroundColor = '#007bff'}
          >
            <FiRefreshCw size={16} />
            Try Again
          </button>
          
          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <details style={{ marginTop: '20px', textAlign: 'left', maxWidth: '600px' }}>
              <summary style={{ cursor: 'pointer', color: '#007bff' }}>Error Details (Development)</summary>
              <pre style={{ 
                fontSize: '12px', 
                color: '#ff6b6b', 
                backgroundColor: '#2a2a2a', 
                padding: '10px',
                borderRadius: '4px',
                overflow: 'auto',
                marginTop: '10px'
              }}>
                {this.state.error && this.state.error.toString()}
                <br />
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;