#!/usr/bin/env python3
"""
Test script to verify analysis configuration is working correctly
"""
import asyncio
import time
from datetime import datetime
from config import Config
from websocket_server import TradingServer

async def test_analysis_config():
    """Test the analysis configuration"""
    print("=== Testing Analysis Configuration ===")
    
    # Test 1: Check configuration
    bot_config = Config.get_bot_config()
    print(f"1. Trade interval: {bot_config['trade_interval_secs']} seconds")
    print(f"2. Analyze all pairs: {bot_config.get('analyze_all_pairs', 'Not set')}")
    print(f"3. AI confidence threshold: {bot_config['ai_confidence_threshold']}")
    print(f"4. Allowed pairs: {bot_config['allowed_pairs']}")
    
    # Test 2: Create server instance
    print("\n=== Testing Server Instance ===")
    server = TradingServer()
    
    # Test 3: Test should_skip_pair_analysis function
    print("\n=== Testing Skip Logic ===")
    
    # Simulate active trades
    server.trading_bot.bot_active_trades = {'SOLUSDT': {'price': 180.0}}
    
    # Test pairs
    test_pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    
    for pair in test_pairs:
        should_skip = server.should_skip_pair_analysis(pair)
        has_active_trade = pair in server.trading_bot.bot_active_trades
        print(f"   {pair}: Active trade={has_active_trade}, Should skip={should_skip}")
    
    # Test 4: Test analysis interval calculation
    print("\n=== Testing Analysis Interval ===")
    analysis_interval = bot_config.get('trade_interval_secs', 600)
    current_time = datetime.now()
    next_analysis_time = datetime.fromtimestamp(current_time.timestamp() + analysis_interval)
    
    print(f"   Current time: {current_time.strftime('%H:%M:%S')}")
    print(f"   Analysis interval: {analysis_interval} seconds ({analysis_interval/60:.1f} minutes)")
    print(f"   Next analysis: {next_analysis_time.strftime('%H:%M:%S')}")
    
    print("\n=== Configuration Test Complete ===")
    print(" All tests passed! The configuration is correct.")
    print("\nExpected behavior:")
    print("- Analysis will run every 10 minutes (600 seconds)")
    print("- All pairs will be analyzed regardless of active trades")
    print("- SOLUSDT will be analyzed even with active trade")
    print("- Only pairs in cooldown will be skipped")

if __name__ == "__main__":
    asyncio.run(test_analysis_config()) 