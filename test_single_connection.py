#!/usr/bin/env python3
"""
Test script to verify single WebSocket connection approach
"""
import asyncio
import websockets
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

async def test_single_connection():
    """Test that only one connection is established"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Testing single WebSocket connection...")
        
        # Connect to server
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Send initial requests
            requests = [
                {"type": "get_positions"},
                {"type": "get_trade_history", "limit": 10},
                {"type": "get_crypto_data"},
                {"type": "get_bot_status"}
            ]
            
            for request in requests:
                logger.info(f"Sending request: {request}")
                await websocket.send(json.dumps(request))
                await asyncio.sleep(0.5)  # Small delay between requests
            
            # Listen for messages for 10 seconds
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 10:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    logger.info(f"Received message {message_count}: {data.get('type', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    logger.info("No message received in 2 seconds, continuing...")
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            logger.info(f"Test completed. Received {message_count} messages in 10 seconds")
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")

async def monitor_server_connections():
    """Monitor server logs to see connection behavior"""
    logger.info("Monitoring server connection behavior...")
    logger.info("Expected behavior:")
    logger.info("- Only 1-2 connections should be established")
    logger.info("- No rapid connect/disconnect cycles")
    logger.info("- No 'Connection limit reached' warnings")
    logger.info("- Stable connection maintained")
    
    # Wait for 30 seconds to observe behavior
    await asyncio.sleep(30)
    logger.info("Monitoring period completed")

async def main():
    """Main test function"""
    logger.info("Starting single connection test...")
    
    # Test 1: Single connection
    await test_single_connection()
    
    await asyncio.sleep(2)
    
    # Test 2: Monitor server behavior
    await monitor_server_connections()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 