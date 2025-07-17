#!/usr/bin/env python3
"""
Quick test to verify AI analysis is working
"""
import asyncio
import websockets
import json

async def quick_ai_test():
    """Quick test of AI analysis"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔍 Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for initial data
            for _ in range(5):
                await websocket.recv()
            
            # Manually request AI analysis
            print("🔍 Requesting AI analysis for BTCUSDT...")
            await websocket.send(json.dumps({
                'type': 'get_ai_analysis',
                'symbol': 'BTCUSDT'
            }))
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'ai_insights':
                print("✅ AI analysis response received!")
                print(f"   Symbol: {data['data']['symbol']}")
                print(f"   Confidence: {data['data']['confidence_score']}")
                print(f"   Timestamp: {data['data']['timestamp']}")
            elif data['type'] == 'error':
                print(f"❌ AI analysis error: {data['data']['message']}")
            else:
                print(f"📨 Unexpected response: {data['type']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Quick AI analysis test...")
    asyncio.run(quick_ai_test()) 