import React, { useState } from "react";
import "./News.css";

const News = () => {
  const [selectedCategory, setSelectedCategory] = useState("all");

  const categories = [
    { id: "all", name: "All News" },
    { id: "bitcoin", name: "Bitcoin" },
    { id: "ethereum", name: "Ethereum" },
    { id: "defi", name: "DeFi" },
    { id: "nft", name: "NFT" },
    { id: "regulation", name: "Regulation" },
  ];

  const newsData = [
    {
      id: 1,
      title: "Bitcoin ETF Approval Expected by End of Year",
      summary:
        "Major financial institutions are optimistic about Bitcoin ETF approval, which could bring significant institutional investment.",
      category: "bitcoin",
      source: "CryptoNews",
      time: "2 hours ago",
      sentiment: "positive",
      image: "📈",
    },
    {
      id: 2,
      title: "Ethereum Layer 2 Solutions See Record Growth",
      summary:
        "Ethereum scaling solutions like Polygon and Arbitrum are experiencing unprecedented adoption rates.",
      category: "ethereum",
      source: "BlockchainDaily",
      time: "4 hours ago",
      sentiment: "positive",
      image: "🚀",
    },
    {
      id: 3,
      title: "New DeFi Protocol Launches with $100M TVL",
      summary:
        "A revolutionary DeFi protocol has launched with innovative yield farming mechanisms.",
      category: "defi",
      source: "DeFiPulse",
      time: "6 hours ago",
      sentiment: "positive",
      image: "💰",
    },
    {
      id: 4,
      title: "Regulatory Concerns in Asian Markets",
      summary:
        "Several Asian countries are considering stricter cryptocurrency regulations.",
      category: "regulation",
      source: "CryptoRegulation",
      time: "8 hours ago",
      sentiment: "negative",
      image: "⚠️",
    },
    {
      id: 5,
      title: "NFT Market Shows Signs of Recovery",
      summary:
        "The NFT market is showing positive momentum with increased trading volume.",
      category: "nft",
      source: "NFTInsider",
      time: "10 hours ago",
      sentiment: "positive",
      image: "🎨",
    },
    {
      id: 6,
      title: "Major Bank Announces Crypto Custody Services",
      summary:
        "Traditional banking giant enters the cryptocurrency space with new custody offerings.",
      category: "bitcoin",
      source: "FinanceToday",
      time: "12 hours ago",
      sentiment: "positive",
      image: "🏦",
    },
  ];

  const filteredNews =
    selectedCategory === "all"
      ? newsData
      : newsData.filter((news) => news.category === selectedCategory);

  return (
    <div className="news">
      <div className="news-header">
        <h1>Crypto News</h1>
        <p>
          Stay updated with the latest cryptocurrency news and market insights
        </p>
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

      <div className="news-grid">
        {filteredNews.map((article) => (
          <article
            key={article.id}
            className={`news-card ${article.sentiment}`}
          >
            <div className="news-image">
              <span className="emoji">{article.image}</span>
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
              <div className="news-actions">
                <button className="btn btn-primary">Read More</button>
                <button className="btn btn-outline">Share</button>
              </div>
            </div>
          </article>
        ))}
      </div>

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
