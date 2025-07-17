#!/usr/bin/env python3
import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def handler(websocket, path):
    logger.info("Client connected.")
    try:
        async for message in websocket:
            logger.info(f"Received: {message}")
            # Do NOT echo back, just log
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"Error: {e}")

async def main():
    logger.info("Starting WebSocket server on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}") 