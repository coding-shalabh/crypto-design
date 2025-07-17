#!/usr/bin/env python3
"""
Start Enhanced Fake Trading Server
==================================

This script starts the enhanced fake trading server with comprehensive debugging.
Run this to start the server, then use debug_test_client.py to test it.
"""

import asyncio
import sys
from simple_websocket_server import EnhancedFakeTradingServer

def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("🚀 ENHANCED FAKE TRADING SERVER WITH COMPREHENSIVE DEBUGGING")
    print("=" * 80)
    print()
    print("This server simulates a complete crypto trading system with:")
    print("✅ Real-time price updates for 8 crypto symbols")
    print("✅ Trade execution simulation (BUY/SELL)")
    print("✅ AI analysis generation with sentiment analysis")
    print("✅ Position management with P&L calculations")
    print("✅ Bot status updates and performance metrics")
    print("✅ Comprehensive debugging with emojis and markers")
    print()
    print("Server will start on: ws://localhost:8765")
    print("Debug markers: All logs start with '-----' and end with '-----'")
    print("Emojis used: 🚀📈💼🤖📊🔌👥✅❌💥")
    print()
    print("To test the server:")
    print("1. Keep this server running")
    print("2. Open another terminal and run: python debug_test_client.py")
    print("3. Or connect your frontend to ws://localhost:8765")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 80)
    print()

async def main():
    """Main function"""
    print_banner()
    
    # Create and start server
    server = EnhancedFakeTradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        print("\n-----🛑 SERVER INTERRUPTED BY USER -----")
    except Exception as e:
        print(f"\n-----💥 SERVER ERROR: {e} -----")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n-----🛑 SERVER STOPPED BY USER -----")
    except Exception as e:
        print(f"\n-----💥 SERVER ERROR: {e} -----")
        sys.exit(1) 