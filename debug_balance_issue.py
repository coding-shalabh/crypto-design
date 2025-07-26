#!/usr/bin/env python3
"""
Debug script to test balance fetching and identify issues
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test if required environment variables are set"""
    print(" Testing Environment Variables:")
    print("=" * 50)
    
    required_vars = ['BINANCE_API_KEY', 'BINANCE_API_SECRET']
    optional_vars = ['OPEN_ROUTER', 'CRYPTOPANIC_API_KEY', 'REDIS_URL']
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}... (length: {len(value)})")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    print("\nOptional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 10)}... (length: {len(value)})")
        else:
            print(f"⚠️  {var}: NOT SET")
    
    return all_good

def test_binance_connection():
    """Test Binance API connection"""
    print("\n Testing Binance API Connection:")
    print("=" * 50)
    
    try:
        from binance_service import BinanceService
        
        binance = BinanceService()
        
        # Test basic connectivity
        print("Testing basic connectivity...")
        connectivity = binance.test_connectivity()
        print(f"Connectivity test: {'✅ SUCCESS' if connectivity else '❌ FAILED'}")
        
        if not connectivity:
            print("❌ Basic connectivity failed - API credentials may be invalid")
            return False
        
        # Test account info
        print("\nTesting account info...")
        try:
            account_info = binance.get_account_info()
            print(f"✅ Account info retrieved successfully")
            print(f"   Account type: {account_info.get('accountType', 'Unknown')}")
            print(f"   Permissions: {account_info.get('permissions', [])}")
        except Exception as e:
            print(f"❌ Failed to get account info: {e}")
            return False
        
        # Test spot balances
        print("\nTesting spot balances...")
        try:
            spot_balances = binance.get_spot_balances()
            print(f"✅ Spot balances retrieved: {len(spot_balances)} assets")
            for balance in spot_balances[:5]:  # Show first 5
                print(f"   {balance['asset']}: {balance['total']} (free: {balance['free']})")
        except Exception as e:
            print(f"❌ Failed to get spot balances: {e}")
        
        # Test futures balances
        print("\nTesting futures balances...")
        try:
            futures_balances = binance.get_futures_balances()
            print(f"✅ Futures balances retrieved: {len(futures_balances)} assets")
            for balance in futures_balances[:5]:  # Show first 5
                print(f"   {balance['asset']}: {balance['total']} (free: {balance['free']})")
        except Exception as e:
            print(f"❌ Failed to get futures balances: {e}")
        
        # Test specific USDT balance
        print("\nTesting USDT balance specifically...")
        try:
            usdt_balance = binance.get_balance('USDT')
            print(f"✅ USDT Spot balance: {usdt_balance}")
        except Exception as e:
            print(f"❌ Failed to get USDT balance: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize Binance service: {e}")
        return False

def test_trading_manager():
    """Test trading manager balance fetching"""
    print("\n Testing Trading Manager:")
    print("=" * 50)
    
    try:
        from trading_manager import TradingManager
        
        trading_manager = TradingManager()
        
        # Test mock mode
        print("Testing mock mode...")
        trading_manager.set_trading_mode('mock')
        mock_balance = trading_manager.get_trading_balance('USDT')
        print(f"✅ Mock balance: {mock_balance}")
        
        # Test live mode
        print("\nTesting live mode...")
        trading_manager.set_trading_mode('live')
        try:
            live_balance = trading_manager.get_trading_balance('USDT')
            print(f"✅ Live balance: {live_balance}")
        except Exception as e:
            print(f"❌ Failed to get live balance: {e}")
        
        # Test connection
        print("\nTesting connection...")
        try:
            connection_test = trading_manager.test_connection()
            print(f"✅ Connection test: {connection_test}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test trading manager: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Starting Balance Issue Diagnostic")
    print("=" * 60)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables are not properly configured!")
        print("Please check your .env file and ensure BINANCE_API_KEY and BINANCE_API_SECRET are set.")
        return
    
    # Test Binance connection
    binance_ok = test_binance_connection()
    
    if not binance_ok:
        print("\n❌ Binance API connection failed!")
        print("Please check your API credentials and ensure they have the correct permissions.")
        return
    
    # Test trading manager
    trading_ok = test_trading_manager()
    
    if not trading_ok:
        print("\n❌ Trading manager test failed!")
        return
    
    print("\n✅ All tests completed successfully!")
    print("If you're still seeing balance issues in the frontend, check the WebSocket connection and message handling.")

if __name__ == "__main__":
    main() 