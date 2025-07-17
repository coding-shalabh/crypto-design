import React, { useState, useEffect } from 'react';
import './OrderBook.css';

const OrderBook = ({ symbol = 'BTCUSDT', currentPrice = 0 }) => {
  const [orderBook, setOrderBook] = useState({
    asks: [],
    bids: []
  });

  // Generate mock order book data
  useEffect(() => {
    const generateOrderBook = () => {
      const asks = [];
      const bids = [];
      
      // Generate sell orders (asks) - prices above current price
      for (let i = 1; i <= 15; i++) {
        const price = currentPrice + (i * (currentPrice * 0.001));
        const size = Math.random() * 1000 + 100;
        const sum = asks.length > 0 ? asks[asks.length - 1].sum + size : size;
        
        asks.push({
          price: price.toFixed(2),
          size: size.toFixed(2),
          sum: sum.toFixed(2)
        });
      }
      
      // Generate buy orders (bids) - prices below current price
      for (let i = 1; i <= 15; i++) {
        const price = currentPrice - (i * (currentPrice * 0.001));
        const size = Math.random() * 1000 + 100;
        const sum = bids.length > 0 ? bids[bids.length - 1].sum + size : size;
        
        bids.push({
          price: price.toFixed(2),
          size: size.toFixed(2),
          sum: sum.toFixed(2)
        });
      }
      
      setOrderBook({ asks: asks.reverse(), bids });
    };

    if (currentPrice > 0) {
      generateOrderBook();
    }
  }, [currentPrice]);

  const formatNumber = (num) => {
    return parseFloat(num).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const getDepthPercentage = (sum, maxSum) => {
    return (sum / maxSum) * 100;
  };

  const maxSum = Math.max(
    ...orderBook.asks.map(ask => parseFloat(ask.sum)),
    ...orderBook.bids.map(bid => parseFloat(bid.sum))
  );

  return (
    <div className="orderbook">
      {/* Asks (Sell Orders) */}
      <div className="orderbook-asks">
        {orderBook.asks.map((ask, index) => (
          <div 
            key={`ask-${index}`} 
            className="orderbook-row ask"
            style={{
              background: `linear-gradient(to left, rgba(255, 0, 0, 0.1) ${getDepthPercentage(ask.sum, maxSum)}%, transparent ${getDepthPercentage(ask.sum, maxSum)}%)`
            }}
          >
            <span className="price ask-price">{formatNumber(ask.price)}</span>
            <span className="size">{formatNumber(ask.size)}</span>
            <span className="sum">{formatNumber(ask.sum)}</span>
          </div>
        ))}
      </div>

      {/* Current Price Separator */}
      <div className="current-price-row">
        <span className="current-price-label">Mark Price</span>
        <span className="current-price-value">{formatNumber(currentPrice)}</span>
        <span className="current-price-label">USDT</span>
      </div>

      {/* Bids (Buy Orders) */}
      <div className="orderbook-bids">
        {orderBook.bids.map((bid, index) => (
          <div 
            key={`bid-${index}`} 
            className="orderbook-row bid"
            style={{
              background: `linear-gradient(to left, rgba(0, 255, 0, 0.1) ${getDepthPercentage(bid.sum, maxSum)}%, transparent ${getDepthPercentage(bid.sum, maxSum)}%)`
            }}
          >
            <span className="price bid-price">{formatNumber(bid.price)}</span>
            <span className="size">{formatNumber(bid.size)}</span>
            <span className="sum">{formatNumber(bid.sum)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default OrderBook; 