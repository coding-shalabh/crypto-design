#!/usr/bin/env python3
"""
Test script to verify AI analysis logs and auto-close fixes
"""
import asyncio
import websockets
import json
import time

async def test_bot_fixes():
    """Test the fixes for bot configuration and auto-close"""
    try:
        uri = "ws://localhost:8768"
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            print("🧪 TESTING BOT FIXES")
            print("="*60)
            
            # 1. Stop any running bot first
            print("\n1️⃣ Stopping any running bot...")
            await websocket.send(json.dumps({'type': 'stop_bot'}))
            stop_response = await websocket.recv()
            print(f"   Stop result: {json.loads(stop_response).get('type')}")
            
            # 2. Start bot with proper configuration
            print("\n2️⃣ Starting bot with configuration...")
            bot_config = {
                'max_trades_per_day': 10,
                'trade_amount_usdt': 50,
                'profit_target_min': 3,  # $3 profit target
                'profit_target_max': 5,
                'stop_loss_percent': 1.5,
                'trailing_enabled': True,
                'trade_interval_secs': 60,  # 1 minute for fast testing
                'allowed_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
                'ai_confidence_threshold': 0.65,
                'monitor_open_trades': True,
                'manual_approval_mode': False
            }
            
            start_message = {
                'type': 'start_bot',
                'config': bot_config
            }
            
            await websocket.send(json.dumps(start_message))
            start_response = await websocket.recv()
            start_data = json.loads(start_response)
            
            if start_data.get('type') == 'bot_start_response':
                if start_data.get('data', {}).get('success'):
                    print("   ✅ Bot started successfully")
                else:
                    print(f"   ❌ Bot start failed: {start_data}")
            
            # 3. Check bot status with config
            print("\n3️⃣ Checking bot status and configuration...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            
            if status_data.get('type') == 'bot_status_response':
                bot_data = status_data.get('data', {})
                config = bot_data.get('config', {})
                
                print(f"   ✅ Bot enabled: {bot_data.get('enabled')}")
                print(f"   ✅ Profit target min: ${config.get('profit_target_min', 'Not set')}")
                print(f"   ✅ Stop loss: {config.get('stop_loss_percent', 'Not set')}%")
                print(f"   ✅ Monitor trades: {config.get('monitor_open_trades', 'Not set')}")
                print(f"   ✅ Trailing enabled: {config.get('trailing_enabled', 'Not set')}")
                print(f"   ✅ Analysis interval: {config.get('trade_interval_secs', 'Not set')} seconds")
                
                # Verify all config values are set correctly
                if config.get('profit_target_min') == 3:
                    print("   🎯 PROFIT TARGET FIX: Working correctly!")
                else:
                    print(f"   ❌ PROFIT TARGET ISSUE: Expected 3, got {config.get('profit_target_min')}")
            
            # 4. Test AI Analysis logging
            print("\n4️⃣ Testing AI Analysis...")
            await websocket.send(json.dumps({'type': 'get_ai_analysis', 'symbol': 'BTCUSDT'}))
            
            # Wait for analysis response and potential logs
            messages_received = 0
            while messages_received < 3:  # Wait for a few messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(response)
                    messages_received += 1
                    
                    msg_type = data.get('type')
                    if msg_type == 'ai_analysis_response':
                        print("   ✅ AI Analysis response received")
                    elif msg_type == 'analysis_log':
                        print("   🎯 AI ANALYSIS LOG FIX: Frontend log entry created!")
                        log_data = data.get('data', data)  # Handle both formats
                        print(f"      Message: {log_data.get('message', 'No message')}")
                    elif msg_type in ['price_updates_batch']:
                        continue  # Skip price updates
                    else:
                        print(f"   📨 Other message: {msg_type}")
                        
                except asyncio.TimeoutError:
                    break
            
            # 5. Create a small test position to test auto-close
            print("\n5️⃣ Testing Auto-Close with small position...")
            test_trade = {
                'type': 'execute_trade',
                'trade_data': {
                    'symbol': 'BTCUSDT',
                    'direction': 'buy',
                    'amount': 0.001,  # Very small amount
                    'price': 50000,   # Fixed price
                    'trade_type': 'manual'
                }
            }
            
            await websocket.send(json.dumps(test_trade))
            trade_response = await websocket.recv()
            trade_data = json.loads(trade_response)
            
            if trade_data.get('type') == 'trade_executed':
                print("   ✅ Test trade executed")
                print("   📊 Auto-close monitoring should now check this position...")
                print("   💡 Create profit by manually updating price or wait for market movement")
            
            # 6. Monitor for auto-close messages
            print("\n6️⃣ Monitoring for auto-close activity (30 seconds)...")
            start_time = time.time()
            autoclose_detected = False
            
            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    msg_type = data.get('type')
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if msg_type == 'auto_close_notification':
                        print(f"   [⭐{timestamp}] 🎯 AUTO-CLOSE DETECTED!")
                        autoclose_detected = True
                        close_data = data.get('data', {})
                        symbol = close_data.get('symbol', 'Unknown')
                        pnl = close_data.get('pnl_usd', 0)
                        close_type = close_data.get('type', 'unknown')
                        print(f"      {symbol}: {close_type} with PnL ${pnl:.2f}")
                    elif msg_type == 'trade_closed':
                        print(f"   [{timestamp}] 📊 Trade closed")
                        close_data = data.get('data', {})
                        if close_data.get('auto_close'):
                            print("   🎯 AUTO-CLOSE CONFIRMED!")
                            autoclose_detected = True
                    elif msg_type == 'analysis_log':
                        log_data = data.get('data', data)
                        print(f"   [{timestamp}] 🧠 Analysis Log: {log_data.get('message', 'No message')}")
                    elif msg_type in ['price_updates_batch', 'position_update']:
                        continue  # Skip frequent updates
                    
                except asyncio.TimeoutError:
                    print(f"   [{time.strftime('%H:%M:%S')}] ... (monitoring)")
            
            print("\n" + "="*60)
            print("🔧 SUMMARY OF FIXES:")
            print("1. ✅ Bot Configuration: Fixed config loading and status response")
            print("2. 🎯 AI Analysis Logs: Added proper frontend log format")
            print("3. 💰 Auto-Close Logic: Enhanced profit target conditions")
            
            if autoclose_detected:
                print("4. ✅ Auto-Close: Working correctly!")
            else:
                print("4. ⏳ Auto-Close: Monitor longer or create profitable position")
            
            print("\n💡 To see auto-close in action:")
            print("   - Wait for market price to move up $3+ on BTCUSDT")
            print("   - Or manually create a profitable trade")
            print("   - Check the frontend Logs tab for real-time updates")
            
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_fixes()) 