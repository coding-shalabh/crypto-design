#!/usr/bin/env python3
"""
Test script to diagnose Binance API connection issues
"""
import asyncio
import aiohttp
import ssl
import certifi
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BinanceConnectionTester:
    def __init__(self):
        self.test_results = []
    
    async def test_basic_connection(self):
        """Test basic connection to Binance API"""
        logger.info("🔍 Testing basic connection to Binance API...")
        
        try:
            # Create SSL context
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
                # Test ping endpoint
                url = "https://api.binance.com/api/v3/ping"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info(" Binance API ping successful")
                        self.test_results.append(("Basic Connection", " PASS"))
                        return True
                    else:
                        logger.error(f"❌ Binance API ping failed: {response.status}")
                        self.test_results.append(("Basic Connection", f"❌ FAIL - Status: {response.status}"))
                        return False
        
        except Exception as e:
            logger.error(f"❌ Basic connection test failed: {e}")
            self.test_results.append(("Basic Connection", f"❌ FAIL - Error: {str(e)}"))
            return False
    
    async def test_server_time(self):
        """Test server time endpoint"""
        logger.info("🔍 Testing server time endpoint...")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                url = "https://api.binance.com/api/v3/time"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        server_time = data.get('serverTime', 0)
                        server_datetime = datetime.fromtimestamp(server_time / 1000)
                        logger.info(f" Server time: {server_datetime}")
                        self.test_results.append(("Server Time", " PASS"))
                        return True
                    else:
                        logger.error(f"❌ Server time failed: {response.status}")
                        self.test_results.append(("Server Time", f"❌ FAIL - Status: {response.status}"))
                        return False
        
        except Exception as e:
            logger.error(f"❌ Server time test failed: {e}")
            self.test_results.append(("Server Time", f"❌ FAIL - Error: {str(e)}"))
            return False
    
    async def test_exchange_info(self):
        """Test exchange info endpoint"""
        logger.info("🔍 Testing exchange info endpoint...")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=15, connect=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                url = "https://api.binance.com/api/v3/exchangeInfo"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        symbols_count = len(data.get('symbols', []))
                        logger.info(f" Exchange info: {symbols_count} symbols available")
                        self.test_results.append(("Exchange Info", " PASS"))
                        return True
                    else:
                        logger.error(f"❌ Exchange info failed: {response.status}")
                        self.test_results.append(("Exchange Info", f"❌ FAIL - Status: {response.status}"))
                        return False
        
        except Exception as e:
            logger.error(f"❌ Exchange info test failed: {e}")
            self.test_results.append(("Exchange Info", f"❌ FAIL - Error: {str(e)}"))
            return False
    
    async def test_24hr_ticker(self):
        """Test 24hr ticker endpoint"""
        logger.info("🔍 Testing 24hr ticker endpoint...")
        
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                url = "https://api.binance.com/api/v3/ticker/24hr"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        ticker_count = len(data)
                        logger.info(f" 24hr ticker: {ticker_count} tickers received")
                        
                        # Check for specific symbols
                        target_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
                        found_symbols = [item['symbol'] for item in data if item['symbol'] in target_symbols]
                        logger.info(f" Found target symbols: {found_symbols}")
                        
                        self.test_results.append(("24hr Ticker", " PASS"))
                        return True
                    else:
                        logger.error(f"❌ 24hr ticker failed: {response.status}")
                        self.test_results.append(("24hr Ticker", f"❌ FAIL - Status: {response.status}"))
                        return False
        
        except Exception as e:
            logger.error(f"❌ 24hr ticker test failed: {e}")
            self.test_results.append(("24hr Ticker", f"❌ FAIL - Error: {str(e)}"))
            return False
    
    async def test_fallback_endpoints(self):
        """Test fallback endpoints"""
        logger.info("🔍 Testing fallback endpoints...")
        
        fallback_urls = [
            "https://api.binance.com/api/v3/ticker/price",
            "https://api.binance.us/api/v3/ticker/24hr",
            "https://api1.binance.com/api/v3/ticker/24hr",
        ]
        
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=15, connect=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            for url in fallback_urls:
                try:
                    logger.info(f"Testing fallback: {url}")
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f" Fallback {url} - Status: {response.status}, Data length: {len(data)}")
                            self.test_results.append((f"Fallback {url}", " PASS"))
                        else:
                            logger.warning(f"⚠️ Fallback {url} - Status: {response.status}")
                            self.test_results.append((f"Fallback {url}", f"⚠️ FAIL - Status: {response.status}"))
                except Exception as e:
                    logger.warning(f"⚠️ Fallback {url} failed: {e}")
                    self.test_results.append((f"Fallback {url}", f"⚠️ FAIL - Error: {str(e)}"))
    
    async def run_all_tests(self):
        """Run all connection tests"""
        logger.info("🚀 Starting Binance API connection tests...")
        
        tests = [
            self.test_basic_connection,
            self.test_server_time,
            self.test_exchange_info,
            self.test_24hr_ticker,
            self.test_fallback_endpoints
        ]
        
        for test in tests:
            await test()
            await asyncio.sleep(1)  # Brief pause between tests
        
        # Print summary
        logger.info("\n" + "="*50)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("="*50)
        
        for test_name, result in self.test_results:
            logger.info(f"{test_name}: {result}")
        
        # Count results
        passed = sum(1 for _, result in self.test_results if result.startswith(""))
        failed = sum(1 for _, result in self.test_results if result.startswith("❌"))
        warnings = sum(1 for _, result in self.test_results if result.startswith("⚠️"))
        
        logger.info(f"\n Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"⚠️ Warnings: {warnings}")
        
        if failed == 0:
            logger.info("\n🎉 All critical tests passed! Binance API connection should work.")
        else:
            logger.error("\n💥 Some tests failed. Check your network connection and firewall settings.")
        
        return failed == 0

async def main():
    """Main test function"""
    tester = BinanceConnectionTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("🎉 Connection test completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())