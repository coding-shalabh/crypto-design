"""
Main entry point for the crypto trading bot backend
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from websocket_server import TradingServer
from config import Config

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('trading_bot.log')
        ]
    )

async def main():
    """Main entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Crypto Trading Bot Backend")
    logger.info(f"Target pairs: {Config.TARGET_PAIRS}")
    logger.info(f"Starting balance: ${Config.PAPER_BALANCE:,.2f}")
    
    # Create and start server
    server = TradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info(" Received shutdown signal")
    except Exception as e:
        logger.error(f" Server error: {e}")
    finally:
        await server.shutdown()
        logger.info("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main()) 