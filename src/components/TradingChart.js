import React, { useRef, useEffect, useState } from "react";
import "./TradingChart.css";
import {
  FiTrendingUp,
  FiActivity,
  FiBarChart2,
  FiLayers,
  FiCircle,
  FiTrash2,
  FiSliders,
  FiEye,
  FiGrid,
  FiChevronRight,
  FiChevronLeft,
  FiSettings,
  FiPlusCircle,
} from "react-icons/fi";

// TradingView widget loader
const TradingViewWidget = ({
  symbol = "BTCUSDT",
  interval = "D",
  theme = "light",
  studies = [],
  drawings = [],
  containerId = "tradingview_chart",
  autosize = true,
  locale = "en",
  onWidgetReady,
}) => {
  const widgetRef = useRef(null);

  useEffect(() => {
    // Remove previous widget if exists
    if (widgetRef.current) {
      widgetRef.current.innerHTML = "";
    }
    // Load TradingView script if not already loaded
    if (!window.TradingView) {
      const script = document.createElement("script");
      script.src = "https://s3.tradingview.com/tv.js";
      script.async = true;
      script.onload = () => {
        createWidget();
      };
      document.body.appendChild(script);
    } else {
      createWidget();
    }

    function createWidget() {
      if (window.TradingView && window.TradingView.widget) {
        /* global TradingView */
        new window.TradingView.widget({
          autosize,
          symbol,
          interval,
          timezone: "Etc/UTC",
          theme,
          style: "1",
          locale,
          toolbar_bg: theme === "dark" ? "#181A20" : "#fff",
          enable_publishing: false,
          allow_symbol_change: true,
          container_id: containerId,
          studies,
          drawings_access: {
            type: "black",
            tools: drawings,
          },
          withdateranges: true,
          hide_side_toolbar: false,
          details: true,
          hotlist: true,
          calendar: true,
          studies_overrides: {},
          overrides: {},
          loading_screen: { backgroundColor: theme === "dark" ? "#181A20" : "#fff", foregroundColor: "#2196F3" },
          events: {
            onReady: onWidgetReady,
          },
        });
      }
    }
    // eslint-disable-next-line
  }, [symbol, interval, theme, studies, drawings, containerId, autosize, locale, onWidgetReady]);

  return <div id={containerId} ref={widgetRef} style={{ width: "100%", height: "100%" }} />;
};

const INDICATOR_LIST = [
  { key: "SMA", label: "SMA", icon: <FiTrendingUp /> },
  { key: "EMA", label: "EMA", icon: <FiActivity /> },
  { key: "BOLL", label: "Bollinger Bands", icon: <FiBarChart2 /> },
  { key: "RSI", label: "RSI", icon: <FiSliders /> },
  { key: "MACD", label: "MACD", icon: <FiGrid /> },
  { key: "VOLUME", label: "Volume", icon: <FiBarChart2 /> },
];

const DRAWING_TOOLS = [
  { key: "trend_line", label: "Trend Line", icon: <FiTrendingUp /> },
  { key: "fibonacci", label: "Fibonacci", icon: <FiLayers /> },
  { key: "rectangle", label: "Rectangle", icon: <FiBarChart2 /> },
  { key: "ellipse", label: "Ellipse", icon: <FiCircle /> },
];

const PATTERNS = [
  { key: "head_and_shoulders", label: "Head & Shoulders" },
  { key: "double_top", label: "Double Top" },
  { key: "double_bottom", label: "Double Bottom" },
  { key: "triangle", label: "Triangle" },
  { key: "flag", label: "Flag" },
  { key: "cup_and_handle", label: "Cup & Handle" },
];

const TradingChart = ({
  coinData = "BTCUSDT",
  timeframe = "1D",
  chartType = "candlestick",
  onChartReady,
  theme = "light",
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeIndicators, setActiveIndicators] = useState([]);
  const [activeDrawings, setActiveDrawings] = useState([]);
  const [activePattern, setActivePattern] = useState(null);
  const [showPatternPanel, setShowPatternPanel] = useState(false);

  // Map timeframe to TradingView interval
  const intervalMap = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1H": "60",
    "4H": "240",
    "1D": "D",
    "1W": "W",
    "1M": "M",
    "1d": "D",
    "1w": "W",
    "1m": "1",
    "1h": "60",
    "4h": "240",
  };
  const interval = intervalMap[timeframe] || "D";

  // TradingView studies mapping
  const indicatorToStudy = {
    SMA: "MAExp@tv-basicstudies",
    EMA: "EMA@tv-basicstudies",
    BOLL: "BollingerBands@tv-basicstudies",
    RSI: "RSI@tv-basicstudies",
    MACD: "MACD@tv-basicstudies",
    VOLUME: "Volume@tv-basicstudies",
  };

  // TradingView drawing tools mapping
  const drawingToTool = {
    trend_line: "trend_line",
    fibonacci: "fibonacci_retracement",
    rectangle: "rectangle",
    ellipse: "ellipse",
  };

  // Handle indicator toggle
  const handleIndicatorToggle = (key) => {
    setActiveIndicators((prev) =>
      prev.includes(key)
        ? prev.filter((i) => i !== key)
        : [...prev, key]
    );
  };

  // Handle drawing tool toggle
  const handleDrawingToggle = (key) => {
    setActiveDrawings((prev) =>
      prev.includes(key)
        ? prev.filter((i) => i !== key)
        : [...prev, key]
    );
  };

  // Handle pattern selection
  const handlePatternSelect = (key) => {
    setActivePattern(key);
    setShowPatternPanel(false);
  };

  // Handle clear chart (reset indicators, drawings, pattern)
  const handleClear = () => {
    setActiveIndicators([]);
    setActiveDrawings([]);
    setActivePattern(null);
  };

  // Notify parent when chart is ready
  useEffect(() => {
    if (onChartReady) {
      onChartReady({
        type: "tradingview",
        data: {
          symbol: coinData,
          interval,
          indicators: activeIndicators,
          drawings: activeDrawings,
          pattern: activePattern,
        },
      });
    }
    // eslint-disable-next-line
  }, [onChartReady, coinData, interval, activeIndicators, activeDrawings, activePattern]);

  return (
    <div className="trading-chart-container tradingview-layout">
      <div className={`tradingview-sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="sidebar-toggle" onClick={() => setSidebarOpen((v) => !v)}>
          {sidebarOpen ? <FiChevronLeft /> : <FiChevronRight />}
        </div>
        {sidebarOpen && (
          <div className="sidebar-content">
            <div className="sidebar-section">
              <h4>
                <FiSliders style={{ marginRight: 6 }} />
                Indicators
              </h4>
              <div className="indicator-controls">
                {INDICATOR_LIST.map((ind) => (
                  <button
                    key={ind.key}
                    className={`indicator-btn${activeIndicators.includes(ind.key) ? " active" : ""}`}
                    onClick={() => handleIndicatorToggle(ind.key)}
                  >
                    {ind.icon}
                    <span style={{ marginLeft: 6 }}>{ind.label}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="sidebar-section">
              <h4>
                <FiLayers style={{ marginRight: 6 }} />
                Drawing Tools
              </h4>
              <div className="drawing-tools">
                {DRAWING_TOOLS.map((tool) => (
                  <button
                    key={tool.key}
                    className={`tool-btn${activeDrawings.includes(tool.key) ? " active" : ""}`}
                    onClick={() => handleDrawingToggle(tool.key)}
                  >
                    {tool.icon}
                    <span style={{ marginLeft: 6 }}>{tool.label}</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="sidebar-section">
              <h4>
                <FiPlusCircle style={{ marginRight: 6 }} />
                Pattern Addwell
              </h4>
              <button
                className="pattern-btn"
                onClick={() => setShowPatternPanel((v) => !v)}
              >
                {activePattern
                  ? PATTERNS.find((p) => p.key === activePattern)?.label
                  : "Select Pattern"}
                <FiChevronRight style={{ marginLeft: 8 }} />
              </button>
              {showPatternPanel && (
                <div className="pattern-panel">
                  {PATTERNS.map((pattern) => (
                    <div
                      key={pattern.key}
                      className={`pattern-item${activePattern === pattern.key ? " selected" : ""}`}
                      onClick={() => handlePatternSelect(pattern.key)}
                    >
                      {pattern.label}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="sidebar-section">
              <h4>
                <FiSettings style={{ marginRight: 6 }} />
                Chart Options
              </h4>
              <div className="chart-options">
                <button className="tool-btn" onClick={handleClear}>
                  <FiTrash2 style={{ marginRight: 6 }} />
                  Clear
                </button>
                {/* You can add more chart options here */}
              </div>
            </div>
            <div className="sidebar-section">
              <h4>
                <FiEye style={{ marginRight: 6 }} />
                Chart Info
              </h4>
              <div className="chart-info">
                <div className="info-item">
                  <span className="info-label">Timeframe:</span>
                  <span className="info-value">{timeframe}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Chart Type:</span>
                  <span className="info-value">{chartType}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Active Indicators:</span>
                  <span className="info-value">
                    {activeIndicators.length
                      ? activeIndicators.join(", ")
                      : "None"}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Active Drawings:</span>
                  <span className="info-value">
                    {activeDrawings.length
                      ? activeDrawings.join(", ")
                      : "None"}
                  </span>
                </div>
                <div className="info-item">
                  <span className="info-label">Pattern:</span>
                  <span className="info-value">
                    {activePattern
                      ? PATTERNS.find((p) => p.key === activePattern)?.label
                      : "None"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="tradingview-main-panel">
        <TradingViewWidget
          symbol={coinData}
          interval={interval}
          theme={theme}
          studies={activeIndicators.map((ind) => indicatorToStudy[ind]).filter(Boolean)}
          drawings={activeDrawings.map((draw) => drawingToTool[draw]).filter(Boolean)}
          containerId="tradingview_chart"
          autosize={true}
          locale="en"
          onWidgetReady={() => {}}
        />
        {/* Optionally, show pattern overlay panel */}
        {activePattern && (
          <div className="pattern-overlay">
            <span>
              Pattern: {PATTERNS.find((p) => p.key === activePattern)?.label}
            </span>
            <button
              className="close-pattern-btn"
              onClick={() => setActivePattern(null)}
              title="Remove Pattern"
            >
              <FiTrash2 />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingChart;
