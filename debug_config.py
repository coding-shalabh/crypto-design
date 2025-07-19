#!/usr/bin/env python3
"""
Debug bot configuration and AI analysis issues
"""
import asyncio
import websockets
import json
import time

async def debug_bot_configuration():
    """Debug the bot configuration and AI analysis issues"""
    try:
        uri = "ws://localhost:8769"  # Updated port from the logs
        print(f"🔍 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            print(f"✅ Connected - Initial data type: {initial_data.get('type')}")
            
            print("\n" + "="*60)
            print("🔍 DEBUGGING BOT CONFIGURATION & AI ANALYSIS")
            print("="*60)
            
            # 1. Start bot with config
            print("\n1️⃣ Starting bot with configuration...")
            bot_config = {
                'max_trades_per_day': 5,
                'trade_amount_usdt': 25,
                'profit_target_min': 2.0,
                'profit_target_max': 4.0,
                'stop_loss_percent': 1.0,
                'trailing_enabled': True,
                'trailing_trigger_usd': 1.0,
                'trailing_distance_usd': 0.5,
                'monitor_open_trades': True,
                'ai_confidence_threshold': 0.6,
                'analysis_interval_minutes': 5
            }
            
            start_message = {
                'type': 'start_bot',
                'config': bot_config
            }
            await websocket.send(json.dumps(start_message))
            
            start_response = await websocket.recv()
            start_data = json.loads(start_response)
            print(f"   Start result: {start_data.get('type')} - {start_data.get('message', 'Success')}")
            
            # 2. Check bot status
            print("\n2️⃣ Checking bot status...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            
            if status_data.get('type') == 'bot_status_response':
                bot_data = status_data.get('data', {})
                print(f"   ✅ Bot Enabled: {bot_data.get('enabled', False)}")
                print(f"   📊 Config Keys: {list(bot_data.get('config', {}).keys())}")
                print(f"   💰 Profit Target: {bot_data.get('config', {}).get('profit_target_min', 'Not Set')}")
                print(f"   🛡️ Stop Loss: {bot_data.get('config', {}).get('stop_loss_percent', 'Not Set')}")
                print(f"   📈 Monitor Trades: {bot_data.get('config', {}).get('monitor_open_trades', 'Not Set')}")
                print(f"   🔄 Active Trades: {len(bot_data.get('active_trades', []))}")
            else:
                print(f"   ❌ Unexpected response: {status_data.get('type')}")
            
            # 3. Test AI Analysis
            print("\n3️⃣ Testing AI Analysis...")
            await websocket.send(json.dumps({'type': 'get_ai_analysis', 'symbol': 'BTCUSDT'}))
            
            ai_response = await websocket.recv()
            ai_data = json.loads(ai_response)
            print(f"   AI Response Type: {ai_data.get('type')}")
            
            if ai_data.get('type') == 'ai_analysis_response':
                analysis = ai_data.get('analysis', {})
                print(f"   ✅ Analysis Received for: {ai_data.get('symbol')}")
                print(f"   📊 Analysis Keys: {list(analysis.keys()) if analysis else 'None'}")
            
            # 4. Listen for logs for 10 seconds
            print("\n4️⃣ Listening for AI analysis logs (10 seconds)...")
            start_time = time.time()
            analysis_logs_received = 0
            
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    
                    if data.get('type') == 'analysis_log':
                        analysis_logs_received += 1
                        print(f"   📝 Analysis Log #{analysis_logs_received}: {data.get('message', '')[:100]}...")
                    elif data.get('type') == 'ai_analysis_response':
                        print(f"   🧠 AI Analysis Response for: {data.get('symbol')}")
                    elif 'analysis' in data.get('type', '').lower():
                        print(f"   🔍 Analysis Message: {data.get('type')}")
                        
                except asyncio.TimeoutError:
                    continue
            
            print(f"\n📊 Summary:")
            print(f"   Total analysis logs received: {analysis_logs_received}")
            
            # 5. Check for any active trades
            print("\n5️⃣ Checking for active trades...")
            await websocket.send(json.dumps({'type': 'get_positions'}))
            
            positions_response = await websocket.recv()
            positions_data = json.loads(positions_response)
            
            if positions_data.get('type') == 'positions_response':
                positions = positions_data.get('positions', [])
                print(f"   Active Positions: {len(positions)}")
                for pos in positions:
                    print(f"   - {pos.get('symbol')}: {pos.get('side')} ${pos.get('unrealized_pnl', 0):.2f}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bot_configuration()) 