#!/usr/bin/env python3
"""
Script to start the trading bot with configuration
This will enable AI analysis logging
"""
import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_trading_bot():
    """Start the trading bot with configuration"""
    try:
        uri = "ws://localhost:8768"
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            # Start bot with configuration
            bot_config = {
                'max_trades_per_day': 10,
                'trade_amount_usdt': 50,
                'profit_target_min': 3,
                'profit_target_max': 5,
                'stop_loss_percent': 1.5,
                'trailing_enabled': True,
                'trailing_trigger_usd': 1,
                'trailing_distance_usd': 0.5,
                'trade_interval_secs': 120,  # 2 minutes for testing
                'max_concurrent_trades': 20,
                'cooldown_secs': 300,
                'allowed_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
                'ai_confidence_threshold': 0.65,
                'run_time_minutes': 180,
                'test_mode': False,
                'risk_per_trade_percent': 5.0,
                'monitor_open_trades': True,
                'loss_check_interval_percent': 1,
                'rollback_enabled': True,
                'reanalysis_cooldown_seconds': 300,
                'reconfirm_before_entry': True,
                'slippage_tolerance_percent': 0.1,
                'signal_sources': ['gpt', 'claude'],
                'manual_approval_mode': False
            }
            
            message = {
                'type': 'start_bot',
                'config': bot_config
            }
            
            await websocket.send(json.dumps(message))
            logger.info("Sent start_bot request with configuration")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            print("\n" + "="*60)
            print("🤖 TRADING BOT START RESULT")
            print("="*60)
            
            if data.get('type') == 'bot_start_response':
                result = data.get('data', {})
                success = result.get('success', False)
                
                if success:
                    print("✅ Trading bot started successfully!")
                    print("🧠 AI analysis should now be running every 2 minutes")
                    print("📊 You should see analysis logs appearing soon")
                    
                    # Get updated bot status
                    await asyncio.sleep(1)
                    status_message = {'type': 'get_bot_status'}
                    await websocket.send(json.dumps(status_message))
                    
                    status_response = await websocket.recv()
                    status_data = json.loads(status_response)
                    
                    if status_data.get('type') == 'bot_status_response':
                        bot_data = status_data.get('data', {})
                        print(f"📈 Bot Status: Enabled = {bot_data.get('enabled', False)}")
                        print(f"⚙️ Config Loaded: {len(bot_data.get('config', {}))} settings")
                        print(f"🎯 Allowed Pairs: {bot_data.get('config', {}).get('allowed_pairs', [])}")
                        print(f"🤖 AI Threshold: {bot_data.get('config', {}).get('ai_confidence_threshold', 0)}")
                        print(f"⏱️ Analysis Interval: {bot_data.get('config', {}).get('trade_interval_secs', 0)} seconds")
                else:
                    print(f"❌ Failed to start trading bot: {result.get('message', 'Unknown error')}")
                    
            elif data.get('type') == 'start_bot_response':  # Alternative response type
                result = data.get('data', {})
                success = result.get('success', False)
                
                if success:
                    print("✅ Trading bot started successfully!")
                    print("🧠 AI analysis monitoring is now active")
                else:
                    print(f"❌ Failed to start trading bot: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Unexpected response: {data.get('type')}")
                print(f"Data: {data}")
                
            print("="*60)
            
    except Exception as e:
        logger.error(f"Error starting trading bot: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Trading Bot with Configuration...")
    print("💡 This will enable AI analysis logging every 2 minutes")
    
    asyncio.run(start_trading_bot())
    
    print("\n✅ Bot start attempt complete!")
    print("\n📊 What to expect:")
    print("  1. AI analysis will run every 2 minutes")
    print("  2. Analysis logs will appear in the web interface")
    print("  3. Trading opportunities will be evaluated automatically")
    print("  4. Check the web interface at http://localhost:3000") 