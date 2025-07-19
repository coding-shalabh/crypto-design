#!/usr/bin/env python3
"""
Detailed debug for bot configuration issue
"""
import asyncio
import websockets
import json
import time

async def debug_config_detailed():
    """Debug the exact bot configuration issue"""
    try:
        uri = "ws://localhost:8769"
        print(f"🔍 Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            print("✅ Connected successfully")
            
            print("\n" + "="*70)
            print("🔍 DETAILED BOT CONFIGURATION DEBUG")
            print("="*70)
            
            # 1. Stop any running bot first
            print("\n1️⃣ Stopping any running bot...")
            await websocket.send(json.dumps({'type': 'stop_bot'}))
            
            try:
                stop_response = await asyncio.wait_for(websocket.recv(), timeout=3)
                stop_data = json.loads(stop_response)
                print(f"   Stop result: {stop_data.get('type')}")
            except asyncio.TimeoutError:
                print("   Stop timeout")
            
            # 2. Check initial bot status
            print("\n2️⃣ Checking initial bot status...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            try:
                status_response = await asyncio.wait_for(websocket.recv(), timeout=3)
                status_data = json.loads(status_response)
                print(f"   Status response type: {status_data.get('type')}")
                
                if status_data.get('type') == 'bot_status_response':
                    data = status_data.get('data', {})
                    config = data.get('config', {})
                    print(f"   Initial enabled: {data.get('enabled', False)}")
                    print(f"   Initial config keys: {list(config.keys())}")
                    print(f"   Initial profit_target_min: {config.get('profit_target_min', 'NOT FOUND')}")
                    
            except asyncio.TimeoutError:
                print("   Initial status timeout")
            
            # 3. Start bot with explicit configuration
            print("\n3️⃣ Starting bot with explicit configuration...")
            bot_config = {
                'max_trades_per_day': 5,
                'trade_amount_usdt': 25,
                'profit_target_min': 2.5,  # Explicit USD value
                'profit_target_max': 5.0,
                'stop_loss_percent': 1.0,
                'trailing_enabled': False,
                'monitor_open_trades': True,
                'ai_confidence_threshold': 0.5,
                'analysis_interval_minutes': 2,
                'test_mode': True,
                'manual_approval_mode': False
            }
            
            print(f"   📤 Sending config: {json.dumps(bot_config, indent=2)}")
            
            start_message = {
                'type': 'start_bot',
                'config': bot_config
            }
            await websocket.send(json.dumps(start_message))
            
            # 4. Wait for start response and check status immediately
            print("\n4️⃣ Waiting for start response...")
            try:
                start_response = await asyncio.wait_for(websocket.recv(), timeout=5)
                start_data = json.loads(start_response)
                print(f"   Start response: {start_data.get('type')}")
                
                if 'data' in start_data:
                    start_result = start_data.get('data', {})
                    print(f"   Start success: {start_result.get('success', False)}")
                    print(f"   Start message: {start_result.get('message', 'No message')}")
                    
                    # Check if config is in start response
                    if 'config' in start_result:
                        start_config = start_result.get('config', {})
                        print(f"   Start response config keys: {list(start_config.keys())}")
                        print(f"   Start response profit_target_min: {start_config.get('profit_target_min', 'NOT FOUND')}")
                        
            except asyncio.TimeoutError:
                print("   Start response timeout")
            
            # 5. Wait 2 seconds and check status again
            print("\n5️⃣ Waiting 2 seconds and checking status again...")
            await asyncio.sleep(2)
            
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            # Look through multiple responses to find bot_status_response
            for attempt in range(5):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    response_type = data.get('type')
                    
                    print(f"   Response #{attempt + 1}: {response_type}")
                    
                    if response_type == 'bot_status_response':
                        bot_data = data.get('data', {})
                        config = bot_data.get('config', {})
                        
                        print(f"\n   📊 FINAL BOT STATUS:")
                        print(f"      Enabled: {bot_data.get('enabled', False)}")
                        print(f"      Config type: {type(config)}")
                        print(f"      Config keys: {list(config.keys())}")
                        print(f"      Profit Target Min: {config.get('profit_target_min', 'NOT FOUND')}")
                        print(f"      Stop Loss: {config.get('stop_loss_percent', 'NOT FOUND')}")
                        print(f"      Monitor Trades: {config.get('monitor_open_trades', 'NOT FOUND')}")
                        print(f"      Test Mode: {config.get('test_mode', 'NOT FOUND')}")
                        
                        # Print full config for debugging
                        print(f"\n   🔍 FULL CONFIG DEBUG:")
                        for key, value in config.items():
                            print(f"      {key}: {value} ({type(value).__name__})")
                        
                        break
                        
                except asyncio.TimeoutError:
                    print(f"   Timeout on attempt {attempt + 1}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_config_detailed()) 