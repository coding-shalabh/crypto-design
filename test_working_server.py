#!/usr/bin/env python3
"""
Test client for the working fake crypto trading server
"""

import asyncio
import json
import logging
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_server():
    """Test the WebSocket server"""
    uri = "ws://localhost:8765"
    
    try:
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully!")
            
            # Listen for messages for 10 seconds
            timeout = 10
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    
                    # Parse and display message
                    data = json.loads(message)
                    logger.info(f"Received: {json.dumps(data, indent=2)}")
                    
                except asyncio.TimeoutError:
                    # No message received within timeout, continue
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break
            
            logger.info("Test completed successfully!")
            
    except websockets.exceptions.ConnectionRefused:
        logger.error("Connection refused. Make sure the server is running on localhost:8765")
    except Exception as e:
        logger.error(f"Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_server()) 