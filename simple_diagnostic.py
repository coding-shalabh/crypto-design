#!/usr/bin/env python3
"""
Simple diagnostic for AI analysis logs and auto-close
"""
import asyncio
import websockets
import json
import time

async def check_ai_logs_and_autoclose():
    """Check AI analysis logs and auto-close functionality"""
    try:
        uri = "ws://localhost:8768"
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            print("🔍 DIAGNOSTIC: AI Logs & Auto-Close")
            print("="*50)
            
            # 1. Check if AI analysis is working
            print("\n1️⃣ Testing AI Analysis...")
            await websocket.send(json.dumps({'type': 'get_ai_analysis', 'symbol': 'BTCUSDT'}))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get('type') == 'ai_analysis_response':
                print("✅ AI Analysis working")
                analysis = data.get('data', {}).get('analysis', {})
                action = analysis.get('final_recommendation', {}).get('action', 'UNKNOWN')
                confidence = analysis.get('combined_confidence', 0)
                source = analysis.get('source', 'unknown')
                print(f"   Result: {action} ({confidence:.2f}) from {source}")
            else:
                print(f"❌ AI Analysis issue: {data.get('type')}")
            
            # 2. Check analysis logs
            print("\n2️⃣ Checking Analysis Logs...")
            await websocket.send(json.dumps({'type': 'get_analysis_logs', 'limit': 3}))
            
            logs_response = await websocket.recv()
            logs_data = json.loads(logs_response)
            
            if logs_data.get('type') == 'analysis_logs_response':
                logs = logs_data.get('data', {}).get('logs', [])
                print(f"✅ Analysis logs found: {len(logs)}")
                for i, log in enumerate(logs[:2]):
                    print(f"   {i+1}. {log.get('message', 'No message')}")
            else:
                print("❌ No analysis logs response")
            
            # 3. Check bot status and config
            print("\n3️⃣ Checking Bot Configuration...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            status_response = await websocket.recv()
            status_data = json.loads(status_response)
            
            if status_data.get('type') == 'bot_status_response':
                bot_data = status_data.get('data', {})
                config = bot_data.get('config', {})
                print(f"✅ Bot enabled: {bot_data.get('enabled')}")
                print(f"   Profit target min: ${config.get('profit_target_min', 'Not set')}")
                print(f"   Stop loss: {config.get('stop_loss_percent', 'Not set')}%")
                print(f"   Monitor trades: {config.get('monitor_open_trades', 'Not set')}")
                
                # Check if there's a config issue
                if not config.get('monitor_open_trades', True):
                    print("❌ ISSUE: monitor_open_trades is disabled!")
                    
                profit_min = config.get('profit_target_min', 0)
                if profit_min <= 0:
                    print("❌ ISSUE: profit_target_min not set properly!")
                    
            # 4. Check current positions
            print("\n4️⃣ Checking Positions...")
            await websocket.send(json.dumps({'type': 'get_positions'}))
            
            pos_response = await websocket.recv()
            pos_data = json.loads(pos_response)
            
            if pos_data.get('type') == 'positions_response':
                positions = pos_data.get('data', {}).get('positions', {})
                print(f"✅ Active positions: {len(positions)}")
                
                for symbol, pos in positions.items():
                    pnl = pos.get('unrealized_pnl', 0)
                    entry_price = pos.get('entry_price', 0)
                    current_price = pos.get('current_price', 0)
                    
                    print(f"   {symbol}: PnL=${pnl:.2f}, Entry=${entry_price:.2f}, Current=${current_price:.2f}")
                    
                    # Check if should auto-close
                    if config and pnl > 0:
                        target_min = config.get('profit_target_min', 3)
                        if pnl >= target_min:
                            print(f"   🎯 SHOULD AUTO-CLOSE: PnL ${pnl:.2f} >= Target ${target_min}")
                        else:
                            print(f"   ⏳ Not yet profitable enough: ${pnl:.2f} < ${target_min}")
            
            print("\n" + "="*50)
            print("🔧 SUMMARY:")
            print("- AI Analysis: Check if working and logs are created")
            print("- Auto-Close: Check if monitoring is enabled and thresholds are correct")
            print("- Frontend: Logs should appear in TradingBot > Logs tab")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_ai_logs_and_autoclose()) 