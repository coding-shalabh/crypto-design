#!/usr/bin/env python3
"""
Improved debug script for bot configuration and AI analysis
"""
import asyncio
import websockets
import json
import time

async def improved_debug():
    """Improved debug with proper message handling"""
    try:
        uri = "ws://localhost:8769"
        print(f"🔍 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully")
            
            # Consume initial data
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            print(f"📥 Initial message: {initial_data.get('type')}")
            
            print("\n" + "="*60)
            print("🔍 IMPROVED DIAGNOSTIC - BOT CONFIG & AI ANALYSIS")
            print("="*60)
            
            # 1. First stop any running bot
            print("\n1️⃣ Stopping any running bot...")
            await websocket.send(json.dumps({'type': 'stop_bot'}))
            
            # Consume any immediate responses
            try:
                stop_response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                stop_data = json.loads(stop_response)
                print(f"   Stop result: {stop_data.get('type')}")
            except asyncio.TimeoutError:
                print("   Stop timeout - continuing...")
            
            # 2. Start bot with clear configuration
            print("\n2️⃣ Starting bot with configuration...")
            bot_config = {
                'max_trades_per_day': 3,
                'trade_amount_usdt': 20,
                'profit_target_min': 2.0,  # USD
                'profit_target_max': 5.0,  # USD
                'stop_loss_percent': 1.0,
                'trailing_enabled': False,  # Disable for testing
                'monitor_open_trades': True,
                'ai_confidence_threshold': 0.5,
                'analysis_interval_minutes': 1,  # Short interval for testing
                'test_mode': True
            }
            
            start_message = {
                'type': 'start_bot',
                'config': bot_config
            }
            await websocket.send(json.dumps(start_message))
            print(f"   📤 Sent start_bot message with config")
            
            # Wait for start response
            try:
                start_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                start_data = json.loads(start_response)
                print(f"   📥 Start response: {start_data.get('type')} - {start_data.get('message', 'No message')}")
            except asyncio.TimeoutError:
                print("   ⏰ Start response timeout")
            
            # 3. Wait a moment for bot to initialize
            print("\n3️⃣ Waiting for bot initialization...")
            await asyncio.sleep(2)
            
            # 4. Check bot status with proper response handling
            print("\n4️⃣ Checking bot status...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            # Collect multiple responses to find the bot_status_response
            for attempt in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(response)
                    response_type = data.get('type')
                    
                    print(f"   📥 Response #{attempt + 1}: {response_type}")
                    
                    if response_type == 'bot_status_response':
                        bot_data = data.get('data', {})
                        config = bot_data.get('config', {})
                        
                        print(f"   ✅ Bot Status Found!")
                        print(f"   📊 Bot Enabled: {bot_data.get('enabled', False)}")
                        print(f"   💰 Profit Target: ${config.get('profit_target_min', 'Not Set')}")
                        print(f"   🛡️ Stop Loss: {config.get('stop_loss_percent', 'Not Set')}%")
                        print(f"   📈 Monitor Trades: {config.get('monitor_open_trades', False)}")
                        print(f"   🎯 Test Mode: {config.get('test_mode', False)}")
                        print(f"   🔄 Active Trades Count: {len(bot_data.get('active_trades', []))}")
                        break
                        
                except asyncio.TimeoutError:
                    print(f"   ⏰ Timeout on attempt {attempt + 1}")
                    break
            
            # 5. Test AI Analysis
            print("\n5️⃣ Testing AI Analysis...")
            await websocket.send(json.dumps({'type': 'get_ai_analysis', 'symbol': 'BTCUSDT'}))
            
            # Look for AI analysis response
            for attempt in range(3):
                try:
                    ai_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    ai_data = json.loads(ai_response)
                    
                    if ai_data.get('type') == 'ai_analysis_response':
                        print(f"   ✅ AI Analysis received for: {ai_data.get('symbol')}")
                        analysis = ai_data.get('analysis', {})
                        print(f"   📊 Analysis has keys: {list(analysis.keys()) if analysis else 'None'}")
                        break
                    else:
                        print(f"   📥 Other message: {ai_data.get('type')}")
                        
                except asyncio.TimeoutError:
                    print(f"   ⏰ AI analysis timeout on attempt {attempt + 1}")
            
            # 6. Monitor for analysis logs and auto-close activity
            print("\n6️⃣ Monitoring for analysis logs and auto-close activity (15 seconds)...")
            start_time = time.time()
            analysis_logs = 0
            autoclose_logs = 0
            
            while time.time() - start_time < 15:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    msg_type = data.get('type', '')
                    
                    if msg_type == 'analysis_log':
                        analysis_logs += 1
                        message = data.get('message', '')
                        print(f"   📝 Analysis Log #{analysis_logs}: {message[:80]}...")
                        
                    elif 'analysis' in msg_type.lower():
                        print(f"   🧠 Analysis Message: {msg_type}")
                        
                    elif 'close' in msg_type.lower() or 'profit' in msg_type.lower():
                        autoclose_logs += 1
                        print(f"   💰 Auto-close Log #{autoclose_logs}: {msg_type}")
                        
                    elif msg_type == 'trade_execution':
                        trade_data = data.get('data', {})
                        print(f"   📈 Trade Execution: {trade_data.get('action')} {trade_data.get('symbol')}")
                        
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                    continue
            
            print(f"\n\n📊 FINAL SUMMARY:")
            print(f"   Analysis logs received: {analysis_logs}")
            print(f"   Auto-close logs received: {autoclose_logs}")
            
            # 7. Final status check
            print("\n7️⃣ Final bot status check...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            try:
                final_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                final_data = json.loads(final_response)
                
                if final_data.get('type') == 'bot_status_response':
                    final_bot_data = final_data.get('data', {})
                    print(f"   🔄 Final - Bot Enabled: {final_bot_data.get('enabled', False)}")
                    print(f"   📊 Final - Active Trades: {len(final_bot_data.get('active_trades', []))}")
                    
            except asyncio.TimeoutError:
                print("   ⏰ Final status timeout")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(improved_debug()) 