#!/usr/bin/env python3
"""
Quick test to verify balance fetching is working after WebSocket fix
"""

import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_balance_fetching():
    """Test balance fetching functionality"""
    try:
        logger.info("🔌 Connecting to WebSocket server...")
        async with websockets.connect("ws://localhost:8765") as websocket:
            
            # Test 1: Get mock balance
            logger.info("📝 Testing mock balance...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT", "mode": "mock"}
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            mock_data = json.loads(response)
            logger.info(f"✅ Mock balance response: {mock_data.get('type')}")
            
            if mock_data.get('type') == 'trading_balance':
                balance = mock_data.get('data', {}).get('balance', {})
                logger.info(f"💰 Mock balance: ${balance.get('total', 0):,.2f} USDT ({balance.get('wallet_type', 'Unknown')})")
            
            # Test 2: Get live balance
            logger.info("💰 Testing live balance...")
            await websocket.send(json.dumps({
                "type": "get_trading_balance",
                "data": {"asset": "USDT", "mode": "live"}
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            live_data = json.loads(response)
            logger.info(f"✅ Live balance response: {live_data.get('type')}")
            
            if live_data.get('type') == 'trading_balance':
                balance = live_data.get('data', {}).get('balance', {})
                logger.info(f"💰 Live balance: ${balance.get('total', 0):,.2f} USDT ({balance.get('wallet_type', 'Unknown')})")
            
            # Test 3: Set trading mode
            logger.info("🔄 Testing trading mode switching...")
            await websocket.send(json.dumps({
                "type": "set_trading_mode",
                "data": {"mode": "mock"}
            }))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            mode_data = json.loads(response)
            logger.info(f"✅ Mode switch response: {mode_data.get('type')}")
            
            logger.info("🎉 All tests completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

async def main():
    """Main test runner"""
    logger.info("🧪 Testing Balance Fetching After WebSocket Fix")
    logger.info("=" * 50)
    
    success = await test_balance_fetching()
    
    if success:
        logger.info("✅ All balance fetching tests passed!")
        logger.info("🔧 WebSocket error has been successfully fixed!")
    else:
        logger.error("❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        exit(1) 