#!/usr/bin/env python3
"""
Simple test to get trading balance with proper message waiting
"""
import asyncio
import websockets
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_balance_retrieval():
    """Test balance retrieval with proper message filtering"""
    print("=" * 60)
    print("SIMPLE BALANCE TEST")
    print("=" * 60)
    
    uri = "ws://localhost:8767"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("SUCCESS - Connected successfully!")
            
            # Skip initial data and any price updates
            print("\nSkipping initial messages...")
            for i in range(3):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(message)
                    print(f"   Skipped: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    print("   No more initial messages")
                    break
            
            # Test 1: Set trading mode to live
            print("\n1. Setting trading mode to LIVE...")
            await websocket.send(json.dumps({
                "type": "set_trading_mode",
                "data": {"mode": "live"}
            }))
            
            # Wait for trading_mode_set response specifically
            for attempt in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    data = json.loads(message)
                    
                    if data.get('type') == 'trading_mode_set':
                        print("SUCCESS - Trading mode set to LIVE")
                        print(f"   Connection test: {data.get('data', {}).get('connection_test', {})}")
                        break
                    else:
                        print(f"   Ignoring: {data.get('type', 'unknown')}")
                        continue
                except asyncio.TimeoutError:
                    print(f"   Timeout waiting for trading_mode_set (attempt {attempt + 1})")
                    continue
            else:
                print("ERROR - Never received trading_mode_set response")
                return False
            
            # Test 2: Get USDT balance
            print("\n2. Getting USDT balance...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT"}
            }))
            
            # Wait specifically for trading_balance response
            for attempt in range(15):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    data = json.loads(message)
                    
                    if data.get('type') == 'trading_balance':
                        print("SUCCESS - Balance retrieved!")
                        balance_data = data.get('data', {})
                        balance = balance_data.get('balance', {})
                        mode = balance_data.get('mode', 'unknown')
                        print(f"   Mode: {mode}")
                        print(f"   Free: ${balance.get('free', 0):.2f}")
                        print(f"   Locked: ${balance.get('locked', 0):.2f}")
                        print(f"   Total: ${balance.get('total', 0):.2f}")
                        return True
                    elif data.get('type') == 'error':
                        print(f"ERROR - {data.get('data', {}).get('message', 'Unknown error')}")
                        return False
                    else:
                        print(f"   Ignoring: {data.get('type', 'unknown')}")
                        continue
                except asyncio.TimeoutError:
                    print(f"   Timeout waiting for trading_balance (attempt {attempt + 1})")
                    continue
            
            print("ERROR - Never received trading_balance response")
            return False
            
    except Exception as e:
        print(f"ERROR - Test failed: {e}")
        return False

async def main():
    """Main function"""
    success = await test_balance_retrieval()
    if success:
        print("\nSUCCESS - Balance retrieval is working!")
    else:
        print("\nFAILED - Balance retrieval test failed!")
        
if __name__ == "__main__":
    asyncio.run(main())