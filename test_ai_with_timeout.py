#!/usr/bin/env python3
"""
Test AI analysis with proper timeout handling
"""
import asyncio
import websockets
import json
import time

async def test_ai_with_timeout():
    """Test AI analysis with timeout"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔍 Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for initial data
            print("🔍 Waiting for initial data...")
            for _ in range(5):
                await websocket.recv()
            print("✅ Initial data received")
            
            # Manually request AI analysis
            print("🔍 Requesting AI analysis for BTCUSDT...")
            await websocket.send(json.dumps({
                'type': 'get_ai_analysis',
                'symbol': 'BTCUSDT'
            }))
            
            # Wait for response with timeout
            print("🔍 Waiting for AI analysis response (30 seconds timeout)...")
            start_time = time.time()
            
            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data['type'] == 'ai_insights':
                        print("✅ AI analysis response received!")
                        print(f"   Symbol: {data['data']['symbol']}")
                        print(f"   Confidence: {data['data']['confidence_score']}")
                        print(f"   Timestamp: {data['data']['timestamp']}")
                        return
                    elif data['type'] == 'error':
                        print(f"❌ AI analysis error: {data['data']['message']}")
                        return
                    elif data['type'] == 'price_update':
                        print(f"💰 Price update received (continuing to wait for AI response)...")
                    else:
                        print(f"📨 Other message: {data['type']}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No response in 5 seconds, continuing to wait...")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print("⏰ Timeout reached - no AI analysis response received")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 AI analysis test with timeout...")
    asyncio.run(test_ai_with_timeout()) 