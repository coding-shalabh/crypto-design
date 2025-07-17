#!/usr/bin/env python3
"""
Test script to verify bot start functionality
"""
import asyncio
import websockets
import json
import time

async def test_bot_start():
    """Test bot start functionality"""
    uri = "ws://localhost:8765"
    
    try:
        print("🔍 Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for all initial data messages
            print("🔍 Waiting for initial data messages...")
            initial_messages = []
            
            # Wait for initial data
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            initial_messages.append(initial_data)
            print(f"📊 Received: {initial_data['type']}")
            
            # Wait for positions response
            positions_response = await websocket.recv()
            positions_data = json.loads(positions_response)
            initial_messages.append(positions_data)
            print(f"💰 Received: {positions_data['type']}")
            
            # Wait for trade history response
            trade_history_response = await websocket.recv()
            trade_history_data = json.loads(trade_history_response)
            initial_messages.append(trade_history_data)
            print(f"📈 Received: {trade_history_data['type']}")
            
            # Wait for crypto data response
            crypto_data_response = await websocket.recv()
            crypto_data = json.loads(crypto_data_response)
            initial_messages.append(crypto_data)
            print(f"🪙 Received: {crypto_data['type']}")
            
            # Wait for bot status response
            bot_status_response = await websocket.recv()
            bot_status_data = json.loads(bot_status_response)
            initial_messages.append(bot_status_data)
            print(f"🤖 Received: {bot_status_data['type']}")
            
            print(f"✅ Received {len(initial_messages)} initial messages")
            
            # Now test bot start
            print("🔍 Testing bot start...")
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
            
            # Wait a moment and check bot status again
            await asyncio.sleep(2)
            
            print("🔍 Checking bot status after start...")
            await websocket.send(json.dumps({
                'type': 'get_bot_status'
            }))
            
            final_status_response = await websocket.recv()
            final_status = json.loads(final_status_response)
            print(f"🤖 Final bot status: {final_status}")
            
            # Test analysis start
            print("🔍 Testing analysis start...")
            await websocket.send(json.dumps({
                'type': 'start_analysis'
            }))
            
            # Wait for analysis status
            await asyncio.sleep(2)
            
            print("🔍 Checking analysis status...")
            await websocket.send(json.dumps({
                'type': 'get_analysis_status'
            }))
            
            analysis_status_response = await websocket.recv()
            analysis_status = json.loads(analysis_status_response)
            print(f"  Analysis status: {analysis_status}")
            
            # Test position request
            print("🔍 Testing position request...")
            await websocket.send(json.dumps({
                'type': 'get_positions'
            }))
            
            positions_response = await websocket.recv()
            positions_data = json.loads(positions_response)
            print(f"💰 Positions data: {positions_data}")
            
            print("✅ All tests completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    print("🧪 Starting bot functionality tests...")
    asyncio.run(test_bot_start()) 