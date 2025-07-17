#!/usr/bin/env python3
"""
Simple Test WebSocket Server
============================

A minimal WebSocket server to test basic functionality.
"""

import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simple_handler(websocket, path):
    """Simple WebSocket handler"""
    logger.info(f"🔌 Client connected from {websocket.remote_address}")
    
    try:
        # Send a simple welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'data': {'message': 'Hello from simple server!'}
        }))
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"📨 Received: {data}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    'type': 'echo',
                    'data': data
                }))
                
            except json.JSONDecodeError:
                logger.error("❌ Invalid JSON received")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': 'Invalid JSON'}
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("🔌 Client disconnected")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

async def main():
    """Main function"""
    logger.info("🚀 Starting simple WebSocket server on ws://localhost:8765")
    
    try:
        async with websockets.serve(simple_handler, "localhost", 8765):
            logger.info("✅ Server is running. Press Ctrl+C to stop.")
            await asyncio.Future()  # Run forever
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}") 