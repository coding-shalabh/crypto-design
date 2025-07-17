#!/usr/bin/env python3
"""
Backend Server Startup Script
=============================

This script starts the real backend WebSocket server for the crypto trading application.
It initializes all components and starts the server on the configured host and port.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from websocket_server import TradingServer
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the backend server"""
    try:
        logger.info(" Starting Crypto Trading Backend Server")
        logger.info(f" Server will run on {Config.HOST}:{Config.PORT}")
        logger.info(" Paper trading balance: $%.2f", Config.PAPER_BALANCE)
        logger.info(" Target pairs: %s", ', '.join(Config.TARGET_PAIRS))
        logger.info("Bot config: %s", Config.DEFAULT_BOT_CONFIG)
        logger.info("=" * 60)
        
        # Create and start the server
        server = TradingServer()
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.info(" Received shutdown signal")
    except Exception as e:
        logger.error(f" Server error: {e}")
        sys.exit(1)
    finally:
        logger.info(" Backend server shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Server stopped by user")
    except Exception as e:
        logger.error(f" Server error: {e}")
        sys.exit(1) 