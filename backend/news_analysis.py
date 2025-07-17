"""
News analysis and sentiment processing for crypto trading
"""
import aiohttp
import asyncio
import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config import Config

logger = logging.getLogger(__name__)

class NewsAnalysisManager:
    """Manages news collection and sentiment analysis"""
    
    def __init__(self):
        self.news_cache = {}
        self.last_news_fetch = {}
        self.last_grok_fetch = {}
        self.last_cryptopanic_fetch = {}
        self.last_llm_request = {}
        
    async def grok_internet_search(self, symbol: str) -> Dict:
        """Perform internet search using Grok API for comprehensive market analysis"""
        current_time = time.time()
        
        # Check rate limiting
        if symbol in self.last_grok_fetch:
            time_since_last = current_time - self.last_grok_fetch[symbol]
            if time_since_last < Config.GROK_NEWS_INTERVAL:
                logger.info(f"⏰ Grok search rate limited for {symbol}, using cached data")
                return self.news_cache.get(symbol, {}).get('grok_data', {})
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for Grok search")
            return self.create_empty_news_data(symbol)
        
        try:
            # Create comprehensive search query
            search_query = f"""
            Analyze the current market conditions for {symbol} cryptocurrency. 
            Consider recent price movements, trading volume, market sentiment, 
            technical indicators, and any significant news or events that might 
            impact the price. Provide insights on:
            1. Current market sentiment (bullish/bearish/neutral)
            2. Key support and resistance levels
            3. Potential catalysts for price movement
            4. Risk factors to consider
            5. Short-term price outlook (next 1-4 hours)
            
            Focus on recent developments and actionable insights for short-term trading.
            """
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://crypto-trading-bot.com',
                    'X-Title': 'Crypto Trading Bot'
                }
                
                payload = {
                    'model': 'xai/grok-beta',
                    'messages': [
                        {
                            'role': 'user',
                            'content': search_query
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1500
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            # Parse the response for sentiment and insights
                            sentiment_score = self.extract_sentiment_from_grok(content)
                            
                            grok_data = {
                                'search_query': search_query,
                                'response': content,
                                'sentiment_score': sentiment_score,
                                'sentiment_label': self.get_sentiment_label(sentiment_score),
                                'key_insights': self.extract_key_insights(content),
                                'timestamp': datetime.now().isoformat(),
                                'source': 'grok_internet_search'
                            }
                            
                            # Update cache
                            if symbol not in self.news_cache:
                                self.news_cache[symbol] = {}
                            self.news_cache[symbol]['grok_data'] = grok_data
                            self.last_grok_fetch[symbol] = current_time
                            
                            logger.info(f" Grok search completed for {symbol}, sentiment: {grok_data['sentiment_label']}")
                            return grok_data
                        else:
                            logger.error(f" Invalid Grok response format for {symbol}")
                            return self.create_empty_news_data(symbol)
                    else:
                        logger.error(f" Grok API error for {symbol}: {response.status}")
                        return self.create_empty_news_data(symbol)
                        
        except asyncio.TimeoutError:
            logger.error(f"⏰ Grok search timeout for {symbol}")
            return self.create_empty_news_data(symbol)
        except Exception as e:
            logger.error(f" Grok search error for {symbol}: {e}")
            return self.create_empty_news_data(symbol)
    
    async def fallback_news_search(self, symbol: str) -> Dict:
        """Fallback news search when Grok is not available"""
        current_time = time.time()
        
        # Check rate limiting
        if symbol in self.last_llm_request:
            time_since_last = current_time - self.last_llm_request[symbol]
            if time_since_last < Config.GENERAL_API_INTERVAL:
                logger.info(f"⏰ Fallback search rate limited for {symbol}")
                return self.news_cache.get(symbol, {}).get('fallback_data', {})
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for fallback search")
            return self.create_empty_news_data(symbol)
        
        try:
            # Simplified search query for fallback
            search_query = f"""
            Provide a brief market analysis for {symbol} cryptocurrency.
            Focus on current sentiment and short-term outlook.
            Keep response under 200 words.
            """
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://crypto-trading-bot.com',
                    'X-Title': 'Crypto Trading Bot'
                }
                
                payload = {
                    'model': 'openai/gpt-3.5-turbo',
                    'messages': [
                        {
                            'role': 'user',
                            'content': search_query
                        }
                    ],
                    'temperature': 0.5,
                    'max_tokens': 300
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            fallback_data = {
                                'search_query': search_query,
                                'response': content,
                                'sentiment_score': 0.0,  # Neutral for fallback
                                'sentiment_label': 'neutral',
                                'key_insights': ['Fallback analysis provided'],
                                'timestamp': datetime.now().isoformat(),
                                'source': 'fallback_news_search'
                            }
                            
                            # Update cache
                            if symbol not in self.news_cache:
                                self.news_cache[symbol] = {}
                            self.news_cache[symbol]['fallback_data'] = fallback_data
                            self.last_llm_request[symbol] = current_time
                            
                            logger.info(f" Fallback search completed for {symbol}")
                            return fallback_data
                        else:
                            return self.create_empty_news_data(symbol)
                    else:
                        return self.create_empty_news_data(symbol)
                        
        except Exception as e:
            logger.error(f" Fallback search error for {symbol}: {e}")
            return self.create_empty_news_data(symbol)
    
    def create_empty_news_data(self, symbol: str) -> Dict:
        """Create empty news data structure"""
        return {
            'search_query': f"Market analysis for {symbol}",
            'response': f"No news data available for {symbol}",
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'key_insights': ['No data available'],
            'timestamp': datetime.now().isoformat(),
            'source': 'empty_data'
        }
    
    def extract_sentiment_from_grok(self, content: str) -> float:
        """Extract sentiment score from Grok response"""
        try:
            content_lower = content.lower()
            
            # Positive indicators
            positive_words = ['bullish', 'positive', 'upward', 'gains', 'rally', 'breakout', 'strong', 'buy', 'long']
            positive_count = sum(1 for word in positive_words if word in content_lower)
            
            # Negative indicators
            negative_words = ['bearish', 'negative', 'downward', 'losses', 'decline', 'breakdown', 'weak', 'sell', 'short']
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            # Calculate sentiment score (-1 to 1)
            total_words = positive_count + negative_count
            if total_words == 0:
                return 0.0
            
            sentiment_score = (positive_count - negative_count) / total_words
            return max(-1.0, min(1.0, sentiment_score))
            
        except Exception as e:
            logger.error(f" Error extracting sentiment: {e}")
            return 0.0
    
    def get_sentiment_label(self, sentiment_score: float) -> str:
        """Convert sentiment score to label"""
        if sentiment_score >= 0.3:
            return 'bullish'
        elif sentiment_score <= -0.3:
            return 'bearish'
        else:
            return 'neutral'
    
    def extract_key_insights(self, content: str) -> List[str]:
        """Extract key insights from content"""
        try:
            # Simple extraction - look for sentences with key terms
            sentences = content.split('.')
            insights = []
            
            key_terms = ['support', 'resistance', 'breakout', 'breakdown', 'trend', 'momentum', 'volume']
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(term in sentence_lower for term in key_terms):
                    insights.append(sentence.strip())
            
            return insights[:3]  # Limit to 3 insights
            
        except Exception as e:
            logger.error(f" Error extracting insights: {e}")
            return ['Analysis completed']
    
    async def get_news_data(self, symbol: str) -> Dict:
        """Get news data for a symbol"""
        # Try Grok first, then fallback
        grok_data = await self.grok_internet_search(symbol)
        
        if grok_data.get('source') == 'empty_data':
            fallback_data = await self.fallback_news_search(symbol)
            return fallback_data
        
        return grok_data
    
    def get_cached_news(self, symbol: str) -> Dict:
        """Get cached news data"""
        return self.news_cache.get(symbol, {})
    
    def clear_news_cache(self):
        """Clear news cache"""
        self.news_cache.clear()
        self.last_news_fetch.clear()
        self.last_grok_fetch.clear()
        self.last_cryptopanic_fetch.clear()
        self.last_llm_request.clear()
        logger.info(" News cache cleared")

# Import time for timestamp calculations
import time 