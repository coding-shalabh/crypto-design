#!/usr/bin/env python3
"""
Start Fake Server for Frontend Testing
======================================

This script starts the fake WebSocket server for frontend testing.
It provides a simple way to start the server and test it.
"""

import asyncio
import sys
import os
from fake_server_for_frontend_testing import FakeTradingServer

def print_banner():
    """Print startup banner"""
    print("=" * 60)
    print("🚀 FAKE WEBSOCKET SERVER FOR FRONTEND TESTING")
    print("=" * 60)
    print()
    print("This server simulates the exact backend behavior expected by the frontend.")
    print("It will send properly formatted messages that match the frontend's expectations.")
    print()
    print("Features:")
    print("✅ Real-time price updates")
    print("✅ Trade execution simulation")
    print("✅ Bot control and status")
    print("✅ AI analysis responses")
    print("✅ Position management")
    print("✅ Error handling")
    print()
    print("Server will start on: ws://localhost:8765")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

async def main():
    """Main function"""
    print_banner()
    
    # Create and start server
    server = FakeTradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        await server.shutdown()
        print("👋 Server shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1) 