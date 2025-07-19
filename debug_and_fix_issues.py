#!/usr/bin/env python3
"""
Debug and fix AI analysis logs and auto-close issues
"""
import asyncio
import websockets
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_system_issues():
    """Debug AI analysis and auto-close issues"""
    try:
        uri = "ws://localhost:8768"
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            print("🔍 DEBUGGING SYSTEM ISSUES")
            print("="*60)
            
            # 1. Test AI Analysis Response
            print("\n1️⃣ Testing AI Analysis Response...")
            ai_message = {'type': 'get_ai_analysis', 'symbol': 'BTCUSDT'}
            await websocket.send(json.dumps(ai_message))
            
            ai_response = await websocket.recv()
            ai_data = json.loads(ai_response)
            
            if ai_data.get('type') == 'ai_analysis_response':
                print("✅ AI Analysis Response received")
                analysis = ai_data.get('data', {}).get('analysis', {})
                print(f"   Source: {analysis.get('source', 'Unknown')}")
                print(f"   Final Action: {analysis.get('final_recommendation', {}).get('action', 'Unknown')}")
                print(f"   Confidence: {analysis.get('combined_confidence', 0):.2f}")
                
                # Check if this should create logs in frontend
                print("   Message format for frontend:")
                print(f"   - Type: {ai_data.get('type')}")
                print(f"   - Symbol: {ai_data.get('data', {}).get('symbol')}")
                print(f"   - Timestamp: {ai_data.get('data', {}).get('timestamp')}")
            else:
                print(f"❌ Unexpected AI response: {ai_data.get('type')}")
            
            # 2. Check Bot Status and Active Trades
            print("\n2️⃣ Checking Bot Status and Active Trades...")
            status_message = {'type': 'get_bot_status'}
            await websocket.send(json.dumps(status_message))
            
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            
            if status_data.get('type') == 'bot_status_response':
                bot_data = status_data.get('data', {})
                print(f"✅ Bot Enabled: {bot_data.get('enabled', False)}")
                print(f"   Active Trades: {len(bot_data.get('active_trades', []))}")
                print(f"   Config Keys: {list(bot_data.get('config', {}).keys())}")
                
                config = bot_data.get('config', {})
                print(f"   Profit Target Min: {config.get('profit_target_min', 'Not set')}")
                print(f"   Profit Target Max: {config.get('profit_target_max', 'Not set')}")
                print(f"   Stop Loss Percent: {config.get('stop_loss_percent', 'Not set')}")
                print(f"   Monitor Open Trades: {config.get('monitor_open_trades', 'Not set')}")
                print(f"   Trailing Enabled: {config.get('trailing_enabled', 'Not set')}")
            
            # 3. Check Current Positions
            print("\n3️⃣ Checking Current Positions...")
            positions_message = {'type': 'get_positions'}
            await websocket.send(json.dumps(positions_message))
            
            positions_response = await websocket.recv()
            positions_data = json.loads(positions_response)
            
            if positions_data.get('type') == 'positions_response':
                positions = positions_data.get('data', {}).get('positions', {})
                print(f"✅ Current Positions: {len(positions)}")
                
                for symbol, position in positions.items():
                    entry_price = position.get('entry_price', 0)
                    current_price = position.get('current_price', 0)
                    pnl = position.get('unrealized_pnl', 0)
                    direction = position.get('direction', 'unknown')
                    
                    print(f"   {symbol}: {direction.upper()}")
                    print(f"     Entry: ${entry_price:.2f}, Current: ${current_price:.2f}")
                    print(f"     PnL: ${pnl:.2f}")
                    
                    # Calculate profit percentage and check auto-close conditions
                    if entry_price > 0:
                        profit_percent = ((current_price - entry_price) / entry_price) * 100
                        print(f"     Profit %: {profit_percent:.2f}%")
                        
                        # Check against config
                        if config:
                            target_min = config.get('profit_target_min', 3)
                            target_max = config.get('profit_target_max', 5)
                            stop_loss = config.get('stop_loss_percent', 1.5)
                            
                            print(f"     Should close if profit > ${target_min} or loss > {stop_loss}%")
                            
                            if pnl >= target_min:
                                print(f"     🎯 SHOULD AUTO-CLOSE: Profit ${pnl:.2f} >= Target ${target_min}")
                            elif profit_percent <= -stop_loss:
                                print(f"     🛑 SHOULD AUTO-CLOSE: Loss {profit_percent:.2f}% >= Stop {stop_loss}%")
                            else:
                                print(f"     ⏳ No auto-close conditions met")
            
            # 4. Request Analysis and Trade Logs
            print("\n4️⃣ Checking Analysis and Trade Logs...")
            
            # Get analysis logs
            logs_message = {'type': 'get_analysis_logs', 'limit': 5}
            await websocket.send(json.dumps(logs_message))
            
            logs_response = await websocket.recv()
            logs_data = json.loads(logs_response)
            
            if logs_data.get('type') == 'analysis_logs_response':
                logs = logs_data.get('data', {}).get('logs', [])
                print(f"✅ Analysis Logs Available: {len(logs)}")
                for i, log in enumerate(logs[:3]):
                    print(f"   {i+1}. {log.get('message', 'No message')}")
            
            # Get trade logs
            trade_logs_message = {'type': 'get_trade_logs', 'limit': 5}
            await websocket.send(json.dumps(trade_logs_message))
            
            trade_logs_response = await websocket.recv()
            trade_logs_data = json.loads(trade_logs_response)
            
            if trade_logs_data.get('type') == 'trade_logs_response':
                trade_logs = trade_logs_data.get('data', {}).get('logs', [])
                print(f"✅ Trade Logs Available: {len(trade_logs)}")
                for i, log in enumerate(trade_logs[:3]):
                    symbol = log.get('symbol', 'Unknown')
                    decision = log.get('trade_decision', 'Unknown')
                    confidence = log.get('final_confidence_score', 0)
                    print(f"   {i+1}. {symbol}: {decision} (Confidence: {confidence:.2f})")
            
            # 5. Test Manual Trade Execution to Check Auto-Close
            print("\n5️⃣ Testing Manual Trade for Auto-Close Debug...")
            if len(positions) == 0:
                print("No active positions. Creating a test trade...")
                
                # Execute a small test trade
                test_trade = {
                    'type': 'execute_trade',
                    'trade_data': {
                        'symbol': 'BTCUSDT',
                        'direction': 'buy',
                        'amount': 0.001,  # Very small amount
                        'price': 50000,   # Fixed price for testing
                        'trade_type': 'manual'
                    }
                }
                
                await websocket.send(json.dumps(test_trade))
                trade_response = await websocket.recv()
                trade_data = json.loads(trade_response)
                
                print(f"Test trade result: {trade_data.get('type')}")
                if trade_data.get('type') == 'trade_executed':
                    print("✅ Test trade executed. Auto-close should monitor this position.")
                    print("   Check if auto-close monitoring detects this trade...")
                else:
                    print(f"❌ Test trade failed: {trade_data}")
            
            print("\n" + "="*60)
            print("🔧 RECOMMENDATIONS:")
            print("1. Check if AI analysis logs are properly formatted for frontend")
            print("2. Verify auto-close monitoring is running and detecting positions")
            print("3. Check profit target configuration (USD vs percentage)")
            print("4. Monitor WebSocket message flow for missing broadcasts")
            
    except Exception as e:
        logger.error(f"Error in debug: {e}")
        print(f"\n❌ Debug Error: {e}")

async def test_live_monitoring():
    """Test live monitoring for a few cycles"""
    try:
        uri = "ws://localhost:8768"
        
        print("\n🔄 TESTING LIVE MONITORING...")
        print("Monitoring WebSocket messages for 30 seconds...")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:  # Monitor for 30 seconds
                try:
                    # Wait for incoming messages with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    timestamp = time.strftime('%H:%M:%S')
                    
                    if msg_type == 'ai_analysis_response':
                        symbol = data.get('data', {}).get('symbol', 'Unknown')
                        analysis = data.get('data', {}).get('analysis', {})
                        action = analysis.get('final_recommendation', {}).get('action', 'Unknown')
                        confidence = analysis.get('combined_confidence', 0)
                        print(f"[{timestamp}] 🧠 AI Analysis: {symbol} -> {action} ({confidence:.2f})")
                    
                    elif msg_type == 'auto_close_notification':
                        symbol = data.get('data', {}).get('symbol', 'Unknown')
                        pnl = data.get('data', {}).get('pnl_usd', 0)
                        close_type = data.get('data', {}).get('type', 'unknown')
                        print(f"[{timestamp}] 🎯 AUTO-CLOSE: {symbol} -> {close_type} (${pnl:.2f})")
                    
                    elif msg_type == 'trade_closed':
                        symbol = data.get('data', {}).get('symbol', 'Unknown')
                        reason = data.get('data', {}).get('reason', 'unknown')
                        pnl = data.get('data', {}).get('pnl_usd', 0)
                        auto_close = data.get('data', {}).get('auto_close', False)
                        auto_indicator = "🤖" if auto_close else "👤"
                        print(f"[{timestamp}] {auto_indicator} Trade Closed: {symbol} -> {reason} (${pnl:.2f})")
                    
                    elif msg_type == 'position_update':
                        positions = data.get('data', {}).get('positions', {})
                        print(f"[{timestamp}] 📊 Position Update: {len(positions)} positions")
                    
                    elif msg_type in ['price_updates_batch']:
                        # Skip frequent price updates for cleaner output
                        continue
                    
                    else:
                        print(f"[{timestamp}] 📨 {msg_type}")
                        
                except asyncio.TimeoutError:
                    print(f"[{time.strftime('%H:%M:%S')}] ... (no messages)")
                    
            print(f"\n📊 Monitoring complete. Received {message_count} messages in 30 seconds.")
    
    except Exception as e:
        logger.error(f"Error in live monitoring: {e}")

if __name__ == "__main__":
    print("🔧 DEBUGGING SYSTEM ISSUES")
    print("This script will identify problems with:")
    print("1. AI Analysis logs not appearing in frontend")
    print("2. Auto-close not working for profitable trades")
    print("3. Missing WebSocket message broadcasts")
    
    # Run system debug
    asyncio.run(debug_system_issues())
    
    # Test live monitoring
    asyncio.run(test_live_monitoring())
    
    print("\n✅ Debug complete!") 