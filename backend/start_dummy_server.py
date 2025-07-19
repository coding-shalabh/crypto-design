"""
Simple startup script for the dummy analysis server
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dummy_analysis_server import DummyAnalysisServer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the dummy server"""
    logger.info("Starting Dummy Analysis Server...")
    
    # Create and start the server
    server = DummyAnalysisServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        server.stop_server()
    except Exception as e:
        logger.error(f"Server error: {e}")
        server.stop_server()

if __name__ == "__main__":
    print("="*60)
    print("DUMMY ANALYSIS SERVER")
    print("="*60)
    print("HTTP API: http://localhost:5001")
    print("WebSocket: ws://localhost:8766")
    print("Press Ctrl+C to stop")
    print("="*60)
    
    asyncio.run(main())