#!/usr/bin/env python3
"""
Comprehensive test for AI analysis logs and auto-close functionality
"""
import asyncio
import websockets
import json
import time

async def comprehensive_test():
    """Test both AI analysis logs and auto-close functionality"""
    try:
        uri = "ws://localhost:8769"
        print(f"🔍 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            print("✅ Connected successfully")
            
            print("\n" + "="*70)
            print("🧪 COMPREHENSIVE TEST: AI LOGS & AUTO-CLOSE")
            print("="*70)
            
            # 1. Start bot with auto-close configuration
            print("\n1️⃣ Starting bot with auto-close configuration...")
            bot_config = {
                'max_trades_per_day': 5,
                'trade_amount_usdt': 10,  # Small amount for testing
                'profit_target_min': 1.0,  # $1 USD profit target (easy to hit)
                'profit_target_max': 3.0,
                'stop_loss_percent': 0.5,  # 0.5% stop loss
                'trailing_enabled': False,  # Disable for simple testing
                'monitor_open_trades': True,  # Enable monitoring
                'ai_confidence_threshold': 0.4,  # Lower threshold for testing
                'analysis_interval_minutes': 1,  # Fast analysis
                'test_mode': True,
                'manual_approval_mode': False  # Auto-execute trades
            }
            
            await websocket.send(json.dumps({'type': 'start_bot', 'config': bot_config}))
            
            # Wait for start response
            start_response = await asyncio.wait_for(websocket.recv(), timeout=3)
            start_data = json.loads(start_response)
            print(f"   ✅ Bot started: {start_data.get('type')}")
            
            # 2. Check bot status to verify configuration
            print("\n2️⃣ Verifying bot configuration...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            # Look for bot status response in next few messages
            for attempt in range(5):
                response = await asyncio.wait_for(websocket.recv(), timeout=2)
                data = json.loads(response)
                if data.get('type') == 'bot_status_response':
                    bot_data = data.get('data', {})
                    config = bot_data.get('config', {})
                    print(f"   ✅ Bot Enabled: {bot_data.get('enabled', False)}")
                    print(f"   💰 Profit Target: ${config.get('profit_target_min', 'Not Set')}")
                    print(f"   📈 Monitor Trades: {config.get('monitor_open_trades', False)}")
                    break
            
            # 3. Monitor for AI analysis logs for 30 seconds
            print("\n3️⃣ Monitoring for AI analysis logs (30 seconds)...")
            start_time = time.time()
            analysis_logs = []
            ai_responses = []
            
            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    msg_type = data.get('type', '')
                    
                    if msg_type == 'analysis_log':
                        analysis_logs.append(data)
                        message = data.get('message', '')
                        print(f"   📝 Analysis Log: {message[:100]}...")
                        
                    elif msg_type == 'ai_analysis_response':
                        ai_responses.append(data)
                        symbol = data.get('symbol', 'Unknown')
                        analysis = data.get('analysis', {})
                        final_rec = analysis.get('final_recommendation', {})
                        action = final_rec.get('action', 'UNKNOWN')
                        confidence = final_rec.get('confidence', 0)
                        print(f"   🧠 AI Analysis: {symbol} -> {action} ({confidence:.2f})")
                        
                    elif 'trade' in msg_type.lower():
                        print(f"   📈 Trade Message: {msg_type}")
                        
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                    continue
            
            print(f"\n\n📊 AI Analysis Summary:")
            print(f"   Analysis logs received: {len(analysis_logs)}")
            print(f"   AI responses received: {len(ai_responses)}")
            
            # 4. Try to execute a manual trade to test auto-close
            print("\n4️⃣ Executing a test trade to verify auto-close...")
            
            # Execute a BUY trade that should quickly hit profit target
            trade_data = {
                'symbol': 'BTCUSDT',
                'direction': 'buy',
                'amount_usdt': 10,
                'price': 95000,  # Set a lower entry price to simulate immediate profit
                'trade_type': 'manual'
            }
            
            await websocket.send(json.dumps({
                'type': 'execute_trade',
                'trade_data': trade_data
            }))
            
            # Wait for trade execution response
            try:
                trade_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                trade_data_result = json.loads(trade_response)
                print(f"   📈 Trade executed: {trade_data_result.get('type')}")
                
                if trade_data_result.get('type') == 'trade_executed':
                    print(f"   ✅ Trade successful: {trade_data_result.get('data', {}).get('trade', {}).get('symbol')}")
                    
                    # 5. Monitor for auto-close for 60 seconds
                    print("\n5️⃣ Monitoring for auto-close activity (60 seconds)...")
                    autoclose_start = time.time()
                    autoclose_messages = []
                    position_updates = []
                    
                    while time.time() - autoclose_start < 60:
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            data = json.loads(response)
                            msg_type = data.get('type', '')
                            
                            if 'close' in msg_type.lower() or 'profit' in msg_type.lower():
                                autoclose_messages.append(data)
                                print(f"   💰 Auto-close: {msg_type}")
                                
                            elif msg_type == 'auto_close_notification':
                                notification = data.get('message', '')
                                print(f"   🔔 Notification: {notification}")
                                
                            elif msg_type == 'position_update':
                                position_updates.append(data)
                                positions = data.get('data', {}).get('positions', {})
                                print(f"   📊 Position Update: {len(positions)} positions")
                                
                            elif msg_type == 'trade_closed':
                                trade_data = data.get('data', data)
                                symbol = trade_data.get('symbol', 'Unknown')
                                reason = trade_data.get('reason', 'Unknown')
                                pnl = trade_data.get('pnl_usd', 0)
                                print(f"   🎯 Trade Closed: {symbol} - {reason} - ${pnl:.2f}")
                                
                        except asyncio.TimeoutError:
                            print(".", end="", flush=True)
                            continue
                    
                    print(f"\n\n💰 Auto-close Summary:")
                    print(f"   Auto-close messages: {len(autoclose_messages)}")
                    print(f"   Position updates: {len(position_updates)}")
                    
                else:
                    print(f"   ❌ Trade failed: {trade_data_result.get('type')}")
                    
            except asyncio.TimeoutError:
                print("   ⏰ Trade execution timeout")
            
            # 6. Final status check
            print("\n6️⃣ Final system status...")
            await websocket.send(json.dumps({'type': 'get_positions'}))
            
            try:
                positions_response = await asyncio.wait_for(websocket.recv(), timeout=3)
                positions_data = json.loads(positions_response)
                positions = positions_data.get('positions', {})
                print(f"   📊 Final positions: {len(positions)}")
                for symbol, pos in positions.items():
                    pnl = pos.get('unrealized_pnl', 0)
                    print(f"      - {symbol}: ${pnl:.2f} PnL")
                    
            except asyncio.TimeoutError:
                print("   ⏰ Positions check timeout")
            
            print("\n🎉 COMPREHENSIVE TEST COMPLETE!")
            print("="*70)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(comprehensive_test()) 