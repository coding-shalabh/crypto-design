import React, { useState, useEffect } from 'react';
import { FaToggleOn, FaToggleOff, FaWallet, FaExchangeAlt } from 'react-icons/fa';
import { MdTrendingUp, MdShowChart } from 'react-icons/md';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useTradingMode } from '../contexts/TradingModeContext';
import tradingService from '../services/tradingService';
import CategorizedBalances from './CategorizedBalances';
import './TradingModeToggle.css';

const TradingModeToggle = ({ onModeChange }) => {
  const { isLiveMode, toggleTradingMode } = useTradingMode();
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showZeroBalanceModal, setShowZeroBalanceModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [showBalances, setShowBalances] = useState(false);
  const [futuresBalance, setFuturesBalance] = useState(null);
  const [transferAmount, setTransferAmount] = useState('');
  const [transferLoading, setTransferLoading] = useState(false);
  const { socket } = useWebSocket();

  useEffect(() => {
    // Set up trading service with WebSocket
    if (socket) {
      tradingService.setWebSocket(socket);
    }

    // Sync with global trading mode
    if (onModeChange) {
      onModeChange(isLiveMode ? 'live' : 'mock');
    }
    
    // Set mode in trading service
    if (socket) {
      tradingService.setTradingMode(isLiveMode ? 'live' : 'mock').catch(console.error);
    }
    
    // Check futures balance if in live mode
    if (isLiveMode && socket) {
      checkFuturesBalance();
    }
  }, [onModeChange, socket, isLiveMode]);

  const checkFuturesBalance = async () => {
    try {
      const balance = await tradingService.getTradingBalance('USDT');
      setFuturesBalance(balance);
      
      // Show zero balance modal if futures balance is 0 and we're in live mode
      if (balance && balance.total === 0 && balance.wallet_type === 'FUTURES') {
        setShowZeroBalanceModal(true);
      }
    } catch (error) {
      console.error('Failed to check futures balance:', error);
    }
  };

  const handleToggle = () => {
    if (!isLiveMode) {
      // Switching to live trading - show confirmation
      setShowConfirmation(true);
    } else {
      // Switching to mock trading - use global toggle
      toggleTradingMode();
    }
  };

  const confirmLiveTrading = async () => {
    setIsLoading(true);
    try {
      const result = await tradingService.setTradingMode('live');
      toggleTradingMode(); // Update global state
      setConnectionStatus(result.connection_test);
      setShowConfirmation(false);
      
      // Check futures balance after switching to live
      await checkFuturesBalance();
    } catch (error) {
      console.error('Failed to switch to live trading:', error);
      setConnectionStatus({ success: false, message: error.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTransferToFutures = async () => {
    if (!transferAmount || parseFloat(transferAmount) <= 0) {
      alert('Please enter a valid transfer amount');
      return;
    }

    setTransferLoading(true);
    try {
      const result = await tradingService.transferBetweenWallets(
        'USDT',
        parseFloat(transferAmount),
        'SPOT',
        'FUTURES'
      );

      if (result.success) {
        alert(`Successfully transferred ${transferAmount} USDT to Futures wallet`);
        setShowZeroBalanceModal(false);
        setTransferAmount('');
        // Refresh balance
        await checkFuturesBalance();
      } else {
        alert(`Transfer failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Transfer failed:', error);
      alert(`Transfer failed: ${error.message}`);
    } finally {
      setTransferLoading(false);
    }
  };

  return (
    <>
      <div className="trading-mode-toggle">
        <div className="toggle-container">
          <div className="mode-indicator">
            {isLiveMode ? (
              <MdTrendingUp className="live-icon" />
            ) : (
              <MdShowChart className="mock-icon" />
            )}
            <span className={`mode-text ${isLiveMode ? 'live' : 'mock'}`}>
              {isLiveMode ? 'LIVE' : 'MOCK'}
            </span>
          </div>
          
          <button 
            className="toggle-button"
            onClick={handleToggle}
            disabled={isLoading}
            title={`Switch to ${isLiveMode ? 'Mock' : 'Live'} Trading`}
          >
            {isLoading ? (
              <div className="loading-spinner" />
            ) : isLiveMode ? (
              <FaToggleOn className="toggle-icon live" />
            ) : (
              <FaToggleOff className="toggle-icon mock" />
            )}
          </button>
          
          <button 
            className="balance-button"
            onClick={() => setShowBalances(true)}
            title="View Categorized Balances"
          >
            <FaWallet className="wallet-icon" />
          </button>
        </div>
        
        <div className="mode-description">
          {isLoading ? 'Switching...' : isLiveMode ? 'Real Binance Trading' : 'Paper Trading'}
        </div>
        
        {connectionStatus && (
          <div className={`connection-status ${connectionStatus.success ? 'success' : 'error'}`}>
            {connectionStatus.success ? '✓ Connected' : '✗ Connection Failed'}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="confirmation-overlay">
          <div className="confirmation-modal">
            <div className="modal-header">
              <MdTrendingUp className="warning-icon" />
              <h3>Enable Live Trading?</h3>
            </div>
            
            <div className="modal-content">
              <p>
                You are about to enable <strong>LIVE TRADING</strong> mode.
              </p>
              <p>
                This will connect to your real Binance account and execute 
                trades with real money. All bot trades will be executed on 
                the live market.
              </p>
              <div className="warning-box">
                <strong>⚠️ Warning:</strong> Live trading involves real financial risk. 
                Make sure you understand the risks before proceeding.
              </div>
            </div>
            
            <div className="modal-actions">
              <button 
                className="cancel-button"
                onClick={() => setShowConfirmation(false)}
              >
                Cancel
              </button>
              <button 
                className="confirm-button"
                onClick={confirmLiveTrading}
                disabled={isLoading}
              >
                {isLoading ? 'Connecting...' : 'Enable Live Trading'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Zero Balance Transfer Modal */}
      {showZeroBalanceModal && (
        <div className="confirmation-overlay">
          <div className="confirmation-modal zero-balance-modal">
            <div className="modal-header">
              <FaExchangeAlt className="warning-icon" />
              <h3>Futures Wallet Balance is Zero</h3>
            </div>
            
            <div className="modal-content">
              <p>
                Your Futures wallet has <strong>0 USDT</strong> balance.
              </p>
              <p>
                To use live trading, you need to transfer USDT from your Spot wallet 
                to your Futures wallet. This is required for margin trading.
              </p>
              
              <div className="transfer-form">
                <label>Transfer Amount (USDT):</label>
                <input
                  type="number"
                  value={transferAmount}
                  onChange={(e) => setTransferAmount(e.target.value)}
                  placeholder="Enter amount to transfer"
                  min="0"
                  step="0.01"
                />
              </div>
              
              <div className="balance-info">
                <div className="balance-row">
                  <span>Futures Balance:</span>
                  <span>0 USDT</span>
                </div>
                <div className="balance-note">
                  💡 You can also transfer manually from the Binance website
                </div>
              </div>
            </div>
            
            <div className="modal-actions">
              <button 
                className="cancel-button"
                onClick={() => setShowZeroBalanceModal(false)}
              >
                Skip for Now
              </button>
              <button 
                className="confirm-button"
                onClick={handleTransferToFutures}
                disabled={transferLoading || !transferAmount}
              >
                {transferLoading ? 'Transferring...' : 'Transfer to Futures'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Categorized Balances Modal */}
      <CategorizedBalances 
        isVisible={showBalances}
        onClose={() => setShowBalances(false)}
      />
    </>
  );
};

export default TradingModeToggle;