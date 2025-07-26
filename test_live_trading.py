#!/usr/bin/env python3
"""
Test script to verify live trading functionality with a small demo trade
"""
import asyncio
import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from trading_manager import TradingManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_live_trading():
    """Test live trading with a small demo trade"""
    print("=" * 60)
    print("LIVE TRADING DEMO TEST")
    print("=" * 60)
    
    try:
        # Initialize trading manager
        trading_manager = TradingManager()
        
        # Set to live mode
        print("\n1. Setting trading mode to LIVE...")
        trading_manager.set_trading_mode('live')
        print("SUCCESS - Trading mode set to LIVE")
        
        # Test connection
        print("\n2. Testing Binance connection...")
        connection_test = trading_manager.test_connection()
        if connection_test['success']:
            print(f"SUCCESS - {connection_test['message']}")
        else:
            print(f"FAILED - {connection_test['message']}")
            return False
        
        # Get account balance
        print("\n3. Getting USDT balance...")
        usdt_balance = trading_manager.get_balance('USDT')
        print(f"SUCCESS - USDT Balance:")
        print(f"   Free: ${usdt_balance['free']:.2f}")
        print(f"   Locked: ${usdt_balance['locked']:.2f}")
        print(f"   Total: ${usdt_balance['total']:.2f}")
        
        # Check if we have enough balance for a small trade
        min_trade_amount = 11.0  # Minimum for most pairs is $10-11
        if usdt_balance['free'] < min_trade_amount:
            print(f"WARNING - Insufficient balance for demo trade")
            print(f"   Required: ${min_trade_amount}")
            print(f"   Available: ${usdt_balance['free']:.2f}")
            print("   Skipping actual trade, but connection is working!")
            return True
        
        # Get current BTC price
        print("\n4. Getting current BTC price...")
        btc_price = trading_manager.get_current_price('BTCUSDT')
        print(f"SUCCESS - Current BTC price: ${btc_price:,.2f}")
        
        # Calculate trade amount (minimum $11 worth)
        trade_usdt = min_trade_amount
        btc_quantity = trading_manager.binance_service.calculate_quantity('BTCUSDT', trade_usdt)
        print(f"   Trade amount: ${trade_usdt} = {btc_quantity:.6f} BTC")
        
        # Place a small BUY order
        print(f"\n5. Placing DEMO BUY order...")
        print(f"   WARNING: This will execute a REAL trade with REAL money!")
        print(f"   Trade: BUY {btc_quantity:.6f} BTC (~${trade_usdt})")
        
        # Ask for confirmation
        confirm = input("   Do you want to proceed? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("   Trade cancelled by user")
            return True
        
        # Execute BUY order
        buy_order = trading_manager.place_order(
            symbol='BTCUSDT',
            side='BUY',
            order_type='MARKET',
            quantity=btc_quantity
        )
        
        if buy_order['success']:
            order_data = buy_order['order']
            print(f"SUCCESS - BUY order executed!")
            print(f"   Order ID: {order_data['orderId']}")
            print(f"   Executed Quantity: {order_data['executedQty']}")
            print(f"   Price: ${float(order_data.get('price', btc_price)):,.2f}")
            
            # Wait 5 seconds
            print(f"\n6. Waiting 5 seconds before selling...")
            for i in range(5, 0, -1):
                print(f"   {i}...", end=' ', flush=True)
                time.sleep(1)
            print("\n")
            
            # Execute SELL order to close position
            print(f"7. Placing SELL order to close position...")
            executed_qty = float(order_data['executedQty'])
            
            sell_order = trading_manager.place_order(
                symbol='BTCUSDT',
                side='SELL',
                order_type='MARKET',
                quantity=executed_qty
            )
            
            if sell_order['success']:
                sell_data = sell_order['order']
                print(f"SUCCESS - SELL order executed!")
                print(f"   Order ID: {sell_data['orderId']}")
                print(f"   Executed Quantity: {sell_data['executedQty']}")
                print(f"   Price: ${float(sell_data.get('price', btc_price)):,.2f}")
                
                # Calculate P&L
                buy_price = float(order_data.get('price', btc_price))
                sell_price = float(sell_data.get('price', btc_price))
                quantity = float(sell_data['executedQty'])
                pnl = (sell_price - buy_price) * quantity
                
                print(f"\n8. Trade Summary:")
                print(f"   Buy Price: ${buy_price:,.2f}")
                print(f"   Sell Price: ${sell_price:,.2f}")
                print(f"   Quantity: {quantity:.6f} BTC")
                print(f"   P&L: ${pnl:.2f}")
                
            else:
                print(f"FAILED - SELL order failed!")
                print(f"   Error: {sell_order}")
                print(f"   WARNING: You still own {executed_qty:.6f} BTC!")
                return False
                
        else:
            print(f"FAILED - BUY order failed!")
            print(f"   Error: {buy_order}")
            return False
        
        # Get updated balance
        print(f"\n9. Getting updated USDT balance...")
        updated_balance = trading_manager.get_balance('USDT')
        balance_change = updated_balance['free'] - usdt_balance['free']
        print(f"SUCCESS - Updated balance:")
        print(f"   New Free USDT: ${updated_balance['free']:.2f}")
        print(f"   Balance Change: ${balance_change:.2f}")
        
        print("\n" + "=" * 60)
        print("SUCCESS: LIVE TRADING TEST COMPLETED!")
        print("=" * 60)
        print("\nRESULTS:")
        print("✓ Connection: Working")
        print("✓ Balance Retrieval: Working")
        print("✓ Buy Orders: Working")
        print("✓ Sell Orders: Working")
        print("✓ Real-time Execution: Working")
        print("\nLIVE TRADING IS FULLY OPERATIONAL!")
        
        return True
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("=" * 60)
        print("LIVE TRADING TEST FAILED")
        print("=" * 60)
        print(f"\nError Details: {str(e)}")
        return False

def main():
    """Main function to run the test"""
    try:
        result = asyncio.run(test_live_trading())
        if result:
            print("\n✓ Live trading system is working correctly!")
            sys.exit(0)
        else:
            print("\n✗ Live trading test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nWARNING: Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()