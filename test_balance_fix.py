#!/usr/bin/env python3
"""
Test script to verify balance fetching works correctly
"""

import asyncio
import websockets
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_balance_fetching():
    """Test balance fetching via WebSocket"""
    uri = "ws://localhost:8767"
    
    try:
        print(" Testing WebSocket balance fetching...")
        print("=" * 50)
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Test get_trading_balance request
            request = {
                "type": "get_trading_balance",
                "data": {"asset": "USDT"}
            }
            
            print(f"📤 Sending request: {request}")
            await websocket.send(json.dumps(request))
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"📥 Received response: {response_data}")
            
            if response_data.get('type') == 'trading_balance':
                balance = response_data.get('data', {}).get('balance', {})
                mode = response_data.get('data', {}).get('mode', 'unknown')
                
                print(f"✅ Balance fetched successfully!")
                print(f"   Mode: {mode}")
                print(f"   Asset: {balance.get('asset', 'Unknown')}")
                print(f"   Total: {balance.get('total', 0)}")
                print(f"   Free: {balance.get('free', 0)}")
                print(f"   Locked: {balance.get('locked', 0)}")
                print(f"   Wallet Type: {balance.get('wallet_type', 'Unknown')}")
                print(f"   Note: {balance.get('note', 'No note')}")
                
                if mode == 'live' and balance.get('total', 0) > 0:
                    print("🎉 SUCCESS: Live balance is working correctly!")
                elif mode == 'mock' and balance.get('total', 0) == 100000:
                    print("🎉 SUCCESS: Mock balance is working correctly!")
                else:
                    print("⚠️  Balance fetched but values may be unexpected")
            else:
                print(f"❌ Unexpected response type: {response_data.get('type')}")
                if response_data.get('type') == 'error':
                    print(f"   Error: {response_data.get('data', {}).get('message', 'Unknown error')}")
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_balance_fetching()) 