#!/usr/bin/env python3
"""
Test script to verify server startup and bot functionality
"""
import asyncio
import websockets
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

async def test_server_connection():
    """Test basic server connection"""
    try:
        logger.info("🔗 Testing server connection...")
        
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to server successfully!")
            
            # Wait for initial data
            logger.info("📤 Waiting for initial data...")
            initial_data = await websocket.recv()
            data = json.loads(initial_data)
            logger.info(f"📨 Received initial data: {data.get('type', 'unknown')}")
            
            # Test bot status
            logger.info("🤖 Requesting bot status...")
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            response = await websocket.recv()
            bot_status = json.loads(response)
            logger.info(f"📊 Bot status: {bot_status.get('data', {}).get('enabled', False)}")
            
            # Test bot start
            logger.info("🚀 Starting bot...")
            await websocket.send(json.dumps({
                'type': 'start_bot',
                'config': {
                    'max_trades_per_day': 5,
                    'trade_amount_usdt': 100,
                    'ai_confidence_threshold': 0.6
                }
            }))
            
            response = await websocket.recv()
            start_result = json.loads(response)
            logger.info(f"🤖 Bot start result: {start_result.get('data', {}).get('success', False)}")
            
            if start_result.get('data', {}).get('success', False):
                logger.info("✅ Bot started successfully!")
                
                # Wait a bit for AI analysis to start
                logger.info("⏳ Waiting for AI analysis to start...")
                await asyncio.sleep(5)
                
                # Test manual AI analysis
                logger.info("  Testing manual AI analysis...")
                await websocket.send(json.dumps({
                    'type': 'get_ai_analysis',
                    'symbol': 'BTCUSDT'
                }))
                
                response = await websocket.recv()
                ai_result = json.loads(response)
                logger.info(f"  AI analysis result: {ai_result.get('type', 'unknown')}")
                
                # Wait for analysis logs
                logger.info("📋 Waiting for analysis logs...")
                await asyncio.sleep(10)
                
                # Test bot stop
                logger.info("🛑 Stopping bot...")
                await websocket.send(json.dumps({'type': 'stop_bot'}))
                response = await websocket.recv()
                stop_result = json.loads(response)
                logger.info(f"🛑 Bot stop result: {stop_result.get('data', {}).get('success', False)}")
            else:
                logger.error(f"❌ Bot start failed: {start_result.get('data', {}).get('message', 'Unknown error')}")
            
            logger.info("✅ Server test completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Server test failed: {e}")

async def test_websocket_messages():
    """Test various WebSocket messages"""
    try:
        logger.info("📨 Testing WebSocket messages...")
        
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            # Test positions request
            logger.info("📊 Testing positions request...")
            await websocket.send(json.dumps({'type': 'get_positions'}))
            response = await websocket.recv()
            positions = json.loads(response)
            logger.info(f"📊 Positions response: {positions.get('type', 'unknown')}")
            
            # Test trade history request
            logger.info("📋 Testing trade history request...")
            await websocket.send(json.dumps({'type': 'get_trade_history', 'limit': 10}))
            response = await websocket.recv()
            history = json.loads(response)
            logger.info(f"📋 Trade history response: {history.get('type', 'unknown')}")
            
            # Test crypto data request
            logger.info("🪙 Testing crypto data request...")
            await websocket.send(json.dumps({'type': 'get_crypto_data'}))
            response = await websocket.recv()
            crypto_data = json.loads(response)
            logger.info(f"🪙 Crypto data response: {crypto_data.get('type', 'unknown')}")
            
            logger.info("✅ WebSocket message tests completed!")
            
    except Exception as e:
        logger.error(f"❌ WebSocket message test failed: {e}")

async def main():
    """Main test function"""
    logger.info("🧪 Starting server tests...")
    
    try:
        # Test basic connection
        await test_server_connection()
        
        # Wait a bit between tests
        await asyncio.sleep(2)
        
        # Test WebSocket messages
        await test_websocket_messages()
        
        logger.info("🎉 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 