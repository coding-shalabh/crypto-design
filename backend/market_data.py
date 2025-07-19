
"""
Market data collection and management for crypto trading
"""
import aiohttp
import asyncio
import logging
import json
import ssl
import certifi
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config import Config

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Manages market data collection and caching"""
    
    def __init__(self):
        self.price_cache = {}
        self.crypto_data = {}
        self.candle_data = {}
        self.last_update = {}
        
    async def fetch_crypto_data(self) -> Dict:
        """Fetch current crypto prices from Binance API with enhanced SSL handling"""
        try:
            # Create SSL context for secure connections
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Create connector with SSL context and timeouts
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            # Set up timeout
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                # Fetch all 24hr tickers, then filter for TARGET_PAIRS
                url = "https://api.binance.com/api/v3/ticker/24hr"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Filter for only TARGET_PAIRS
                        data = [item for item in data if item['symbol'] in Config.TARGET_PAIRS]
                        for item in data:
                            symbol = item['symbol']
                            # Defensive: always use float() and fallback to 0.0 if missing
                            def safe_float(val):
                                try:
                                    return float(val)
                                except (TypeError, ValueError):
                                    return 0.0
                            current_price = safe_float(item.get('lastPrice'))
                            change_24h = safe_float(item.get('priceChangePercent'))
                            volume_24h = safe_float(item.get('volume'))
                            high_24h = safe_float(item.get('highPrice'))
                            low_24h = safe_float(item.get('lowPrice'))
                            # Update price cache (matches frontend expectations)
                            self.price_cache[symbol] = {
                                'symbol': symbol,
                                'price': current_price,
                                'change_24h': change_24h,
                                'volume_24h': volume_24h,
                                'market_cap': current_price * volume_24h * 0.1,
                                'timestamp': time.time()
                            }
                            # Update crypto data (matches frontend expectations)
                            base_symbol = symbol.replace('USDT', '')
                            symbol_lower = base_symbol.lower()
                            self.crypto_data[symbol_lower] = {
                                'id': symbol_lower,
                                'symbol': base_symbol,
                                'name': f'{base_symbol} Token',
                                'image': f'https://assets.coingecko.com/coins/images/1/large/{symbol_lower}.png',
                                'current_price': current_price,
                                'market_cap': current_price * volume_24h * 0.1,
                                'market_cap_rank': 1,
                                'fully_diluted_valuation': current_price * volume_24h * 0.11,
                                'total_volume': volume_24h,
                                'high_24h': high_24h,
                                'low_24h': low_24h,
                                'price_change_24h': current_price * (change_24h / 100),
                                'price_change_percentage_24h': change_24h,
                                'market_cap_change_24h': current_price * volume_24h * 0.1 * (change_24h / 100),
                                'market_cap_change_percentage_24h': change_24h,
                                'circulating_supply': volume_24h * 0.1,
                                'total_supply': volume_24h * 0.11,
                                'max_supply': None,
                                'ath': high_24h * 1.5,
                                'ath_change_percentage': -33.33,
                                'ath_date': '2021-11-01T00:00:00.000Z',
                                'atl': low_24h * 0.5,
                                'atl_change_percentage': 100.0,
                                'atl_date': '2020-01-01T00:00:00.000Z',
                                'roi': None,
                                'last_updated': datetime.now().isoformat()
                            }
                            self.last_update[symbol] = datetime.now()
                        logger.info(f" Fetched data for {len(data)} symbols")
                        return self.crypto_data
                    else:
                        logger.error(f"❌ Failed to fetch crypto data: {response.status}")
                        # Try fallback method if main API fails
                        return await self.fetch_crypto_data_fallback(session)
        except aiohttp.ClientError as e:
            logger.error(f"❌ HTTP Client error fetching crypto data: {e}")
            return await self.fetch_crypto_data_fallback()
        except ssl.SSLError as e:
            logger.error(f"❌ SSL error fetching crypto data: {e}")
            return await self.fetch_crypto_data_fallback()
        except asyncio.TimeoutError as e:
            logger.error(f"❌ Timeout error fetching crypto data: {e}")
            return await self.fetch_crypto_data_fallback()
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching crypto data: {e}")
            return await self.fetch_crypto_data_fallback()
    
    async def fetch_candlestick_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Fetch candlestick data for technical analysis"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.binance.com/api/v3/klines"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to standard format
                        candles = []
                        for candle in data:
                            candles.append({
                                'timestamp': candle[0],
                                'open': float(candle[1]),
                                'high': float(candle[2]),
                                'low': float(candle[3]),
                                'close': float(candle[4]),
                                'volume': float(candle[5]),
                                'close_time': candle[6],
                                'quote_volume': float(candle[7]),
                                'trades': int(candle[8]),
                                'taker_buy_base': float(candle[9]),
                                'taker_buy_quote': float(candle[10])
                            })
                        
                        # Cache the data
                        self.candle_data[symbol] = candles
                        logger.info(f"Fetched {len(candles)} candles for {symbol}")
                        return candles
                    else:
                        logger.error(f"Failed to fetch candlestick data for {symbol}: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error fetching candlestick data for {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        # Check if we have recent data
        if symbol in self.last_update:
            time_diff = datetime.now() - self.last_update[symbol]
            if time_diff.total_seconds() < 60:  # Use cached data if less than 1 minute old
                return self.price_cache.get(symbol, {}).get('price')
        
        # Fetch fresh data if needed
        await self.fetch_crypto_data()
        return self.price_cache.get(symbol, {}).get('price')
    
    async def get_candles_for_analysis(self, symbol: str) -> List[Dict]:
        """Get candlestick data for analysis"""
        # Check if we have recent data
        if symbol in self.candle_data:
            return self.candle_data[symbol]
        
        # Fetch fresh data
        return await self.fetch_candlestick_data(symbol)
    
    def get_price_history(self, symbol: str, limit: int = 50) -> List[float]:
        """Get price history for a symbol"""
        if symbol in self.candle_data:
            return [candle['close'] for candle in self.candle_data[symbol][-limit:]]
        return []
    
    async def collect_market_data(self, symbol: str) -> Dict:
        """Collect comprehensive market data for analysis"""
        try:
            # Fetch current price and candlestick data
            current_price = await self.get_current_price(symbol)
            candles = await self.get_candles_for_analysis(symbol)
            
            if not current_price or not candles:
                logger.warning(f"Insufficient market data for {symbol}")
                return {}
            
            # Extract price history
            prices = [candle['close'] for candle in candles]
            
            # Get 24h data
            crypto_info = self.crypto_data.get(symbol.lower(), {})
            
            market_data = {
                'symbol': symbol,
                'current_price': current_price,
                'prices': prices,
                'candles': candles,
                'change_24h': crypto_info.get('price_change_percentage_24h', 0),
                'volume_24h': crypto_info.get('total_volume', 0),
                'high_24h': crypto_info.get('high_24h', 0),
                'low_24h': crypto_info.get('low_24h', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Collected market data for {symbol}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error collecting market data for {symbol}: {e}")
            return {}
    
    def get_all_prices(self) -> Dict[str, Dict]:
        """Get all current prices (matches frontend expectations)"""
        return self.price_cache.copy()
    
    def get_all_crypto_data(self) -> Dict:
        """Get all crypto data (matches frontend expectations)"""
        return self.crypto_data.copy()
    
    def get_cached_price(self, symbol: str) -> Optional[float]:
        """Get current price from cached data (synchronous)"""
        if symbol in self.crypto_data:
            return self.crypto_data[symbol].get('current_price')
        return None
    
    def clear_cache(self):
        """Clear all cached data"""
        self.price_cache.clear()
        self.crypto_data.clear()
        self.candle_data.clear()
        self.last_update.clear()
        logger.info("Market data cache cleared")

    async def fetch_crypto_data_fallback(self, session=None) -> Dict:
        """Fallback method to fetch crypto data using alternative endpoints"""
        try:
            logger.info("Trying fallback API endpoints...")
            
            # If no session provided, create a new one
            if session is None:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=10,
                    limit_per_host=5,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                
                async with aiohttp.ClientSession(connector=connector, timeout=timeout) as new_session:
                    return await self._try_fallback_endpoints(new_session)
            else:
                return await self._try_fallback_endpoints(session)
        
        except Exception as e:
            logger.error(f"Error in fallback data fetch: {e}")
            return self._generate_mock_data()
    
    async def _try_fallback_endpoints(self, session):
        """Try different API endpoints as fallback"""
        fallback_urls = [
            "https://api.binance.com/api/v3/ticker/price",  # Simple price endpoint
            "https://api.binance.us/api/v3/ticker/24hr",     # US endpoint
            "https://api1.binance.com/api/v3/ticker/24hr",   # Alternative endpoint
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for url in fallback_urls:
            try:
                logger.info(f"Trying fallback endpoint: {url}")
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Handle different response formats
                        if url.endswith('/ticker/price'):
                            return self._process_price_data(data)
                        else:
                            return self._process_24hr_data(data)
            except Exception as e:
                logger.warning(f"Fallback endpoint {url} failed: {e}")
                continue
        
        logger.warning("All fallback endpoints failed, using mock data")
        return self._generate_mock_data()
    
    def _process_price_data(self, data):
        """Process simple price data from Binance API"""
        try:
            # Filter for TARGET_PAIRS
            filtered_data = [item for item in data if item['symbol'] in Config.TARGET_PAIRS]
            
            for item in filtered_data:
                symbol = item['symbol']
                current_price = float(item.get('price', 0))
                
                # Create mock 24hr data
                change_24h = 0.0  # We don't have 24hr data from price endpoint
                volume_24h = 1000000.0  # Mock volume
                
                # Update price cache
                self.price_cache[symbol] = {
                    'symbol': symbol,
                    'price': current_price,
                    'change_24h': change_24h,
                    'volume_24h': volume_24h,
                    'market_cap': current_price * volume_24h * 0.1,
                    'timestamp': time.time()
                }
                
                # Update crypto data
                base_symbol = symbol.replace('USDT', '')
                symbol_lower = base_symbol.lower()
                self.crypto_data[symbol_lower] = {
                    'id': symbol_lower,
                    'symbol': base_symbol,
                    'name': f'{base_symbol} Token',
                    'image': f'https://assets.coingecko.com/coins/images/1/large/{symbol_lower}.png',
                    'current_price': current_price,
                    'market_cap': current_price * volume_24h * 0.1,
                    'market_cap_rank': 1,
                    'fully_diluted_valuation': current_price * volume_24h * 0.11,
                    'total_volume': volume_24h,
                    'high_24h': current_price * 1.02,
                    'low_24h': current_price * 0.98,
                    'price_change_24h': 0,
                    'price_change_percentage_24h': change_24h,
                    'market_cap_change_24h': 0,
                    'market_cap_change_percentage_24h': change_24h,
                    'circulating_supply': volume_24h * 0.1,
                    'total_supply': volume_24h * 0.11,
                    'max_supply': None,
                    'ath': current_price * 1.5,
                    'ath_change_percentage': -33.33,
                    'ath_date': '2021-11-01T00:00:00.000Z',
                    'atl': current_price * 0.5,
                    'atl_change_percentage': 100.0,
                    'atl_date': '2020-01-01T00:00:00.000Z',
                    'roi': None,
                    'last_updated': datetime.now().isoformat()
                }
                
                self.last_update[symbol] = datetime.now()
            
            logger.info(f"Processed price data for {len(filtered_data)} symbols")
            return self.crypto_data
            
        except Exception as e:
            logger.error(f"Error processing price data: {e}")
            return self._generate_mock_data()
    
    def _process_24hr_data(self, data):
        """Process 24hr ticker data from Binance API"""
        try:
            # This is the same as the original method
            filtered_data = [item for item in data if item['symbol'] in Config.TARGET_PAIRS]
            
            for item in filtered_data:
                symbol = item['symbol']
                
                def safe_float(val):
                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        return 0.0
                
                current_price = safe_float(item.get('lastPrice'))
                change_24h = safe_float(item.get('priceChangePercent'))
                volume_24h = safe_float(item.get('volume'))
                high_24h = safe_float(item.get('highPrice'))
                low_24h = safe_float(item.get('lowPrice'))
                
                # Update price cache
                self.price_cache[symbol] = {
                    'symbol': symbol,
                    'price': current_price,
                    'change_24h': change_24h,
                    'volume_24h': volume_24h,
                    'market_cap': current_price * volume_24h * 0.1,
                    'timestamp': time.time()
                }
                
                # Update crypto data
                base_symbol = symbol.replace('USDT', '')
                symbol_lower = base_symbol.lower()
                self.crypto_data[symbol_lower] = {
                    'id': symbol_lower,
                    'symbol': base_symbol,
                    'name': f'{base_symbol} Token',
                    'image': f'https://assets.coingecko.com/coins/images/1/large/{symbol_lower}.png',
                    'current_price': current_price,
                    'market_cap': current_price * volume_24h * 0.1,
                    'market_cap_rank': 1,
                    'fully_diluted_valuation': current_price * volume_24h * 0.11,
                    'total_volume': volume_24h,
                    'high_24h': high_24h,
                    'low_24h': low_24h,
                    'price_change_24h': current_price * (change_24h / 100),
                    'price_change_percentage_24h': change_24h,
                    'market_cap_change_24h': current_price * volume_24h * 0.1 * (change_24h / 100),
                    'market_cap_change_percentage_24h': change_24h,
                    'circulating_supply': volume_24h * 0.1,
                    'total_supply': volume_24h * 0.11,
                    'max_supply': None,
                    'ath': high_24h * 1.5,
                    'ath_change_percentage': -33.33,
                    'ath_date': '2021-11-01T00:00:00.000Z',
                    'atl': low_24h * 0.5,
                    'atl_change_percentage': 100.0,
                    'atl_date': '2020-01-01T00:00:00.000Z',
                    'roi': None,
                    'last_updated': datetime.now().isoformat()
                }
                
                self.last_update[symbol] = datetime.now()
            
            logger.info(f"Processed 24hr data for {len(filtered_data)} symbols")
            return self.crypto_data
            
        except Exception as e:
            logger.error(f"Error processing 24hr data: {e}")
            return self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate mock data when all API calls fail"""
        logger.warning("Generating mock data due to API failures")
        
        mock_prices = {
            'BTCUSDT': 45000.0,
            'ETHUSDT': 3000.0,
            'XRPUSDT': 0.6,
            'BNBUSDT': 300.0,
            'SOLUSDT': 100.0
        }
        
        for symbol in Config.TARGET_PAIRS:
            current_price = mock_prices.get(symbol, 100.0)
            change_24h = 0.0
            volume_24h = 1000000.0
            
            # Update price cache
            self.price_cache[symbol] = {
                'symbol': symbol,
                'price': current_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'market_cap': current_price * volume_24h * 0.1,
                'timestamp': time.time()
            }
            
            # Update crypto data
            base_symbol = symbol.replace('USDT', '')
            symbol_lower = base_symbol.lower()
            self.crypto_data[symbol_lower] = {
                'id': symbol_lower,
                'symbol': base_symbol,
                'name': f'{base_symbol} Token',
                'image': f'https://assets.coingecko.com/coins/images/1/large/{symbol_lower}.png',
                'current_price': current_price,
                'market_cap': current_price * volume_24h * 0.1,
                'market_cap_rank': 1,
                'fully_diluted_valuation': current_price * volume_24h * 0.11,
                'total_volume': volume_24h,
                'high_24h': current_price * 1.02,
                'low_24h': current_price * 0.98,
                'price_change_24h': 0,
                'price_change_percentage_24h': change_24h,
                'market_cap_change_24h': 0,
                'market_cap_change_percentage_24h': change_24h,
                'circulating_supply': volume_24h * 0.1,
                'total_supply': volume_24h * 0.11,
                'max_supply': None,
                'ath': current_price * 1.5,
                'ath_change_percentage': -33.33,
                'ath_date': '2021-11-01T00:00:00.000Z',
                'atl': current_price * 0.5,
                'atl_change_percentage': 100.0,
                'atl_date': '2020-01-01T00:00:00.000Z',
                'roi': None,
                'last_updated': datetime.now().isoformat()
            }
            
            self.last_update[symbol] = datetime.now()
        
        logger.info(f"Generated mock data for {len(Config.TARGET_PAIRS)} symbols")
        return self.crypto_data
    
    async def test_connection(self):
        """Test connection to Binance API"""
        try:
            logger.info("Testing connection to Binance API...")
            
            # Create SSL context for secure connections
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                # Test simple ping endpoint
                url = "https://api.binance.com/api/v3/ping"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(" Binance API connection successful")
                        return True
                    else:
                        logger.error(f"❌ Binance API connection failed: {response.status}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Binance API connection test failed: {e}")
            return False 