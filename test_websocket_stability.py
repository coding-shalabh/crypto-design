#!/usr/bin/env python3
"""
Test script to verify WebSocket connection stability and trading flow
"""
import asyncio
import websockets
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

async def test_websocket_stability():
    """Test WebSocket connection stability and trading flow"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Test 1: Get initial data
            logger.info("Test 1: Getting initial data...")
            await websocket.send(json.dumps({"type": "get_positions"}))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received positions response: {data['type']}")
            
            await websocket.send(json.dumps({"type": "get_trade_history", "limit": 10}))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received trade history response: {data['type']}")
            
            await websocket.send(json.dumps({"type": "get_crypto_data"}))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received crypto data response: {data['type']}")
            
            # Test 2: Get bot status
            logger.info("Test 2: Getting bot status...")
            await websocket.send(json.dumps({"type": "get_bot_status"}))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received bot status: {data['data']['enabled']}")
            
            # Test 3: Start bot
            logger.info("Test 3: Starting bot...")
            await websocket.send(json.dumps({
                "type": "start_bot",
                "config": {
                    "max_trades_per_day": 5,
                    "trade_amount_usdt": 100,
                    "ai_confidence_threshold": 0.6,
                    "max_concurrent_trades": 3
                }
            }))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Bot start response: {data['data']['success']}")
            
            # Test 4: Monitor for messages
            logger.info("Test 4: Monitoring for messages for 30 seconds...")
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    message_count += 1
                    logger.info(f"Message {message_count}: {data['type']}")
                    
                    # Check for specific message types
                    if data['type'] == 'analysis_log':
                        logger.info(f"Analysis log: {data['data']['message']}")
                    elif data['type'] == 'trade_log':
                        logger.info(f"Trade log: {data['data']['message']}")
                    elif data['type'] == 'bot_trade_executed':
                        logger.info(f"Bot trade executed: {data['data']['symbol']}")
                    elif data['type'] == 'position_update':
                        positions_count = len(data['data']['positions'])
                        logger.info(f"Position update: {positions_count} positions")
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            logger.info(f"Received {message_count} messages during monitoring")
            
            # Test 5: Stop bot
            logger.info("Test 5: Stopping bot...")
            await websocket.send(json.dumps({"type": "stop_bot"}))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Bot stop response: {data['data']['success']}")
            
            logger.info("All tests completed successfully!")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

async def test_manual_trade():
    """Test manual trade execution"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Testing manual trade execution...")
        async with websockets.connect(uri) as websocket:
            # Execute a manual trade
            trade_data = {
                "type": "paper_trade",
                "trade_data": {
                    "symbol": "BTCUSDT",
                    "direction": "LONG",
                    "amount": 0.001,
                    "price": 50000,
                    "trade_id": f"test_{int(time.time())}"
                }
            }
            
            await websocket.send(json.dumps(trade_data))
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Manual trade response: {data['type']}")
            
            if data['type'] == 'trade_executed':
                logger.info("Manual trade executed successfully!")
                return True
            else:
                logger.error(f"Manual trade failed: {data}")
                return False
                
    except Exception as e:
        logger.error(f"Manual trade test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting WebSocket stability tests...")
    
    # Test 1: Connection stability
    success1 = await test_websocket_stability()
    
    # Test 2: Manual trade
    success2 = await test_manual_trade()
    
    if success1 and success2:
        logger.info("All tests passed! WebSocket connection is stable.")
    else:
        logger.error("Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main()) 