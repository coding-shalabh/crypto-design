#!/usr/bin/env python3
"""
Check Binance Futures Trading History
- Fetches recent orders and trades
- Verifies if our test trade executed
- Shows order details, fills, and PnL

Usage: python check_trade_history.py
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_service import BinanceService

class TradeHistoryChecker:
    def __init__(self):
        self.binance = BinanceService()
        
    def print_separator(self, title):
        """Print a nice separator"""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
        
    def format_time(self, timestamp):
        """Format timestamp to readable time"""
        return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        
    def format_number(self, num):
        """Format numbers for display"""
        if abs(num) < 0.01:
            return f"{num:.8f}"
        else:
            return f"{num:.4f}"
            
    def get_recent_orders(self, symbol='BTCUSDT', limit=10):
        """Get recent futures orders"""
        try:
            print(f"[FETCH] Getting recent orders for {symbol}...")
            
            # Get recent orders (last 24 hours)
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            orders = self.binance._make_futures_request('/fapi/v1/allOrders', params, signed=True)
            
            if not orders:
                print("[INFO] No orders found")
                return []
                
            # Filter recent orders (last 2 hours)
            recent_time = datetime.now() - timedelta(hours=2)
            recent_timestamp = int(recent_time.timestamp() * 1000)
            
            recent_orders = [order for order in orders if order['time'] >= recent_timestamp]
            
            print(f"[INFO] Found {len(recent_orders)} recent orders in last 2 hours")
            return recent_orders
            
        except Exception as e:
            print(f"[ERROR] Error getting recent orders: {e}")
            return []
            
    def get_recent_trades(self, symbol='BTCUSDT', limit=10):
        """Get recent futures trades"""
        try:
            print(f"[FETCH] Getting recent trades for {symbol}...")
            
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            trades = self.binance._make_futures_request('/fapi/v1/userTrades', params, signed=True)
            
            if not trades:
                print("[INFO] No trades found")
                return []
                
            # Filter recent trades (last 2 hours)
            recent_time = datetime.now() - timedelta(hours=2)
            recent_timestamp = int(recent_time.timestamp() * 1000)
            
            recent_trades = [trade for trade in trades if trade['time'] >= recent_timestamp]
            
            print(f"[INFO] Found {len(recent_trades)} recent trades in last 2 hours")
            return recent_trades
            
        except Exception as e:
            print(f"[ERROR] Error getting recent trades: {e}")
            return []
            
    def get_account_info(self):
        """Get futures account information"""
        try:
            print("[FETCH] Getting futures account info...")
            account = self.binance._make_futures_request('/fapi/v2/account', {}, signed=True)
            return account
        except Exception as e:
            print(f"[ERROR] Error getting account info: {e}")
            return None
            
    def display_orders(self, orders):
        """Display order information"""
        if not orders:
            print("[INFO] No recent orders to display")
            return
            
        print(f"\n[ORDERS] Recent Orders ({len(orders)} found):")
        print("-" * 100)
        print(f"{'Order ID':<15} {'Time':<20} {'Side':<5} {'Type':<10} {'Qty':<12} {'Price':<12} {'Status':<10}")
        print("-" * 100)
        
        for order in orders:
            order_id = order['orderId']
            order_time = self.format_time(order['time'])
            side = order['side']
            order_type = order['type']
            quantity = self.format_number(float(order['origQty']))
            price = self.format_number(float(order['price'])) if order['price'] != '0' else 'MARKET'
            status = order['status']
            
            print(f"{order_id:<15} {order_time:<20} {side:<5} {order_type:<10} {quantity:<12} {price:<12} {status:<10}")
            
            # Show additional details for filled orders
            if status == 'FILLED':
                filled_qty = self.format_number(float(order['executedQty']))
                avg_price = self.format_number(float(order['avgPrice'])) if order['avgPrice'] != '0' else 'N/A'
                commission = self.format_number(float(order.get('commission', 0)))
                print(f"    -> Filled: {filled_qty} @ ${avg_price} | Commission: {commission}")
                
    def display_trades(self, trades):
        """Display trade information"""
        if not trades:
            print("[INFO] No recent trades to display")
            return
            
        print(f"\n[TRADES] Recent Trades ({len(trades)} found):")
        print("-" * 110)
        print(f"{'Trade ID':<15} {'Order ID':<15} {'Time':<20} {'Side':<5} {'Qty':<12} {'Price':<12} {'Realized PnL':<12}")
        print("-" * 110)
        
        total_pnl = 0
        
        for trade in trades:
            trade_id = trade['id']
            order_id = trade['orderId']
            trade_time = self.format_time(trade['time'])
            side = trade['side']
            quantity = self.format_number(float(trade['qty']))
            price = self.format_number(float(trade['price']))
            realized_pnl = self.format_number(float(trade['realizedPnl']))
            
            total_pnl += float(trade['realizedPnl'])
            
            print(f"{trade_id:<15} {order_id:<15} {trade_time:<20} {side:<5} {quantity:<12} ${price:<11} {realized_pnl:<12}")
            
        if trades:
            print("-" * 110)
            print(f"{'TOTAL REALIZED PnL:':<85} {self.format_number(total_pnl):<12}")
            
    def display_account_summary(self, account):
        """Display account summary"""
        if not account:
            print("[INFO] No account information available")
            return
            
        print(f"\n[ACCOUNT] Futures Account Summary:")
        print("-" * 50)
        
        total_wallet_balance = float(account.get('totalWalletBalance', 0))
        total_unrealized_pnl = float(account.get('totalUnrealizedProfit', 0))
        total_margin_balance = float(account.get('totalMarginBalance', 0))
        available_balance = float(account.get('availableBalance', 0))
        
        print(f"Total Wallet Balance: {self.format_number(total_wallet_balance)} USDT")
        print(f"Unrealized PnL: {self.format_number(total_unrealized_pnl)} USDT")
        print(f"Margin Balance: {self.format_number(total_margin_balance)} USDT")
        print(f"Available Balance: {self.format_number(available_balance)} USDT")
        
        # Show positions with non-zero amounts
        positions = account.get('positions', [])
        active_positions = [pos for pos in positions if float(pos['positionAmt']) != 0]
        
        if active_positions:
            print(f"\n[POSITIONS] Active Positions ({len(active_positions)} found):")
            print("-" * 80)
            print(f"{'Symbol':<12} {'Size':<12} {'Entry Price':<12} {'Mark Price':<12} {'PnL':<12}")
            print("-" * 80)
            
            for pos in active_positions:
                symbol = pos['symbol']
                size = self.format_number(float(pos['positionAmt']))
                entry_price = self.format_number(float(pos['entryPrice']))
                mark_price = self.format_number(float(pos.get('markPrice', 0)))
                unrealized_pnl = self.format_number(float(pos.get('unrealizedProfit', 0)))
                
                print(f"{symbol:<12} {size:<12} ${entry_price:<11} ${mark_price:<11} {unrealized_pnl:<12}")
        else:
            print(f"\n[POSITIONS] No active positions")
            
    def check_specific_order(self, order_id):
        """Check specific order by ID"""
        try:
            print(f"\n[CHECK] Looking for order ID: {order_id}")
            
            params = {
                'symbol': 'BTCUSDT',
                'orderId': order_id
            }
            
            order = self.binance._make_futures_request('/fapi/v1/order', params, signed=True)
            
            if order:
                print(f"[FOUND] Order {order_id} details:")
                print(f"  Status: {order['status']}")
                print(f"  Side: {order['side']}")
                print(f"  Type: {order['type']}")
                print(f"  Original Qty: {order['origQty']}")
                print(f"  Executed Qty: {order['executedQty']}")
                print(f"  Average Price: {order['avgPrice']}")
                print(f"  Time: {self.format_time(order['time'])}")
                return order
            else:
                print(f"[NOT FOUND] Order {order_id} not found")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error checking order {order_id}: {e}")
            return None
            
    def run_check(self):
        """Run the complete trade history check"""
        self.print_separator("BINANCE FUTURES TRADE HISTORY CHECK")
        print(f"[TIME] Check started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test connectivity first
        if not self.binance.test_connectivity():
            print("[ERROR] Could not connect to Binance API")
            return
            
        # Get account info
        account = self.get_account_info()
        if account:
            self.display_account_summary(account)
            
        # Get recent orders
        orders = self.get_recent_orders('BTCUSDT', 20)
        self.display_orders(orders)
        
        # Get recent trades
        trades = self.get_recent_trades('BTCUSDT', 20)
        self.display_trades(trades)
        
        # Check the specific order ID from our test (738984649854)
        test_order_id = 738984649854
        self.check_specific_order(test_order_id)
        
        self.print_separator("CHECK COMPLETED")
        print(f"[TIME] Check finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main function"""
    try:
        # Check API credentials first
        binance = BinanceService()
        if not binance.api_key or not binance.api_secret:
            print("[ERROR] Binance API credentials not found!")
            print("Please ensure the .env file exists and contains BINANCE_API_KEY and BINANCE_API_SECRET")
            return
            
        # Run the check
        checker = TradeHistoryChecker()
        checker.run_check()
        
    except KeyboardInterrupt:
        print("\n[INFO] Check interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")

if __name__ == "__main__":
    main()