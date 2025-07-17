#!/usr/bin/env python3
"""
Simple Test WebSocket Client
============================

A minimal WebSocket client to test the simple server.
"""

import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_server():
    """Test the simple WebSocket server"""
    try:
        logger.info("🔌 Connecting to ws://localhost:8765")
        
        async with websockets.connect('ws://localhost:8765') as websocket:
            logger.info("✅ Connected successfully!")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            data = json.loads(welcome)
            logger.info(f"📥 Received welcome: {data}")
            
            # Send a test message
            test_message = {
                'type': 'test',
                'data': {'message': 'Hello server!'}
            }
            
            await websocket.send(json.dumps(test_message))
            logger.info(f"📤 Sent: {test_message}")
            
            # Wait for echo response
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"📥 Received echo: {data}")
            
            logger.info("✅ Test completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_simple_server())
    except KeyboardInterrupt:
        logger.info("🛑 Test stopped by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}") 