#!/usr/bin/env python3
"""
Test script to verify Binance API connectivity and functionality
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from binance_service import BinanceService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_binance_api():
    """Test Binance API functionality"""
    print("=" * 60)
    print("BINANCE API CONNECTIVITY TEST")
    print("=" * 60)
    
    try:
        # Initialize Binance service
        binance = BinanceService()
        
        # Test 1: Basic connectivity
        print("\n1. Testing basic connectivity...")
        if binance.test_connectivity():
            print("PASS - Basic connectivity: PASSED")
        else:
            print("FAIL - Basic connectivity: FAILED")
            return False
        
        # Test 2: Get account information
        print("\n2. Testing account information...")
        try:
            account_info = binance.get_account_info()
            print(f"PASS - Account info retrieved successfully")
            print(f"   Account Type: {account_info.get('accountType', 'N/A')}")
            print(f"   Can Trade: {account_info.get('canTrade', 'N/A')}")
            print(f"   Can Withdraw: {account_info.get('canWithdraw', 'N/A')}")
            print(f"   Can Deposit: {account_info.get('canDeposit', 'N/A')}")
        except Exception as e:
            print(f"FAIL - Account info: FAILED - {e}")
            return False
        
        # Test 3: Get USDT balance
        print("\n3. Testing USDT balance retrieval...")
        try:
            usdt_balance = binance.get_balance('USDT')
            print(f"PASS - USDT balance retrieved successfully")
            print(f"   Free USDT: {usdt_balance['free']}")
            print(f"   Locked USDT: {usdt_balance['locked']}")
            print(f"   Total USDT: {usdt_balance['total']}")
        except Exception as e:
            print(f"FAIL - USDT balance: FAILED - {e}")
            return False
        
        # Test 4: Get all non-zero balances
        print("\n4. Testing all balances retrieval...")
        try:
            all_balances = binance.get_all_balances()
            print(f"PASS - All balances retrieved successfully")
            print(f"   Assets with balance: {len(all_balances)}")
            for balance in all_balances[:5]:  # Show first 5
                print(f"   {balance['asset']}: {balance['total']}")
            if len(all_balances) > 5:
                print(f"   ... and {len(all_balances) - 5} more assets")
        except Exception as e:
            print(f"FAIL - All balances: FAILED - {e}")
            return False
        
        # Test 5: Get current BTC price
        print("\n5. Testing price retrieval...")
        try:
            btc_price = binance.get_current_price('BTCUSDT')
            print(f"PASS - BTC price retrieved successfully")
            print(f"   Current BTC/USDT price: ${btc_price:,.2f}")
        except Exception as e:
            print(f"FAIL - Price retrieval: FAILED - {e}")
            return False
        
        # Test 6: Get symbol info
        print("\n6. Testing symbol information...")
        try:
            symbol_info = binance.get_symbol_info('BTCUSDT')
            print(f"PASS - Symbol info retrieved successfully")
            print(f"   Symbol: {symbol_info['symbol']}")
            print(f"   Status: {symbol_info['status']}")
            print(f"   Base Asset: {symbol_info['baseAsset']}")
            print(f"   Quote Asset: {symbol_info['quoteAsset']}")
        except Exception as e:
            print(f"FAIL - Symbol info: FAILED - {e}")
            return False
        
        # Test 7: Calculate proper quantity (for potential orders)
        print("\n7. Testing quantity calculation...")
        try:
            # Calculate quantity for $10 worth of BTC
            quantity = binance.calculate_quantity('BTCUSDT', 10.0)
            print(f"PASS - Quantity calculation successful")
            print(f"   $10 worth of BTC = {quantity:.8f} BTC")
        except Exception as e:
            print(f"FAIL - Quantity calculation: FAILED - {e}")
            return False
        
        # Test 8: Get open orders (should be empty or show existing)
        print("\n8. Testing open orders retrieval...")
        try:
            open_orders = binance.get_open_orders()
            print(f"PASS - Open orders retrieved successfully")
            print(f"   Current open orders: {len(open_orders)}")
            if open_orders:
                for order in open_orders[:3]:  # Show first 3
                    print(f"   Order {order['orderId']}: {order['symbol']} {order['side']} {order['origQty']}")
        except Exception as e:
            print(f"FAIL - Open orders: FAILED - {e}")
            return False
        
        print("\n" + "=" * 60)
        print("SUCCESS: ALL TESTS PASSED - BINANCE API IS WORKING CORRECTLY!")
        print("=" * 60)
        print("\nSUMMARY: SUMMARY:")
        print("PASS - API Connectivity: Working")
        print("PASS - Authentication: Valid")
        print("PASS - Account Access: Enabled")
        print("PASS - Balance Retrieval: Working")
        print("PASS - Price Data: Working")
        print("PASS - Trading Information: Available")
        print("\nREADY: Ready for Live Trading!")
        
        return True
        
    except Exception as e:
        print(f"\nFAIL - CRITICAL ERROR: {e}")
        print("=" * 60)
        print("FAILED: BINANCE API TEST FAILED")
        print("=" * 60)
        print("\nTROUBLESHOOTING: TROUBLESHOOTING STEPS:")
        print("1. Check your API key and secret in .env file")
        print("2. Ensure API key has trading permissions enabled")
        print("3. Verify your IP is whitelisted (if applicable)")
        print("4. Check your internet connection")
        print("5. Verify Binance API is not under maintenance")
        return False

def main():
    """Main function to run the test"""
    try:
        # Run the async test
        result = asyncio.run(test_binance_api())
        if result:
            print("\nPASS - Binance API is ready for integration!")
            sys.exit(0)
        else:
            print("\nFAIL - Binance API test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nWARNING: Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAIL - Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()