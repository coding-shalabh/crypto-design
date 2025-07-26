#!/usr/bin/env python3
"""
Futures Trading Test Script with Live PnL Tracking
- Fetches current balances categorized by wallet type
- Places a futures trade if USDT balance > 0
- Shows live PnL data for 20 seconds
- Automatically closes the position

Usage: python test_futures_trading.py
"""

import os
import sys
import time
import threading
from decimal import Decimal
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_service import BinanceService
from trading_manager import TradingManager

class FuturesTradingTest:
    def __init__(self):
        self.binance = BinanceService()
        self.trading_manager = TradingManager()
        self.trading_manager.set_trading_mode('live')  # Set to live mode for real trading
        self.position_data = None
        self.initial_balance = 0
        self.running = False
        
    def print_separator(self, title):
        """Print a nice separator"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
        
    def format_number(self, num):
        """Format numbers for display"""
        if abs(num) < 0.01:
            return f"{num:.8f}"
        else:
            return f"{num:.4f}"
            
    def get_futures_balance(self):
        """Get USDT futures balance"""
        try:
            # Try direct futures balance first
            futures_balances = self.binance.get_futures_balances()
            for balance in futures_balances:
                if balance['asset'] == 'USDT':
                    return float(balance.get('free', 0))
            
            # Fallback to trading manager
            balance = self.trading_manager.get_trading_balance('USDT')
            if balance and balance.get('wallet_type') == 'FUTURES':
                return float(balance.get('free', 0))
            return 0
        except Exception as e:
            print(f"[ERROR] Error getting futures balance: {e}")
            return 0
            
    def get_current_price(self, symbol):
        """Get current market price for symbol"""
        try:
            response = self.binance._make_futures_request('/fapi/v1/ticker/price', {'symbol': symbol})
            return float(response.get('price', 0))
        except Exception as e:
            print(f"[ERROR] Error getting price for {symbol}: {e}")
            return 0
            
    def get_position_info(self, symbol):
        """Get current position information"""
        try:
            response = self.binance._make_futures_request('/fapi/v2/positionRisk', {'symbol': symbol})
            for pos in response:
                if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                    return {
                        'symbol': pos['symbol'],
                        'size': float(pos['positionAmt']),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos['markPrice']),
                        'unrealized_pnl': float(pos['unRealizedProfit']),
                        'percentage': float(pos['percentage'])
                    }
            return None
        except Exception as e:
            print(f"[ERROR] Error getting position info: {e}")
            return None
            
    def calculate_quantity(self, balance, price, leverage=1):
        """Calculate quantity based on balance and leverage"""
        # Use 50% of balance for the trade (more conservative)
        trade_amount = balance * 0.5
        # Apply leverage (using 1x for safer testing)
        notional_value = trade_amount * leverage
        # Calculate quantity
        quantity = notional_value / price
        
        # Ensure minimum quantity and round to appropriate precision
        min_quantity = 0.001  # Minimum for BTCUSDT
        if quantity < min_quantity:
            quantity = min_quantity
            
        # Round to appropriate precision (BTCUSDT typically allows 3 decimal places)
        return round(quantity, 3)
        
    def place_futures_trade(self, symbol='BTCUSDT', side='BUY'):
        """Place a futures trade"""
        try:
            current_price = self.get_current_price(symbol)
            if current_price == 0:
                print(f"[ERROR] Could not get current price for {symbol}")
                return None
                
            balance = self.get_futures_balance()
            if balance <= 0:
                print(f"[ERROR] Insufficient USDT balance: {balance}")
                return None
                
            print(f"[INFO] Current {symbol} price: ${self.format_number(current_price)}")
            print(f"[INFO] Available USDT balance: ${self.format_number(balance)}")
            
            # Calculate quantity (using 1x leverage, 50% of balance for safer testing)
            quantity = self.calculate_quantity(balance, current_price)
            
            print(f"[TRADE] Placing {side} order for {quantity} {symbol}")
            print(f"[TRADE] Order type: MARKET")
            
            # Place market order
            order_result = self.binance.place_futures_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type='MARKET'
            )
            
            if order_result:
                print(f"[SUCCESS] Order placed successfully!")
                print(f"[ORDER] Order ID: {order_result.get('orderId')}")
                print(f"[ORDER] Status: {order_result.get('status')}")
                return order_result
            else:
                print(f"[ERROR] Failed to place order")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error placing futures trade: {e}")
            return None
            
    def close_position(self, symbol='BTCUSDT'):
        """Close the current position"""
        try:
            position = self.get_position_info(symbol)
            if not position:
                print(f"[INFO] No open position found for {symbol}")
                return True
                
            # Determine opposite side to close position
            close_side = 'SELL' if position['size'] > 0 else 'BUY'
            close_quantity = abs(position['size'])
            
            print(f"\n[CLOSE] Closing position...")
            print(f"[CLOSE] Position size: {self.format_number(position['size'])}")
            print(f"[CLOSE] Close side: {close_side}")
            print(f"[CLOSE] Close quantity: {self.format_number(close_quantity)}")
            
            # Place market order to close position
            close_order = self.binance.place_futures_order(
                symbol=symbol,
                side=close_side,
                quantity=close_quantity,
                order_type='MARKET'
            )
            
            if close_order:
                print(f"[SUCCESS] Position closed successfully!")
                print(f"[CLOSE] Order ID: {close_order.get('orderId')}")
                return True
            else:
                print(f"[ERROR] Failed to close position")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error closing position: {e}")
            return False
            
    def display_live_pnl(self, symbol='BTCUSDT', duration=20):
        """Display live PnL data for specified duration"""
        print(f"\n[LIVE] Starting live PnL tracking for {duration} seconds...")
        print("[LIVE] Press Ctrl+C to stop early")
        
        start_time = time.time()
        self.running = True
        
        try:
            while self.running and (time.time() - start_time) < duration:
                position = self.get_position_info(symbol)
                current_price = self.get_current_price(symbol)
                current_balance = self.get_futures_balance()
                
                # Clear previous line and print new data
                print(f"\r[LIVE] Time: {int(time.time() - start_time):02d}s | Price: ${self.format_number(current_price):>10} | Balance: ${self.format_number(current_balance):>10}", end="")
                
                if position:
                    pnl = position['unrealized_pnl']
                    pnl_pct = position['percentage']
                    entry_price = position['entry_price']
                    size = position['size']
                    
                    pnl_color = "+" if pnl >= 0 else ""
                    print(f" | Size: {self.format_number(size):>8} | Entry: ${self.format_number(entry_price):>10} | PnL: {pnl_color}{self.format_number(pnl):>8} ({pnl_color}{self.format_number(pnl_pct):>6}%)", end="")
                else:
                    print(" | Position: CLOSED", end="")
                    
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n[INFO] Live tracking stopped by user")
            self.running = False
            
        print(f"\n[LIVE] Live tracking completed")
        
    def run_test(self):
        """Run the complete futures trading test"""
        self.print_separator("FUTURES TRADING TEST WITH LIVE PnL")
        print(f"[TIME] Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Check current balances
        print("\n[STEP 1] Checking current balances...")
        try:
            balance = self.get_futures_balance()
            self.initial_balance = balance
            print(f"[BALANCE] USDT Futures Balance: ${self.format_number(balance)}")
            
            if balance <= 0:
                print("[ERROR] No USDT balance available for trading")
                return
                
        except Exception as e:
            print(f"[ERROR] Error checking balances: {e}")
            return
            
        # Step 2: Place futures trade
        print("\n[STEP 2] Placing futures trade...")
        symbol = 'BTCUSDT'
        side = 'BUY'  # You can change this to 'SELL' for short position
        
        order_result = self.place_futures_trade(symbol, side)
        if not order_result:
            print("[ERROR] Failed to place trade, exiting...")
            return
            
        # Wait a moment for order to fill
        time.sleep(2)
        
        # Step 3: Display live PnL for 20 seconds
        print("\n[STEP 3] Monitoring live PnL...")
        self.display_live_pnl(symbol, duration=20)
        
        # Step 4: Close position
        print("\n[STEP 4] Closing position...")
        success = self.close_position(symbol)
        
        # Step 5: Final summary
        print("\n[STEP 5] Final summary...")
        try:
            final_balance = self.get_futures_balance()
            pnl_realized = final_balance - self.initial_balance
            
            print(f"[SUMMARY] Initial Balance: ${self.format_number(self.initial_balance)}")
            print(f"[SUMMARY] Final Balance: ${self.format_number(final_balance)}")
            print(f"[SUMMARY] Realized PnL: {'+' if pnl_realized >= 0 else ''}{self.format_number(pnl_realized)} USDT")
            
            if success:
                print("[SUCCESS] Test completed successfully!")
            else:
                print("[WARNING] Test completed with some issues")
                
        except Exception as e:
            print(f"[ERROR] Error getting final summary: {e}")
            
        self.print_separator("TEST COMPLETED")
        print(f"[TIME] Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    try:
        # Check API credentials first
        binance = BinanceService()
        if not binance.api_key or not binance.api_secret:
            print("[ERROR] Binance API credentials not found!")
            print("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
            return
            
        # Test connectivity
        if not binance.test_connectivity():
            print("[ERROR] Could not connect to Binance API")
            return
            
        # Run the test
        test = FuturesTradingTest()
        test.run_test()
        
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    main()