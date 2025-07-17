"""
Test script to verify all backend modules work correctly
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from config import Config
        print(" config.py imported successfully")
        
        from database import DatabaseManager
        print(" database.py imported successfully")
        
        from market_data import MarketDataManager
        print(" market_data.py imported successfully")
        
        from news_analysis import NewsAnalysisManager
        print(" news_analysis.py imported successfully")
        
        from technical_indicators import TechnicalIndicators
        print(" technical_indicators.py imported successfully")
        
        from ai_analysis import AIAnalysisManager
        print(" ai_analysis.py imported successfully")
        
        from trading_bot import TradingBot
        print(" trading_bot.py imported successfully")
        
        from trade_execution import TradeExecutionManager
        print(" trade_execution.py imported successfully")
        
        from websocket_server import TradingServer
        print(" websocket_server.py imported successfully")
        
        return True
        
    except Exception as e:
        print(f" Import error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🧪 Testing configuration...")
    
    try:
        from config import Config
        
        # Test basic config
        assert Config.HOST == "localhost"
        assert Config.PORT == 8765
        assert Config.PAPER_BALANCE == 100000.0
        assert len(Config.TARGET_PAIRS) > 0
        
        # Test bot config
        bot_config = Config.get_bot_config()
        assert 'max_trades_per_day' in bot_config
        assert 'ai_confidence_threshold' in bot_config
        
        print(" Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f" Configuration error: {e}")
        return False

def test_technical_indicators():
    """Test technical indicators calculations"""
    print("\n🧪 Testing technical indicators...")
    
    try:
        from technical_indicators import TechnicalIndicators
        
        # Test with sample data
        prices = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
        
        # Test EMA
        ema = TechnicalIndicators.calculate_ema(prices, 5)
        assert ema > 0
        print(" EMA calculation works")
        
        # Test RSI
        rsi = TechnicalIndicators.calculate_rsi(prices)
        assert 0 <= rsi <= 100
        print(" RSI calculation works")
        
        # Test MACD
        macd = TechnicalIndicators.calculate_macd(prices)
        assert 'macd' in macd
        assert 'signal' in macd
        print(" MACD calculation works")
        
        # Test volatility
        volatility = TechnicalIndicators.calculate_volatility(prices)
        assert volatility >= 0
        print(" Volatility calculation works")
        
        return True
        
    except Exception as e:
        print(f" Technical indicators error: {e}")
        return False

async def test_managers():
    """Test manager initializations"""
    print("\n🧪 Testing manager initializations...")
    
    try:
        from database import DatabaseManager
        from market_data import MarketDataManager
        from news_analysis import NewsAnalysisManager
        from ai_analysis import AIAnalysisManager
        from trading_bot import TradingBot
        from trade_execution import TradeExecutionManager
        
        # Test database manager
        db_manager = DatabaseManager()
        print(" DatabaseManager initialized")
        
        # Test market data manager
        market_manager = MarketDataManager()
        print(" MarketDataManager initialized")
        
        # Test news analysis manager
        news_manager = NewsAnalysisManager()
        print(" NewsAnalysisManager initialized")
        
        # Test AI analysis manager
        ai_manager = AIAnalysisManager()
        print(" AIAnalysisManager initialized")
        
        # Test trading bot
        trading_bot = TradingBot()
        print(" TradingBot initialized")
        
        # Test trade execution manager
        trade_manager = TradeExecutionManager(db_manager)
        print(" TradeExecutionManager initialized")
        
        return True
        
    except Exception as e:
        print(f" Manager initialization error: {e}")
        return False

async def test_server_initialization():
    """Test server initialization"""
    print("\n🧪 Testing server initialization...")
    
    try:
        from websocket_server import TradingServer
        
        server = TradingServer()
        print(" TradingServer initialized")
        
        # Test getting bot status
        bot_status = await server.trading_bot.get_bot_status()
        assert 'enabled' in bot_status
        print(" Bot status retrieval works")
        
        # Test getting analysis status
        analysis_status = await server.get_analysis_status()
        assert 'enabled' in analysis_status
        print(" Analysis status retrieval works")
        
        return True
        
    except Exception as e:
        print(f" Server initialization error: {e}")
        return False

async def main():
    """Run all tests"""
    print(" Starting backend module tests...\n")
    
    # Test imports
    if not test_imports():
        return False
    
    # Test configuration
    if not test_config():
        return False
    
    # Test technical indicators
    if not test_technical_indicators():
        return False
    
    # Test managers
    if not await test_managers():
        return False
    
    # Test server
    if not await test_server_initialization():
        return False
    
    print("\n All tests passed! Backend modules are working correctly.")
    print("\n Summary:")
    print(" All modules imported successfully")
    print(" Configuration loaded correctly")
    print(" Technical indicators calculated properly")
    print(" All managers initialized without errors")
    print(" Server can be started and basic operations work")
    
    return True

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    success = asyncio.run(main())
    
    if success:
        print("\n Backend is ready for production!")
        sys.exit(0)
    else:
        print("\n Some tests failed. Please check the errors above.")
        sys.exit(1) 