#!/usr/bin/env python3
"""
Debug script to check trading bot status and AI analysis
"""
import asyncio
import websockets
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_bot_status():
    """Check the current bot status"""
    try:
        # Connect to WebSocket server
        uri = "ws://localhost:8768"  # Updated port from logs
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            # First, consume the initial_data message
            initial_response = await websocket.recv()
            initial_data = json.loads(initial_response)
            logger.info(f"Received initial data: {initial_data.get('type', 'unknown')}")
            
            # Now send get_bot_status request
            message = {
                'type': 'get_bot_status'
            }
            await websocket.send(json.dumps(message))
            logger.info("Sent get_bot_status request")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            
            logger.info(f"Received response: {data}")
            
            if data.get('type') == 'bot_status_response':
                bot_data = data.get('data', {})
                enabled = bot_data.get('enabled', False)
                config = bot_data.get('config', {})
                active_trades = bot_data.get('active_trades', [])
                
                print("\n" + "="*50)
                print("🤖 BOT STATUS DEBUG")
                print("="*50)
                print(f"Bot Enabled: {enabled}")
                print(f"Active Trades: {len(active_trades)}")
                print(f"Bot Config Keys: {list(config.keys()) if config else 'No config'}")
                if config:
                    print(f"Allowed Pairs: {config.get('allowed_pairs', 'Not set')}")
                    print(f"AI Confidence Threshold: {config.get('ai_confidence_threshold', 'Not set')}")
                    print(f"Trade Interval: {config.get('trade_interval_secs', 'Not set')} seconds")
                    print(f"Manual Approval Mode: {config.get('manual_approval_mode', 'Not set')}")
                print("="*50)
                
                if not enabled:
                    print("❌ BOT IS NOT ENABLED - This is why AI analysis is not running!")
                    print("💡 You need to start the bot to see AI analysis logs")
                    print("💡 Go to the web interface and click 'Start Bot'")
                else:
                    print("✅ BOT IS ENABLED - AI analysis should be running")
                    
                    # Request AI analysis logs
                    logs_message = {
                        'type': 'get_analysis_logs',
                        'limit': 10
                    }
                    await websocket.send(json.dumps(logs_message))
                    
                    logs_response = await websocket.recv()
                    logs_data = json.loads(logs_response)
                    
                    if logs_data.get('type') == 'analysis_logs_response':
                        logs = logs_data.get('data', {}).get('logs', [])
                        print(f"\n📊 Recent Analysis Logs ({len(logs)} entries):")
                        for i, log in enumerate(logs[:5]):
                            print(f"  {i+1}. {log.get('message', 'No message')}")
                            
                    # Also request trade logs
                    trade_logs_message = {
                        'type': 'get_trade_logs',
                        'limit': 10
                    }
                    await websocket.send(json.dumps(trade_logs_message))
                    
                    trade_logs_response = await websocket.recv()
                    trade_logs_data = json.loads(trade_logs_response)
                    
                    if trade_logs_data.get('type') == 'trade_logs_response':
                        trade_logs = trade_logs_data.get('data', {}).get('logs', [])
                        print(f"\n📈 Recent Trade Logs ({len(trade_logs)} entries):")
                        for i, log in enumerate(trade_logs[:5]):
                            symbol = log.get('symbol', 'Unknown')
                            confidence = log.get('final_confidence_score', 0)
                            decision = log.get('trade_decision', 'Unknown')
                            print(f"  {i+1}. {symbol}: {decision} (Confidence: {confidence:.2f})")
                
            else:
                print(f"❌ Unexpected response type: {data.get('type')}")
                print(f"Full response: {data}")
                
    except Exception as e:
        logger.error(f"Error checking bot status: {e}")
        print(f"\n❌ Connection Error: {e}")
        print("💡 Make sure the WebSocket server is running")

async def test_manual_ai_analysis():
    """Test manual AI analysis request"""
    try:
        uri = "ws://localhost:8768"
        
        async with websockets.connect(uri) as websocket:
            # Consume initial data
            await websocket.recv()
            
            # Send manual AI analysis request
            message = {
                'type': 'get_ai_analysis',
                'symbol': 'BTCUSDT'
            }
            await websocket.send(json.dumps(message))
            logger.info("Sent manual AI analysis request for BTCUSDT")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30)
                data = json.loads(response)
                
                print("\n" + "="*50)
                print("🧠 MANUAL AI ANALYSIS TEST")
                print("="*50)
                
                if data.get('type') == 'ai_analysis_response':
                    analysis_data = data.get('data', {})
                    analysis = analysis_data.get('analysis', {})
                    
                    if analysis:
                        final_rec = analysis.get('final_recommendation', {})
                        action = final_rec.get('action', 'UNKNOWN')
                        confidence = final_rec.get('confidence', 0)
                        
                        print(f"✅ AI Analysis Successful!")
                        print(f"Symbol: {analysis_data.get('symbol', 'UNKNOWN')}")
                        print(f"Action: {action}")
                        print(f"Confidence: {confidence:.2f}")
                        print(f"Source: {analysis.get('source', 'unknown')}")
                        
                        # Show more details
                        grok_analysis = analysis.get('grok_analysis', {})
                        claude_analysis = analysis.get('claude_analysis', {})
                        
                        if grok_analysis:
                            print(f"Grok Sentiment: {grok_analysis.get('sentiment', 'unknown')}")
                        if claude_analysis:
                            print(f"Claude Recommendation: {claude_analysis.get('recommendation', {}).get('action', 'unknown')}")
                    else:
                        print("❌ No analysis data received")
                        print(f"Raw response: {data}")
                elif data.get('type') == 'error':
                    print(f"❌ Analysis Error: {data.get('data', {}).get('message', 'Unknown error')}")
                else:
                    print(f"❌ Unexpected response: {data.get('type')}")
                    print(f"Data: {data}")
                    
            except asyncio.TimeoutError:
                print("❌ AI Analysis request timed out (30 seconds)")
                print("💡 This might indicate the AI analysis system is not responding")
                
    except Exception as e:
        logger.error(f"Error testing AI analysis: {e}")
        print(f"\n❌ AI Analysis Test Error: {e}")

if __name__ == "__main__":
    print("🔍 Debugging Trading Bot Status and AI Analysis...")
    
    # Run bot status check
    asyncio.run(check_bot_status())
    
    print("\n" + "="*50)
    print("🧠 Testing Manual AI Analysis...")
    
    # Run manual AI analysis test
    asyncio.run(test_manual_ai_analysis())
    
    print("\n✅ Debug complete!")
    print("\n💡 Key Points:")
    print("  - If bot is not enabled, no AI analysis logs will appear")
    print("  - Start the bot through the web interface to see analysis logs")
    print("  - Manual AI analysis should work regardless of bot status") 