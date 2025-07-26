#!/usr/bin/env python3
"""
Test script to fetch and display Binance balances in categorized format
Usage: python test_balance_fetch.py
"""

import os
import sys
from decimal import Decimal
from datetime import datetime

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance_service import BinanceService
from trading_manager import TradingManager

def format_balance(amount):
    """Format balance for display"""
    if amount == 0:
        return "0.00"
    elif amount < 0.01:
        return f"{amount:.8f}"
    else:
        return f"{amount:.2f}"

def print_separator(title):
    """Print a nice separator"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_wallet_balances(wallet_name, balances, icon="[WALLET]"):
    """Print balances for a specific wallet"""
    print(f"\n{icon} {wallet_name}")
    print("-" * 40)
    
    if not balances:
        print("  No balances found")
        return
    
    total_value = 0
    count = 0
    
    for balance in balances:
        if balance['total'] > 0:
            count += 1
            asset = balance['asset']
            free = balance['free']
            locked = balance['locked']
            total = balance['total']
            
            print(f"  {asset:8} | Total: {format_balance(total):>12} | Free: {format_balance(free):>12} | Locked: {format_balance(locked):>12}")
            
            # Calculate USDT value if it's not USDT
            if asset == 'USDT':
                total_value += total
    
    if count > 0:
        print(f"\n  [INFO] Assets with balance: {count}")
        if total_value > 0:
            print(f"  [USDT] USDT Value: {format_balance(total_value)}")
    else:
        print("  No assets with positive balance")

def test_individual_wallets():
    """Test individual wallet balance fetching"""
    print_separator("TESTING INDIVIDUAL WALLET METHODS")
    
    try:
        binance = BinanceService()
        
        # Test API credentials
        print(f"API Key Present: {bool(binance.api_key)}")
        print(f"API Secret Present: {bool(binance.api_secret)}")
        
        if not binance.api_key or not binance.api_secret:
            print("\n[ERROR] ERROR: No API credentials found!")
            print("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
            return False
        
        # Test connectivity
        print("\n[CONNECT] Testing API connectivity...")
        if binance.test_connectivity():
            print("[SUCCESS] API connectivity successful")
        else:
            print("[ERROR] API connectivity failed")
            return False
        
        # Test Spot balances
        print("\n[FETCH] Fetching Spot balances...")
        try:
            spot_balances = binance.get_spot_balances()
            print_wallet_balances("SPOT WALLET", spot_balances, "[SPOT]")
        except Exception as e:
            print(f"[ERROR] Error fetching spot balances: {e}")
        
        # Test Futures balances
        print("\n[FETCH] Fetching Futures balances...")
        try:
            futures_balances = binance.get_futures_balances()
            print_wallet_balances("FUTURES WALLET", futures_balances, "[FUTURES]")
        except Exception as e:
            print(f"[ERROR] Error fetching futures balances: {e}")
        
        # Test Margin balances
        print("\n[FETCH] Fetching Margin balances...")
        try:
            margin_balances = binance.get_margin_balances()
            print_wallet_balances("MARGIN WALLET", margin_balances, "[MARGIN]")
        except Exception as e:
            print(f"[ERROR] Error fetching margin balances: {e}")
        
        # Test Funding balances
        print("\n[FETCH] Fetching Funding balances...")
        try:
            funding_balances = binance.get_funding_balances()
            print_wallet_balances("FUNDING WALLET", funding_balances, "[FUNDING]")
        except Exception as e:
            print(f"[ERROR] Error fetching funding balances: {e}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error in individual wallet testing: {e}")
        return False

def test_categorized_balances():
    """Test the categorized balance method"""
    print_separator("TESTING CATEGORIZED BALANCE METHOD")
    
    try:
        binance = BinanceService()
        
        print("[FETCH] Fetching categorized balances...")
        categorized = binance.get_categorized_balances()
        
        wallet_icons = {
            'SPOT': '[SPOT]',
            'FUTURES': '[FUTURES]', 
            'MARGIN': '[MARGIN]',
            'FUNDING': '[FUNDING]'
        }
        
        total_portfolio_value = 0
        
        for wallet_type, wallet_data in categorized.items():
            icon = wallet_icons.get(wallet_type, '[WALLET]')
            wallet_name = wallet_data.get('name', wallet_type)
            balances = wallet_data.get('balances', [])
            total_usdt = wallet_data.get('total_usdt', 0)
            
            print_wallet_balances(wallet_name, balances, icon)
            
            if total_usdt > 0:
                print(f"  [USDT] Estimated USDT Value: {format_balance(total_usdt)}")
                total_portfolio_value += total_usdt
        
        print_separator("PORTFOLIO SUMMARY")
        print(f"[PORTFOLIO] Total Portfolio Value: {format_balance(total_portfolio_value)} USDT")
        
    except Exception as e:
        print(f"[ERROR] Error in categorized balance testing: {e}")

def test_trading_manager():
    """Test the trading manager balance methods"""
    print_separator("TESTING TRADING MANAGER")
    
    try:
        tm = TradingManager()
        
        # Test in live mode
        print("\n[LIVE] Testing LIVE mode:")
        tm.trading_mode = 'live'
        
        # Test get_trading_balance
        print("[FETCH] Getting USDT trading balance...")
        usdt_balance = tm.get_trading_balance('USDT')
        print(f"  USDT Balance: {usdt_balance}")
        
        # Test get_categorized_balances
        print("[FETCH] Getting categorized balances...")
        cat_balances = tm.get_categorized_balances()
        print(f"  Wallet types found: {list(cat_balances.keys())}")
        
        # Test in mock mode
        print("\n[MOCK] Testing MOCK mode:")
        tm.trading_mode = 'mock'
        
        usdt_balance_mock = tm.get_trading_balance('USDT')
        print(f"  Mock USDT Balance: {usdt_balance_mock}")
        
    except Exception as e:
        print(f"[ERROR] Error in trading manager testing: {e}")

def main():
    """Main test function"""
    print_separator("BINANCE BALANCE FETCH TEST")
    print(f"[TIME] Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Individual wallet methods
    if test_individual_wallets():
        print("\n[SUCCESS] Individual wallet tests completed")
    else:
        print("\n[ERROR] Individual wallet tests failed")
        return
    
    # Test 2: Categorized balance method
    test_categorized_balances()
    
    # Test 3: Trading manager
    test_trading_manager()
    
    print_separator("TEST COMPLETED")
    print(f"[TIME] Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()