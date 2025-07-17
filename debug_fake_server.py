#!/usr/bin/env python3
"""
Debug Script for Fake WebSocket Server
======================================

This script provides detailed debugging capabilities for the fake server,
including connection testing, message validation, and step-by-step debugging.
"""

import asyncio
import json
import websockets
import logging
import time
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FakeServerDebugger:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.websocket = None
        self.debug_log = []
        
    def log_debug(self, message, data=None):
        """Log debug information"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        if data:
            log_entry += f" | Data: {json.dumps(data, indent=2)}"
        
        self.debug_log.append(log_entry)
        logger.debug(log_entry)
    
    async def test_connection(self):
        """Test basic WebSocket connection"""
        logger.info("🔍 Testing WebSocket connection...")
        
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.log_debug("✅ WebSocket connection established")
            
            # Test connection is alive
            pong_waiter = await self.websocket.ping()
            await pong_waiter
            self.log_debug("✅ Ping/Pong test passed")
            
            return True
            
        except Exception as e:
            self.log_debug(f"❌ Connection failed: {e}")
            return False
    
    async def test_initial_handshake(self):
        """Test initial handshake and data loading"""
        logger.info("🔍 Testing initial handshake...")
        
        try:
            # Wait for initial messages
            initial_messages = []
            timeout_count = 0
            max_timeouts = 10
            
            while len(initial_messages) < 4 and timeout_count < max_timeouts:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    initial_messages.append(data)
                    self.log_debug(f"📥 Received initial message: {data['type']}", data)
                except asyncio.TimeoutError:
                    timeout_count += 1
                    self.log_debug(f"⏰ Timeout {timeout_count}/{max_timeouts} waiting for initial message")
            
            # Analyze initial messages
            message_types = [msg['type'] for msg in initial_messages]
            self.log_debug(f"📊 Initial message types received: {message_types}")
            
            expected_types = ['positions_response', 'trade_history_response', 'crypto_data_response', 'bot_status_response']
            missing_types = [t for t in expected_types if t not in message_types]
            
            if missing_types:
                self.log_debug(f"⚠️ Missing initial message types: {missing_types}")
                return False
            else:
                self.log_debug("✅ All expected initial messages received")
                return True
                
        except Exception as e:
            self.log_debug(f"❌ Initial handshake failed: {e}")
            return False
    
    async def test_message_format(self, message_type, test_data):
        """Test specific message format"""
        logger.info(f"🔍 Testing {message_type} message format...")
        
        try:
            # Send test message
            await self.websocket.send(json.dumps(test_data))
            self.log_debug(f"📤 Sent {message_type} message", test_data)
            
            # Wait for response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            self.log_debug(f"📥 Received response: {response_data['type']}", response_data)
            
            # Validate response format
            if self.validate_response_format(message_type, response_data):
                self.log_debug(f"✅ {message_type} response format is valid")
                return True
            else:
                self.log_debug(f"❌ {message_type} response format is invalid")
                return False
                
        except Exception as e:
            self.log_debug(f"❌ {message_type} test failed: {e}")
            return False
    
    def validate_response_format(self, message_type, response_data):
        """Validate response format based on message type"""
        try:
            if not isinstance(response_data, dict):
                return False
            
            if 'type' not in response_data or 'data' not in response_data:
                return False
            
            response_type = response_data['type']
            data = response_data['data']
            
            # Define expected response types for each message type
            expected_responses = {
                'get_positions': 'positions_response',
                'get_trade_history': 'trade_history_response',
                'get_crypto_data': 'crypto_data_response',
                'execute_trade': 'trade_executed',
                'close_position': 'position_closed',
                'start_bot': 'start_bot_response',
                'stop_bot': 'stop_bot_response',
                'get_bot_status': 'bot_status_response',
                'update_bot_config': 'bot_config_update_result',
                'get_ai_analysis': 'ai_insights'
            }
            
            expected_type = expected_responses.get(message_type)
            if expected_type and response_type != expected_type:
                self.log_debug(f"⚠️ Expected response type '{expected_type}', got '{response_type}'")
                return False
            
            # Validate data structure based on response type
            return self.validate_data_structure(response_type, data)
            
        except Exception as e:
            self.log_debug(f"❌ Response validation error: {e}")
            return False
    
    def validate_data_structure(self, response_type, data):
        """Validate data structure for specific response types"""
        try:
            if response_type == 'positions_response':
                return 'balance' in data and 'positions' in data and isinstance(data['positions'], dict)
            
            elif response_type == 'trade_history_response':
                return 'trades' in data and isinstance(data['trades'], list)
            
            elif response_type == 'crypto_data_response':
                return isinstance(data, dict) and len(data) > 0
            
            elif response_type == 'trade_executed':
                return all(key in data for key in ['trade', 'new_balance', 'positions'])
            
            elif response_type == 'position_closed':
                return all(key in data for key in ['trade', 'new_balance', 'positions'])
            
            elif response_type == 'start_bot_response':
                return 'success' in data
            
            elif response_type == 'stop_bot_response':
                return 'success' in data
            
            elif response_type == 'bot_status_response':
                return all(key in data for key in ['enabled', 'active_trades'])
            
            elif response_type == 'bot_config_update_result':
                return 'success' in data
            
            elif response_type == 'ai_insights':
                return all(key in data for key in ['symbol', 'claude_analysis', 'gpt_refinement'])
            
            elif response_type == 'price_update':
                return all(key in data for key in ['symbol', 'price', 'timestamp'])
            
            else:
                self.log_debug(f"⚠️ Unknown response type: {response_type}")
                return True  # Allow unknown types
            
        except Exception as e:
            self.log_debug(f"❌ Data structure validation error: {e}")
            return False
    
    async def test_real_time_updates(self):
        """Test real-time price updates"""
        logger.info("🔍 Testing real-time price updates...")
        
        try:
            # Wait for price updates
            price_updates = []
            start_time = time.time()
            timeout = 15  # 15 seconds timeout
            
            while time.time() - start_time < timeout and len(price_updates) < 5:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=3.0)
                    data = json.loads(message)
                    
                    if data['type'] == 'price_update':
                        price_updates.append(data['data']['symbol'])
                        self.log_debug(f"📈 Price update for {data['data']['symbol']}: ${data['data']['price']}")
                    
                except asyncio.TimeoutError:
                    continue
            
            if len(price_updates) >= 3:
                self.log_debug(f"✅ Real-time updates working: {len(price_updates)} price updates received")
                return True
            else:
                self.log_debug(f"⚠️ Insufficient real-time updates: {len(price_updates)} received")
                return False
                
        except Exception as e:
            self.log_debug(f"❌ Real-time updates test failed: {e}")
            return False
    
    async def test_error_handling(self):
        """Test error handling with invalid messages"""
        logger.info("🔍 Testing error handling...")
        
        try:
            # Test invalid JSON
            await self.websocket.send("invalid json")
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data['type'] == 'error':
                self.log_debug("✅ Invalid JSON handled correctly")
            else:
                self.log_debug("⚠️ Invalid JSON not handled as expected")
                return False
            
            # Test unknown message type
            await self.websocket.send(json.dumps({'type': 'unknown_message_type'}))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data['type'] == 'error':
                self.log_debug("✅ Unknown message type handled correctly")
                return True
            else:
                self.log_debug("⚠️ Unknown message type not handled as expected")
                return False
                
        except Exception as e:
            self.log_debug(f"❌ Error handling test failed: {e}")
            return False
    
    async def run_comprehensive_debug(self):
        """Run comprehensive debugging tests"""
        logger.info("🚀 Starting comprehensive debugging...")
        
        # Test connection
        if not await self.test_connection():
            logger.error("❌ Connection test failed")
            return False
        
        # Test initial handshake
        if not await self.test_initial_handshake():
            logger.error("❌ Initial handshake test failed")
            return False
        
        # Test individual message types
        test_messages = [
            ('get_positions', {'type': 'get_positions'}),
            ('get_trade_history', {'type': 'get_trade_history', 'limit': 5}),
            ('get_crypto_data', {'type': 'get_crypto_data'}),
            ('execute_trade', {
                'type': 'execute_trade',
                'symbol': 'ETH',
                'direction': 'BUY',
                'amount': 0.01,
                'price': 3000.0
            }),
            ('start_bot', {
                'type': 'start_bot',
                'config': {'trade_amount_usdt': 50}
            }),
            ('get_bot_status', {'type': 'get_bot_status'}),
            ('get_ai_analysis', {
                'type': 'get_ai_analysis',
                'symbol': 'BTC'
            })
        ]
        
        message_tests_passed = 0
        for message_type, test_data in test_messages:
            if await self.test_message_format(message_type, test_data):
                message_tests_passed += 1
            else:
                logger.warning(f"⚠️ {message_type} test failed")
        
        # Test real-time updates
        real_time_ok = await self.test_real_time_updates()
        
        # Test error handling
        error_handling_ok = await self.test_error_handling()
        
        # Close connection
        await self.websocket.close()
        
        # Summary
        logger.info(f"\n📊 Debug Summary:")
        logger.info(f"   Connection: ✅")
        logger.info(f"   Initial Handshake: ✅")
        logger.info(f"   Message Tests: {message_tests_passed}/{len(test_messages)} passed")
        logger.info(f"   Real-time Updates: {'✅' if real_time_ok else '❌'}")
        logger.info(f"   Error Handling: {'✅' if error_handling_ok else '❌'}")
        
        # Save debug log
        with open('fake_server_debug.log', 'w') as f:
            f.write('\n'.join(self.debug_log))
        
        logger.info("📝 Debug log saved to 'fake_server_debug.log'")
        
        return message_tests_passed == len(test_messages) and real_time_ok and error_handling_ok

async def main():
    """Main function"""
    debugger = FakeServerDebugger()
    
    try:
        success = await debugger.run_comprehensive_debug()
        if success:
            logger.info("🎉 All debug tests passed! Fake server is working correctly.")
        else:
            logger.error("❌ Some debug tests failed. Check the logs above and 'fake_server_debug.log'")
    except Exception as e:
        logger.error(f"❌ Debug runner error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Debug stopped by user")
    except Exception as e:
        logger.error(f"❌ Debug error: {e}") 