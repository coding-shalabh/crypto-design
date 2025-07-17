#!/usr/bin/env python3
"""
Simple WebSocket Server V2 for Frontend Testing
===============================================

A more robust WebSocket server for testing the frontend.
"""

import asyncio
import websockets
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

clients = set()

async def handle_client(websocket, path):
    clients.add(websocket)
    logger.info(f"Client connected. Total clients: {len(clients)}")
    try:
        async for message in websocket:
            logger.info(f"Received: {message}")
            # Echo to all clients
            for client in clients:
                try:
                    await client.send(message)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(clients)}")

async def main():
    logger.info("Starting WebSocket server on ws://localhost:8765 ...")
    async with websockets.serve(handle_client, "localhost", 8765):
        logger.info("Server running. Press Ctrl+C to stop.")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user.") 