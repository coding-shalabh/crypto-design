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
  const [spotBalance, setSpotBalance] = useState(null);
  const [availableCoins, setAvailableCoins] = useState(['USDT']);
  const [selectedCoin, setSelectedCoin] = useState('USDT');
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
    
    // Check futures balance if in live mode (with debouncing)
    if (isLiveMode && socket) {
      const timeoutId = setTimeout(() => {
        checkFuturesBalance();
        checkSpotBalance();
      }, 200); // 200ms debounce for balance checks
      
      return () => clearTimeout(timeoutId);
    }
  }, [onModeChange, socket, isLiveMode]);

  const checkFuturesBalance = async () => {
    try {
      const balance = await tradingService.getTradingBalance(selectedCoin);
      setFuturesBalance(balance);
      
      // Show zero balance modal if futures balance is 0 and we're in live mode
      if (balance && balance.total === 0 && balance.wallet_type === 'FUTURES' && isLiveMode) {
        setShowZeroBalanceModal(true);
      }
    } catch (error) {
      // Set a fallback balance to prevent undefined errors
      setFuturesBalance({
        asset: selectedCoin,
        free: 0,
        locked: 0,
        total: 0,
        wallet_type: 'ERROR',
        error: error.message
      });
    }
  };

  const checkSpotBalance = async () => {
    try {
      // Get all wallet balances to find available coins
      const response = await tradingService.getAllTradingBalances();
      
      if (response && response.balances) {
        // Filter coins with balance > 0
        const coinsWithBalance = Object.keys(response.balances.spot || {})
          .filter(coin => response.balances.spot[coin].total > 0);
        setAvailableCoins(['USDT', ...coinsWithBalance.filter(coin => coin !== 'USDT')]);
        
        // Set USDT spot balance
        const usdtSpotBalance = response.balances.spot?.USDT;
        if (usdtSpotBalance) {
          setSpotBalance(usdtSpotBalance);
        }
      }
    } catch (error) {
      // Set fallback balance
      setSpotBalance({
        asset: 'USDT',
        free: 0,
        locked: 0,
        total: 0,
        wallet_type: 'ERROR',
        error: error.message
      });
    }
  };

  const setMaxAmount = () => {
    if (spotBalance && spotBalance.free > 0) {
      setTransferAmount(spotBalance.free.toString());
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
      // Just update global state - the context will handle sending to backend
      toggleTradingMode(); // This will trigger TradingModeContext to send the mode change
      setShowConfirmation(false);
      
      // Check futures balance after switching to live
      await checkFuturesBalance();
      
      // Set a simple success status
      setConnectionStatus({ success: true, message: 'Live trading enabled' });
    } catch (error) {
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

    if (spotBalance && parseFloat(transferAmount) > spotBalance.free) {
      alert(`Transfer amount exceeds available balance (${spotBalance.free} ${selectedCoin})`);
      return;
    }

    setTransferLoading(true);
    try {
      const result = await tradingService.transferBetweenWallets(
        selectedCoin,
        parseFloat(transferAmount),
        'SPOT',
        'FUTURES'
      );

      if (result.success) {
        alert(`Successfully transferred ${transferAmount} ${selectedCoin} to Futures wallet`);
        setShowZeroBalanceModal(false);
        setTransferAmount('');
        // Refresh balances
        await checkFuturesBalance();
        await checkSpotBalance();
      } else {
        alert(`Transfer failed: ${result.message}`);
      }
    } catch (error) {
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
            onClick={() => {
              if (isLiveMode) {
                checkFuturesBalance();
                checkSpotBalance();
              }
              setShowBalances(true);
            }}
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
                <label>Select Asset:</label>
                <select 
                  value={selectedCoin} 
                  onChange={(e) => setSelectedCoin(e.target.value)}
                  className="coin-selector"
                >
                  {availableCoins.map(coin => (
                    <option key={coin} value={coin}>{coin}</option>
                  ))}
                </select>
                
                <label>Transfer Amount ({selectedCoin}):</label>
                <div className="amount-input-group">
                  <input
                    type="number"
                    value={transferAmount}
                    onChange={(e) => setTransferAmount(e.target.value)}
                    placeholder={`Enter amount to transfer`}
                    min="0"
                    step="0.01"
                  />
                  <button 
                    type="button" 
                    className="max-button"
                    onClick={setMaxAmount}
                    disabled={!spotBalance || spotBalance.free <= 0}
                  >
                    MAX
                  </button>
                </div>
              </div>
              
              <div className="balance-info">
                <div className="balance-row">
                  <span>Spot Balance:</span>
                  <span>{spotBalance ? `${spotBalance.free} ${selectedCoin}` : 'Loading...'}</span>
                </div>
                <div className="balance-row">
                  <span>Futures Balance:</span>
                  <span>{futuresBalance ? `${futuresBalance.total} ${selectedCoin}` : '0 USDT'}</span>
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