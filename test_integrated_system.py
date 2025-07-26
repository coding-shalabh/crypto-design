#!/usr/bin/env python3
"""
Comprehensive Integration Test for Trading Bot System
Tests the complete flow from mode switching to bot trading with real balance verification
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from typing import Dict, List
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingBotIntegrationTest:
    def __init__(self):
        self.websocket_url = "ws://localhost:8765"
        self.test_results = []
        
    async def test_websocket_connection(self) -> bool:
        """Test basic WebSocket connection"""
        try:
            logger.info("🔌 Testing WebSocket connection...")
            async with websockets.connect(self.websocket_url) as websocket:
                # Send ping message
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    logger.info("✅ WebSocket connection successful")
                    return True
                else:
                    logger.error(f"❌ Unexpected response: {data}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def test_trading_mode_switching(self) -> Dict:
        """Test trading mode switching and balance updates"""
        try:
            logger.info("🔄 Testing trading mode switching...")
            async with websockets.connect(self.websocket_url) as websocket:
                
                # Test 1: Switch to mock mode
                logger.info("📝 Testing mock mode switch...")
                await websocket.send(json.dumps({
                    "type": "set_trading_mode",
                    "data": {"mode": "mock"}
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mock_response = json.loads(response)
                logger.info(f"Mock mode response: {mock_response}")
                
                # Wait for balance update
                await asyncio.sleep(2)
                
                # Request mock balance
                await websocket.send(json.dumps({
                    "type": "get_trading_balance",
                    "data": {"asset": "USDT", "mode": "mock"}
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                mock_balance = json.loads(response)
                logger.info(f"Mock balance: {mock_balance}")
                
                # Test 2: Switch to live mode
                logger.info("💰 Testing live mode switch...")
                await websocket.send(json.dumps({
                    "type": "set_trading_mode",
                    "data": {"mode": "live"}
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                live_response = json.loads(response)
                logger.info(f"Live mode response: {live_response}")
                
                # Wait for balance update
                await asyncio.sleep(2)
                
                # Request live balance
                await websocket.send(json.dumps({
                    "type": "get_trading_balance",
                    "data": {"asset": "USDT", "mode": "live"}
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                live_balance = json.loads(response)
                logger.info(f"Live balance: {live_balance}")
                
                # Verify results
                mock_success = mock_balance.get("type") == "trading_balance" and mock_balance.get("data", {}).get("wallet_type") == "MOCK"
                live_success = live_balance.get("type") == "trading_balance" and live_balance.get("data", {}).get("wallet_type") in ["FUTURES", "SPOT"]
                
                return {
                    "success": mock_success and live_success,
                    "mock_balance": mock_balance,
                    "live_balance": live_balance,
                    "mock_success": mock_success,
                    "live_success": live_success
                }
                
        except Exception as e:
            logger.error(f"❌ Trading mode switching test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_trading_readiness_verification(self) -> Dict:
        """Test trading readiness verification"""
        try:
            logger.info("🔍 Testing trading readiness verification...")
            async with websockets.connect(self.websocket_url) as websocket:
                
                # Test readiness verification
                await websocket.send(json.dumps({
                    "type": "verify_trading_readiness"
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                readiness = json.loads(response)
                logger.info(f"Trading readiness: {readiness}")
                
                success = readiness.get("type") == "trading_readiness" and readiness.get("data", {}).get("ready") is not None
                
                return {
                    "success": success,
                    "readiness": readiness
                }
                
        except Exception as e:
            logger.error(f"❌ Trading readiness test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_bot_startup_with_verification(self) -> Dict:
        """Test bot startup with trading readiness verification"""
        try:
            logger.info("🤖 Testing bot startup with verification...")
            async with websockets.connect(self.websocket_url) as websocket:
                
                # Start bot
                await websocket.send(json.dumps({
                    "type": "start_bot",
                    "data": {
                        "max_trades_per_day": 5,
                        "trade_amount_usdt": 50,
                        "ai_confidence_threshold": 0.7,
                        "allowed_pairs": ["BTCUSDT", "ETHUSDT"]
                    }
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                bot_start = json.loads(response)
                logger.info(f"Bot startup response: {bot_start}")
                
                # Check if bot started successfully
                success = bot_start.get("type") == "bot_status" and bot_start.get("data", {}).get("success") == True
                
                if success:
                    # Stop bot
                    await websocket.send(json.dumps({"type": "stop_bot"}))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    stop_response = json.loads(response)
                    logger.info(f"Bot stop response: {stop_response}")
                
                return {
                    "success": success,
                    "bot_start": bot_start,
                    "stop_response": stop_response if success else None
                }
                
        except Exception as e:
            logger.error(f"❌ Bot startup test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_categorized_balance_fetching(self) -> Dict:
        """Test categorized balance fetching"""
        try:
            logger.info("📊 Testing categorized balance fetching...")
            async with websockets.connect(self.websocket_url) as websocket:
                
                # Request categorized balances
                await websocket.send(json.dumps({
                    "type": "get_categorized_balances"
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                categorized = json.loads(response)
                logger.info(f"Categorized balances: {categorized}")
                
                success = categorized.get("type") == "categorized_balances" and "data" in categorized
                
                return {
                    "success": success,
                    "categorized": categorized
                }
                
        except Exception as e:
            logger.error(f"❌ Categorized balance test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_ai_analysis_integration(self) -> Dict:
        """Test AI analysis integration with trading bot"""
        try:
            logger.info("🧠 Testing AI analysis integration...")
            async with websockets.connect(self.websocket_url) as websocket:
                
                # Send AI analysis
                analysis_data = {
                    "symbol": "BTCUSDT",
                    "source": "gpt_final",
                    "final_recommendation": {
                        "action": "BUY",
                        "confidence": 0.85,
                        "timeframe": "30 minutes",
                        "reasoning": "Strong bullish signals detected"
                    },
                    "trade_setup": {
                        "entry_price": 45000,
                        "stop_loss": 44000,
                        "take_profit": 47000
                    }
                }
                
                await websocket.send(json.dumps({
                    "type": "process_ai_analysis",
                    "data": analysis_data
                }))
                
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                analysis_response = json.loads(response)
                logger.info(f"AI analysis response: {analysis_response}")
                
                success = analysis_response.get("type") == "ai_analysis_processed"
                
                return {
                    "success": success,
                    "analysis_response": analysis_response
                }
                
        except Exception as e:
            logger.error(f"❌ AI analysis test failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_all_tests(self) -> Dict:
        """Run all integration tests"""
        logger.info("🚀 Starting comprehensive integration tests...")
        
        test_results = {}
        
        # Test 1: WebSocket Connection
        test_results["websocket_connection"] = await self.test_websocket_connection()
        
        if not test_results["websocket_connection"]:
            logger.error("❌ WebSocket connection failed - stopping tests")
            return test_results
        
        # Test 2: Trading Mode Switching
        test_results["trading_mode_switching"] = await self.test_trading_mode_switching()
        
        # Test 3: Trading Readiness Verification
        test_results["trading_readiness"] = await self.test_trading_readiness_verification()
        
        # Test 4: Bot Startup with Verification
        test_results["bot_startup"] = await self.test_bot_startup_with_verification()
        
        # Test 5: Categorized Balance Fetching
        test_results["categorized_balances"] = await self.test_categorized_balance_fetching()
        
        # Test 6: AI Analysis Integration
        test_results["ai_analysis"] = await self.test_ai_analysis_integration()
        
        # Calculate overall success
        successful_tests = sum(1 for result in test_results.values() if result.get("success", False))
        total_tests = len(test_results)
        
        overall_success = successful_tests == total_tests
        
        logger.info(f"📊 Test Results Summary:")
        logger.info(f"   Successful tests: {successful_tests}/{total_tests}")
        logger.info(f"   Overall success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")
        
        return {
            "overall_success": overall_success,
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "test_results": test_results
        }

async def main():
    """Main test runner"""
    logger.info("🎯 Trading Bot Integration Test Suite")
    logger.info("=" * 50)
    
    # Check if backend is running
    logger.info("⚠️  Make sure the backend server is running on ws://localhost:8765")
    logger.info("   Run: python backend/main.py")
    
    # Wait for user confirmation
    input("Press Enter to start tests...")
    
    # Run tests
    tester = TradingBotIntegrationTest()
    results = await tester.run_all_tests()
    
    # Print final summary
    logger.info("=" * 50)
    logger.info("🎯 FINAL RESULTS")
    logger.info("=" * 50)
    
    if results["overall_success"]:
        logger.info("🎉 ALL TESTS PASSED! Trading bot system is working correctly.")
        logger.info("✅ The following features are verified:")
        logger.info("   • WebSocket communication")
        logger.info("   • Trading mode switching (mock/live)")
        logger.info("   • Balance fetching and categorization")
        logger.info("   • Trading readiness verification")
        logger.info("   • Bot startup with safety checks")
        logger.info("   • AI analysis integration")
    else:
        logger.error("❌ SOME TESTS FAILED! Please check the logs above.")
        logger.error("🔧 Failed tests need to be fixed before production use.")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if results["overall_success"] else 1)
    except KeyboardInterrupt:
        logger.info("⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test suite failed: {e}")
        sys.exit(1) 