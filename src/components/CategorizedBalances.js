import React, { useState, useEffect } from 'react';
import './CategorizedBalances.css';
import tradingService from '../services/tradingService';

const CategorizedBalances = ({ isVisible, onClose }) => {
  const [balances, setBalances] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedWallet, setSelectedWallet] = useState('SPOT');
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferData, setTransferData] = useState({
    asset: '',
    amount: '',
    fromWallet: 'SPOT',
    toWallet: 'FUTURES'
  });
  const [transferLoading, setTransferLoading] = useState(false);

  const walletTypes = {
    'SPOT': { name: 'Spot Wallet', icon: '💰' },
    'FUTURES': { name: 'Futures Wallet', icon: '📈' },
    'MARGIN': { name: 'Cross Margin', icon: '⚖️' },
    'FUNDING': { name: 'Funding Wallet', icon: '💳' }
  };

  useEffect(() => {
    if (isVisible) {
      loadCategorizedBalances();
    }
  }, [isVisible]);

  const loadCategorizedBalances = async () => {
    setLoading(true);
    try {
      const result = await tradingService.getCategorizedBalances();
      setBalances(result.balances || {});
    } catch (error) {
      console.error('Failed to load categorized balances:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTransfer = async () => {
    if (!transferData.asset || !transferData.amount) {
      alert('Please enter asset and amount');
      return;
    }

    setTransferLoading(true);
    try {
      const result = await tradingService.transferBetweenWallets(
        transferData.asset,
        parseFloat(transferData.amount),
        transferData.fromWallet,
        transferData.toWallet
      );

      if (result.success) {
        alert(result.message);
        setShowTransferModal(false);
        setTransferData({ asset: '', amount: '', fromWallet: 'SPOT', toWallet: 'FUTURES' });
        loadCategorizedBalances(); // Refresh balances
      } else {
        alert(result.message);
      }
    } catch (error) {
      alert('Transfer failed: ' + error.message);
    } finally {
      setTransferLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num === 0) return '0.00';
    if (num < 0.01) return num.toFixed(8);
    return num.toFixed(2);
  };

  if (!isVisible) return null;

  return (
    <div className="balance-modal-overlay">
      <div className="balance-modal">
        <div className="balance-modal-header">
          <h2>Wallet Balances</h2>
          <div className="balance-modal-actions">
            <button 
              className="transfer-btn"
              onClick={() => setShowTransferModal(true)}
            >
              Transfer
            </button>
            <button 
              className="refresh-btn" 
              onClick={loadCategorizedBalances}
              disabled={loading}
            >
              {loading ? '⟳' : '↻'}
            </button>
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
        </div>

        <div className="balance-content">
          <div className="wallet-tabs">
            {Object.keys(walletTypes).map(walletType => (
              <button
                key={walletType}
                className={`wallet-tab ${selectedWallet === walletType ? 'active' : ''}`}
                onClick={() => setSelectedWallet(walletType)}
              >
                <span className="wallet-icon">{walletTypes[walletType].icon}</span>
                <span className="wallet-name">{walletTypes[walletType].name}</span>
                <span className="wallet-total">
                  ${formatNumber(balances[walletType]?.total_usdt || 0)}
                </span>
              </button>
            ))}
          </div>

          <div className="balance-details">
            <div className="wallet-header">
              <h3>
                {walletTypes[selectedWallet].icon} {walletTypes[selectedWallet].name}
              </h3>
              <div className="total-value">
                Total: ${formatNumber(balances[selectedWallet]?.total_usdt || 0)}
              </div>
            </div>

            <div className="asset-list">
              {loading ? (
                <div className="loading">Loading balances...</div>
              ) : (
                <>
                  {balances[selectedWallet]?.balances?.length > 0 ? (
                    balances[selectedWallet].balances.map((balance, index) => (
                      <div key={index} className="asset-row">
                        <div className="asset-info">
                          <div className="asset-name">{balance.asset}</div>
                          <div className="asset-wallet">{balance.wallet_type}</div>
                        </div>
                        <div className="asset-amounts">
                          <div className="amount-row">
                            <span className="amount-label">Total:</span>
                            <span className="amount-value">{formatNumber(balance.total)}</span>
                          </div>
                          <div className="amount-row">
                            <span className="amount-label">Free:</span>
                            <span className="amount-value">{formatNumber(balance.free)}</span>
                          </div>
                          <div className="amount-row">
                            <span className="amount-label">Locked:</span>
                            <span className="amount-value">{formatNumber(balance.locked)}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="no-balances">
                      No assets found in {walletTypes[selectedWallet].name}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Transfer Modal */}
        {showTransferModal && (
          <div className="transfer-modal-overlay">
            <div className="transfer-modal">
              <div className="transfer-modal-header">
                <h3>Transfer Between Wallets</h3>
                <button 
                  className="close-btn" 
                  onClick={() => setShowTransferModal(false)}
                >
                  ×
                </button>
              </div>

              <div className="transfer-form">
                <div className="form-group">
                  <label>Asset</label>
                  <input
                    type="text"
                    placeholder="e.g., USDT, BTC"
                    value={transferData.asset}
                    onChange={(e) => setTransferData({...transferData, asset: e.target.value.toUpperCase()})}
                  />
                </div>

                <div className="form-group">
                  <label>Amount</label>
                  <input
                    type="number"
                    step="0.00000001"
                    placeholder="0.00"
                    value={transferData.amount}
                    onChange={(e) => setTransferData({...transferData, amount: e.target.value})}
                  />
                </div>

                <div className="transfer-direction">
                  <div className="form-group">
                    <label>From Wallet</label>
                    <select
                      value={transferData.fromWallet}
                      onChange={(e) => setTransferData({...transferData, fromWallet: e.target.value})}
                    >
                      {Object.keys(walletTypes).map(walletType => (
                        <option key={walletType} value={walletType}>
                          {walletTypes[walletType].name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="transfer-arrow">→</div>

                  <div className="form-group">
                    <label>To Wallet</label>
                    <select
                      value={transferData.toWallet}
                      onChange={(e) => setTransferData({...transferData, toWallet: e.target.value})}
                    >
                      {Object.keys(walletTypes).map(walletType => (
                        <option key={walletType} value={walletType}>
                          {walletTypes[walletType].name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="transfer-actions">
                  <button
                    className="cancel-btn"
                    onClick={() => setShowTransferModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    className="confirm-btn"
                    onClick={handleTransfer}
                    disabled={transferLoading}
                  >
                    {transferLoading ? 'Transferring...' : 'Confirm Transfer'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CategorizedBalances;