#!/usr/bin/env python3
"""
Test script to verify WebSocket connection stability
"""
import asyncio
import websockets
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

async def test_connection_stability():
    """Test WebSocket connection stability"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Testing WebSocket connection stability...")
        
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
            
            # Listen for messages for 30 seconds
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    message_count += 1
                    
                    if message_count <= 5:  # Log first 5 messages
                        logger.info(f"Received message {message_count}: {data.get('type', 'unknown')}")
                    elif message_count % 10 == 0:  # Log every 10th message
                        logger.info(f"Received {message_count} messages so far...")
                        
                except asyncio.TimeoutError:
                    logger.info("No message received in 5 seconds, continuing...")
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            logger.info(f"Test completed. Received {message_count} messages in 30 seconds")
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")

async def test_multiple_connections():
    """Test multiple simultaneous connections"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info("Testing multiple simultaneous connections...")
        
        # Create 3 connections
        connections = []
        for i in range(3):
            try:
                websocket = await websockets.connect(uri)
                connections.append(websocket)
                logger.info(f"Connection {i+1} established")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to establish connection {i+1}: {e}")
        
        if connections:
            logger.info(f"Successfully established {len(connections)} connections")
            
            # Send a message from each connection
            for i, websocket in enumerate(connections):
                try:
                    await websocket.send(json.dumps({"type": "get_bot_status"}))
                    logger.info(f"Sent message from connection {i+1}")
                except Exception as e:
                    logger.error(f"Error sending from connection {i+1}: {e}")
            
            # Wait a bit
            await asyncio.sleep(5)
            
            # Close all connections
            for i, websocket in enumerate(connections):
                try:
                    await websocket.close()
                    logger.info(f"Connection {i+1} closed")
                except Exception as e:
                    logger.error(f"Error closing connection {i+1}: {e}")
        
    except Exception as e:
        logger.error(f"Multiple connections test failed: {e}")

async def main():
    """Main test function"""
    logger.info("Starting WebSocket connection stability tests...")
    
    # Test 1: Single connection stability
    await test_connection_stability()
    
    await asyncio.sleep(2)
    
    # Test 2: Multiple connections
    await test_multiple_connections()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 