#!/usr/bin/env python3
"""
Test script to simulate multiple rapid balance requests to test rate limiting
Usage: python test_websocket_balance.py
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_rapid_balance_requests():
    """Test rapid balance requests to verify rate limiting works"""
    uri = "ws://localhost:8765"
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected successfully!")
            
            # Send 10 rapid balance requests
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending 10 rapid balance requests...")
            
            start_time = time.time()
            
            for i in range(10):
                request = {
                    "type": "get_trading_balance",
                    "data": {"asset": "USDT"},
                    "mode": "mock"
                }
                await websocket.send(json.dumps(request))
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Sent request {i+1}")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    if data.get('type') == 'trading_balance':
                        balance = data.get('data', {}).get('balance', {})
                        total = balance.get('total', 0)
                        wallet_type = balance.get('wallet_type', 'UNKNOWN')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Response {i+1}: {total} USDT ({wallet_type})")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Response {i+1}: {data.get('type', 'UNKNOWN')}")
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Response {i+1}: TIMEOUT")
                
                # Small delay between requests (simulate rapid frontend requests)
                await asyncio.sleep(0.1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"\n[SUMMARY] Total time: {total_time:.2f} seconds")
            print(f"[SUMMARY] Average request time: {total_time/10:.2f} seconds")
            
            # Test mode switching
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Testing mode switching...")
            
            # Switch to live mode
            mode_request = {
                "type": "set_trading_mode",
                "data": {"mode": "live"}
            }
            await websocket.send(json.dumps(mode_request))
            
            # Wait for mode change response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(response)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Mode change response: {data}")
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Mode change: TIMEOUT")
            
            # Request balance in live mode
            live_request = {
                "type": "get_trading_balance",
                "data": {"asset": "USDT"},
                "mode": "live"
            }
            await websocket.send(json.dumps(live_request))
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get('type') == 'trading_balance':
                    balance = data.get('data', {}).get('balance', {})
                    total = balance.get('total', 0)
                    wallet_type = balance.get('wallet_type', 'UNKNOWN')
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Live balance: {total} USDT ({wallet_type})")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Live balance response: {data}")
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Live balance: TIMEOUT")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Test completed successfully!")
            
    except ConnectionRefusedError:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] Could not connect to WebSocket server")
        print("Make sure the backend server is running on port 8765")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] {e}")

async def main():
    """Main test function"""
    print("="*60)
    print("  WEBSOCKET BALANCE RATE LIMITING TEST")
    print("="*60)
    print(f"[TIME] Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await test_rapid_balance_requests()
    
    print("="*60)
    print("  TEST COMPLETED")
    print("="*60)
    print(f"[TIME] Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())