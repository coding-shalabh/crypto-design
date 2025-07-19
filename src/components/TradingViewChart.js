import React, { useEffect, useRef, memo } from 'react';
import './TradingViewChart.css';

const TradingViewChart = ({ symbol = 'BTCUSDT', timeframe = '1D', theme = 'dark' }) => {
  const containerRef = useRef(null);
  const isScriptLoaded = useRef(false);

  useEffect(() => {
    const loadScript = () => {
      return new Promise((resolve) => {
        if (isScriptLoaded.current || window.TradingView) {
          resolve();
          return;
        }
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => {
          isScriptLoaded.current = true;
          resolve();
        };
        script.onerror = () => {
          console.error('Failed to load TradingView script.');
        };
        document.body.appendChild(script);
      });
    };

    const initializeChart = () => {
      if (!window.TradingView || !containerRef.current) return;

      // Clear previous widget if it exists
      containerRef.current.innerHTML = '';

      new window.TradingView.widget({
        autosize: true,
        symbol: symbol,
        interval: timeframe,
        timezone: 'Etc/UTC',
        theme: theme,
        style: '1',
        locale: 'en',
        toolbar_bg: theme === 'dark' ? '#131722' : '#ffffff',
        enable_publishing: false,
        allow_symbol_change: true,
        container_id: containerRef.current.id,
        hide_side_toolbar: false,
        withdateranges: true,
        studies: [
          'Volume@tv-basicstudies'
        ],
        drawings_access: {
          type: 'black',
          tools: []
        },
        overrides: {
          'paneProperties.background': theme === 'dark' ? '#131722' : '#ffffff',
          'paneProperties.vertGridProperties.color': theme === 'dark' ? '#2A2E39' : '#E6E6E6',
          'paneProperties.horzGridProperties.color': theme === 'dark' ? '#2A2E39' : '#E6E6E6',
          'symbolWatermarkProperties.transparency': 90,
          'scalesProperties.textColor': theme === 'dark' ? '#AAA' : '#333',
          'mainSeriesProperties.candleStyle.upColor': '#26a69a',
          'mainSeriesProperties.candleStyle.downColor': '#ef5350',
        },
      });
    };

    loadScript().then(initializeChart);

    return () => {
      if (containerRef.current) {
        // Don't remove the script, just the widget
        // containerRef.current.innerHTML = '';
      }
    };
  }, [symbol, timeframe, theme]);

  return (
    <div className="tradingview-chart-container" ref={containerRef} id={`tradingview_chart_${symbol}_${timeframe}`}>
    </div>
  );
};

export default memo(TradingViewChart);
