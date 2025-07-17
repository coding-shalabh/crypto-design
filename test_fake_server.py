#!/usr/bin/env python3
"""
Test Script for Fake WebSocket Server
=====================================

This script tests the fake server by connecting to it and sending
all the message types that the frontend would send, then verifying
the responses match the expected formats.
"""

import asyncio
import json
import websockets
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FakeServerTester:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.test_results = []
        
    async def connect(self):
        """Connect to the fake server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            logger.info(f"✅ Connected to {self.server_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Disconnected from server")
    
    async def send_message(self, message):
        """Send a message to the server"""
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Sent: {message['type']}")
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    async def receive_message(self, timeout=5):
        """Receive a message from the server"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            data = json.loads(message)
            logger.info(f"📥 Received: {data['type']}")
            return data
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for message")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to receive message: {e}")
            return None
    
    async def test_initial_data(self):
        """Test initial data loading"""
        logger.info("🧪 Testing initial data loading...")
        
        # Wait for initial data messages
        messages_received = []
        for _ in range(4):  # Expect 4 initial messages
            message = await self.receive_message()
            if message:
                messages_received.append(message['type'])
        
        expected_types = ['positions_response', 'trade_history_response', 'crypto_data_response', 'bot_status_response']
        missing_types = [t for t in expected_types if t not in messages_received]
        
        if missing_types:
            logger.error(f"❌ Missing initial data types: {missing_types}")
            return False
        else:
            logger.info("✅ Initial data received successfully")
            return True
    
    async def test_get_positions(self):
        """Test get_positions message"""
        logger.info("🧪 Testing get_positions...")
        
        await self.send_message({'type': 'get_positions'})
        response = await self.receive_message()
        
        if response and response['type'] == 'positions_response':
            data = response['data']
            if 'balance' in data and 'positions' in data:
                logger.info(f"✅ Positions received: Balance=${data['balance']}, Positions={len(data['positions'])}")
                return True
        
        logger.error("❌ Invalid positions response")
        return False
    
    async def test_get_trade_history(self):
        """Test get_trade_history message"""
        logger.info("🧪 Testing get_trade_history...")
        
        await self.send_message({'type': 'get_trade_history', 'limit': 10})
        response = await self.receive_message()
        
        if response and response['type'] == 'trade_history_response':
            data = response['data']
            if 'trades' in data:
                logger.info(f"✅ Trade history received: {len(data['trades'])} trades")
                return True
        
        logger.error("❌ Invalid trade history response")
        return False
    
    async def test_get_crypto_data(self):
        """Test get_crypto_data message"""
        logger.info("🧪 Testing get_crypto_data...")
        
        await self.send_message({'type': 'get_crypto_data'})
        response = await self.receive_message()
        
        if response and response['type'] == 'crypto_data_response':
            data = response['data']
            if isinstance(data, dict) and len(data) > 0:
                logger.info(f"✅ Crypto data received: {len(data)} cryptocurrencies")
                return True
        
        logger.error("❌ Invalid crypto data response")
        return False
    
    async def test_execute_trade(self):
        """Test execute_trade message"""
        logger.info("🧪 Testing execute_trade...")
        
        trade_data = {
            'type': 'execute_trade',
            'symbol': 'BTC',
            'direction': 'BUY',
            'amount': 0.01,
            'price': 45000.0
        }
        
        await self.send_message(trade_data)
        response = await self.receive_message()
        
        if response and response['type'] == 'trade_executed':
            data = response['data']
            if 'trade' in data and 'new_balance' in data and 'positions' in data:
                logger.info(f"✅ Trade executed: {data['trade']['trade_id']}")
                return True
        
        logger.error("❌ Invalid trade execution response")
        return False
    
    async def test_close_position(self):
        """Test close_position message"""
        logger.info("🧪 Testing close_position...")
        
        await self.send_message({'type': 'close_position', 'symbol': 'BTC'})
        response = await self.receive_message()
        
        if response and response['type'] == 'position_closed':
            data = response['data']
            if 'trade' in data and 'new_balance' in data and 'positions' in data:
                logger.info(f"✅ Position closed: {data['trade']['trade_id']}")
                return True
        
        logger.error("❌ Invalid position close response")
        return False
    
    async def test_start_bot(self):
        """Test start_bot message"""
        logger.info("🧪 Testing start_bot...")
        
        bot_config = {
            'max_trades_per_day': 5,
            'trade_amount_usdt': 25,
            'ai_confidence_threshold': 0.8
        }
        
        await self.send_message({
            'type': 'start_bot',
            'config': bot_config
        })
        response = await self.receive_message()
        
        if response and response['type'] == 'start_bot_response':
            data = response['data']
            if data.get('success'):
                logger.info("✅ Bot started successfully")
                return True
        
        logger.error("❌ Invalid bot start response")
        return False
    
    async def test_get_bot_status(self):
        """Test get_bot_status message"""
        logger.info("🧪 Testing get_bot_status...")
        
        await self.send_message({'type': 'get_bot_status'})
        response = await self.receive_message()
        
        if response and response['type'] == 'bot_status_response':
            data = response['data']
            if 'enabled' in data and 'active_trades' in data:
                logger.info(f"✅ Bot status received: enabled={data['enabled']}, active_trades={data['active_trades']}")
                return True
        
        logger.error("❌ Invalid bot status response")
        return False
    
    async def test_update_bot_config(self):
        """Test update_bot_config message"""
        logger.info("🧪 Testing update_bot_config...")
        
        new_config = {
            'trade_amount_usdt': 100,
            'profit_target_usd': 5
        }
        
        await self.send_message({
            'type': 'update_bot_config',
            'config': new_config
        })
        response = await self.receive_message()
        
        if response and response['type'] == 'bot_config_update_result':
            data = response['data']
            if data.get('success'):
                logger.info("✅ Bot config updated successfully")
                return True
        
        logger.error("❌ Invalid bot config update response")
        return False
    
    async def test_stop_bot(self):
        """Test stop_bot message"""
        logger.info("🧪 Testing stop_bot...")
        
        await self.send_message({'type': 'stop_bot'})
        response = await self.receive_message()
        
        if response and response['type'] == 'stop_bot_response':
            data = response['data']
            if data.get('success'):
                logger.info("✅ Bot stopped successfully")
                return True
        
        logger.error("❌ Invalid bot stop response")
        return False
    
    async def test_get_ai_analysis(self):
        """Test get_ai_analysis message"""
        logger.info("🧪 Testing get_ai_analysis...")
        
        await self.send_message({
            'type': 'get_ai_analysis',
            'symbol': 'BTC'
        })
        response = await self.receive_message()
        
        if response and response['type'] == 'ai_insights':
            data = response['data']
            if 'symbol' in data and 'claude_analysis' in data and 'gpt_refinement' in data:
                logger.info(f"✅ AI analysis received for {data['symbol']}")
                return True
        
        logger.error("❌ Invalid AI analysis response")
        return False
    
    async def test_price_updates(self):
        """Test real-time price updates"""
        logger.info("🧪 Testing real-time price updates...")
        
        # Wait for price updates
        price_updates = []
        for _ in range(3):  # Wait for 3 price updates
            message = await self.receive_message(timeout=10)
            if message and message['type'] == 'price_update':
                price_updates.append(message['data']['symbol'])
        
        if len(price_updates) >= 2:
            logger.info(f"✅ Price updates received: {len(price_updates)} updates")
            return True
        else:
            logger.error("❌ Insufficient price updates received")
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting fake server tests...")
        
        if not await self.connect():
            return False
        
        tests = [
            ("Initial Data", self.test_initial_data),
            ("Get Positions", self.test_get_positions),
            ("Get Trade History", self.test_get_trade_history),
            ("Get Crypto Data", self.test_get_crypto_data),
            ("Execute Trade", self.test_execute_trade),
            ("Close Position", self.test_close_position),
            ("Start Bot", self.test_start_bot),
            ("Get Bot Status", self.test_get_bot_status),
            ("Update Bot Config", self.test_update_bot_config),
            ("Get AI Analysis", self.test_get_ai_analysis),
            ("Price Updates", self.test_price_updates),
            ("Stop Bot", self.test_stop_bot),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        await self.disconnect()
        
        logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Fake server is working correctly.")
        else:
            logger.error(f"⚠️ {total - passed} tests failed. Check the logs above.")
        
        return passed == total

async def main():
    """Main function"""
    tester = FakeServerTester()
    
    try:
        success = await tester.run_all_tests()
        if success:
            logger.info("🎯 Fake server is ready for frontend testing!")
        else:
            logger.error("❌ Fake server has issues that need to be fixed.")
    except Exception as e:
        logger.error(f"❌ Test runner error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Tests stopped by user")
    except Exception as e:
        logger.error(f"❌ Test error: {e}") 