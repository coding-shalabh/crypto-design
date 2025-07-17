#!/usr/bin/env python3
"""
Simple WebSocket Connection Test
===============================

This script tests basic WebSocket connectivity and sends a few test messages
to verify the frontend is receiving data correctly.
"""

import asyncio
import json
import websockets
import time

async def test_websocket_connection():
    """Test basic WebSocket connection and send test data"""
    
    # Test different ports where frontend might be listening
    test_urls = [
        "ws://localhost:3000",
        "ws://localhost:3001", 
        "ws://localhost:8765",
        "ws://localhost:8080"
    ]
    
    for url in test_urls:
        print(f"🔍 Testing connection to {url}")
        
        try:
            async with websockets.connect(url) as websocket:
                print(f"✅ Successfully connected to {url}")
                
                # Send initial data
                initial_data = {
                    "type": "initial_data",
                    "data": {
                        "paper_balance": 10000.0,
                        "positions": {},
                        "recent_trades": [],
                        "price_cache": {
                            "BTC": {
                                "symbol": "BTC",
                                "price": 45000.0,
                                "change_24h": 2.5,
                                "volume_24h": 25000000,
                                "market_cap": 850000000000,
                                "timestamp": time.time()
                            }
                        },
                        "crypto_data": {
                            "bitcoin": {
                                "id": "bitcoin",
                                "symbol": "BTC",
                                "name": "Bitcoin",
                                "current_price": 45000.0,
                                "market_cap": 850000000000,
                                "market_cap_rank": 1
                            }
                        }
                    }
                }
                
                await websocket.send(json.dumps(initial_data))
                print("📤 Sent initial data")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    print(f"📥 Received response: {response}")
                except asyncio.TimeoutError:
                    print("⏰ No response received (timeout)")
                
                # Send a price update
                price_update = {
                    "type": "price_update",
                    "data": {
                        "symbol": "BTC",
                        "price": 45100.0,
                        "change_24h": 2.8,
                        "volume_24h": 25000000,
                        "market_cap": 850000000000,
                        "timestamp": time.time()
                    }
                }
                
                await websocket.send(json.dumps(price_update))
                print("📤 Sent price update")
                
                # Send a test trade
                trade_data = {
                    "type": "trade_executed",
                    "data": {
                        "new_balance": 9950.0,
                        "positions": {
                            "BTC": {
                                "symbol": "BTC",
                                "amount": 0.1,
                                "entry_price": 45000.0,
                                "current_price": 45100.0,
                                "direction": "LONG",
                                "value": 4500.0,
                                "timestamp": time.time()
                            }
                        },
                        "trade": {
                            "trade_id": f"test_trade_{int(time.time())}",
                            "symbol": "BTC",
                            "direction": "BUY",
                            "amount": 0.1,
                            "price": 45000.0,
                            "value": 4500.0,
                            "timestamp": time.time(),
                            "trade_type": "MANUAL",
                            "status": "executed"
                        }
                    }
                }
                
                await websocket.send(json.dumps(trade_data))
                print("📤 Sent test trade")
                
                print(f"✅ Successfully tested {url}")
                return url
                
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {e}")
            continue
    
    print("❌ Could not connect to any WebSocket endpoint")
    return None

async def main():
    """Main function"""
    print("🧪 WebSocket Connection Test")
    print("=" * 40)
    
    working_url = await test_websocket_connection()
    
    if working_url:
        print(f"\n🎉 Found working WebSocket at: {working_url}")
        print("💡 Use this URL in the fake data generator")
    else:
        print("\n❌ No working WebSocket found")
        print("💡 Make sure the frontend is running and listening for WebSocket connections")

if __name__ == "__main__":
    asyncio.run(main()) 