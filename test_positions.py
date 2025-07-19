#!/usr/bin/env python3
"""
Test script to verify position functionality
"""
import asyncio
import websockets
import json
import time

async def test_positions():
    """Test position functionality"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Test 1: Execute a long position
            print("\n=== Test 1: Execute LONG position ===")
            long_trade = {
                "type": "execute_trade",
                "trade_data": {
                    "symbol": "BTCUSDT",
                    "direction": "buy",
                    "amount": 0.001,
                    "price": 50000,
                    "order_type": "market",
                    "trade_id": f"test_long_{int(time.time())}"
                }
            }
            
            await websocket.send(json.dumps(long_trade))
            response = await websocket.recv()
            print(f"Long trade response: {response}")
            
            # Test 2: Check positions
            print("\n=== Test 2: Check positions ===")
            await websocket.send(json.dumps({"type": "get_positions"}))
            response = await websocket.recv()
            print(f"Positions response: {response}")
            
            # Test 3: Execute a short position  
            print("\n=== Test 3: Execute SHORT position ===")
            short_trade = {
                "type": "execute_trade",
                "trade_data": {
                    "symbol": "ETHUSDT",
                    "direction": "sell",
                    "amount": 0.01,
                    "price": 3000,
                    "order_type": "market",
                    "trade_id": f"test_short_{int(time.time())}"
                }
            }
            
            await websocket.send(json.dumps(short_trade))
            response = await websocket.recv()
            print(f"Short trade response: {response}")
            
            # Test 4: Check positions again
            print("\n=== Test 4: Check positions again ===")
            await websocket.send(json.dumps({"type": "get_positions"}))
            response = await websocket.recv()
            print(f"Positions response: {response}")
            
            # Test 5: Wait for price updates
            print("\n=== Test 5: Wait for price updates ===")
            for i in range(3):
                response = await websocket.recv()
                data = json.loads(response)
                if data.get('type') == 'position_update':
                    print(f"Position update {i+1}: {response}")
                elif data.get('type') == 'price_updates_batch':
                    print(f"Price update {i+1}: Found {len(data.get('data', {}).get('updates', []))} price updates")
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_positions())