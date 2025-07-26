#!/usr/bin/env python3
"""
Debug script to test WebSocket trading functionality
"""
import asyncio
import websockets
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_websocket_trading():
    """Test WebSocket trading functionality"""
    print("=" * 60)
    print("WEBSOCKET TRADING DEBUG TEST")
    print("=" * 60)
    
    uri = "ws://localhost:8767"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("PASS - Connected successfully!")
            
            # Test 1: Set trading mode to live
            print("\n1. Setting trading mode to LIVE...")
            await websocket.send(json.dumps({
                "type": "set_trading_mode",
                "data": {"mode": "live"}
            }))
            
            # Wait for trading_mode_set response, skip initial_data
            response_data = None
            for attempt in range(5):
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get('type') == 'trading_mode_set':
                    break
                elif response_data.get('type') == 'initial_data':
                    print("   Skipping initial_data...")
                    continue
                else:
                    print(f"   Received unexpected: {response_data.get('type')}")
            
            print(f"Response: {response_data}")
            
            if response_data and response_data.get('type') == 'trading_mode_set':
                print("PASS - Trading mode set to LIVE successfully")
                connection_test = response_data.get('data', {}).get('connection_test', {})
                print(f"   Connection test: {connection_test}")
            else:
                print(f"FAIL - Failed to set trading mode: {response_data}")
                return False
            
            # Test 2: Get USDT balance
            print("\n2. Getting USDT balance...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT"}
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Balance response: {response_data}")
            
            if response_data.get('type') == 'trading_balance':
                balance_data = response_data.get('data', {})
                balance = balance_data.get('balance', {})
                mode = balance_data.get('mode', 'unknown')
                print(f"PASS - Balance retrieved in {mode.upper()} mode:")
                print(f"   Free: ${balance.get('free', 0):.2f}")
                print(f"   Locked: ${balance.get('locked', 0):.2f}")
                print(f"   Total: ${balance.get('total', 0):.2f}")
            else:
                print(f"FAIL - Failed to get balance: {response_data}")
                return False
            
            # Test 3: Get all balances
            print("\n3. Getting all balances...")
            await websocket.send(json.dumps({
                "type": "get_all_trading_balances"
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"All balances response: {response_data}")
            
            if response_data.get('type') == 'all_trading_balances':
                balances_data = response_data.get('data', {})
                balances = balances_data.get('balances', [])
                mode = balances_data.get('mode', 'unknown')
                print(f"PASS - All balances retrieved in {mode.upper()} mode:")
                print(f"   Assets with balance: {len(balances)}")
                for balance in balances:
                    print(f"   {balance['asset']}: {balance['total']}")
            else:
                print(f"FAIL - Failed to get all balances: {response_data}")
                return False
            
            # Test 4: Get portfolio summary
            print("\n4. Getting portfolio summary...")
            await websocket.send(json.dumps({
                "type": "get_portfolio_summary"
            }))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Portfolio response: {response_data}")
            
            if response_data.get('type') == 'portfolio_summary':
                portfolio = response_data.get('data', {})
                mode = portfolio.get('mode', 'unknown')
                print(f"PASS - Portfolio summary in {mode.upper()} mode:")
                print(f"   Total Value: ${portfolio.get('total_value_usdt', 0):.2f}")
                print(f"   P&L: ${portfolio.get('pnl', 0):.2f}")
                print(f"   P&L %: {portfolio.get('pnl_percentage', 0):.2f}%")
            else:
                print(f"FAIL - Failed to get portfolio: {response_data}")
                return False
            
            print("\n" + "=" * 60)
            print("WEBSOCKET TRADING TEST COMPLETED")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"FAIL - WebSocket test failed: {e}")
        return False

async def main():
    """Main function"""
    success = await test_websocket_trading()
    if success:
        print("\nPASS - WebSocket trading functionality is working!")
    else:
        print("\nFAIL - WebSocket trading test failed!")
        
if __name__ == "__main__":
    asyncio.run(main())