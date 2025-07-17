import React, { useState, useEffect } from "react";
import "./News.css";

const News = () => {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [newsData, setNewsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newsSources, setNewsSources] = useState({ grok: [], cryptopanic: [] });

  const categories = [
    { id: "all", name: "All News" },
    { id: "grok", name: "Grok AI News" },
    { id: "cryptopanic", name: "CryptoPanic News" },
    { id: "bitcoin", name: "Bitcoin" },
    { id: "ethereum", name: "Ethereum" },
    { id: "defi", name: "DeFi" },
    { id: "nft", name: "NFT" },
    { id: "regulation", name: "Regulation" },
  ];

  // Fetch news data from WebSocket backend
  useEffect(() => {
    const fetchNewsData = async () => {
      try {
        setLoading(true);
        
        // Check if WebSocket is available
        if (window.wsRef && window.wsRef.current) {
          // Request news data from backend
          window.wsRef.current.send(JSON.stringify({
            type: 'get_news_data'
          }));
        } else {
          // Fallback to mock data if WebSocket not available
          setNewsData(getMockNewsData());
        }
      } catch (err) {
        console.error('Error fetching news:', err);
        setError('Failed to fetch news data');
        setNewsData(getMockNewsData());
      } finally {
        setLoading(false);
      }
    };

    fetchNewsData();

    // Listen for news data from WebSocket
    const handleNewsMessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'news_data_response') {
          console.log('Received news data:', data.data);
          processNewsData(data.data);
        }
      } catch (error) {
        console.error('Error parsing news message:', error);
      }
    };

    if (window.wsRef && window.wsRef.current) {
      window.wsRef.current.addEventListener('message', handleNewsMessage);
    }

    return () => {
      if (window.wsRef && window.wsRef.current) {
        window.wsRef.current.removeEventListener('message', handleNewsMessage);
      }
    };
  }, []);

  const processNewsData = (data) => {
    const processedNews = [];
    
    // Process Grok news data
    if (data.grok_news) {
      Object.entries(data.grok_news).forEach(([symbol, newsInfo]) => {
        if (newsInfo.headlines && Array.isArray(newsInfo.headlines)) {
          newsInfo.headlines.forEach((headline, index) => {
            processedNews.push({
              id: `grok_${symbol}_${index}`,
              title: headline.title,
              summary: headline.summary,
              category: "grok",
              source: "Grok AI Search",
              time: formatTime(headline.timestamp),
              sentiment: headline.sentiment || 'neutral',
              image: getSentimentEmoji(headline.sentiment),
              symbol: symbol,
              relevance_score: headline.relevance_score || 5,
              search_queries: newsInfo.search_queries_used || 0,
              overall_sentiment: newsInfo.sentiment_label || 'neutral',
              news_count: newsInfo.news_count || 0,
              timestamp: headline.timestamp
            });
          });
        }
      });
    }

    // Process CryptoPanic news data
    if (data.cryptopanic_news) {
      Object.entries(data.cryptopanic_news).forEach(([symbol, newsInfo]) => {
        if (newsInfo.headlines && Array.isArray(newsInfo.headlines)) {
          newsInfo.headlines.forEach((headline, index) => {
            processedNews.push({
              id: `cryptopanic_${symbol}_${index}`,
              title: headline.title,
              summary: headline.summary,
              category: "cryptopanic",
              source: "CryptoPanic",
              time: formatTime(headline.timestamp),
              sentiment: headline.sentiment || 'neutral',
              image: getSentimentEmoji(headline.sentiment),
              symbol: symbol,
              relevance_score: headline.relevance_score || 5,
              search_queries: 0, // CryptoPanic doesn't use search queries
              overall_sentiment: newsInfo.sentiment_label || 'neutral',
              news_count: newsInfo.news_count || 0,
              timestamp: headline.timestamp
            });
          });
        }
      });
    }

    setNewsData(processedNews);
    setLoading(false);
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Unknown time';
    
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minutes ago`;
      if (diffHours < 24) return `${diffHours} hours ago`;
      if (diffDays < 7) return `${diffDays} days ago`;
      
      return date.toLocaleDateString();
    } catch (error) {
      return 'Unknown time';
    }
  };

  const getSentimentEmoji = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      case 'bullish': return '🚀';
      case 'bearish': return '🐻';
      default: return '➡️';
    }
  };

  const getMockNewsData = () => {
    return [
      {
        id: 1,
        title: "Bitcoin ETF Approval Expected by End of Year",
        summary: "Major financial institutions are optimistic about Bitcoin ETF approval, which could bring significant institutional investment.",
        category: "bitcoin",
        source: "CryptoNews",
        time: "2 hours ago",
        sentiment: "positive",
        image: "📈",
        symbol: "BTCUSDT",
        relevance_score: 8,
        search_queries: 5,
        overall_sentiment: "positive",
        news_count: 15
      },
      {
        id: 2,
        title: "Ethereum Layer 2 Solutions See Record Growth",
        summary: "Ethereum scaling solutions like Polygon and Arbitrum are experiencing unprecedented adoption rates.",
        category: "ethereum",
        source: "BlockchainDaily",
        time: "4 hours ago",
        sentiment: "positive",
        image: "🚀",
        symbol: "ETHUSDT",
        relevance_score: 7,
        search_queries: 3,
        overall_sentiment: "positive",
        news_count: 12
      }
    ];
  };

  const filteredNews = newsData.filter((news) => {
    if (selectedCategory === "all") return true;
    if (selectedCategory === "grok") return news.category === "grok";
    if (selectedCategory === "cryptopanic") return news.category === "cryptopanic";
    return news.category === selectedCategory;
  });

  const getSourceStats = () => {
    const grokNews = newsData.filter(n => n.category === 'grok');
    const cryptopanicNews = newsData.filter(n => n.category === 'cryptopanic');
    
    return {
      grok: {
        count: grokNews.length,
        avgSentiment: grokNews.length > 0 ? 
          grokNews.reduce((sum, n) => sum + (n.sentiment === 'positive' ? 1 : n.sentiment === 'negative' ? -1 : 0), 0) / grokNews.length : 0
      },
      cryptopanic: {
        count: cryptopanicNews.length,
        avgSentiment: cryptopanicNews.length > 0 ? 
          cryptopanicNews.reduce((sum, n) => sum + (n.sentiment === 'positive' ? 1 : n.sentiment === 'negative' ? -1 : 0), 0) / cryptopanicNews.length : 0
      }
    };
  };

  const stats = getSourceStats();

  return (
    <div className="news">
      <div className="news-header">
        <h1>Crypto News</h1>
        <p>Stay updated with the latest cryptocurrency news and market insights</p>
        
        {/* News Source Stats */}
        <div className="news-stats">
          <div className="stat-item">
            <span className="stat-label">Grok AI News:</span>
            <span className="stat-value">{stats.grok.count} articles</span>
            <span className={`stat-sentiment ${stats.grok.avgSentiment > 0 ? 'positive' : stats.grok.avgSentiment < 0 ? 'negative' : 'neutral'}`}>
              {stats.grok.avgSentiment > 0 ? '📈' : stats.grok.avgSentiment < 0 ? '📉' : '➡️'}
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">CryptoPanic News:</span>
            <span className="stat-value">{stats.cryptopanic.count} articles</span>
            <span className={`stat-sentiment ${stats.cryptopanic.avgSentiment > 0 ? 'positive' : stats.cryptopanic.avgSentiment < 0 ? 'negative' : 'neutral'}`}>
              {stats.cryptopanic.avgSentiment > 0 ? '📈' : stats.cryptopanic.avgSentiment < 0 ? '📉' : '➡️'}
            </span>
          </div>
        </div>
      </div>

      <div className="news-controls">
        <div className="category-filter">
          {categories.map((category) => (
            <button
              key={category.id}
              className={`category-btn ${
                selectedCategory === category.id ? "active" : ""
              }`}
              onClick={() => setSelectedCategory(category.id)}
            >
              {category.name}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Fetching latest news...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      ) : (
        <div className="news-grid">
          {filteredNews.map((article) => (
            <article
              key={article.id}
              className={`news-card ${article.sentiment} ${article.category}`}
            >
              <div className="news-image">
                <span className="emoji">{article.image}</span>
                <div className="news-source-badge">
                  <span className="source-name">{article.source}</span>
                  {article.category === 'grok' && (
                    <span className="ai-badge">AI</span>
                  )}
                </div>
              </div>
              <div className="news-content">
                <div className="news-meta">
                  <span className="news-source">{article.source}</span>
                  <span className="news-time">{article.time}</span>
                  <span className={`sentiment-badge ${article.sentiment}`}>
                    {article.sentiment === "positive"
                      ? "📈"
                      : article.sentiment === "negative"
                      ? "📉"
                      : "➡️"}
                  </span>
                </div>
                <h3 className="news-title">{article.title}</h3>
                <p className="news-summary">{article.summary}</p>
                
                {/* Additional News Details */}
                <div className="news-details">
                  {article.symbol && (
                    <div className="detail-item">
                      <span className="detail-label">Symbol:</span>
                      <span className="detail-value">{article.symbol}</span>
                    </div>
                  )}
                  {article.relevance_score && (
                    <div className="detail-item">
                      <span className="detail-label">Relevance:</span>
                      <span className="detail-value">{article.relevance_score}/10</span>
                    </div>
                  )}
                  {article.category === 'grok' && article.search_queries && (
                    <div className="detail-item">
                      <span className="detail-label">Search Queries:</span>
                      <span className="detail-value">{article.search_queries}</span>
                    </div>
                  )}
                  {article.news_count && (
                    <div className="detail-item">
                      <span className="detail-label">Total News:</span>
                      <span className="detail-value">{article.news_count}</span>
                    </div>
                  )}
                </div>
                
                <div className="news-actions">
                  <button className="btn btn-primary">Read More</button>
                  <button className="btn btn-outline">Share</button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className="news-sidebar">
        <div className="trending-topics">
          <h3>Trending Topics</h3>
          <div className="topic-list">
            <div className="topic-item">
              <span className="topic-name">#BitcoinETF</span>
              <span className="topic-count">2.5K mentions</span>
            </div>
            <div className="topic-item">
              <span className="topic-name">#Ethereum</span>
              <span className="topic-count">1.8K mentions</span>
            </div>
            <div className="topic-item">
              <span className="topic-name">#DeFi</span>
              <span className="topic-count">1.2K mentions</span>
            </div>
            <div className="topic-item">
              <span className="topic-name">#CryptoRegulation</span>
              <span className="topic-count">950 mentions</span>
            </div>
          </div>
        </div>

        <div className="market-sentiment">
          <h3>Market Sentiment</h3>
          <div className="sentiment-overview">
            <div className="sentiment-item">
              <span className="sentiment-label">Overall Sentiment</span>
              <div className="sentiment-bar">
                <div
                  className="sentiment-fill positive"
                  style={{ width: "65%" }}
                ></div>
              </div>
              <span className="sentiment-value">65% Bullish</span>
            </div>
            <div className="sentiment-item">
              <span className="sentiment-label">News Volume</span>
              <div className="sentiment-bar">
                <div
                  className="sentiment-fill neutral"
                  style={{ width: "45%" }}
                ></div>
              </div>
              <span className="sentiment-value">Medium</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default News;
