import asyncio
import websockets
import json
import aiohttp
import time
from datetime import datetime, timedelta
import logging
import random
from typing import Dict, List, Optional
import math
import os
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingServer:
    def __init__(self):
        self.clients = set()
        self.paper_balance = 100000.0  # Starting balance - increased to $100k for more realistic trading
        self.positions = {}  # symbol -> position data
        self.recent_trades = []
        self.price_cache = {}
        self.crypto_data = {}
        self.processed_trade_ids = set()  # Track processed trade IDs to prevent duplicates
        
        # MongoDB connection for trade logging
        self.mongo_client = None
        self.mongo_db = None
        self.trades_collection = None
        self.setup_mongodb()
        
        # AI Analysis System - Multi-Stage Reasoning Engine
        self.target_pairs = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'BNBUSDT', 'SOLUSDT']
        self.ai_analysis_cache = {}  # Store recent AI analysis results
        self.last_analysis_time = {}  # Track when each pair was last analyzed
        self.analysis_interval = 60  # 1 minute between analyses (as per spec)
        self.high_confidence_threshold = 0.5  # Minimum confidence score to trigger alert (lowered for testing)
        
        # NEW: 15-minute cooldown after finding trading opportunity
        self.opportunity_cooldown = {}  # symbol -> cooldown end time
        self.cooldown_duration = 900  # 15 minutes in seconds
        
        # NEW: Trade direction monitoring for re-analysis
        self.accepted_trade_directions = {}  # symbol -> {'direction': 'LONG/SHORT', 'entry_price': float, 'accepted_time': timestamp}
        self.trade_reversal_threshold = 0.02  # 2% price movement against trade direction triggers re-analysis
        
        # Real-time analysis status tracking
        self.analysis_status = {}  # symbol -> current analysis status
        self.analysis_progress = {}
        
        # Market data storage for analysis
        self.candle_data = {}  # symbol -> recent candle data
        self.technical_indicators = {}  # symbol -> calculated indicators
        self.news_sentiment = {}  # symbol -> recent news sentiment
        self.social_sentiment = {}  # symbol -> social media sentiment
        
        # News and Internet Search System
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.cryptopanic_api_key = os.getenv('CRYPTOPANIC_API_KEY')
        self.news_cache = {}  # symbol -> recent news
        self.last_news_fetch = {}  # symbol -> last fetch time
        
        # UPDATED: Separate intervals for different news sources
        self.grok_news_interval = 1800  # 30 minutes for Grok internet search
        self.cryptopanic_news_interval = 60  # 1 minute for CryptoPanic news
        self.general_api_interval = 60  # 1 minute for other API requests (LLM calls)
        
        # Separate tracking for different API types
        self.last_grok_fetch = {}  # symbol -> last Grok fetch time
        self.last_cryptopanic_fetch = {}  # symbol -> last CryptoPanic fetch time
        self.last_llm_request = {}  # symbol -> last LLM request time
        
        self.pending_trades = {}  # symbol -> pending trade data for 30min wait
        
        # Trade acceptance system
        self.accepted_trades = {}  # symbol -> accepted trade data
        self.trade_wait_time = 1800  # 30 minutes in seconds
        
        # Analysis control system
        self.analysis_enabled = False  # Analysis only starts when user clicks start button
        self.analysis_start_time = None
        
        # Store trade entry details for comprehensive logging
        self.trade_entries = {}  # symbol -> entry details for logging when closed
        
        # Trading Bot System
        self.bot_enabled = False
        self.bot_config = {
            'max_trades_per_day': 10,
            'trade_amount_usdt': 50,
            'profit_target_usd': 2,
            'stop_loss_usd': 1,
            'trailing_enabled': True,
            'trailing_trigger_usd': 1,
            'trailing_distance_usd': 0.5,
            'trade_interval_secs': 60,
            'max_concurrent_trades': 3,
            'cooldown_secs': 300,
            'allowed_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            'ai_confidence_threshold': 0.1,
            'run_time_minutes': 180,
            'test_mode': False,
            'risk_per_trade_percent': 1.0,
            'slippage_tolerance_percent': 0.1,
            'signal_sources': ['gpt', 'claude'],
            'manual_approval_mode': False
        }
        
        # Bot state tracking
        self.bot_start_time = None
        self.bot_trades_today = 0
        self.bot_last_trade_reset = time.time()
        self.bot_active_trades = {}  # symbol -> trade details
        self.bot_pair_status = {}  # symbol -> 'idle', 'in_trade', 'cooldown'
        self.bot_cooldown_end = {}  # symbol -> cooldown end timestamp
        self.bot_trailing_stops = {}  # symbol -> trailing stop details
        self.bot_trade_history = []  # List of completed trades
        self.bot_total_profit = 0.0
        self.bot_total_trades = 0
        self.bot_winning_trades = 0

    def setup_mongodb(self):
        """Setup MongoDB connection for trade logging"""
        try:
            # Try to connect to MongoDB (will work even if not available)
            mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_db = self.mongo_client['crypto_trading']
            self.trades_collection = self.mongo_db['trades']
            
            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully")
            
            # Create indexes for better query performance
            self.trades_collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.trades_collection.create_index([("trade_id", 1)], unique=True)
            self.trades_collection.create_index([("status", 1)])
            
        except Exception as e:
            logger.warning(f"⚠️ MongoDB not available: {e}")
            logger.info("📝 Trade logging will be local only (no MongoDB)")
            self.mongo_client = None
            self.mongo_db = None
            self.trades_collection = None

    async def log_trade_to_mongodb(self, trade_data: Dict):
        """Log comprehensive trade data to MongoDB"""
        if not self.trades_collection:
            logger.info("📝 MongoDB not available, skipping trade logging")
            return
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now().isoformat()
            
            # Add trade_id if not present
            if 'trade_id' not in trade_data:
                trade_data['trade_id'] = f"trade_{int(time.time())}_{trade_data.get('symbol', 'UNKNOWN')}"
            
            # Insert trade record
            result = self.trades_collection.insert_one(trade_data)
            logger.info(f"📝 Trade logged to MongoDB with ID: {result.inserted_id}")
            
        except Exception as e:
            logger.error(f"❌ Error logging trade to MongoDB: {e}")

    async def log_closed_trade_comprehensive(self, symbol: str, position: Dict, close_price: float, close_value: float, profit_loss: float):
        """Log comprehensive trade details when a position is closed"""
        try:
            # Get entry details
            entry_details = self.trade_entries.get(symbol, {})
            
            # Calculate comprehensive trade data
            entry_price = position.get('avg_price', 0)
            entry_value = position.get('amount', 0) * entry_price
            balance_before = self.paper_balance - profit_loss
            balance_after = self.paper_balance
            
            # Get current analysis if available
            current_analysis = self.ai_analysis_cache.get(symbol, {})
            
            # Create comprehensive trade log
            trade_log = {
                'trade_id': f"closed_trade_{int(time.time())}_{symbol}",
                'symbol': symbol,
                'status': 'closed',
                'position_type': position.get('direction', 'unknown'),
                'entry_details': {
                    'price': entry_price,
                    'amount': position.get('amount', 0),
                    'value': entry_value,
                    'timestamp': entry_details.get('entry_timestamp', datetime.now().isoformat()),
                    'trade_type': entry_details.get('trade_type', 'manual'),
                    'confidence_score': entry_details.get('confidence_score', 0),
                    'analysis_id': entry_details.get('analysis_id', None)
                },
                'exit_details': {
                    'price': close_price,
                    'amount': position.get('amount', 0),
                    'value': close_value,
                    'timestamp': datetime.now().isoformat(),
                    'exit_reason': 'manual_close'
                },
                'profit_loss': {
                    'absolute': profit_loss,
                    'percentage': (profit_loss / entry_value * 100) if entry_value > 0 else 0,
                    'currency': 'USDT'
                },
                'balance_changes': {
                    'before': balance_before,
                    'after': balance_after,
                    'change': profit_loss
                },
                'trade_analysis': {
                    'market_conditions': current_analysis.get('market_data', {}),
                    'claude_analysis': current_analysis.get('claude_analysis', {}),
                    'gpt_analysis': current_analysis.get('gpt_analysis', {}),
                    'technical_indicators': current_analysis.get('market_data', {}).get('indicators', {})
                },
                'execution_notes': {
                    'entry_strategy': entry_details.get('strategy', 'manual'),
                    'exit_strategy': 'manual_close',
                    'risk_management': entry_details.get('risk_management', {}),
                    'market_sentiment': current_analysis.get('claude_analysis', {}).get('bias', 'neutral'),
                    'confidence_at_entry': entry_details.get('confidence_score', 0),
                    'hold_duration_seconds': int(time.time()) - entry_details.get('entry_timestamp_unix', time.time())
                },
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'platform': 'crypto_trading_v1'
                }
            }
            
            # Log to MongoDB
            await self.log_trade_to_mongodb(trade_log)
            
            # Also add to recent trades for immediate display
            self.recent_trades.insert(0, {
                'id': len(self.recent_trades) + 1,
                'symbol': symbol,
                'direction': 'close',
                'amount': position.get('amount', 0),
                'price': close_price,
                'value': close_value,
                'position_type': position.get('direction', 'unknown'),
                'profit_loss': profit_loss,
                'timestamp': datetime.now().isoformat(),
                'trade_id': trade_log['trade_id']
            })
            
            # Clean up entry details
            if symbol in self.trade_entries:
                del self.trade_entries[symbol]
            
            logger.info(f"📊 Comprehensive trade log created for {symbol}: P&L ${profit_loss:,.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error creating comprehensive trade log: {e}")

    async def fetch_crypto_data(self):
        """Fetch real crypto data from Binance API for accurate prices"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get 24hr ticker price change statistics from Binance
                url = "https://api.binance.com/api/v3/ticker/24hr"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Filter for USDT pairs and popular cryptocurrencies
                        popular_symbols = [
                            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 
                            'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT',
                            'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'XLMUSDT', 'VETUSDT',
                            'FILUSDT', 'ATOMUSDT', 'ALGOUSDT', 'XMRUSDT', 'TRXUSDT'
                        ]
                        
                        filtered_data = [item for item in data if item['symbol'] in popular_symbols]
                        
                        # Update crypto data from Binance API
                        for item in filtered_data:
                            symbol = item['symbol']
                            
                            # Extract base asset name (remove USDT)
                            base_asset = symbol.replace('USDT', '')
                            
                            self.crypto_data[symbol] = {
                                'id': symbol.lower(),
                                'symbol': symbol,
                                'name': base_asset,
                                'current_price': float(item['lastPrice']),
                                'market_cap': float(item['quoteVolume']),  # 24h volume in USDT
                                'volume_24h': float(item['volume']),
                                'price_change_24h': float(item['priceChange']),
                                'price_change_percentage_24h': float(item['priceChangePercent']),
                                'market_cap_rank': 0,  # Binance doesn't provide this
                                'last_updated': datetime.now().isoformat()
                            }
                            
                            # Update price cache with real-time Binance prices
                            self.price_cache[symbol] = {
                                'price': float(item['lastPrice']),
                                'change_24h': float(item['priceChangePercent']),
                                'volume': float(item['volume']),
                                'timestamp': time.time()
                            }
                        
                        logger.info(f"Updated crypto data for {len(filtered_data)} coins from Binance")
                        # Log some key prices for verification
                        btc_price = self.price_cache.get('BTCUSDT', {}).get('price', 'N/A')
                        eth_price = self.price_cache.get('ETHUSDT', {}).get('price', 'N/A')
                        logger.info(f"Current Binance prices - BTC: ${btc_price}, ETH: ${eth_price}")
                        logger.info(f"Price cache keys: {list(self.price_cache.keys())}")
                        logger.info(f"Sample price data: {list(self.price_cache.items())[:3]}")
                        return True
                    else:
                        logger.error(f"Failed to fetch crypto data: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            return False

    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow + signal:
            return {"line": 0, "signal": 0, "hist": 0}
        
        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD line)
        macd_values = []
        for i in range(slow, len(prices)):
            ema_f = self.calculate_ema(prices[:i+1], fast)
            ema_s = self.calculate_ema(prices[:i+1], slow)
            macd_values.append(ema_f - ema_s)
        
        signal_line = self.calculate_ema(macd_values, signal) if len(macd_values) >= signal else macd_line
        histogram = macd_line - signal_line
        
        return {
            "line": round(macd_line, 2),
            "signal": round(signal_line, 2),
            "hist": round(histogram, 2)
        }

    def calculate_vwap(self, candles: List[Dict]) -> float:
        """Calculate Volume Weighted Average Price"""
        if not candles:
            return 0
        
        total_volume = sum(candle.get('volume', 0) for candle in candles)
        if total_volume == 0:
            return candles[-1].get('close', 0) if candles else 0
        
        vwap = sum(
            (candle.get('high', 0) + candle.get('low', 0) + candle.get('close', 0)) / 3 * candle.get('volume', 0)
            for candle in candles
        ) / total_volume
        
        return round(vwap, 2)

    def calculate_volatility(self, prices: List[float], period: int = 20) -> float:
        """Calculate price volatility (standard deviation)"""
        if len(prices) < period:
            return 0
        
        recent_prices = prices[-period:]
        mean_price = sum(recent_prices) / len(recent_prices)
        
        variance = sum((price - mean_price) ** 2 for price in recent_prices) / len(recent_prices)
        volatility = math.sqrt(variance)
        
        return round(volatility, 2)

    async def grok_internet_search(self, symbol: str) -> Dict:
        """Step 1: Grok Internet Search - Real-time news and market intelligence"""
        try:
            # Check if we should fetch new Grok data (30-minute interval)
            current_time = time.time()
            last_grok_fetch = self.last_grok_fetch.get(symbol, 0)
            
            if current_time - last_grok_fetch < self.grok_news_interval:
                # Return cached data if available
                if symbol in self.news_cache:
                    cached_data = self.news_cache[symbol]
                    if 'grok_data' in cached_data:
                        remaining_time = int((self.grok_news_interval - (current_time - last_grok_fetch)) / 60)
                        logger.info(f"📰 Using cached Grok data for {symbol} (next fetch in {remaining_time} minutes)")
                        return cached_data['grok_data']
                
                # If no cached data, return empty structure
                logger.info(f"📰 No cached Grok data for {symbol}, skipping fetch (next fetch in {int((self.grok_news_interval - (current_time - last_grok_fetch)) / 60)} minutes)")
                return self.create_empty_news_data(symbol)
            
            if not self.openrouter_api_key:
                logger.warning("OpenRouter API key not found, using fallback news search")
                return await self.fallback_news_search(symbol)
            
            # Update last fetch time
            self.last_grok_fetch[symbol] = current_time
            logger.info(f"🔍 Fetching fresh Grok data for {symbol} (30-minute interval)")
            
            base_asset = symbol.replace('USDT', '')
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Comprehensive search queries for crypto analysis
            search_queries = [
                f"latest {base_asset} Bitcoin cryptocurrency news today {current_time_str}",
                f"{base_asset} crypto price analysis market sentiment",
                f"cryptocurrency {base_asset} trading volume market cap",
                f"Bitcoin {base_asset} regulation news United States Trump",
                f"crypto market {base_asset} institutional adoption",
                f"{base_asset} blockchain technology developments",
                f"cryptocurrency {base_asset} DeFi yield farming",
                f"Bitcoin {base_asset} ETF approval status",
                f"crypto {base_asset} exchange listings partnerships",
                f"cryptocurrency {base_asset} mining difficulty network",
                f"Bitcoin {base_asset} halving countdown impact",
                f"crypto {base_asset} whale movements large transactions",
                f"cryptocurrency {base_asset} technical analysis charts",
                f"Bitcoin {base_asset} institutional investors",
                f"crypto {base_asset} regulatory news SEC CFTC",
                f"cryptocurrency {base_asset} adoption mainstream",
                f"Bitcoin {base_asset} macroeconomic factors inflation",
                f"crypto {base_asset} market manipulation concerns",
                f"cryptocurrency {base_asset} security vulnerabilities",
                f"Bitcoin {base_asset} environmental impact mining"
            ]
            
            all_news = []
            sentiment_scores = []
            
            async with aiohttp.ClientSession() as session:
                for query in search_queries[:5]:  # Limit to 5 queries to avoid rate limits
                    try:
                        # Grok API call for internet search
                        grok_url = "https://openrouter.ai/api/v1/chat/completions"
                        headers = {
                            "Authorization": f"Bearer {self.openrouter_api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        payload = {
                            "model": "x-ai/grok-4",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"Search the internet for: {query}. Return only the most recent and relevant news headlines with brief summaries. Focus on breaking news, price movements, regulatory updates, and market sentiment. Format as JSON with 'headlines' array containing 'title', 'summary', 'sentiment' (positive/negative/neutral), and 'relevance_score' (0-10)."
                                }
                            ],
                            "max_tokens": 1000,
                            "temperature": 0.3
                        }
                        
                        async with session.post(grok_url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                result = await response.json()
                                content = result['choices'][0]['message']['content']
                                
                                # Parse the response
                                try:
                                    # Try to extract JSON from the response
                                    if '{' in content and '}' in content:
                                        start = content.find('{')
                                        end = content.rfind('}') + 1
                                        json_str = content[start:end]
                                        news_data = json.loads(json_str)
                                        
                                        if 'headlines' in news_data:
                                            for headline in news_data['headlines']:
                                                all_news.append({
                                                    'title': headline.get('title', ''),
                                                    'summary': headline.get('summary', ''),
                                                    'sentiment': headline.get('sentiment', 'neutral'),
                                                    'relevance_score': headline.get('relevance_score', 5),
                                                    'source': 'Grok Internet Search',
                                                    'timestamp': datetime.now().isoformat()
                                                })
                                                
                                                # Calculate sentiment score
                                                sentiment_map = {'positive': 1, 'negative': -1, 'neutral': 0}
                                                sentiment_scores.append(sentiment_map.get(headline.get('sentiment', 'neutral'), 0))
                                except json.JSONDecodeError:
                                    # Fallback: extract information from text
                                    logger.warning(f"Failed to parse Grok JSON response for {symbol}")
                                    all_news.append({
                                        'title': f"Grok Search: {query}",
                                        'summary': content[:200] + "..." if len(content) > 200 else content,
                                        'sentiment': 'neutral',
                                        'relevance_score': 5,
                                        'source': 'Grok Internet Search',
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    sentiment_scores.append(0)
                            else:
                                # Log the response body for debugging
                                error_text = await response.text()
                                logger.warning(f"Grok API request failed for {symbol}: {response.status} - {error_text}")
                                
                    except Exception as e:
                        logger.error(f"Error in Grok search for {symbol}: {e}")
                        continue
                    
                    # Small delay between requests
                    await asyncio.sleep(1)
            
            # Calculate overall sentiment
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            
            return {
                'symbol': symbol,
                'news_count': len(all_news),
                'headlines': all_news[:10],  # Keep top 10 headlines
                'overall_sentiment': avg_sentiment,
                'sentiment_label': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral',
                'search_queries_used': len(search_queries[:5]),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Grok internet search for {symbol}: {e}")
            return await self.fallback_news_search(symbol)

    async def fallback_news_search(self, symbol: str) -> Dict:
        """Fallback news search when Grok is not available"""
        try:
            # Check if we should fetch new CryptoPanic data (1-minute interval)
            current_time = time.time()
            last_cryptopanic_fetch = self.last_cryptopanic_fetch.get(symbol, 0)
            
            if current_time - last_cryptopanic_fetch < self.cryptopanic_news_interval:
                # Return cached data if available
                if symbol in self.news_cache:
                    cached_data = self.news_cache[symbol]
                    if 'cryptopanic_data' in cached_data:
                        remaining_time = int((self.cryptopanic_news_interval - (current_time - last_cryptopanic_fetch)))
                        logger.info(f"📰 Using cached CryptoPanic data for {symbol} (next fetch in {remaining_time} seconds)")
                        return cached_data['cryptopanic_data']
                
                # If no cached data, return empty structure
                logger.info(f"📰 No cached CryptoPanic data for {symbol}, skipping fetch (next fetch in {int((self.cryptopanic_news_interval - (current_time - last_cryptopanic_fetch)))} seconds)")
                return self.create_empty_news_data(symbol)
            
            # Update last fetch time
            self.last_cryptopanic_fetch[symbol] = current_time
            logger.info(f"🔍 Fetching fresh CryptoPanic data for {symbol} (1-minute interval)")
            
            base_asset = symbol.replace('USDT', '')
            
            # Use CryptoPanic API as fallback
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={self.cryptopanic_api_key}&currencies={base_asset.lower()}&public=true"
            headers = {}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        news_items = data.get('results', [])
                        
                        headlines = []
                        sentiment_scores = []
                        
                        for item in news_items[:10]:
                            headlines.append({
                                'title': item.get('title', ''),
                                'summary': item.get('body', '')[:200],
                                'sentiment': 'neutral',  # CryptoPanic doesn't provide sentiment
                                'relevance_score': 7,
                                'source': 'CryptoPanic',
                                'timestamp': item.get('published_at', datetime.now().isoformat())
                            })
                            sentiment_scores.append(0)
                        
                        return {
                            'symbol': symbol,
                            'news_count': len(headlines),
                            'headlines': headlines,
                            'overall_sentiment': 0,
                            'sentiment_label': 'neutral',
                            'search_queries_used': 0,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"CryptoPanic API failed for {symbol}: {response.status}")
                        return self.create_empty_news_data(symbol)
                        
        except Exception as e:
            logger.error(f"Error in fallback news search for {symbol}: {e}")
            return self.create_empty_news_data(symbol)

    def create_empty_news_data(self, symbol: str) -> Dict:
        """Create empty news data structure"""
        return {
            'symbol': symbol,
            'news_count': 0,
            'headlines': [],
            'overall_sentiment': 0,
            'sentiment_label': 'neutral',
            'search_queries_used': 0,
            'timestamp': datetime.now().isoformat()
        }

    async def collect_market_data(self, symbol: str) -> Dict:
        """Step 1: Input Collection - Live Market Snapshot with Real-time News"""
        try:
            # Get current price data
            price_data = self.price_cache.get(symbol, {})
            if not price_data:
                logger.error(f"No price data available for {symbol}")
                return None
            
            current_price = price_data['price']
            
            # Generate some sample candle data for technical analysis
            # In a real implementation, you'd fetch this from Binance API
            base_price = current_price
            candles = []
            for i in range(100):
                # Simulate price movement
                change = random.uniform(-0.02, 0.02) * base_price
                high = base_price + abs(change) * 1.1
                low = base_price - abs(change) * 0.9
                close = base_price + change
                volume = random.uniform(1000, 10000)
                
                candles.append({
                    'open': base_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume,
                    'timestamp': time.time() - (100 - i) * 3600  # Hourly data
                })
                base_price = close
            
            # Calculate technical indicators
            prices = [candle['close'] for candle in candles]
            volumes = [candle['volume'] for candle in candles]
            
            indicators = {
                'EMA_9': self.calculate_ema(prices, 9),
                'EMA_21': self.calculate_ema(prices, 21),
                'RSI_14': self.calculate_rsi(prices, 14),
                'VWAP': self.calculate_vwap(candles),
                'Volatility': self.calculate_volatility(prices, 20),
                'MACD': self.calculate_macd(prices)
            }
            
            # Fetch real-time news using Grok internet search
            await self.broadcast_analysis_status(symbol, 'fetching_news', '🌐 Fetching real-time news and market intelligence...')
            news_data = await self.grok_internet_search(symbol)
            
            # Store news data in cache with proper categorization
            if symbol not in self.news_cache:
                self.news_cache[symbol] = {}
            
            # Store based on the source
            if news_data.get('search_queries_used', 0) > 0:
                # This is Grok data
                self.news_cache[symbol]['grok_data'] = news_data
            else:
                # This is CryptoPanic data
                self.news_cache[symbol]['cryptopanic_data'] = news_data
            
            # Update general news fetch time
            self.last_news_fetch[symbol] = time.time()
            
            await self.broadcast_analysis_status(symbol, 'news_collected', f'📰 News collected: {news_data["news_count"]} headlines, {news_data["sentiment_label"]} sentiment')
            
            # Simulate social sentiment data
            social_data = {
                'x_mentions': random.randint(1000, 50000),
                'reddit_posts': random.randint(100, 2000),
                'telegram_messages': random.randint(5000, 50000),
                'sentiment_score': random.uniform(-1, 1)
            }
            
            return {
                'symbol': symbol,
                'price': current_price,
                'change_24h': price_data['change_24h'],
                'volume_24h': price_data['volume'],
                'timestamp': datetime.now().isoformat(),
                'indicators': indicators,
                'news_sentiment': news_data,
                'social_sentiment': social_data,
                'market_cap': self.crypto_data.get(symbol, {}).get('market_cap', 0),
                'candles': candles[-20:]  # Keep last 20 candles for analysis
            }
            
        except Exception as e:
            logger.error(f"Error collecting market data for {symbol}: {e}")
            return None

    async def grok_sentiment_analysis(self, symbol: str) -> Dict:
        """Grok - Market Sentiment & News Intelligence"""
        try:
            # Get current price data
            current_price = self.price_cache.get(symbol, {}).get('price', 0)
            change_24h = self.price_cache.get(symbol, {}).get('change_24h', 0)
            volume = self.price_cache.get(symbol, {}).get('volume', 0)
            
            # Simulate news sentiment analysis (in real implementation, this would call Grok API)
            sentiment_options = ['Bullish', 'Bearish', 'Neutral']
            volatility_options = ['High', 'Medium', 'Low']
            
            # Generate realistic sentiment based on price movement
            if change_24h > 5:
                sentiment = 'Bullish'
            elif change_24h < -5:
                sentiment = 'Bearish'
            else:
                sentiment = random.choice(sentiment_options)
            
            volatility = random.choice(volatility_options)
            
            # Generate mock news headlines
            news_headlines = [
                f"{symbol.replace('USDT', '')} shows strong momentum with {change_24h:.2f}% gain",
                f"Trading volume for {symbol.replace('USDT', '')} reaches {volume:,.0f}",
                f"Market sentiment for {symbol.replace('USDT', '')} remains {sentiment.lower()}"
            ]
            
            return {
                'symbol': symbol,
                'news_summary': news_headlines,
                'market_sentiment': sentiment,
                'volatility_snapshot': volatility,
                'reasoning': f"Based on {change_24h:.2f}% 24h change and {volatility.lower()} volatility",
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in Grok sentiment analysis for {symbol}: {e}")
            return None

    async def claude_deep_analysis(self, market_data: Dict) -> Dict:
        """Step 2: Claude Sonnet 4 — Deep Strategy Brain"""
        try:
            symbol = market_data['symbol']
            
            # Check if we should make a new LLM request (1-minute interval)
            current_time = time.time()
            last_llm_request = self.last_llm_request.get(symbol, 0)
            
            if current_time - last_llm_request < self.general_api_interval:
                # Return cached analysis if available
                if symbol in self.news_cache:
                    cached_data = self.news_cache[symbol]
                    if 'claude_analysis' in cached_data:
                        remaining_time = int((self.general_api_interval - (current_time - last_llm_request)))
                        logger.info(f"🤖 Using cached Claude analysis for {symbol} (next request in {remaining_time} seconds)")
                        return cached_data['claude_analysis']
                
                # If no cached data, proceed with local analysis
                logger.info(f"🤖 No cached Claude analysis for {symbol}, using local analysis (next request in {int((self.general_api_interval - (current_time - last_llm_request)))} seconds)")
            
            # Update last LLM request time
            self.last_llm_request[symbol] = current_time
            logger.info(f"🤖 Making fresh Claude analysis for {symbol} (1-minute interval)")
            
            price = market_data['price']
            indicators = market_data['indicators']
            news_sentiment = market_data['news_sentiment']
            social_sentiment = market_data['social_sentiment']
            
            # Use Claude Sonnet 4 for analysis if API key is available
            if self.openrouter_api_key:
                try:
                    import aiohttp
                    
                    async with aiohttp.ClientSession() as session:
                        claude_url = "https://openrouter.ai/api/v1/chat/completions"
                        headers = {
                            "Authorization": f"Bearer {self.openrouter_api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        # Create analysis prompt
                        analysis_prompt = f"""
                        Analyze the following cryptocurrency market data for {symbol}:
                        
                        Current Price: ${price}
                        RSI: {indicators['RSI_14']}
                        EMA-9: ${indicators['EMA_9']}
                        EMA-21: ${indicators['EMA_21']}
                        MACD: {indicators['MACD']}
                        VWAP: ${indicators['VWAP']}
                        Volatility: {indicators['Volatility']}
                        24h Change: {market_data['change_24h']}%
                        
                        News Sentiment: {news_sentiment.get('sentiment_label', 'neutral')}
                        Social Sentiment: {social_sentiment.get('sentiment_score', 0)}
                        
                        Provide a comprehensive analysis with:
                        1. Technical bias (bullish/bearish/neutral)
                        2. Confidence score (0.1-0.95)
                        3. Detailed reasoning
                        4. Suggested trading direction (LONG/SHORT/NO_TRADE)
                        
                        Return as JSON with keys: bias, confidence_score, reasoning, suggested_direction
                        """
                        
                        payload = {
                            "model": "anthropic/claude-sonnet-4",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": analysis_prompt
                                }
                            ],
                            "max_tokens": 1000,
                            "temperature": 0.3
                        }
                        
                        async with session.post(claude_url, headers=headers, json=payload) as response:
                            if response.status == 200:
                                result = await response.json()
                                content = result['choices'][0]['message']['content']
                                
                                # Parse Claude's response
                                try:
                                    if '{' in content and '}' in content:
                                        start = content.find('{')
                                        end = content.rfind('}') + 1
                                        json_str = content[start:end]
                                        claude_result = json.loads(json_str)
                                        
                                        return {
                                            "bias": claude_result.get('bias', 'neutral'),
                                            "reasoning": claude_result.get('reasoning', 'Analysis completed'),
                                            "confidence_score": float(claude_result.get('confidence_score', 0.5)),
                                            "suggested_direction": claude_result.get('suggested_direction', 'NO_TRADE'),
                                            "technical_analysis": {
                                                "ema_trend": "bullish" if indicators['EMA_9'] > indicators['EMA_21'] else "bearish",
                                                "rsi_level": indicators['RSI_14'],
                                                "macd_signal": "bullish" if indicators['MACD']['hist'] > 0 else "bearish",
                                                "vwap_position": "above" if price > indicators['VWAP'] else "below",
                                                "volatility": indicators['Volatility']
                                            },
                                            "sentiment_analysis": {
                                                "news_bias": news_sentiment.get('sentiment_label', 'neutral'),
                                                "social_bias": "bullish" if social_sentiment.get('sentiment_score', 0) > 0.2 else "bearish" if social_sentiment.get('sentiment_score', 0) < -0.2 else "neutral",
                                                "news_score": 0,
                                                "social_sentiment_score": social_sentiment.get('sentiment_score', 0)
                                            }
                                        }
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse Claude JSON response for {symbol}")
                                    # Fall back to local analysis
                                    pass
                            else:
                                logger.warning(f"Claude API request failed for {symbol}: {response.status}")
                                # Fall back to local analysis
                                pass
                except Exception as e:
                    logger.error(f"Error calling Claude API for {symbol}: {e}")
                    # Fall back to local analysis
                    pass
            
            # Fallback to local analysis if Claude API fails or is not available
            
            # Analyze technical patterns and indicators
            ema_9 = indicators['EMA_9']
            ema_21 = indicators['EMA_21']
            rsi = indicators['RSI_14']
            macd = indicators['MACD']
            vwap = indicators['VWAP']
            volatility = indicators['Volatility']
            
            # Determine technical bias
            technical_bias = "neutral"
            rationale = []
            
            # EMA analysis
            if price > ema_9 and ema_9 > ema_21:
                technical_bias = "bullish"
                rationale.append("Price is above both EMA-9 and EMA-21, showing bullish momentum")
            elif price < ema_9 and ema_9 < ema_21:
                technical_bias = "bearish"
                rationale.append("Price is below both EMA-9 and EMA-21, showing bearish momentum")
            
            # RSI analysis
            if rsi > 70:
                rationale.append(f"RSI at {rsi} indicates overbought conditions")
                if technical_bias == "bullish":
                    technical_bias = "neutral"  # Overbought conditions reduce bullish bias
            elif rsi < 30:
                rationale.append(f"RSI at {rsi} indicates oversold conditions")
                if technical_bias == "bearish":
                    technical_bias = "neutral"  # Oversold conditions reduce bearish bias
            
            # MACD analysis
            if macd['hist'] > 0 and macd['line'] > macd['signal']:
                rationale.append("MACD histogram positive and line above signal - bullish momentum")
                if technical_bias == "neutral":
                    technical_bias = "bullish"
            elif macd['hist'] < 0 and macd['line'] < macd['signal']:
                rationale.append("MACD histogram negative and line below signal - bearish momentum")
                if technical_bias == "neutral":
                    technical_bias = "bearish"
            
            # VWAP analysis
            if price > vwap:
                rationale.append("Price above VWAP - bullish")
            else:
                rationale.append("Price below VWAP - bearish")
            
            # News sentiment analysis - Fix structure handling
            news_bias = "neutral"
            news_score = 0
            
            # Handle news_sentiment structure correctly
            if isinstance(news_sentiment, dict) and 'headlines' in news_sentiment:
                headlines = news_sentiment['headlines']
                for headline in headlines:
                    sentiment = headline.get('sentiment', 'neutral')
                    if sentiment == 'positive':
                        news_score += 1
                    elif sentiment == 'negative':
                        news_score -= 1
                    # neutral sentiment adds 0
                
                # Normalize news score
                if headlines:
                    news_score = news_score / len(headlines)
            else:
                # Fallback for old structure
                for news in news_sentiment if isinstance(news_sentiment, list) else []:
                    if news.get('sentiment') == 'bullish':
                        news_score += news.get('score', 1)
                    elif news.get('sentiment') == 'bearish':
                        news_score -= abs(news.get('score', 1))
            
            if news_score > 0.2:
                news_bias = "bullish"
                rationale.append("News sentiment is predominantly bullish")
            elif news_score < -0.2:
                news_bias = "bearish"
                rationale.append("News sentiment is predominantly bearish")
            
            # Social sentiment analysis - Fix structure handling
            social_bias = "neutral"
            
            # Handle social_sentiment structure correctly
            if isinstance(social_sentiment, dict):
                sentiment_score = social_sentiment.get('sentiment_score', 0)
                if sentiment_score > 0.2:
                    social_bias = "bullish"
                    rationale.append("Social sentiment skewed bullish")
                elif sentiment_score < -0.2:
                    social_bias = "bearish"
                    rationale.append("Social sentiment skewed bearish")
            else:
                # Fallback for old structure
                total_mentions = social_sentiment.get('x_mentions', 1)
                bullish_mentions = social_sentiment.get('bullish_mentions', total_mentions // 2)
                bearish_mentions = social_sentiment.get('bearish_mentions', total_mentions // 2)
                
                bullish_ratio = bullish_mentions / total_mentions if total_mentions > 0 else 0.5
                bearish_ratio = bearish_mentions / total_mentions if total_mentions > 0 else 0.5
                
                if bullish_ratio > 0.6:
                    social_bias = "bullish"
                    rationale.append("Social sentiment skewed bullish")
                elif bearish_ratio > 0.6:
                    social_bias = "bearish"
                    rationale.append("Social sentiment skewed bearish")
            
            # Combine all biases to determine final bias
            biases = [technical_bias, news_bias, social_bias]
            bullish_count = biases.count("bullish")
            bearish_count = biases.count("bearish")
            
            if bullish_count >= 2:
                final_bias = "bullish"
                suggested_direction = "LONG"
            elif bearish_count >= 2:
                final_bias = "bearish"
                suggested_direction = "SHORT"
            else:
                final_bias = "neutral"
                suggested_direction = "NO_TRADE"
            
            # Calculate confidence score based on alignment
            confidence_score = 0.5  # Base confidence
            
            # Increase confidence if all biases align
            if len(set(biases)) == 1 and biases[0] != "neutral":
                confidence_score += 0.3
            
            # Adjust confidence based on volatility
            if volatility > 100:  # High volatility
                confidence_score -= 0.1
                rationale.append("High volatility - tighter SL recommended")
            
            # Adjust confidence based on RSI extremes
            if rsi > 80 or rsi < 20:
                confidence_score -= 0.1
                rationale.append("Extreme RSI levels - caution advised")
            
            # Ensure confidence is within bounds
            confidence_score = max(0.1, min(0.95, confidence_score))
            
            return {
                "bias": final_bias,
                "reasoning": " | ".join(rationale),  # Convert rationale list to string
                "confidence_score": round(confidence_score, 2),
                "warnings": [r for r in rationale if "recommended" in r or "caution" in r],
                "suggested_direction": suggested_direction,
                "technical_analysis": {
                    "ema_trend": "bullish" if ema_9 > ema_21 else "bearish",
                    "rsi_level": rsi,
                    "macd_signal": "bullish" if macd['hist'] > 0 else "bearish",
                    "vwap_position": "above" if price > vwap else "below",
                    "volatility": volatility
                },
                "sentiment_analysis": {
                    "news_bias": news_bias,
                    "social_bias": social_bias,
                    "news_score": round(news_score, 2),
                    "social_sentiment_score": social_sentiment.get('sentiment_score', 0) if isinstance(social_sentiment, dict) else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Claude deep analysis: {e}")
            return None

    async def gpt_trade_plan_generator(self, market_data: Dict, claude_analysis: Dict) -> Dict:
        """Step 3: GPT-4o — Precision Trade Plan Builder"""
        try:
            symbol = market_data['symbol']
            current_price = market_data['price']
            indicators = market_data['indicators']
            claude_bias = claude_analysis['bias']
            confidence_score = claude_analysis['confidence_score']
            suggested_direction = claude_analysis['suggested_direction']
            
            # Only generate trade plan if confidence is high enough and direction is clear
            if confidence_score < self.high_confidence_threshold or suggested_direction == "NO_TRADE":
                return {
                    "symbol": symbol,
                    "direction": "NO_TRADE",
                    "reason": f"Insufficient confidence ({confidence_score}) or unclear direction",
                    "confidence_score": confidence_score
                }
            
            # Calculate entry, stop-loss, and take-profit levels
            volatility = indicators['Volatility']
            vwap = indicators['VWAP']
            ema_9 = indicators['EMA_9']
            ema_21 = indicators['EMA_21']
            
            if suggested_direction == "LONG":
                # Long trade setup
                entry_price = current_price * 1.001  # Slight premium for entry
                stop_loss = min(vwap, ema_21) * 0.995  # Below VWAP or EMA-21
                
                # Calculate take profit based on risk-reward ratio
                risk = entry_price - stop_loss
                if risk > 0:
                    # Target 1.5-2.0 risk-reward ratio
                    target_ratio = random.uniform(1.5, 2.0)
                    take_profit = entry_price + (risk * target_ratio)
                else:
                    take_profit = entry_price * 1.02  # 2% target if no clear risk
                
                direction = "LONG"
                
            else:  # SHORT
                # Short trade setup
                entry_price = current_price * 0.999  # Slight discount for entry
                stop_loss = max(vwap, ema_21) * 1.005  # Above VWAP or EMA-21
                
                # Calculate take profit based on risk-reward ratio
                risk = stop_loss - entry_price
                if risk > 0:
                    # Target 1.5-2.0 risk-reward ratio
                    target_ratio = random.uniform(1.5, 2.0)
                    take_profit = entry_price - (risk * target_ratio)
                else:
                    take_profit = entry_price * 0.98  # 2% target if no clear risk
                
                direction = "SHORT"
            
            # Calculate risk-reward ratio
            if direction == "LONG":
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit
            
            risk_reward_ratio = round(reward / risk, 1) if risk > 0 else 0
            
            # Determine position size based on confidence and volatility
            if confidence_score > 0.8:
                position_size = "20% of account equity"
            elif confidence_score > 0.7:
                position_size = "15% of account equity"
            else:
                position_size = "10% of account equity"
            
            # Generate execution notes
            notes = []
            if direction == "LONG":
                notes.append("Entry just above current price with momentum")
                notes.append(f"SL below {min(vwap, ema_21):.2f} confluence zone")
                notes.append(f"TP based on {risk_reward_ratio}:1 risk-reward ratio")
            else:
                notes.append("Entry just below current price with momentum")
                notes.append(f"SL above {max(vwap, ema_21):.2f} confluence zone")
                notes.append(f"TP based on {risk_reward_ratio}:1 risk-reward ratio")
            
            if volatility > 100:
                notes.append("High volatility - consider reducing position size")
            
            return {
                "symbol": symbol,
                "direction": direction,
                "entry_price": round(entry_price, 2),
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
                "risk_reward_ratio": risk_reward_ratio,
                "position_size": position_size,
                "confidence_score": confidence_score,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in GPT trade plan generation: {e}")
            return None

    async def run_ai_analysis_pipeline(self, symbol: str) -> Optional[Dict]:
        """Run the complete AI analysis pipeline for a symbol"""
        try:
            logger.info(f"Starting multi-stage AI analysis pipeline for {symbol}")
            
            # Initialize analysis status
            self.analysis_status[symbol] = 'starting'
            self.analysis_progress[symbol] = []
            
            # Broadcast initial status
            await self.broadcast_analysis_status(symbol, 'starting', 'Initializing AI analysis pipeline...')
            
            # Step 1: Input Collection - Live Market Snapshot
            await self.broadcast_analysis_status(symbol, 'collecting_data', '🔍 Collecting real-time market data...')
            market_data = await self.collect_market_data(symbol)
            if not market_data:
                await self.broadcast_analysis_status(symbol, 'error', 'Failed to collect market data')
                logger.error(f"Failed to collect market data for {symbol}")
                return None
            
            await self.broadcast_analysis_status(symbol, 'data_collected', f'📊 Market data collected: Price ${market_data["price"]}, RSI {market_data["indicators"]["RSI_14"]}')
            logger.info(f"Market data collected for {symbol}: Price ${market_data['price']}, RSI {market_data['indicators']['RSI_14']}")
            
            # Step 2: Claude - Deep Technical Analysis
            await self.broadcast_analysis_status(symbol, 'claude_analysis', '  Running Claude deep technical analysis...')
            claude_analysis = await self.claude_deep_analysis(market_data)
            if not claude_analysis:
                await self.broadcast_analysis_status(symbol, 'error', 'Failed to get Claude analysis')
                logger.error(f"Failed to get Claude analysis for {symbol}")
                return None
            
            # Cache Claude analysis
            if symbol not in self.news_cache:
                self.news_cache[symbol] = {}
            self.news_cache[symbol]['claude_analysis'] = claude_analysis
            
            await self.broadcast_analysis_status(symbol, 'claude_completed', f'✅ Claude analysis completed: Bias {claude_analysis["bias"]}, Confidence {claude_analysis["confidence_score"]}')
            logger.info(f"Claude analysis completed for {symbol}: Bias {claude_analysis['bias']}, Confidence {claude_analysis['confidence_score']}")
            
            # Step 3: GPT - Trade Plan Generation
            await self.broadcast_analysis_status(symbol, 'gpt_analysis', '🤖 Generating GPT trade plan and final reasoning...')
            gpt_analysis = await self.gpt_trade_plan_generator(market_data, claude_analysis)
            if not gpt_analysis:
                await self.broadcast_analysis_status(symbol, 'error', 'Failed to get GPT analysis')
                logger.error(f"Failed to get GPT analysis for {symbol}")
                return None
            
            # Cache GPT analysis
            self.news_cache[symbol]['gpt_analysis'] = gpt_analysis
            
            await self.broadcast_analysis_status(symbol, 'gpt_completed', f'🎯 GPT analysis completed: Direction {gpt_analysis.get("direction", "NO_TRADE")}')
            logger.info(f"GPT analysis completed for {symbol}: Direction {gpt_analysis.get('direction', 'NO_TRADE')}")
            
            # Combine all outputs into comprehensive analysis
            complete_analysis = {
                'symbol': symbol,
                'market_data': market_data,
                'claude_analysis': claude_analysis,
                'gpt_analysis': gpt_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
            # Store in cache
            self.ai_analysis_cache[symbol] = complete_analysis
            self.last_analysis_time[symbol] = time.time()
            
            # Final status update
            confidence_score = gpt_analysis.get('confidence_score', 0)
            direction = gpt_analysis.get('direction', 'NO_TRADE')
            
            if direction != 'NO_TRADE':
                await self.broadcast_analysis_status(symbol, 'completed', f'🚀 Analysis complete! {direction} signal with {confidence_score:.1%} confidence')
            else:
                await self.broadcast_analysis_status(symbol, 'completed', f'📋 Analysis complete! No trade signal (confidence: {confidence_score:.1%})')
            
            logger.info(f"Completed multi-stage AI analysis for {symbol}")
            return complete_analysis
            
        except Exception as e:
            await self.broadcast_analysis_status(symbol, 'error', f'Error in analysis: {str(e)}')
            logger.error(f"Error in AI analysis pipeline for {symbol}: {e}")
            return None

    async def continuous_ai_monitoring(self):
        """Continuously monitor all target pairs for trading opportunities with real-time news"""
        # Wait a bit for initial price data to be available
        logger.info("AI monitoring starting - waiting for initial price data...")
        await asyncio.sleep(5)
        
        while True:
            try:
                # Only run analysis if enabled by user
                if not self.analysis_enabled:
                    logger.info("⏸️ AI Analysis is disabled. Waiting for user to start analysis...")
                    await asyncio.sleep(10)  # Check every 10 seconds
                    continue
                
                current_time = time.time()
                
                # RULE 1: Check for symbols that need analysis (not in cooldown)
                symbols_to_analyze = []
                for symbol in self.target_pairs:
                    # Check if price data is available for this symbol
                    if symbol not in self.price_cache:
                        logger.warning(f"No price data available for {symbol}, skipping analysis")
                        continue
                    
                    # Check if symbol is in cooldown (15-minute rule)
                    cooldown_end = self.opportunity_cooldown.get(symbol, 0)
                    if current_time < cooldown_end:
                        remaining_cooldown = int((cooldown_end - current_time) / 60)
                        logger.info(f"⏸️ {symbol} in cooldown - {remaining_cooldown} minutes remaining")
                        continue
                    
                    # Check if it's time to analyze this symbol
                    last_analysis = self.last_analysis_time.get(symbol, 0)
                    if current_time - last_analysis >= self.analysis_interval:
                        symbols_to_analyze.append(symbol)
                
                # RULE 3: Run parallel analysis for all symbols that need it
                if symbols_to_analyze:
                    logger.info(f"🔄 Running parallel analysis for {len(symbols_to_analyze)} symbols: {symbols_to_analyze}")
                    
                    # Create parallel analysis tasks
                    analysis_tasks = [self.run_ai_analysis_pipeline(symbol) for symbol in symbols_to_analyze]
                    results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(results):
                        symbol = symbols_to_analyze[i]
                        if isinstance(result, Exception):
                            logger.error(f"Error in analysis for {symbol}: {result}")
                            continue
                        
                        if result:
                            gpt_analysis = result.get('gpt_analysis', {})
                            confidence_score = gpt_analysis.get('confidence_score', 0)
                            direction = gpt_analysis.get('direction', 'NO_TRADE')
                            
                            # Log all analysis results regardless of confidence
                            logger.info(f"Analysis completed for {symbol}: Confidence {confidence_score:.2f}, Direction {direction}")
                            
                            # Broadcast analysis log to all clients
                            if self.clients:
                                analysis_log_message = {
                                    'type': 'analysis_log',
                                    'data': {
                                        'symbol': symbol,
                                        'message': f"📊 Analysis completed: {direction} {symbol} with {confidence_score:.1%} confidence",
                                        'confidence_score': confidence_score,
                                        'direction': direction,
                                        'entry_price': gpt_analysis.get('entry_price', 0),
                                        'take_profit': gpt_analysis.get('take_profit', 0),
                                        'stop_loss': gpt_analysis.get('stop_loss', 0),
                                        'timestamp': datetime.now().isoformat(),
                                        'level': 'info' if confidence_score < self.high_confidence_threshold else 'high'
                                    }
                                }
                                
                                await asyncio.gather(
                                    *[client.send(json.dumps(analysis_log_message)) for client in self.clients],
                                    return_exceptions=True
                                )
                            
                            # Check if this is a high-confidence opportunity for alerts
                            if confidence_score >= self.high_confidence_threshold and direction != 'NO_TRADE':
                                logger.info(f"🚨 HIGH CONFIDENCE OPPORTUNITY DETECTED for {symbol}")
                                logger.info(f"   Direction: {direction}")
                                logger.info(f"   Confidence: {confidence_score:.2f}")
                                logger.info(f"   Entry: ${gpt_analysis.get('entry_price', 0)}")
                                logger.info(f"   SL: ${gpt_analysis.get('stop_loss', 0)}")
                                logger.info(f"   TP: ${gpt_analysis.get('take_profit', 0)}")
                                
                                # RULE 1: Set 15-minute cooldown for this symbol
                                self.opportunity_cooldown[symbol] = current_time + self.cooldown_duration
                                logger.info(f"⏸️ 15-minute cooldown set for {symbol} - no more analysis until {datetime.fromtimestamp(current_time + self.cooldown_duration).strftime('%H:%M:%S')}")
                                
                                # Check if bot is enabled and should execute trades automatically
                                if self.bot_enabled and not self.bot_config.get('manual_approval_mode', False):
                                    # Execute bot trade directly
                                    logger.info(f"🤖 Bot enabled and manual approval disabled - executing trade for {symbol}")
                                    await self.execute_bot_trade(symbol, result)
                                else:
                                    # Store as pending trade for manual approval
                                    self.pending_trades[symbol] = {
                                        'analysis': result,
                                        'confidence_score': confidence_score,
                                        'direction': direction,
                                        'detected_time': current_time,
                                        'wait_until': current_time + self.trade_wait_time,
                                        'status': 'pending_approval'
                                    }
                                    logger.info(f"⏰ Trade opportunity for {symbol} stored - waiting 30 minutes for approval")
                                
                                # Broadcast alert to all clients
                                if self.clients:
                                    alert_message = {
                                        'type': 'ai_opportunity_alert',
                                        'data': {
                                            'symbol': symbol,
                                            'analysis': result,
                                            'priority': 'high',
                                            'confidence_score': confidence_score,
                                            'direction': direction,
                                            'timestamp': datetime.now().isoformat(),
                                            'wait_until': datetime.fromtimestamp(current_time + self.trade_wait_time).isoformat(),
                                            'status': 'pending_approval' if not (self.bot_enabled and not self.bot_config.get('manual_approval_mode', False)) else 'executed'
                                        }
                                    }
                                    
                                    # Also broadcast analysis log
                                    analysis_log_message = {
                                        'type': 'analysis_log',
                                        'data': {
                                            'symbol': symbol,
                                            'message': f"🚨 HIGH CONFIDENCE OPPORTUNITY: {direction} {symbol} with {confidence_score:.1%} confidence",
                                            'confidence_score': confidence_score,
                                            'direction': direction,
                                            'entry_price': gpt_analysis.get('entry_price', 0),
                                            'take_profit': gpt_analysis.get('take_profit', 0),
                                            'stop_loss': gpt_analysis.get('stop_loss', 0),
                                            'timestamp': datetime.now().isoformat(),
                                            'level': 'high'
                                        }
                                    }
                                    
                                    await asyncio.gather(
                                        *[client.send(json.dumps(alert_message)) for client in self.clients],
                                        return_exceptions=True
                                    )
                                    
                                    await asyncio.gather(
                                        *[client.send(json.dumps(analysis_log_message)) for client in self.clients],
                                        return_exceptions=True
                                    )
                                    
                                    logger.info(f"Alert and log broadcasted for {symbol} to {len(self.clients)} clients")
                
                # Check for pending trades that have completed their wait period
                await self.check_pending_trades()
                
                # RULE 2: Check for trade direction reversals and trigger re-analysis
                await self.check_trade_direction_reversal()
                
                # Wait before next monitoring cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in continuous AI monitoring: {e}")
                await asyncio.sleep(60)

    async def start_analysis(self):
        """Start AI analysis monitoring"""
        if self.analysis_enabled:
            return {'success': False, 'error': 'Analysis is already running'}
        
        self.analysis_enabled = True
        self.analysis_start_time = time.time()
        logger.info("🚀 AI Analysis started by user")
        
        # Broadcast analysis status to all clients
        if self.clients:
            status_message = {
                'type': 'analysis_status_update',
                'data': {
                    'enabled': True,
                    'start_time': self.analysis_start_time,
                    'message': 'AI Analysis started successfully'
                }
            }
            
            await asyncio.gather(
                *[client.send(json.dumps(status_message)) for client in self.clients],
                return_exceptions=True
            )
        
        return {'success': True, 'message': 'AI Analysis started successfully'}

    async def stop_analysis(self):
        """Stop AI analysis monitoring"""
        if not self.analysis_enabled:
            return {'success': False, 'error': 'Analysis is not running'}
        
        self.analysis_enabled = False
        self.analysis_start_time = None
        logger.info("⏹️ AI Analysis stopped by user")
        
        # Broadcast analysis status to all clients
        if self.clients:
            status_message = {
                'type': 'analysis_status_update',
                'data': {
                    'enabled': False,
                    'stop_time': time.time(),
                    'message': 'AI Analysis stopped'
                }
            }
            
            await asyncio.gather(
                *[client.send(json.dumps(status_message)) for client in self.clients],
                return_exceptions=True
            )
        
        return {'success': True, 'message': 'AI Analysis stopped successfully'}

    async def get_analysis_status(self):
        """Get current analysis status"""
        return {
            'enabled': self.analysis_enabled,
            'start_time': self.analysis_start_time,
            'running_duration': time.time() - self.analysis_start_time if self.analysis_start_time else 0,
            'target_pairs': self.target_pairs,
            'analysis_interval': self.analysis_interval
        }

    # Trading Bot Methods
    async def start_bot(self, config: Dict = None) -> Dict:
        """Start the trading bot with given configuration"""
        if self.bot_enabled:
            return {'success': False, 'error': 'Bot is already running'}
        
        # Update config if provided
        if config:
            self.bot_config.update(config)
        
        # Reset daily trade counter if it's a new day
        current_time = time.time()
        if current_time - self.bot_last_trade_reset > 86400:  # 24 hours
            self.bot_trades_today = 0
            self.bot_last_trade_reset = current_time
        
        # Initialize bot state
        self.bot_enabled = True
        self.bot_start_time = current_time
        
        # NEW: Start AI analysis if not already running
        if not self.analysis_enabled:
            logger.info("🤖 Starting AI analysis automatically for bot")
            await self.start_analysis()
        
        # Initialize pair statuses
        for pair in self.bot_config['allowed_pairs']:
            self.bot_pair_status[pair] = 'idle'
        
        logger.info("🤖 Trading bot started with config:", self.bot_config)
        
        # Broadcast bot status
        if self.clients:
            status_message = {
                'type': 'bot_status_update',
                'data': {
                    'enabled': True,
                    'start_time': self.bot_start_time,
                    'config': self.bot_config,
                    'message': 'Trading bot started successfully'
                }
            }
            await asyncio.gather(
                *[client.send(json.dumps(status_message)) for client in self.clients],
                return_exceptions=True
            )
        
        return {'success': True, 'message': 'Trading bot started successfully'}

    async def stop_bot(self) -> Dict:
        """Stop the trading bot"""
        if not self.bot_enabled:
            return {'success': False, 'error': 'Bot is not running'}
        
        self.bot_enabled = False
        self.bot_start_time = None
        logger.info("⏹️ Trading bot stopped")
        
        # Broadcast bot status
        if self.clients:
            status_message = {
                'type': 'bot_status_update',
                'data': {
                    'enabled': False,
                    'stop_time': time.time(),
                    'message': 'Trading bot stopped'
                }
            }
            await asyncio.gather(
                *[client.send(json.dumps(status_message)) for client in self.clients],
                return_exceptions=True
            )
        
        return {'success': True, 'message': 'Trading bot stopped successfully'}

    async def get_bot_status(self) -> Dict:
        """Get current bot status"""
        return {
            'enabled': self.bot_enabled,
            'start_time': self.bot_start_time,
            'config': self.bot_config,
            'active_trades': len(self.bot_active_trades),
            'trades_today': self.bot_trades_today,
            'total_profit': self.bot_total_profit,
            'total_trades': self.bot_total_trades,
            'winning_trades': self.bot_winning_trades,
            'win_rate': (self.bot_winning_trades / self.bot_total_trades * 100) if self.bot_total_trades > 0 else 0,
            'pair_status': self.bot_pair_status,
            'running_duration': time.time() - self.bot_start_time if self.bot_start_time else 0
        }

    async def update_bot_config(self, new_config: Dict) -> Dict:
        """Update bot configuration"""
        # Validate config
        required_fields = ['max_trades_per_day', 'trade_amount_usdt', 'profit_target_usd', 'stop_loss_usd']
        for field in required_fields:
            if field not in new_config:
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        # Update config
        self.bot_config.update(new_config)
        logger.info("⚙️ Bot config updated:", self.bot_config)
        
        return {'success': True, 'message': 'Bot configuration updated successfully'}

    async def check_bot_trading_conditions(self, symbol: str, analysis: Dict) -> bool:
        """Check if trading conditions are met for a symbol"""
        if not self.bot_enabled:
            return False
        
        # Check if symbol is allowed
        if symbol not in self.bot_config['allowed_pairs']:
            return False
        
        # Check daily trade limit
        if self.bot_trades_today >= self.bot_config['max_trades_per_day']:
            logger.info(f"🤖 Daily trade limit reached ({self.bot_trades_today}/{self.bot_config['max_trades_per_day']})")
            return False
        
        # Check concurrent trade limit
        if len(self.bot_active_trades) >= self.bot_config['max_concurrent_trades']:
            logger.info(f"🤖 Concurrent trade limit reached ({len(self.bot_active_trades)}/{self.bot_config['max_concurrent_trades']})")
            return False
        
        # Check pair status
        pair_status = self.bot_pair_status.get(symbol, 'idle')
        if pair_status != 'idle':
            if pair_status == 'cooldown':
                cooldown_end = self.bot_cooldown_end.get(symbol, 0)
                if time.time() < cooldown_end:
                    return False
                else:
                    self.bot_pair_status[symbol] = 'idle'
            else:
                return False
        
        # Check AI confidence threshold
        gpt_analysis = analysis.get('gpt_analysis', {})
        confidence_score = gpt_analysis.get('confidence_score', 0)
        if confidence_score < self.bot_config['ai_confidence_threshold']:
            logger.info(f"🤖 Confidence too low for {symbol}: {confidence_score} < {self.bot_config['ai_confidence_threshold']}")
            return False
        
        # Check if there's a valid trade direction
        direction = gpt_analysis.get('direction', 'NO_TRADE')
        if direction == 'NO_TRADE':
            logger.info(f"🤖 No trade direction for {symbol}")
            return False
        
        # Check if profit potential meets target
        entry_price = gpt_analysis.get('entry_price', 0)
        take_profit = gpt_analysis.get('take_profit', 0)
        stop_loss = gpt_analysis.get('stop_loss', 0)
        
        if entry_price > 0 and take_profit > 0 and stop_loss > 0:
            if direction == 'LONG':
                profit_potential = take_profit - entry_price
            else:  # SHORT
                profit_potential = entry_price - take_profit
            
            if profit_potential < self.bot_config['profit_target_usd']:
                logger.info(f"🤖 Profit potential too low for {symbol}: ${profit_potential:.2f} < ${self.bot_config['profit_target_usd']}")
                return False
        
        return True

    async def execute_bot_trade(self, symbol: str, analysis: Dict) -> Dict:
        """Execute a trade based on bot logic"""
        try:
            gpt_analysis = analysis.get('gpt_analysis', {})
            direction = gpt_analysis.get('direction', 'NO_TRADE')
            entry_price = gpt_analysis.get('entry_price', 0)
            take_profit = gpt_analysis.get('take_profit', 0)
            stop_loss = gpt_analysis.get('stop_loss', 0)
            confidence_score = gpt_analysis.get('confidence_score', 0)
            
            # Calculate trade amount
            trade_amount = self.bot_config['trade_amount_usdt']
            if self.bot_config['risk_per_trade_percent'] > 0:
                risk_amount = self.paper_balance * (self.bot_config['risk_per_trade_percent'] / 100)
                trade_amount = min(trade_amount, risk_amount)
            
            # Calculate quantity
            quantity = trade_amount / entry_price if entry_price > 0 else 0
            
            # Create trade data
            trade_data = {
                'symbol': symbol,
                'direction': direction,
                'amount': quantity,
                'price': entry_price,
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'trade_type': 'BOT',
                'confidence_score': confidence_score,
                'analysis_id': f"bot_analysis_{int(time.time())}_{symbol}",
                'bot_config': self.bot_config.copy()
            }
            
            # Execute the trade
            result = await self.execute_paper_trade(trade_data)
            
            if result.get('success'):
                # Update bot state
                self.bot_trades_today += 1
                self.bot_total_trades += 1
                self.bot_pair_status[symbol] = 'in_trade'
                self.bot_active_trades[symbol] = {
                    'trade_data': trade_data,
                    'entry_time': time.time(),
                    'analysis': analysis
                }
                
                # Set up trailing stop if enabled
                if self.bot_config['trailing_enabled']:
                    self.bot_trailing_stops[symbol] = {
                        'trigger_price': take_profit,
                        'trailing_price': take_profit - self.bot_config['trailing_distance_usd'],
                        'activated': False
                    }
                
                logger.info(f"🤖 Bot trade executed for {symbol}: {direction} ${trade_amount:.2f}")
                
                # Broadcast trade execution
                if self.clients:
                    trade_message = {
                        'type': 'bot_trade_executed',
                        'data': {
                            'symbol': symbol,
                            'trade_data': trade_data,
                            'bot_status': await self.get_bot_status()
                        }
                    }
                    
                    # Also broadcast trade log
                    trade_log_message = {
                        'type': 'trade_log',
                        'data': {
                            'symbol': symbol,
                            'message': f"🤖 Bot trade executed: {direction} {symbol} at ${entry_price:.2f}",
                            'direction': direction,
                            'amount': quantity,
                            'price': entry_price,
                            'confidence_score': confidence_score,
                            'timestamp': datetime.now().isoformat(),
                            'level': 'success'
                        }
                    }
                    
                    # Broadcast position update to show the new position in frontend
                    position_update = {
                        'type': 'position_update',
                        'data': {
                            'positions': self.positions,
                            'balance': self.paper_balance
                        }
                    }
                    
                    # Also broadcast trade executed message for paper trade compatibility
                    trade_executed_message = {
                        'type': 'trade_executed',
                        'data': {
                            'new_balance': self.paper_balance,
                            'positions': self.positions,
                            'trade': {
                                'symbol': symbol,
                                'direction': direction,
                                'amount': quantity,
                                'price': entry_price,
                                'timestamp': time.time(),
                                'trade_type': 'BOT'
                            }
                        }
                    }
                    
                    await asyncio.gather(
                        *[client.send(json.dumps(trade_message)) for client in self.clients],
                        return_exceptions=True
                    )
                    
                    await asyncio.gather(
                        *[client.send(json.dumps(trade_log_message)) for client in self.clients],
                        return_exceptions=True
                    )
                    
                    await asyncio.gather(
                        *[client.send(json.dumps(position_update)) for client in self.clients],
                        return_exceptions=True
                    )
                    
                    await asyncio.gather(
                        *[client.send(json.dumps(trade_executed_message)) for client in self.clients],
                        return_exceptions=True
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing bot trade for {symbol}: {e}")
            return {'success': False, 'error': str(e)}

    async def check_bot_trade_exits(self):
        """Check and execute trade exits for bot trades"""
        current_time = time.time()
        
        for symbol, trade_info in list(self.bot_active_trades.items()):
            trade_data = trade_info['trade_data']
            entry_time = trade_info['entry_time']
            
            # Get current price
            current_price = self.price_cache.get(symbol, {}).get('price', 0)
            if current_price == 0:
                continue
            
            direction = trade_data['direction']
            take_profit = trade_data['take_profit']
            stop_loss = trade_data['stop_loss']
            
            should_exit = False
            exit_reason = ''
            
            # Check take profit
            if direction == 'LONG' and current_price >= take_profit:
                should_exit = True
                exit_reason = 'take_profit'
            elif direction == 'SHORT' and current_price <= take_profit:
                should_exit = True
                exit_reason = 'take_profit'
            
            # Check stop loss
            if direction == 'LONG' and current_price <= stop_loss:
                should_exit = True
                exit_reason = 'stop_loss'
            elif direction == 'SHORT' and current_price >= stop_loss:
                should_exit = True
                exit_reason = 'stop_loss'
            
            # Check trailing stop
            if self.bot_config['trailing_enabled'] and symbol in self.bot_trailing_stops:
                trailing_info = self.bot_trailing_stops[symbol]
                
                # Activate trailing if profit target reached
                if not trailing_info['activated']:
                    if direction == 'LONG' and current_price >= trailing_info['trigger_price']:
                        trailing_info['activated'] = True
                    elif direction == 'SHORT' and current_price <= trailing_info['trigger_price']:
                        trailing_info['activated'] = True
                
                # Check trailing stop
                if trailing_info['activated']:
                    if direction == 'LONG' and current_price <= trailing_info['trailing_price']:
                        should_exit = True
                        exit_reason = 'trailing_stop'
                    elif direction == 'SHORT' and current_price >= trailing_info['trailing_price']:
                        should_exit = True
                        exit_reason = 'trailing_stop'
                    
                    # Update trailing price
                    if direction == 'LONG' and current_price > trailing_info['trailing_price'] + self.bot_config['trailing_distance_usd']:
                        trailing_info['trailing_price'] = current_price - self.bot_config['trailing_distance_usd']
                    elif direction == 'SHORT' and current_price < trailing_info['trailing_price'] - self.bot_config['trailing_distance_usd']:
                        trailing_info['trailing_price'] = current_price + self.bot_config['trailing_distance_usd']
            
            # Check time-based exit (15 minutes max)
            if current_time - entry_time > 900:  # 15 minutes
                should_exit = True
                exit_reason = 'timeout'
            
            if should_exit:
                # Close the position
                result = await self.close_position(symbol)
                
                if result.get('success'):
                    # Calculate profit/loss
                    entry_price = trade_data['price']
                    exit_price = current_price
                    quantity = trade_data['amount']
                    
                    if direction == 'LONG':
                        profit_loss = (exit_price - entry_price) * quantity
                    else:  # SHORT
                        profit_loss = (entry_price - exit_price) * quantity
                    
                    # Update bot statistics
                    self.bot_total_profit += profit_loss
                    if profit_loss > 0:
                        self.bot_winning_trades += 1
                    
                    # Add to trade history
                    trade_record = {
                        'symbol': symbol,
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'quantity': quantity,
                        'profit_loss': profit_loss,
                        'exit_reason': exit_reason,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'hold_duration': current_time - entry_time,
                        'confidence_score': trade_data['confidence_score']
                    }
                    self.bot_trade_history.append(trade_record)
                    
                    # Set cooldown
                    self.bot_pair_status[symbol] = 'cooldown'
                    self.bot_cooldown_end[symbol] = current_time + self.bot_config['cooldown_secs']
                    
                    # Clean up
                    del self.bot_active_trades[symbol]
                    if symbol in self.bot_trailing_stops:
                        del self.bot_trailing_stops[symbol]
                    
                    # Broadcast trade closed
                    if self.clients:
                        trade_closed_message = {
                            'type': 'bot_trade_closed',
                            'data': {
                                'symbol': symbol,
                                'direction': direction,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'profit': profit_loss,
                                'trade_record': trade_record,
                                'timestamp': datetime.now().isoformat()
                            }
                        }
                        
                        # Also broadcast trade log
                        trade_log_message = {
                            'type': 'trade_log',
                            'data': {
                                'symbol': symbol,
                                'message': f"💰 Bot trade closed: {direction} {symbol} - Profit: ${profit_loss:.2f}",
                                'direction': direction,
                                'entry_price': entry_price,
                                'exit_price': exit_price,
                                'profit': profit_loss,
                                'timestamp': datetime.now().isoformat(),
                                'level': 'success' if profit_loss > 0 else 'warning'
                            }
                        }
                        
                        # Broadcast position update to show the closed position in frontend
                        position_update = {
                            'type': 'position_update',
                            'data': {
                                'positions': self.positions,
                                'balance': self.paper_balance
                            }
                        }
                        
                        # Also broadcast position closed message for paper trade compatibility
                        position_closed_message = {
                            'type': 'position_closed',
                            'data': {
                                'new_balance': self.paper_balance,
                                'positions': self.positions,
                                'trade': {
                                    'symbol': symbol,
                                    'direction': direction,
                                    'entry_price': entry_price,
                                    'exit_price': exit_price,
                                    'profit_loss': profit_loss,
                                    'timestamp': time.time(),
                                    'trade_type': 'BOT'
                                }
                            }
                        }
                        
                        await asyncio.gather(
                            *[client.send(json.dumps(trade_closed_message)) for client in self.clients],
                            return_exceptions=True
                        )
                        
                        await asyncio.gather(
                            *[client.send(json.dumps(trade_log_message)) for client in self.clients],
                            return_exceptions=True
                        )
                        
                        await asyncio.gather(
                            *[client.send(json.dumps(position_update)) for client in self.clients],
                            return_exceptions=True
                        )
                        
                        await asyncio.gather(
                            *[client.send(json.dumps(position_closed_message)) for client in self.clients],
                            return_exceptions=True
                        )
                    
                    logger.info(f"🤖 Bot trade closed for {symbol}: {exit_reason}, P&L: ${profit_loss:.2f}")
                    
                    # Broadcast trade closure
                    if self.clients:
                        close_message = {
                            'type': 'bot_trade_closed',
                            'data': {
                                'symbol': symbol,
                                'trade_record': trade_record,
                                'bot_status': await self.get_bot_status()
                            }
                        }
                        await asyncio.gather(
                            *[client.send(json.dumps(close_message)) for client in self.clients],
                            return_exceptions=True
                        )

    async def continuous_bot_monitoring(self):
        """Continuous monitoring loop for the trading bot"""
        while True:
            try:
                if self.bot_enabled:
                    # Check for trade exits
                    await self.check_bot_trade_exits()
                    
                    # Check if bot should stop (time limit)
                    if self.bot_start_time and self.bot_config['run_time_minutes'] > 0:
                        running_time = (time.time() - self.bot_start_time) / 60
                        if running_time >= self.bot_config['run_time_minutes']:
                            logger.info(f"🤖 Bot run time limit reached ({running_time:.1f} minutes)")
                            await self.stop_bot()
                            continue
                    
                    # Check for new trading opportunities
                    for symbol in self.bot_config['allowed_pairs']:
                        if symbol in self.ai_analysis_cache:
                            analysis = self.ai_analysis_cache[symbol]
                            
                            # Check if trading conditions are met
                            if await self.check_bot_trading_conditions(symbol, analysis):
                                logger.info(f"🤖 Trading conditions met for {symbol}, executing trade...")
                                await self.execute_bot_trade(symbol, analysis)
                    
                    # Broadcast periodic bot status updates
                    if self.clients:
                        status_message = {
                            'type': 'bot_status_update',
                            'data': await self.get_bot_status()
                        }
                        await asyncio.gather(
                            *[client.send(json.dumps(status_message)) for client in self.clients],
                            return_exceptions=True
                        )
                
                # Wait before next check
                await asyncio.sleep(self.bot_config['trade_interval_secs'])
                
            except Exception as e:
                logger.error(f"❌ Error in bot monitoring: {e}")
                await asyncio.sleep(10)  # Wait before retrying

    async def check_trade_direction_reversal(self):
        """Check if accepted trades are going opposite and trigger re-analysis"""
        current_time = time.time()
        symbols_to_reanalyze = []
        
        for symbol, trade_info in self.accepted_trade_directions.items():
            current_price = self.price_cache.get(symbol, {}).get('price', 0)
            if not current_price:
                continue
                
            entry_price = trade_info['entry_price']
            direction = trade_info['direction']
            
            # Calculate price movement
            if direction == 'LONG':
                price_change = (current_price - entry_price) / entry_price
                if price_change < -self.trade_reversal_threshold:  # Price dropped more than threshold
                    logger.warning(f"🚨 LONG trade for {symbol} going opposite! Entry: ${entry_price}, Current: ${current_price}, Change: {price_change:.2%}")
                    symbols_to_reanalyze.append(symbol)
            elif direction == 'SHORT':
                price_change = (entry_price - current_price) / entry_price
                if price_change < -self.trade_reversal_threshold:  # Price rose more than threshold
                    logger.warning(f"🚨 SHORT trade for {symbol} going opposite! Entry: ${entry_price}, Current: ${current_price}, Change: {price_change:.2%}")
                    symbols_to_reanalyze.append(symbol)
        
        # Trigger re-analysis for symbols going opposite
        if symbols_to_reanalyze:
            logger.info(f"🔄 Triggering re-analysis for {len(symbols_to_reanalyze)} symbols going opposite: {symbols_to_reanalyze}")
            
            # Clear cooldown for these symbols to allow immediate re-analysis
            for symbol in symbols_to_reanalyze:
                if symbol in self.opportunity_cooldown:
                    del self.opportunity_cooldown[symbol]
                if symbol in self.last_analysis_time:
                    del self.last_analysis_time[symbol]
            
            # Run parallel analysis for these symbols
            analysis_tasks = [self.run_ai_analysis_pipeline(symbol) for symbol in symbols_to_reanalyze]
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                symbol = symbols_to_reanalyze[i]
                if isinstance(result, Exception):
                    logger.error(f"Error in re-analysis for {symbol}: {result}")
                elif result:
                    logger.info(f"✅ Re-analysis completed for {symbol} due to trade reversal")
                    
                    # Process the re-analysis result
                    gpt_analysis = result.get('gpt_analysis', {})
                    confidence_score = gpt_analysis.get('confidence_score', 0)
                    new_direction = gpt_analysis.get('direction', 'NO_TRADE')
                    
                    if confidence_score >= self.high_confidence_threshold and new_direction != 'NO_TRADE':
                        logger.info(f"🔄 NEW OPPORTUNITY after reversal for {symbol}: {new_direction} (confidence: {confidence_score:.2f})")
                        
                        # Store as new pending trade
                        self.pending_trades[symbol] = {
                            'analysis': result,
                            'confidence_score': confidence_score,
                            'direction': new_direction,
                            'detected_time': current_time,
                            'wait_until': current_time + self.trade_wait_time,
                            'status': 'pending_approval',
                            'triggered_by': 'trade_reversal'
                        }
                        
                        # Broadcast alert
                        if self.clients:
                            alert_message = {
                                'type': 'ai_opportunity_alert',
                                'data': {
                                    'symbol': symbol,
                                    'analysis': result,
                                    'priority': 'high',
                                    'confidence_score': confidence_score,
                                    'direction': new_direction,
                                    'timestamp': datetime.now().isoformat(),
                                    'wait_until': datetime.fromtimestamp(current_time + self.trade_wait_time).isoformat(),
                                    'status': 'pending_approval',
                                    'triggered_by': 'trade_reversal'
                                }
                            }
                            
                            await asyncio.gather(
                                *[client.send(json.dumps(alert_message)) for client in self.clients],
                                return_exceptions=True
                            )

    async def check_pending_trades(self):
        """Check pending trades and execute them if wait period is complete"""
        current_time = time.time()
        completed_trades = []
        
        for symbol, trade_data in self.pending_trades.items():
            if current_time >= trade_data['wait_until']:
                logger.info(f"⏰ Wait period completed for {symbol} - trade ready for execution")
                
                # Update status to ready
                trade_data['status'] = 'ready_for_execution'
                
                # Broadcast ready status to clients
                if self.clients:
                    ready_message = {
                        'type': 'trade_ready_alert',
                        'data': {
                            'symbol': symbol,
                            'analysis': trade_data['analysis'],
                            'confidence_score': trade_data['confidence_score'],
                            'direction': trade_data['direction'],
                            'timestamp': datetime.now().isoformat(),
                            'status': 'ready_for_execution'
                        }
                    }
                    
                    await asyncio.gather(
                        *[client.send(json.dumps(ready_message)) for client in self.clients],
                        return_exceptions=True
                    )
                
                completed_trades.append(symbol)
        
        # Remove completed trades from pending
        for symbol in completed_trades:
            del self.pending_trades[symbol]

    async def accept_trade(self, symbol: str, trade_data: Dict) -> Dict:
        """Accept and execute a pending trade, allowing user-specified USDT amount."""
        try:
            if symbol not in self.pending_trades:
                return {'success': False, 'error': 'No pending trade found for this symbol'}
            
            pending_trade = self.pending_trades[symbol]
            
            # Check if wait period is complete
            current_time = time.time()
            if current_time < pending_trade['wait_until']:
                remaining_time = pending_trade['wait_until'] - current_time
                return {
                    'success': False, 
                    'error': f'Trade not ready yet. Please wait {int(remaining_time/60)} more minutes.',
                    'remaining_seconds': int(remaining_time)
                }
            
            # Execute the trade
            analysis = pending_trade['analysis']
            gpt_analysis = analysis.get('gpt_analysis', {})
            
            # Allow user to specify USDT amount
            usdt_amount = trade_data.get('usdt_amount')
            if usdt_amount is not None:
                trade_amount = float(usdt_amount) / gpt_analysis.get('entry_price', 1)
            else:
                trade_amount = self.paper_balance * 0.01 / gpt_analysis.get('entry_price', 1)
            
            # Create trade data
            trade_execution_data = {
                'symbol': symbol,
                'direction': 'buy' if pending_trade['direction'] == 'LONG' else 'sell',
                'amount': trade_amount,
                'price': gpt_analysis.get('entry_price', self.price_cache.get(symbol, {}).get('price', 0)),
                'trade_id': f"ai_trade_{int(time.time())}_{symbol}",
                'analysis_id': f"analysis_{symbol}_{int(pending_trade['detected_time'])}",
                'confidence_score': pending_trade['confidence_score'],
                'stop_loss': gpt_analysis.get('stop_loss'),
                'take_profit': gpt_analysis.get('take_profit'),
                'trade_type': pending_trade['direction']  # Add trade type for proper handling
            }
            
            # Execute the trade
            result = await self.execute_paper_trade(trade_execution_data)
            
            if result.get('success'):
                # Store as accepted trade
                self.accepted_trades[symbol] = {
                    'trade_data': trade_execution_data,
                    'analysis': analysis,
                    'accepted_time': current_time,
                    'status': 'executed'
                }
                
                # NEW: Track trade direction for reversal monitoring
                self.accepted_trade_directions[symbol] = {
                    'direction': pending_trade['direction'],
                    'entry_price': gpt_analysis.get('entry_price', self.price_cache.get(symbol, {}).get('price', 0)),
                    'accepted_time': current_time
                }
                
                logger.info(f"📊 Trade direction tracking started for {symbol}: {pending_trade['direction']} at ${gpt_analysis.get('entry_price', 0)}")
                
                # Remove from pending trades
                del self.pending_trades[symbol]
                
                logger.info(f"✅ AI Trade accepted and executed for {symbol}")
                
                return {
                    'success': True,
                    'message': f'AI trade executed successfully for {symbol}',
                    'trade_details': trade_execution_data,
                    'new_balance': result.get('new_balance', self.paper_balance)
                }
            else:
                return {
                    'success': False,
                    'error': f'Trade execution failed: {result.get("error", "Unknown error")}'
                }
                
        except Exception as e:
            logger.error(f"Error accepting trade for {symbol}: {e}")
            return {'success': False, 'error': f'Error accepting trade: {str(e)}'}

    async def get_pending_trades(self) -> Dict:
        """Get all pending trades with their status"""
        current_time = time.time()
        pending_trades_info = {}
        
        for symbol, trade_data in self.pending_trades.items():
            remaining_time = max(0, trade_data['wait_until'] - current_time)
            pending_trades_info[symbol] = {
                'confidence_score': trade_data['confidence_score'],
                'direction': trade_data['direction'],
                'detected_time': trade_data['detected_time'],
                'wait_until': trade_data['wait_until'],
                'remaining_seconds': int(remaining_time),
                'remaining_minutes': int(remaining_time / 60),
                'status': trade_data['status'],
                'analysis': trade_data['analysis']
            }
        
        return pending_trades_info

    async def execute_paper_trade(self, trade_data):
        """Execute a paper trade with support for opening/closing long and short positions, and user-specified USDT amount."""
        try:
            symbol = trade_data['symbol']
            direction = trade_data['direction']
            amount = trade_data['amount']
            price = trade_data.get('price', self.price_cache.get(symbol, {}).get('price', 0))
            trade_id = trade_data.get('trade_id', None)
            trade_type = trade_data.get('trade_type', 'LONG')  # Get trade type for proper handling

            logger.info(f"Executing paper trade: {direction} {amount} {symbol} at ${price} (Type: {trade_type})")
            logger.info(f"Trade data received: {trade_data}")
            logger.info(f"Current price cache keys: {list(self.price_cache.keys())}")

            # Check for duplicate trade ID
            if trade_id and trade_id in self.processed_trade_ids:
                logger.warning(f"Duplicate trade ID detected: {trade_id}")
                return {'success': False, 'error': 'Duplicate trade detected'}

            # Add trade ID to processed set
            if trade_id:
                self.processed_trade_ids.add(trade_id)
                if len(self.processed_trade_ids) > 1000:
                    self.processed_trade_ids = set(list(self.processed_trade_ids)[-1000:])

            if not price:
                return {'success': False, 'error': 'No price available for symbol'}

            if amount <= 0:
                return {'success': False, 'error': 'Trade amount must be greater than 0'}

            trade_value = amount * price

            # Warn about very large trades
            if trade_value > self.paper_balance * 0.5:
                logger.warning(f"Large trade detected: ${trade_value:,.2f} ({(trade_value/self.paper_balance)*100:.1f}% of balance)")

            # --- FIXED LOGIC FOR SHORT/LONG ---
            pos = self.positions.get(symbol)
            
            if direction == 'buy':
                # Opening/increasing a long position
                if pos:
                    if pos['direction'] == 'long':
                        # Add to existing long
                        total_amount = pos['amount'] + amount
                        total_cost = (pos['amount'] * pos['avg_price']) + trade_value
                        avg_price = total_cost / total_amount
                        self.positions[symbol] = {
                            'amount': total_amount,
                            'avg_price': avg_price,
                            'direction': 'long'
                        }
                        # Deduct balance for additional long position
                        self.paper_balance -= trade_value
                    elif pos['direction'] == 'short':
                        # Closing short, possibly flipping to long
                        if amount < pos['amount']:
                            # Reduce short
                            self.positions[symbol]['amount'] -= amount
                            # Add balance back for closing short
                            self.paper_balance += trade_value
                        elif amount == pos['amount']:
                            # Close short completely
                            del self.positions[symbol]
                            # Add balance back for closing short
                            self.paper_balance += trade_value
                        else:
                            # Close short and open long for remaining
                            long_amount = amount - pos['amount']
                            del self.positions[symbol]
                            self.positions[symbol] = {
                                'amount': long_amount,
                                'avg_price': price,
                                'direction': 'long'
                            }
                            # Add balance back for closing short, deduct for new long
                            self.paper_balance += (pos['amount'] * price) - (long_amount * price)
                else:
                    # New long position
                    self.positions[symbol] = {
                        'amount': amount,
                        'avg_price': price,
                        'direction': 'long'
                    }
                    # Deduct balance for long position
                    self.paper_balance -= trade_value
                    
            elif direction == 'sell':
                # Opening/increasing a short position
                if pos:
                    if pos['direction'] == 'short':
                        # Add to existing short
                        total_amount = pos['amount'] + amount
                        total_cost = (pos['amount'] * pos['avg_price']) + trade_value
                        avg_price = total_cost / total_amount
                        self.positions[symbol] = {
                            'amount': total_amount,
                            'avg_price': avg_price,
                            'direction': 'short'
                        }
                        # Deduct margin for additional short (10% of trade value)
                        margin_required = trade_value * 0.1
                        self.paper_balance -= margin_required
                    elif pos['direction'] == 'long':
                        # Closing long, possibly flipping to short
                        if amount < pos['amount']:
                            # Reduce long
                            self.positions[symbol]['amount'] -= amount
                            # Add balance back for closing long
                            self.paper_balance += trade_value
                        elif amount == pos['amount']:
                            # Close long completely
                            del self.positions[symbol]
                            # Add balance back for closing long
                            self.paper_balance += trade_value
                        else:
                            # Close long and open short for remaining
                            short_amount = amount - pos['amount']
                            del self.positions[symbol]
                            self.positions[symbol] = {
                                'amount': short_amount,
                                'avg_price': price,
                                'direction': 'short'
                            }
                            # Add balance back for closing long, deduct margin for new short
                            self.paper_balance += (pos['amount'] * price) - (short_amount * price * 0.1)
                else:
                    # New short position
                    self.positions[symbol] = {
                        'amount': amount,
                        'avg_price': price,
                        'direction': 'short'
                    }
                    # Deduct margin for short position (10% of trade value)
                    margin_required = trade_value * 0.1
                    self.paper_balance -= margin_required
            else:
                return {'success': False, 'error': 'Invalid trade direction'}

            # Store entry details for comprehensive logging when position is closed
            self.trade_entries[symbol] = {
                'entry_timestamp': datetime.now().isoformat(),
                'entry_timestamp_unix': time.time(),
                'trade_type': trade_type,
                'strategy': trade_data.get('strategy', 'manual'),
                'confidence_score': trade_data.get('confidence_score', 0),
                'analysis_id': trade_data.get('analysis_id', None),
                'risk_management': {
                    'stop_loss': trade_data.get('stop_loss'),
                    'take_profit': trade_data.get('take_profit'),
                    'leverage': trade_data.get('leverage', 1)
                }
            }

            # Record the trade
            trade_record = {
                'id': len(self.recent_trades) + 1,
                'symbol': symbol,
                'direction': direction,
                'amount': amount,
                'price': price,
                'value': trade_value,
                'trade_type': trade_type,
                'timestamp': datetime.now().isoformat()
            }
            self.recent_trades.insert(0, trade_record)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]

            logger.info(f"Executed {direction} trade: {amount} {symbol} at ${price} (Type: {trade_type})")
            logger.info(f"Current positions after trade: {self.positions}")
            logger.info(f"Position for {symbol}: {self.positions.get(symbol, 'Not found')}")
            logger.info(f"New balance: ${self.paper_balance:,.2f}")

            # Broadcast position update to all clients
            if self.clients:
                position_update = {
                    'type': 'position_update',
                    'data': {
                        'positions': self.positions,
                        'balance': self.paper_balance
                    }
                }
                await asyncio.gather(
                    *[client.send(json.dumps(position_update)) for client in self.clients],
                    return_exceptions=True
                )

            return {
                'success': True,
                'new_balance': self.paper_balance,
                'positions': self.positions,
                'trade': trade_record
            }
        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
            return {'success': False, 'error': str(e)}

    async def close_position(self, symbol):
        """Close a position completely"""
        try:
            if symbol not in self.positions:
                return {'success': False, 'error': 'Position not found'}
            
            position = self.positions[symbol]
            current_price = self.price_cache.get(symbol, {}).get('price', position['avg_price'])
            
            # Calculate close value and profit/loss based on position type
            if position['direction'] == 'long':
                # For long positions: sell at current price
                close_value = position['amount'] * current_price
                entry_value = position['amount'] * position['avg_price']
                profit_loss = close_value - entry_value  # Profit if price went up
                
                # Add the sale proceeds to balance
                self.paper_balance += close_value
                logger.info(f"Closed LONG position: {position['amount']} {symbol} at ${current_price} - P&L: ${profit_loss:,.2f}")
            else:
                # For short positions: buy back at current price
                close_value = position['amount'] * current_price
                entry_value = position['amount'] * position['avg_price']
                profit_loss = entry_value - close_value  # Profit if price went down
                
                # Add profit/loss to balance (entry_value was never deducted, only margin)
                self.paper_balance += profit_loss
                logger.info(f"Closed SHORT position: {position['amount']} {symbol} at ${current_price} - P&L: ${profit_loss:,.2f}")
            
            # Close position
            del self.positions[symbol]
            
            # Log comprehensive trade details to MongoDB
            await self.log_closed_trade_comprehensive(symbol, position, current_price, close_value, profit_loss)
            
            logger.info(f"Closed {position['direction']} position: {position['amount']} {symbol}")
            logger.info(f"New balance: ${self.paper_balance:,.2f}")
            
            # NEW: Clean up trade direction tracking when position is closed
            if symbol in self.accepted_trade_directions:
                del self.accepted_trade_directions[symbol]
                logger.info(f"🧹 Trade direction tracking cleaned up for {symbol}")
            
            # Broadcast position update to all clients
            if self.clients:
                position_update = {
                    'type': 'position_update',
                    'data': {
                        'positions': self.positions,
                        'balance': self.paper_balance
                    }
                }
                await asyncio.gather(
                    *[client.send(json.dumps(position_update)) for client in self.clients],
                    return_exceptions=True
                )
            
            return {
                'success': True,
                'new_balance': self.paper_balance,
                'positions': self.positions,
                'trade': self.recent_trades[0] if self.recent_trades else None
            }
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {'success': False, 'error': str(e)}

    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Ensure we have fresh price data before sending initial data
            if not self.price_cache:
                await self.fetch_crypto_data()
            
            # Send initial data
            initial_data = {
                'paper_balance': self.paper_balance,
                'positions': self.positions,
                'recent_trades': self.recent_trades[:20],  # Send last 20 trades
                'price_cache': self.price_cache,
                'crypto_data': self.crypto_data
            }
            
            logger.info(f"Sending initial data with {len(self.price_cache)} price entries")
            logger.info(f"Price cache keys: {list(self.price_cache.keys())}")
            
            await websocket.send(json.dumps({
                'type': 'initial_data',
                'data': initial_data
            }))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', 'unknown')
                    logger.info(f"📨 Received message: {message_type}")
                    
                    # Add special logging for bot messages
                    if message_type in ['get_bot_status', 'start_bot', 'stop_bot', 'update_bot_config']:
                        logger.info(f"🤖 BOT MESSAGE RECEIVED: {message_type}")
                        logger.info(f"🤖 Full bot message: {data}")
                    
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except websockets.exceptions.InvalidMessage:
            # This is a common error when browsers make invalid connection attempts
            # It's harmless and doesn't affect functionality
            pass
        except Exception as e:
            logger.error(f"Unexpected error in client handler: {e}")
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

    async def handle_message(self, websocket, data):
        """Handle incoming messages from clients"""
        message_type = data.get('type')
        logger.info(f"🔍 Received message type: {message_type}")
        logger.info(f"🔍 Message data: {data}")
        logger.info(f"🔍 Message type repr: {repr(message_type)}")
        
        # Add debug logging for bot messages
        if message_type in ['get_bot_status', 'start_bot', 'stop_bot', 'update_bot_config']:
            logger.info(f"🤖 BOT MESSAGE DETECTED: {message_type}")
            logger.info(f"🤖 Full bot message data: {data}")
            logger.info(f"🤖 About to process bot message: {message_type}")
        
        if message_type == 'paper_trade':
            result = await self.execute_paper_trade(data)
            await websocket.send(json.dumps({
                'type': 'paper_trade_response',
                'data': result
            }))
            
        elif message_type == 'close_position':
            result = await self.close_position(data['symbol'])
            await websocket.send(json.dumps({
                'type': 'position_closed',
                'data': result
            }))
            
        elif message_type == 'get_positions':
            await websocket.send(json.dumps({
                'type': 'positions_response',
                'data': {
                    'balance': self.paper_balance,
                    'positions': self.positions
                }
            }))
            
        elif message_type == 'get_trade_history':
            limit = data.get('limit', 50)
            symbol = data.get('symbol')
            
            trades = self.recent_trades
            if symbol:
                trades = [t for t in trades if t['symbol'] == symbol]
            
            await websocket.send(json.dumps({
                'type': 'trade_history_response',
                'data': {
                    'trades': trades[:limit]
                }
            }))
            
        elif message_type == 'get_crypto_data':
            symbol = data.get('symbol')
            if symbol:
                # Return specific symbol data
                for coin_id, coin_data in self.crypto_data.items():
                    if coin_data['symbol'] == symbol:
                        await websocket.send(json.dumps({
                            'type': 'crypto_data_response',
                            'data': {coin_id: coin_data}
                        }))
                        break
            else:
                # Return all crypto data
                await websocket.send(json.dumps({
                    'type': 'crypto_data_response',
                    'data': self.crypto_data
                }))
                
        elif message_type == 'get_ai_analysis':
            # Get AI analysis for a specific symbol
            symbol = data.get('symbol')
            if symbol:
                # Check if we have recent analysis in cache
                cached_analysis = self.ai_analysis_cache.get(symbol)
                current_time = time.time()
                last_analysis = self.last_analysis_time.get(symbol, 0)
                
                # If no cached analysis or it's old, run new analysis
                if not cached_analysis or (current_time - last_analysis) >= self.analysis_interval:
                    analysis = await self.run_ai_analysis_pipeline(symbol)
                else:
                    analysis = cached_analysis
                
                if analysis:
                    await websocket.send(json.dumps({
                        'type': 'ai_analysis_response',
                        'data': analysis
                    }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'ai_analysis_response',
                        'data': {
                            'symbol': symbol,
                            'error': 'Unable to generate analysis at this time'
                        }
                    }))
            else:
                await websocket.send(json.dumps({
                    'type': 'ai_analysis_response',
                    'data': {
                        'error': 'Symbol is required for AI analysis'
                    }
                }))
                
        elif message_type == 'get_all_ai_analysis':
            # Get AI analysis for all target pairs
            logger.info("Received get_all_ai_analysis request")
            all_analysis = {}
            
            for symbol in self.target_pairs:
                logger.info(f"Processing {symbol} for all analysis request")
                cached_analysis = self.ai_analysis_cache.get(symbol)
                current_time = time.time()
                last_analysis = self.last_analysis_time.get(symbol, 0)
                
                logger.info(f"Cache status for {symbol}: cached={cached_analysis is not None}, last_analysis={last_analysis}, current_time={current_time}, interval={self.analysis_interval}")
                
                # If no cached analysis or it's old, run new analysis
                if not cached_analysis or (current_time - last_analysis) >= self.analysis_interval:
                    logger.info(f"Running new analysis for {symbol}")
                    analysis = await self.run_ai_analysis_pipeline(symbol)
                else:
                    logger.info(f"Using cached analysis for {symbol}")
                    analysis = cached_analysis
                
                if analysis:
                    all_analysis[symbol] = analysis
                    logger.info(f"Added analysis for {symbol} to response")
                    logger.info(f"Analysis structure for {symbol}: {list(analysis.keys()) if isinstance(analysis, dict) else 'Not a dict'}")
                else:
                    logger.warning(f"No analysis available for {symbol}")
            
            logger.info(f"Sending all_ai_analysis_response with {len(all_analysis)} analyses")
            logger.info(f"Analysis symbols: {list(all_analysis.keys())}")
            logger.info(f"Full response data: {all_analysis}")
            
            # Debug: Check if we have any analysis data
            if all_analysis:
                logger.info(f"✅ Analysis data available: {len(all_analysis)} pairs")
                for symbol, analysis in all_analysis.items():
                    logger.info(f"  {symbol}: {analysis.get('symbol', 'NO_SYMBOL')} - {analysis.get('gpt_analysis', {}).get('direction', 'NO_DIRECTION')}")
            else:
                logger.warning("❌ No analysis data available to send")
            
            await websocket.send(json.dumps({
                'type': 'all_ai_analysis_response',
                'data': all_analysis
            }))
            
            logger.info(f"✅ all_ai_analysis_response sent to client")
                
        elif message_type == 'get_ai_opportunities':
            # Get all analysis results regardless of confidence
            opportunities = {}
            
            for symbol, analysis in self.ai_analysis_cache.items():
                # Include all analysis, not just high-confidence ones
                opportunities[symbol] = analysis
            
            await websocket.send(json.dumps({
                'type': 'ai_opportunities_response',
                'data': opportunities
            }))
                
        elif message_type == 'get_analysis_status':
            # Get current analysis status for all symbols
            status_data = {}
            for symbol in self.target_pairs:
                status_data[symbol] = {
                    'status': self.analysis_status.get(symbol, 'idle'),
                    'progress': self.analysis_progress.get(symbol, []),
                    'last_analysis': self.last_analysis_time.get(symbol, 0)
                }
            
            await websocket.send(json.dumps({
                'type': 'analysis_status_response',
                'data': status_data
            }))
                
        elif message_type == 'accept_trade':
            symbol = data.get('symbol')
            if symbol:
                result = await self.accept_trade(symbol, data)
                await websocket.send(json.dumps({
                    'type': 'trade_accepted',
                    'data': result
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'trade_accepted',
                    'data': {'success': False, 'error': 'Symbol is required for trade acceptance'}
                }))
                
        elif message_type == 'get_pending_trades':
            pending_trades_info = await self.get_pending_trades()
            await websocket.send(json.dumps({
                'type': 'pending_trades_response',
                'data': pending_trades_info
            }))
                
        elif message_type == 'get_news_data':
            # Send both Grok and CryptoPanic news data
            news_data = {
                'grok_news': {},
                'cryptopanic_news': {}
            }
            
            # Collect Grok news data
            for symbol in self.target_pairs:
                if symbol in self.news_cache and 'grok_data' in self.news_cache[symbol]:
                    news_data['grok_news'][symbol] = self.news_cache[symbol]['grok_data']
            
            # Collect CryptoPanic news data
            for symbol in self.target_pairs:
                if symbol in self.news_cache and 'cryptopanic_data' in self.news_cache[symbol]:
                    news_data['cryptopanic_news'][symbol] = self.news_cache[symbol]['cryptopanic_data']
            
            await websocket.send(json.dumps({
                'type': 'news_data_response',
                'data': news_data
            }))
                
        elif message_type == 'start_analysis':
            # Start AI analysis monitoring
            result = await self.start_analysis()
            await websocket.send(json.dumps({
                'type': 'start_analysis_response',
                'data': result
            }))
                
        elif message_type == 'stop_analysis':
            # Stop AI analysis monitoring
            result = await self.stop_analysis()
            await websocket.send(json.dumps({
                'type': 'stop_analysis_response',
                'data': result
            }))
                
        elif message_type == 'get_analysis_control_status':
            # Get current analysis control status
            status = await self.get_analysis_status()
            await websocket.send(json.dumps({
                'type': 'analysis_control_status_response',
                'data': status
            }))
        
        # Bot control messages
        elif message_type == 'start_bot':
            # Start the trading bot
            logger.info("🤖 Processing start_bot message")
            try:
                config = data.get('config', {})
                result = await self.start_bot(config)
                logger.info(f"🤖 Start bot result: {result}")
                response = json.dumps({
                    'type': 'start_bot_response',
                    'data': result
                })
                logger.info(f"🤖 Sending start_bot_response: {response}")
                await websocket.send(response)
                logger.info("🤖 Start bot response sent successfully")
            except Exception as e:
                logger.error(f"❌ Error in start_bot handler: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await websocket.send(json.dumps({
                    'type': 'start_bot_response',
                    'data': {'success': False, 'error': str(e)}
                }))
                
        elif message_type == 'stop_bot':
            # Stop the trading bot
            logger.info("🤖 Processing stop_bot message")
            try:
                result = await self.stop_bot()
                logger.info(f"🤖 Stop bot result: {result}")
                response = json.dumps({
                    'type': 'stop_bot_response',
                    'data': result
                })
                logger.info(f"🤖 Sending stop_bot_response: {response}")
                await websocket.send(response)
                logger.info("🤖 Stop bot response sent successfully")
            except Exception as e:
                logger.error(f"❌ Error in stop_bot handler: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await websocket.send(json.dumps({
                    'type': 'stop_bot_response',
                    'data': {'success': False, 'error': str(e)}
                }))
                
        elif message_type == 'get_bot_status':
            # Get current bot status
            logger.info("🤖 Processing get_bot_status message")
            try:
                status = await self.get_bot_status()
                logger.info(f"🤖 Bot status: {status}")
                await websocket.send(json.dumps({
                    'type': 'bot_status_response',
                    'data': status
                }))
                logger.info("🤖 Bot status response sent successfully")
            except Exception as e:
                logger.error(f"❌ Error in get_bot_status handler: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await websocket.send(json.dumps({
                    'type': 'bot_status_response',
                    'data': {'error': str(e)}
                }))
                
        elif message_type == 'update_bot_config':
            # Update bot configuration
            logger.info("🤖 Processing update_bot_config message")
            try:
                new_config = data.get('config', {})
                result = await self.update_bot_config(new_config)
                logger.info(f"🤖 Update bot config result: {result}")
                response = json.dumps({
                    'type': 'update_bot_config_response',
                    'data': result
                })
                logger.info(f"🤖 Sending update_bot_config_response: {response}")
                await websocket.send(response)
                logger.info("🤖 Update bot config response sent successfully")
            except Exception as e:
                logger.error(f"❌ Error in update_bot_config handler: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                await websocket.send(json.dumps({
                    'type': 'update_bot_config_response',
                    'data': {'success': False, 'error': str(e)}
                }))
                
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def broadcast_price_updates(self):
        """Broadcast price updates to all connected clients"""
        while True:
            try:
                # Fetch latest crypto data
                await self.fetch_crypto_data()
                
                # Broadcast price updates to all clients
                if self.clients:
                    # Send individual price updates for each symbol
                    for symbol, price_data in self.price_cache.items():
                        price_update = {
                            'symbol': symbol,
                            'price': price_data['price'],
                            'change_24h': price_data['change_24h'],
                            'volume': price_data['volume'],
                            'timestamp': price_data['timestamp']
                        }
                        
                        message = json.dumps({
                            'type': 'price_update',
                            'data': price_update
                        })
                        
                        # Debug logging for key symbols
                        if symbol in ['BTCUSDT', 'ETHUSDT', 'BTC', 'ETH']:
                            logger.info(f"Broadcasting price update for {symbol}: ${price_data['price']}")
                        
                        # Send to all connected clients
                        await asyncio.gather(
                            *[client.send(message) for client in self.clients],
                            return_exceptions=True
                        )
                
                # Wait 10 seconds before next update for more real-time prices
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                await asyncio.sleep(30)

    async def broadcast_analysis_status(self, symbol: str, status: str, message: str):
        """Broadcasts analysis status updates to all clients."""
        try:
            if self.clients:
                status_update = {
                    'type': 'analysis_status',
                    'data': {
                        'symbol': symbol,
                        'status': status,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }
                }
                await asyncio.gather(
                    *[client.send(json.dumps(status_update)) for client in self.clients],
                    return_exceptions=True
                )
        except Exception as e:
            logger.error(f"Error broadcasting analysis status: {e}")

async def main():
    """Main server function"""
    server = TradingServer()
    logger.info("Starting WebSocket server on ws://localhost:8765")
    
    # Fetch initial crypto data before starting AI monitoring
    logger.info("Fetching initial crypto data...")
    await server.fetch_crypto_data()
    logger.info(f"Initial data fetched. Price cache keys: {list(server.price_cache.keys())}")
    
    price_task = asyncio.create_task(server.broadcast_price_updates())
    ai_task = asyncio.create_task(server.continuous_ai_monitoring())
    bot_task = asyncio.create_task(server.continuous_bot_monitoring())

    # Create a wrapper function that matches the websockets library signature
    async def handler(websocket):
        await server.handle_client(websocket, "/")

    # Pass the wrapper function to websockets.serve
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.gather(
            price_task,
            ai_task,
            bot_task,
            return_exceptions=True
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 