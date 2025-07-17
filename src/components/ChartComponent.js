import React, { useState, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";
import "./TradingChart.css";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ChartComponent = ({
  coinData,
  timeframe,
  chartType,
  onChartReady,
  theme = "light",
}) => {
  const [indicators, setIndicators] = useState({
    sma: { enabled: false, period: 20 },
    ema: { enabled: false, period: 20 },
    bollinger: { enabled: false, period: 20, stdDev: 2 },
    rsi: { enabled: false, period: 14 },
    macd: { enabled: false },
    volume: { enabled: true },
  });
  const [drawingTool, setDrawingTool] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [priceScale, setPriceScale] = useState("right");
  const [timeScale, setTimeScale] = useState("visible");

  // Generate sample data
  const generateSampleData = (count) => {
    const labels = [];
    const prices = [];
    const volumes = [];
    let price = 50000;
    let volume = 1000000;

    for (let i = 0; i < count; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (count - i));
      labels.push(date.toLocaleDateString());

      const change = (Math.random() - 0.5) * 0.1;
      price = price * (1 + change);
      prices.push(price);

      volume = volume * (0.8 + Math.random() * 0.4);
      volumes.push(volume);
    }

    return { labels, prices, volumes };
  };

  const { labels, prices, volumes } = generateSampleData(30);

  // Calculate technical indicators
  const calculateSMA = (data, period) => {
    const sma = [];
    for (let i = period - 1; i < data.length; i++) {
      const sum = data
        .slice(i - period + 1, i + 1)
        .reduce((acc, val) => acc + val, 0);
      sma.push(sum / period);
    }
    return sma;
  };

  const calculateEMA = (data, period) => {
    const ema = [];
    const multiplier = 2 / (period + 1);

    // First EMA is SMA
    let sum = data.slice(0, period).reduce((acc, val) => acc + val, 0);
    ema.push(sum / period);

    for (let i = period; i < data.length; i++) {
      const newEMA =
        data[i] * multiplier + ema[ema.length - 1] * (1 - multiplier);
      ema.push(newEMA);
    }
    return ema;
  };

  const calculateBollingerBands = (data, period, stdDev) => {
    const upper = [];
    const middle = [];
    const lower = [];

    for (let i = period - 1; i < data.length; i++) {
      const slice = data.slice(i - period + 1, i + 1);
      const sma = slice.reduce((acc, val) => acc + val, 0) / period;
      const variance =
        slice.reduce((acc, val) => acc + Math.pow(val - sma, 2), 0) / period;
      const standardDeviation = Math.sqrt(variance);

      middle.push(sma);
      upper.push(sma + standardDeviation * stdDev);
      lower.push(sma - standardDeviation * stdDev);
    }

    return { upper, middle, lower };
  };

  // Chart configuration
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: theme === "dark" ? "#d1d4dc" : "#333",
        },
      },
      title: {
        display: true,
        text: `${coinData} Price Chart - ${timeframe}`,
        color: theme === "dark" ? "#d1d4dc" : "#333",
      },
      tooltip: {
        mode: "index",
        intersect: false,
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: "Date",
          color: theme === "dark" ? "#d1d4dc" : "#333",
        },
        ticks: {
          color: theme === "dark" ? "#d1d4dc" : "#333",
        },
        grid: {
          color: theme === "dark" ? "#404040" : "#e1e3ef",
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: "Price (USD)",
          color: theme === "dark" ? "#d1d4dc" : "#333",
        },
        ticks: {
          color: theme === "dark" ? "#d1d4dc" : "#333",
        },
        grid: {
          color: theme === "dark" ? "#404040" : "#e1e3ef",
        },
      },
    },
    interaction: {
      mode: "nearest",
      axis: "x",
      intersect: false,
    },
  };

  // Prepare datasets
  const datasets = [
    {
      label: "Price",
      data: prices,
      borderColor: "#ff8000",
      backgroundColor: "rgba(30, 60, 114, 0.1)",
      borderWidth: 2,
      fill: false,
      tension: 0.1,
    },
  ];

  // Add technical indicators
  if (indicators.sma.enabled) {
    const smaData = calculateSMA(prices, indicators.sma.period);
    datasets.push({
      label: `SMA ${indicators.sma.period}`,
      data: [...Array(indicators.sma.period - 1).fill(null), ...smaData],
      borderColor: "#2196F3",
      backgroundColor: "transparent",
      borderWidth: 2,
      fill: false,
      tension: 0.1,
    });
  }

  if (indicators.ema.enabled) {
    const emaData = calculateEMA(prices, indicators.ema.period);
    datasets.push({
      label: `EMA ${indicators.ema.period}`,
      data: [...Array(indicators.ema.period - 1).fill(null), ...emaData],
      borderColor: "#FF9800",
      backgroundColor: "transparent",
      borderWidth: 2,
      fill: false,
      tension: 0.1,
    });
  }

  if (indicators.bollinger.enabled) {
    const bollingerData = calculateBollingerBands(
      prices,
      indicators.bollinger.period,
      indicators.bollinger.stdDev
    );
    datasets.push(
      {
        label: "Bollinger Upper",
        data: [
          ...Array(indicators.bollinger.period - 1).fill(null),
          ...bollingerData.upper,
        ],
        borderColor: "#4CAF50",
        backgroundColor: "transparent",
        borderWidth: 1,
        fill: false,
        tension: 0.1,
      },
      {
        label: "Bollinger Middle",
        data: [
          ...Array(indicators.bollinger.period - 1).fill(null),
          ...bollingerData.middle,
        ],
        borderColor: "#9C27B0",
        backgroundColor: "transparent",
        borderWidth: 1,
        fill: false,
        tension: 0.1,
      },
      {
        label: "Bollinger Lower",
        data: [
          ...Array(indicators.bollinger.period - 1).fill(null),
          ...bollingerData.lower,
        ],
        borderColor: "#F44336",
        backgroundColor: "transparent",
        borderWidth: 1,
        fill: false,
        tension: 0.1,
      }
    );
  }

  // Volume chart data
  const volumeData = {
    labels: labels,
    datasets: [
      {
        label: "Volume",
        data: volumes,
        backgroundColor: "rgba(30, 60, 114, 0.6)",
        borderColor: "#ff8000",
        borderWidth: 1,
      },
    ],
  };

  const toggleIndicator = (indicator) => {
    setIndicators((prev) => ({
      ...prev,
      [indicator]: { ...prev[indicator], enabled: !prev[indicator].enabled },
    }));
  };

  const updateIndicatorPeriod = (indicator, period) => {
    setIndicators((prev) => ({
      ...prev,
      [indicator]: { ...prev[indicator], period: parseInt(period) },
    }));
  };

  const handleDrawingTool = (tool) => {
    setDrawingTool(tool);
    setIsDrawing(false);
  };

  const clearChart = () => {
    // This would clear the chart data
    console.log("Chart cleared");
  };

  useEffect(() => {
    if (onChartReady) {
      onChartReady({ type: "chartjs", data: { labels, prices, volumes } });
    }
  }, [onChartReady, labels, prices, volumes]);

  return (
    <div className="trading-chart-container">
      <div className="chart-toolbar">
        <div className="toolbar-section">
          <h4>Indicators</h4>
          <div className="indicator-controls">
            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.sma.enabled}
                onChange={() => toggleIndicator("sma")}
              />
              SMA
              {indicators.sma.enabled && (
                <input
                  type="number"
                  value={indicators.sma.period}
                  onChange={(e) => updateIndicatorPeriod("sma", e.target.value)}
                  min="1"
                  max="200"
                  className="period-input"
                />
              )}
            </label>

            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.ema.enabled}
                onChange={() => toggleIndicator("ema")}
              />
              EMA
              {indicators.ema.enabled && (
                <input
                  type="number"
                  value={indicators.ema.period}
                  onChange={(e) => updateIndicatorPeriod("ema", e.target.value)}
                  min="1"
                  max="200"
                  className="period-input"
                />
              )}
            </label>

            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.bollinger.enabled}
                onChange={() => toggleIndicator("bollinger")}
              />
              Bollinger Bands
            </label>

            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.rsi.enabled}
                onChange={() => toggleIndicator("rsi")}
              />
              RSI
            </label>

            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.macd.enabled}
                onChange={() => toggleIndicator("macd")}
              />
              MACD
            </label>

            <label className="indicator-toggle">
              <input
                type="checkbox"
                checked={indicators.volume.enabled}
                onChange={() => toggleIndicator("volume")}
              />
              Volume
            </label>
          </div>
        </div>

        <div className="toolbar-section">
          <h4>Drawing Tools</h4>
          <div className="drawing-tools">
            <button
              className={`tool-btn ${
                drawingTool === "trendline" ? "active" : ""
              }`}
              onClick={() => handleDrawingTool("trendline")}
            >
              📈 Trend Line
            </button>
            <button
              className={`tool-btn ${
                drawingTool === "fibonacci" ? "active" : ""
              }`}
              onClick={() => handleDrawingTool("fibonacci")}
            >
              📐 Fibonacci
            </button>
            <button
              className={`tool-btn ${
                drawingTool === "rectangle" ? "active" : ""
              }`}
              onClick={() => handleDrawingTool("rectangle")}
            >
              ⬜ Rectangle
            </button>
            <button
              className={`tool-btn ${
                drawingTool === "ellipse" ? "active" : ""
              }`}
              onClick={() => handleDrawingTool("ellipse")}
            >
              ⭕ Ellipse
            </button>
          </div>
        </div>

        <div className="toolbar-section">
          <h4>Chart Options</h4>
          <div className="chart-options">
            <button className="tool-btn" onClick={clearChart}>
              🗑️ Clear
            </button>
            <button
              className="tool-btn"
              onClick={() =>
                setPriceScale(priceScale === "right" ? "left" : "right")
              }
            >
              📊 Price Scale: {priceScale}
            </button>
          </div>
        </div>
      </div>

      <div className="chart-wrapper">
        <div className="chart-container" style={{ height: "400px" }}>
          <Line data={{ labels, datasets }} options={chartOptions} />
        </div>

        {indicators.volume.enabled && (
          <div
            className="volume-container"
            style={{ height: "150px", marginTop: "20px" }}
          >
            <Bar
              data={volumeData}
              options={{
                ...chartOptions,
                plugins: {
                  ...chartOptions.plugins,
                  title: {
                    display: true,
                    text: "Volume",
                    color: theme === "dark" ? "#d1d4dc" : "#333",
                  },
                },
                scales: {
                  ...chartOptions.scales,
                  y: {
                    ...chartOptions.scales.y,
                    title: {
                      display: true,
                      text: "Volume",
                      color: theme === "dark" ? "#d1d4dc" : "#333",
                    },
                  },
                },
              }}
            />
          </div>
        )}
      </div>

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
            {Object.entries(indicators)
              .filter(([_, config]) => config.enabled)
              .map(([name, _]) => name.toUpperCase())
              .join(", ") || "None"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChartComponent;
