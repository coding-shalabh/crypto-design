import React, { useState } from "react";
import "./Settings.css";

const Settings = () => {
  const [settings, setSettings] = useState({
    theme: "light",
    currency: "USD",
    language: "en",
    notifications: {
      priceAlerts: true,
      newsUpdates: false,
      tradingSignals: true,
      marketUpdates: true,
    },
    display: {
      showPercentages: true,
      showMarketCap: true,
      showVolume: false,
      compactMode: false,
    },
    trading: {
      defaultOrderType: "market",
      confirmTrades: true,
      autoRefresh: true,
      refreshInterval: 30,
    },
  });

  const handleSettingChange = (category, setting, value) => {
    setSettings((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value,
      },
    }));
  };

  const handleSave = () => {
    // Save settings logic here
    console.log("Settings saved:", settings);
  };

  return (
    <div className="settings">
      <div className="settings-header">
        <h1>Settings</h1>
        <p>Customize your trading experience</p>
      </div>

      <div className="settings-container">
        <div className="settings-section">
          <h2>Appearance</h2>
          <div className="setting-group">
            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="theme">Theme</label>
                <p>Choose your preferred color scheme</p>
              </div>
              <select
                id="theme"
                value={settings.theme}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, theme: e.target.value }))
                }
                className="setting-control"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
              </select>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="currency">Default Currency</label>
                <p>Currency for price displays</p>
              </div>
              <select
                id="currency"
                value={settings.currency}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, currency: e.target.value }))
                }
                className="setting-control"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="JPY">JPY</option>
              </select>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="language">Language</label>
                <p>Interface language</p>
              </div>
              <select
                id="language"
                value={settings.language}
                onChange={(e) =>
                  setSettings((prev) => ({ ...prev, language: e.target.value }))
                }
                className="setting-control"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
              </select>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Notifications</h2>
          <div className="setting-group">
            {Object.entries(settings.notifications).map(([key, value]) => (
              <div key={key} className="setting-item">
                <div className="setting-info">
                  <label htmlFor={key}>
                    {key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())}
                  </label>
                  <p>
                    Receive notifications for{" "}
                    {key.toLowerCase().replace(/([A-Z])/g, " $1")}
                  </p>
                </div>
                <label className="toggle">
                  <input
                    type="checkbox"
                    id={key}
                    checked={value}
                    onChange={(e) =>
                      handleSettingChange(
                        "notifications",
                        key,
                        e.target.checked
                      )
                    }
                  />
                  <span className="slider"></span>
                </label>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>Display Options</h2>
          <div className="setting-group">
            {Object.entries(settings.display).map(([key, value]) => (
              <div key={key} className="setting-item">
                <div className="setting-info">
                  <label htmlFor={key}>
                    {key
                      .replace(/([A-Z])/g, " $1")
                      .replace(/^./, (str) => str.toUpperCase())}
                  </label>
                  <p>
                    Show {key.toLowerCase().replace(/([A-Z])/g, " $1")} in the
                    interface
                  </p>
                </div>
                <label className="toggle">
                  <input
                    type="checkbox"
                    id={key}
                    checked={value}
                    onChange={(e) =>
                      handleSettingChange("display", key, e.target.checked)
                    }
                  />
                  <span className="slider"></span>
                </label>
              </div>
            ))}
          </div>
        </div>

        <div className="settings-section">
          <h2>Trading Preferences</h2>
          <div className="setting-group">
            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="orderType">Default Order Type</label>
                <p>Default order type for new trades</p>
              </div>
              <select
                id="orderType"
                value={settings.trading.defaultOrderType}
                onChange={(e) =>
                  handleSettingChange(
                    "trading",
                    "defaultOrderType",
                    e.target.value
                  )
                }
                className="setting-control"
              >
                <option value="market">Market Order</option>
                <option value="limit">Limit Order</option>
                <option value="stop">Stop Order</option>
              </select>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="confirmTrades">Confirm Trades</label>
                <p>Require confirmation before executing trades</p>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  id="confirmTrades"
                  checked={settings.trading.confirmTrades}
                  onChange={(e) =>
                    handleSettingChange(
                      "trading",
                      "confirmTrades",
                      e.target.checked
                    )
                  }
                />
                <span className="slider"></span>
              </label>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label htmlFor="autoRefresh">Auto Refresh</label>
                <p>Automatically refresh market data</p>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  id="autoRefresh"
                  checked={settings.trading.autoRefresh}
                  onChange={(e) =>
                    handleSettingChange(
                      "trading",
                      "autoRefresh",
                      e.target.checked
                    )
                  }
                />
                <span className="slider"></span>
              </label>
            </div>

            {settings.trading.autoRefresh && (
              <div className="setting-item">
                <div className="setting-info">
                  <label htmlFor="refreshInterval">
                    Refresh Interval (seconds)
                  </label>
                  <p>How often to refresh market data</p>
                </div>
                <input
                  type="number"
                  id="refreshInterval"
                  value={settings.trading.refreshInterval}
                  onChange={(e) =>
                    handleSettingChange(
                      "trading",
                      "refreshInterval",
                      parseInt(e.target.value)
                    )
                  }
                  className="setting-control"
                  min="5"
                  max="300"
                />
              </div>
            )}
          </div>
        </div>

        <div className="settings-section">
          <h2>Account</h2>
          <div className="setting-group">
            <div className="setting-item">
              <div className="setting-info">
                <label>API Keys</label>
                <p>Manage your exchange API connections</p>
              </div>
              <button className="btn btn-outline">Manage Keys</button>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label>Export Data</label>
                <p>Download your trading history and portfolio data</p>
              </div>
              <button className="btn btn-outline">Export</button>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <label>Delete Account</label>
                <p>Permanently delete your account and all data</p>
              </div>
              <button className="btn btn-danger">Delete Account</button>
            </div>
          </div>
        </div>
      </div>

      <div className="settings-actions">
        <button
          className="btn btn-secondary"
          onClick={() =>
            setSettings({
              theme: "light",
              currency: "USD",
              language: "en",
              notifications: {
                priceAlerts: true,
                newsUpdates: false,
                tradingSignals: true,
                marketUpdates: true,
              },
              display: {
                showPercentages: true,
                showMarketCap: true,
                showVolume: false,
                compactMode: false,
              },
              trading: {
                defaultOrderType: "market",
                confirmTrades: true,
                autoRefresh: true,
                refreshInterval: 30,
              },
            })
          }
        >
          Reset to Default
        </button>
        <button className="btn btn-primary" onClick={handleSave}>
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default Settings;
