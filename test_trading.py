#!/usr/bin/env python3
"""
Test script to simulate frontend trading requests and debug trade execution issues
"""
import asyncio
import websockets
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingTester:
    def __init__(self, websocket_url="ws://localhost:8765"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.connected = False
        self.messages_received = []
        
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            logger.info(f"Connecting to {self.websocket_url}...")
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            logger.info(" Connected to WebSocket server")
            
            # Start message listener
            asyncio.create_task(self.listen_for_messages())
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Disconnected from WebSocket server")
    
    async def send_message(self, message):
        """Send a message to the server"""
        if not self.connected or not self.websocket:
            logger.error("Not connected to server")
            return None
        
        try:
            message_str = json.dumps(message)
            logger.info(f"📤 Sending: {message_str}")
            await self.websocket.send(message_str)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return None
    
    async def listen_for_messages(self):
        """Listen for incoming messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    self.messages_received.append({
                        'timestamp': datetime.now().isoformat(),
                        'data': data
                    })
                    logger.info(f"📥 Received: {data.get('type', 'unknown')} - {json.dumps(data.get('data', {}), indent=2)[:200]}...")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"❌ Error in message listener: {e}")
            self.connected = False
    
    async def get_initial_data(self):
        """Get initial data from server"""
        logger.info("🔍 Requesting initial data...")
        await self.send_message({'type': 'get_positions'})
        await self.send_message({'type': 'get_crypto_data'})
        await asyncio.sleep(2)  # Wait for responses
    
    async def test_trade_execution(self, symbol="BTCUSDT", direction="buy", amount=0.1, price=50000):
        """Test trade execution with the same format as frontend"""
        logger.info(f"🔍 Testing trade execution: {symbol} {direction} {amount} @ ${price}")
        
        # Create trade data in the same format as frontend
        trade_data = {
            'symbol': symbol,
            'direction': direction,
            'amount': amount,
            'price': price,
            'orderType': 'limit',
            'leverage': 10,
            'marginMode': 'isolated',
            'sizeUnit': 'USDT',
            'useTpSl': False,
            'reduceOnly': False,
            'trade_id': f"test_trade_{int(time.time())}"
        }
        
        # Send trade execution request
        message = {
            'type': 'execute_trade',
            'trade_data': trade_data
        }
        
        await self.send_message(message)
        
        # Wait for response
        await asyncio.sleep(3)
        
        # Check if we received a response
        trade_responses = [msg for msg in self.messages_received if msg['data'].get('type') in ['trade_executed', 'paper_trade_response', 'error']]
        
        if trade_responses:
            latest_response = trade_responses[-1]
            logger.info(f"📋 Trade response: {latest_response['data']}")
            
            if latest_response['data'].get('type') == 'error':
                logger.error(f"❌ Trade failed: {latest_response['data']['data']['message']}")
                return False
            else:
                logger.info(" Trade executed successfully!")
                return True
        else:
            logger.error("❌ No trade response received")
            return False
    
    async def test_multiple_trades(self):
        """Test multiple different trade scenarios"""
        logger.info("🧪 Starting comprehensive trade tests...")
        
        # Test 1: Buy BTC
        logger.info("\n=== Test 1: Buy BTC ===")
        success1 = await self.test_trade_execution("BTCUSDT", "buy", 0.1, 50000)
        
        await asyncio.sleep(2)
        
        # Test 2: Buy ETH
        logger.info("\n=== Test 2: Buy ETH ===")
        success2 = await self.test_trade_execution("ETHUSDT", "buy", 1.0, 3000)
        
        await asyncio.sleep(2)
        
        # Test 3: Sell BTC (should close position)
        logger.info("\n=== Test 3: Sell BTC ===")
        success3 = await self.test_trade_execution("BTCUSDT", "sell", 0.1, 51000)
        
        await asyncio.sleep(2)
        
        # Test 4: Invalid trade (insufficient balance)
        logger.info("\n=== Test 4: Invalid trade (insufficient balance) ===")
        success4 = await self.test_trade_execution("BTCUSDT", "buy", 1000, 50000)  # Should fail
        
        # Summary
        logger.info(f"\n📊 Test Results:")
        logger.info(f"Test 1 (Buy BTC): {' PASS' if success1 else '❌ FAIL'}")
        logger.info(f"Test 2 (Buy ETH): {' PASS' if success2 else '❌ FAIL'}")
        logger.info(f"Test 3 (Sell BTC): {' PASS' if success3 else '❌ FAIL'}")
        logger.info(f"Test 4 (Invalid): {' PASS' if not success4 else '❌ FAIL'}")
        
        return all([success1, success2, success3, not success4])
    
    def print_message_history(self):
        """Print all received messages"""
        logger.info(f"\n📋 Message History ({len(self.messages_received)} messages):")
        for i, msg in enumerate(self.messages_received):
            logger.info(f"{i+1}. [{msg['timestamp']}] {msg['data'].get('type', 'unknown')}")

async def main():
    """Main test function"""
    tester = TradingTester()
    
    try:
        # Connect to server
        if not await tester.connect():
            logger.error("❌ Failed to connect to server. Make sure the backend is running.")
            return
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(1)
        
        # Get initial data
        await tester.get_initial_data()
        
        # Run trade tests
        success = await tester.test_multiple_trades()
        
        # Print message history
        tester.print_message_history()
        
        if success:
            logger.info("🎉 All tests passed!")
        else:
            logger.error("❌ Some tests failed. Check the logs above.")
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 