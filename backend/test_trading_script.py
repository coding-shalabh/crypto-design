#!/usr/bin/env python3
"""
Test script to place trades based on fetched prices and automatically close them after 20 seconds
Usage: python test_trading_script.py
"""

import os
import sys
import time
import threading
from decimal import Decimal
from datetime import datetime

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_service import BinanceService
from trading_manager import TradingManager

class TradingTest:
    def __init__(self):
        self.binance = BinanceService()
        self.trading_manager = TradingManager()
        self.active_orders = []
        self.test_symbol = "BTCUSDT"
        self.trade_quantity = 0.001  # Small test quantity
        self.close_timer = None
        
    def print_separator(self, title):
        """Print a nice separator"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)

    def log(self, message, level="INFO"):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def check_api_credentials(self):
        """Check if API credentials are available"""
        self.log("Checking API credentials...")
        
        if not self.binance.api_key or not self.binance.api_secret:
            self.log("No API credentials found!", "ERROR")
            self.log("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables", "ERROR")
            return False
            
        self.log("API credentials found")
        return True

    def test_connectivity(self):
        """Test API connectivity"""
        self.log("Testing API connectivity...")
        
        try:
            if self.binance.test_connectivity():
                self.log("API connectivity successful")
                return True
            else:
                self.log("API connectivity failed", "ERROR")
                return False
        except Exception as e:
            self.log(f"Connectivity test error: {e}", "ERROR")
            return False

    def get_current_price(self):
        """Fetch current price for the trading symbol"""
        self.log(f"Fetching current price for {self.test_symbol}...")
        
        try:
            # Use direct API call to get current price
            endpoint = "/api/v3/ticker/price"
            params = {"symbol": self.test_symbol}
            
            response = self.binance._make_request(endpoint, params)
            price = float(response['price'])
            self.log(f"Current {self.test_symbol} price: ${price:,.2f}")
            return price
        except Exception as e:
            self.log(f"Error fetching price: {e}", "ERROR")
            return None

    def check_futures_balance(self):
        """Check if we have sufficient futures balance"""
        self.log("Checking futures balance...")
        
        try:
            balance = self.trading_manager.get_trading_balance('USDT')
            if balance and balance.get('total', 0) > 0:
                self.log(f"Futures balance: {balance['total']} USDT")
                return True
            else:
                self.log("Insufficient futures balance for trading", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error checking balance: {e}", "ERROR")
            return False

    def place_test_order(self, price, side='BUY'):
        """Place a small test order"""
        self.log(f"Placing {side} order for {self.trade_quantity} {self.test_symbol} at market price...")
        
        try:
            # Calculate order parameters
            if side == 'BUY':
                # Buy slightly above current price to ensure execution
                order_price = price * 1.001  # 0.1% above market
            else:
                # Sell slightly below current price to ensure execution
                order_price = price * 0.999  # 0.1% below market
            
            # Place limit order using futures API
            order = self.binance.futures_client.new_order(
                symbol=self.test_symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=self.trade_quantity,
                price=f"{order_price:.2f}"
            )
            
            order_id = order['orderId']
            self.active_orders.append({
                'orderId': order_id,
                'symbol': self.test_symbol,
                'side': side,
                'quantity': self.trade_quantity,
                'price': order_price,
                'time': datetime.now()
            })
            
            self.log(f"Order placed successfully! Order ID: {order_id}")
            self.log(f"Side: {side}, Quantity: {self.trade_quantity}, Price: ${order_price:.2f}")
            
            return order
            
        except Exception as e:
            self.log(f"Error placing order: {e}", "ERROR")
            return None

    def close_all_orders(self):
        """Close all active orders and positions"""
        self.log("Closing all active orders and positions...")
        
        orders_closed = 0
        
        # Cancel any open orders
        for order in self.active_orders:
            try:
                self.log(f"Canceling order {order['orderId']}...")
                self.binance.futures_client.cancel_order(
                    symbol=order['symbol'],
                    orderId=order['orderId']
                )
                orders_closed += 1
                self.log(f"Order {order['orderId']} canceled successfully")
            except Exception as e:
                # Order might already be filled or canceled
                self.log(f"Could not cancel order {order['orderId']}: {e}", "WARNING")
        
        # Close any open positions
        try:
            self.log("Checking for open positions...")
            positions = self.binance.futures_client.account()['positions']
            
            for position in positions:
                if position['symbol'] == self.test_symbol and float(position['positionAmt']) != 0:
                    pos_amt = float(position['positionAmt'])
                    self.log(f"Found open position: {pos_amt} {self.test_symbol}")
                    
                    # Close position with market order
                    side = 'SELL' if pos_amt > 0 else 'BUY'
                    quantity = abs(pos_amt)
                    
                    close_order = self.binance.futures_client.new_order(
                        symbol=self.test_symbol,
                        side=side,
                        type='MARKET',
                        quantity=quantity
                    )
                    
                    self.log(f"Position closed with market order: {close_order['orderId']}")
                    
        except Exception as e:
            self.log(f"Error closing positions: {e}", "ERROR")
        
        self.active_orders.clear()
        self.log(f"Cleanup completed. {orders_closed} orders processed.")

    def start_close_timer(self, duration=20):
        """Start a timer to automatically close trades after specified duration"""
        self.log(f"Starting {duration}-second close timer...")
        
        def countdown():
            for remaining in range(duration, 0, -1):
                if remaining <= 10 or remaining % 5 == 0:
                    self.log(f"Auto-close in {remaining} seconds...")
                time.sleep(1)
            
            self.log("Timer expired! Auto-closing all trades...")
            self.close_all_orders()
        
        self.close_timer = threading.Thread(target=countdown)
        self.close_timer.daemon = True
        self.close_timer.start()

    def run_trading_test(self):
        """Run the complete trading test"""
        self.print_separator("TRADING TEST SCRIPT")
        self.log(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Check credentials
        if not self.check_api_credentials():
            return False
        
        # Step 2: Test connectivity
        if not self.test_connectivity():
            return False
        
        # Step 3: Check balance
        if not self.check_futures_balance():
            self.log("Insufficient balance for trading test", "ERROR")
            return False
        
        # Step 4: Get current price
        current_price = self.get_current_price()
        if not current_price:
            return False
        
        # Step 5: Set trading mode to live
        self.log("Setting trading mode to LIVE...")
        self.trading_manager.trading_mode = 'live'
        
        # Step 6: Start the auto-close timer
        self.start_close_timer(20)
        
        # Step 7: Place a small test buy order
        buy_order = self.place_test_order(current_price, 'BUY')
        if not buy_order:
            return False
        
        # Step 8: Wait a few seconds then place a sell order
        self.log("Waiting 3 seconds before placing sell order...")
        time.sleep(3)
        
        sell_order = self.place_test_order(current_price, 'SELL')
        if not sell_order:
            self.log("Buy order placed but sell order failed", "WARNING")
        
        # Step 9: Monitor orders
        self.log("Monitoring orders...")
        self.log("Orders will be automatically closed in 20 seconds")
        self.log("Press Ctrl+C to manually close all orders early")
        
        try:
            # Wait for timer to complete
            while self.close_timer and self.close_timer.is_alive():
                time.sleep(1)
                
                # Check order status periodically
                if len(self.active_orders) > 0:
                    filled_orders = []
                    for order in self.active_orders:
                        try:
                            status = self.binance.futures_client.get_order(
                                symbol=order['symbol'],
                                orderId=order['orderId']
                            )
                            if status['status'] == 'FILLED':
                                self.log(f"Order {order['orderId']} filled!")
                                filled_orders.append(order)
                        except:
                            pass
                    
                    # Remove filled orders from active list
                    for filled in filled_orders:
                        if filled in self.active_orders:
                            self.active_orders.remove(filled)
        
        except KeyboardInterrupt:
            self.log("Manual interrupt received. Closing all orders...")
            self.close_all_orders()
        
        self.print_separator("TEST COMPLETED")
        self.log(f"Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True

def main():
    """Main function"""
    test = TradingTest()
    
    try:
        success = test.run_trading_test()
        if success:
            print("\n[SUCCESS] Trading test completed successfully!")
        else:
            print("\n[ERROR] Trading test failed!")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        # Ensure we clean up any orders in case of error
        try:
            test.close_all_orders()
        except:
            pass

if __name__ == "__main__":
    main()