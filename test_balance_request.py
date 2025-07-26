#!/usr/bin/env python3
"""
Test script to verify balance requests are sent when switching modes
"""

import asyncio
import websockets
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_balance_requests():
    """Test if balance requests are sent when switching modes"""
    uri = "ws://localhost:8767"
    
    try:
        print("🔍 Testing balance requests on mode switch...")
        print("=" * 50)
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # First, set trading mode to mock
            print("\n📤 Setting trading mode to mock...")
            await websocket.send(json.dumps({
                "type": "set_trading_mode",
                "data": {"mode": "mock"}
            }))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Mock mode response: {response_data}")
            
            # Request balance in mock mode
            print("\n📤 Requesting balance in mock mode...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT"}
            }))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Mock balance response: {response_data}")
            
            # Now switch to live mode
            print("\n📤 Setting trading mode to live...")
            await websocket.send(json.dumps({
                "type": "set_trading_mode",
                "data": {"mode": "live"}
            }))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Live mode response: {response_data}")
            
            # Request balance in live mode
            print("\n📤 Requesting balance in live mode...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT"}
            }))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"📥 Live balance response: {response_data}")
            
            # Check if the responses are different
            if response_data.get('type') == 'trading_balance':
                balance = response_data.get('data', {}).get('balance', {})
                mode = response_data.get('data', {}).get('mode', 'unknown')
                
                print(f"\n✅ Balance fetched successfully!")
                print(f"   Mode: {mode}")
                print(f"   Asset: {balance.get('asset', 'Unknown')}")
                print(f"   Total: {balance.get('total', 0)}")
                print(f"   Free: {balance.get('free', 0)}")
                print(f"   Locked: {balance.get('locked', 0)}")
                print(f"   Wallet Type: {balance.get('wallet_type', 'Unknown')}")
                
                if mode == 'live' and balance.get('total', 0) > 0:
                    print("🎉 SUCCESS: Live balance is working correctly!")
                elif mode == 'mock' and balance.get('total', 0) == 100000:
                    print("🎉 SUCCESS: Mock balance is working correctly!")
                else:
                    print("⚠️  Balance fetched but values may be unexpected")
            else:
                print(f"❌ Unexpected response type: {response_data.get('type')}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_balance_requests()) 