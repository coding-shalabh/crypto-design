#!/usr/bin/env python3
"""
Test script to verify AI analysis logs are being sent to frontend
"""
import asyncio
import websockets
import json
import time

async def test_analysis_logs():
    """Test that AI analysis logs are being sent"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔍 Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for initial data
            print("🔍 Waiting for initial data...")
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            print(f"📊 Received: {initial_data['type']}")
            
            # Wait for other initial messages
            for _ in range(4):
                await websocket.recv()
            
            # Start the bot to trigger AI analysis
            print("🔍 Starting bot to trigger AI analysis...")
            start_config = {
                'max_trades_per_day': 10,
                'trade_amount_usdt': 50,
                'profit_target_usd': 2,
                'stop_loss_usd': 1,
                'allowed_pairs': ['BTCUSDT', 'ETHUSDT'],
                'ai_confidence_threshold': 0.75
            }
            
            await websocket.send(json.dumps({
                'type': 'start_bot',
                'config': start_config
            }))
            
            start_response = await websocket.recv()
            start_result = json.loads(start_response)
            print(f"🚀 Bot start result: {start_result}")
            
            # Wait for analysis status
            analysis_status_response = await websocket.recv()
            analysis_status = json.loads(analysis_status_response)
            print(f"  Analysis status: {analysis_status}")
            
            # Wait for bot status update
            bot_status_response = await websocket.recv()
            bot_status = json.loads(bot_status_response)
            print(f"🤖 Bot status update: {bot_status}")
            
            # Now wait for AI analysis logs (should come within 2 minutes)
            print("🔍 Waiting for AI analysis logs (this may take up to 2 minutes)...")
            start_time = time.time()
            analysis_logs_received = 0
            
            while time.time() - start_time < 120:  # Wait up to 2 minutes
                try:
                    # Set a timeout for receiving messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    if data['type'] == 'analysis_log':
                        analysis_logs_received += 1
                        print(f"📝 Analysis Log #{analysis_logs_received}: {data['data']['message']}")
                        print(f"   Confidence: {data['data']['confidence_score']}")
                        print(f"   Entry Price: ${data['data']['entry_price']}")
                        print(f"   Level: {data['data']['level']}")
                    elif data['type'] == 'ai_insights':
                        print(f"  AI Insights for {data['data']['symbol']}")
                        print(f"   Confidence: {data['data']['confidence_score']}")
                    elif data['type'] == 'price_update':
                        print(f"💰 Price Update: {data['data']['symbol']} = ${data['data']['price']['price']}")
                    else:
                        print(f"📨 Other message: {data['type']}")
                        
                except asyncio.TimeoutError:
                    print("⏰ No messages received in 10 seconds, continuing to wait...")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print(f"✅ Test completed! Received {analysis_logs_received} analysis logs")
            
            if analysis_logs_received > 0:
                print("🎉 SUCCESS: AI analysis is working and sending logs to frontend!")
            else:
                print("⚠️ WARNING: No analysis logs received. Check backend logs for issues.")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    print("🧪 Starting AI analysis logs test...")
    asyncio.run(test_analysis_logs()) 