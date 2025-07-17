import React, { useEffect, useRef, useState } from 'react';
import './TradingViewChart.css';
// Feather icons import
import { Zap, BarChart2, ArrowUp, ArrowDown, RefreshCw, Clock, CheckCircle, XCircle, TrendingUp, TrendingDown, FiRefreshCcw, FiBarChart2 } from 'react-icons/fi';

const TradingViewChart = ({ symbol = 'BTCUSDT', onPriceUpdate, onChartReady, timeframe = '1', positions = {} }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [isChartReady, setIsChartReady] = useState(false);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [currentTimeframe, setCurrentTimeframe] = useState(timeframe);
  const [chartError, setChartError] = useState(false);

  useEffect(() => {
    // Check if TradingView is already loaded
    if (window.TradingView) {
      initChart();
      return;
    }

    // Set a timeout to show error if chart doesn't load within 10 seconds
    const timeoutId = setTimeout(() => {
      if (!isChartReady && !chartError) {
        console.error('TradingView chart failed to load within timeout');
        setChartError(true);
      }
    }, 10000);

    // Load TradingView widget script
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      // Add a small delay to ensure the library is fully initialized
      setTimeout(() => {
        initChart();
      }, 100);
    };
    script.onerror = (error) => {
      console.error('Failed to load TradingView script:', error);
      setChartError(true);
      clearTimeout(timeoutId);
    };
    document.head.appendChild(script);

    return () => {
      clearTimeout(timeoutId);
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch (error) {
          console.error('Error removing chart:', error);
        }
      }
    };
  }, []);

  useEffect(() => {
    if (isChartReady && symbol) {
      updateSymbol();
    }
  }, [symbol, isChartReady]);

  useEffect(() => {
    if (isChartReady && currentTimeframe) {
      updateTimeframe();
    }
  }, [currentTimeframe, isChartReady]);

  useEffect(() => {
    if (isChartReady && positions) {
      updatePositionMarkers();
    }
  }, [positions, isChartReady, symbol]);

  const initChart = () => {
    if (!chartContainerRef.current) {
      console.error('Chart container not found');
      return;
    }

    if (!window.TradingView) {
      console.error('TradingView library not loaded');
      return;
    }

    try {
      // Create TradingView widget with Binance-style configuration
      const widget = new window.TradingView.widget({
      container: chartContainerRef.current,
      symbol: `BINANCE:${symbol}`,
      interval: currentTimeframe,
      timezone: 'Etc/UTC',
      theme: 'dark',
      style: '1',
      locale: 'en',
      toolbar_bg: '#1a1a1a',
      enable_publishing: false,
      allow_symbol_change: false,
      container_id: 'tradingview_chart',
      width: '100%',
      height: '100%',
      studies: [
        'MAExp@tv-basicstudies',
        'Volume@tv-basicstudies'
      ],
      disabled_features: [
        'use_localstorage_for_settings',
        'volume_force_overlay',
        'create_volume_indicator_by_default',
        'header_symbol_search',
        'header_settings',
        'header_compare',
        'header_undo_redo',
        'header_fullscreen_button',
        'header_screenshot',
        'timeframes_toolbar',
        'edit_buttons_in_legend',
        'context_menus',
        'border_around_the_chart',
        'header_saveload',
        'control_bar',
        'countdown',
        'display_market_status',
        'chart_property_page_background',
        'compare_symbol',
        'high_density_bars',
        'study_templates',
        'side_toolbar_in_fullscreen_mode'
      ],
      enabled_features: [
        'study_templates',
        'side_toolbar_in_fullscreen_mode'
      ],
      overrides: {
        'mainSeriesProperties.candleStyle.upColor': '#00ff00',
        'mainSeriesProperties.candleStyle.downColor': '#ff4444',
        'mainSeriesProperties.candleStyle.wickUpColor': '#00ff00',
        'mainSeriesProperties.candleStyle.wickDownColor': '#ff4444',
        'mainSeriesProperties.candleStyle.borderUpColor': '#00ff00',
        'mainSeriesProperties.candleStyle.borderDownColor': '#ff4444',
        'paneProperties.background': '#1a1a1a',
        'paneProperties.vertGridProperties.color': '#2a2a2a',
        'paneProperties.horzGridProperties.color': '#2a2a2a',
        'paneProperties.crossHairProperties.color': '#f0b90b',
        'paneProperties.crossHairProperties.style': 1,
        'scalesProperties.backgroundColor': '#1a1a1a',
        'scalesProperties.textColor': '#ffffff',
        'scalesProperties.borderColor': '#2a2a2a'
      },
      loading_screen: { backgroundColor: '#1a1a1a' },
      custom_css_url: 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.css',
      onChartReady: () => {
        chartRef.current = widget;
        setIsChartReady(true);
        if (onChartReady) {
          onChartReady(widget);
        }
        
        // Set up price update listener
        if (widget && widget.chart) {
          const chart = widget.chart();
          
          // Listen for crosshair move to get current price
          chart.onCrosshairMove().subscribe(
            null,
            (param) => {
              if (param && param.seriesPrices && param.seriesPrices.size > 0) {
                const price = param.seriesPrices.get(param.seriesPrices.keys().next().value);
                if (price && typeof price === 'number') {
                  setCurrentPrice(price);
                  
                  // Calculate price change (simplified - you might want to get this from your data source)
                  const previousPrice = currentPrice || price;
                  const change = ((price - previousPrice) / previousPrice) * 100;
                  setPriceChange(change);
                  
                  // Pass price update to parent
                  if (onPriceUpdate) {
                    onPriceUpdate({
                      currentPrice: price,
                      priceChange: change
                    });
                  }
                }
              }
            }
          );
        }
      }
    });
    } catch (error) {
      console.error('Error initializing TradingView chart:', error);
      setChartError(true);
    }
  };

  const updateSymbol = () => {
    if (chartRef.current && chartRef.current.chart) {
      try {
        console.log(`Updating chart symbol to: BINANCE:${symbol}`);
        const chart = chartRef.current.chart();
        chart.setSymbol(`BINANCE:${symbol}`, currentTimeframe);
        
        // Force a chart refresh
        setTimeout(() => {
          if (chart && chart.resetData) {
            chart.resetData();
          }
        }, 100);
        
        console.log(`Chart symbol updated successfully to: ${symbol}`);
      } catch (error) {
        console.error('Error updating chart symbol:', error);
      }
    } else {
      console.log('Chart not ready yet, will update when ready');
    }
  };

  const updateTimeframe = () => {
    if (chartRef.current && chartRef.current.chart) {
      try {
        console.log(`Updating chart timeframe to: ${currentTimeframe}`);
        const chart = chartRef.current.chart();
        chart.setResolution(currentTimeframe);
        
        // Force a chart refresh
        setTimeout(() => {
          if (chart && chart.resetData) {
            chart.resetData();
          }
        }, 100);
        
        console.log(`Chart timeframe updated successfully to: ${currentTimeframe}`);
      } catch (error) {
        console.error('Error updating chart timeframe:', error);
      }
    } else {
      console.log('Chart not ready yet, will update timeframe when ready');
    }
  };

  const updatePositionMarkers = () => {
    if (!chartRef.current || !chartRef.current.chart) return;

    try {
      const chart = chartRef.current.chart();
      
      // Clear existing markers
      chart.removeAllShapes();
      
      // Add position markers for current symbol
      if (positions[symbol]) {
        const position = positions[symbol];
        const isLong = position.amount > 0;
        const color = isLong ? '#00ff00' : '#ff4444';
        const text = `${isLong ? 'LONG' : 'SHORT'} ${Math.abs(position.amount).toFixed(4)} @ $${position.avg_price}`;
        
        // Get current time for marker placement
        const currentTime = Math.floor(Date.now() / 1000);
        
        // Add entry marker
        chart.createShape(
          { time: currentTime, price: position.avg_price },
          {
            shape: 'arrow_up',
            text: text,
            overrides: {
              backgroundColor: color,
              borderColor: color,
              textcolor: '#ffffff',
              fontsize: 12,
              bold: true
            }
          }
        );
        
        console.log(`Added position marker for ${symbol}: ${text}`);
      }
    } catch (error) {
      console.error('Error updating position markers:', error);
    }
  };

  // Handle price updates from WebSocket
  useEffect(() => {
    if (onPriceUpdate) {
      onPriceUpdate({ currentPrice, priceChange });
    }
  }, [currentPrice, priceChange, onPriceUpdate]);

  return (
    <div className="tradingview-chart-container">
      {chartError ? (
        <div className="chart-error-fallback">
          <div className="error-content">
            <FiBarChart2 size={48} />
            <h3>Chart Unavailable</h3>
            <p>TradingView chart failed to load. Please refresh the page or try again later.</p>
            <button 
              onClick={() => {
                setChartError(false);
                initChart();
              }}
              className="retry-button"
            >
              <FiRefreshCcw size={16} />
              Retry
            </button>
          </div>
        </div>
      ) : (
        <div 
          ref={chartContainerRef} 
          id="tradingview_chart" 
          className="tradingview-chart"
        />
      )}
    </div>
  );
};

export default TradingViewChart; 