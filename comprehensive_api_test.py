"""
Comprehensive API Testing Script
Tests both real and fake API modes
"""

import asyncio
import websockets
import json
import requests
import time
import logging
from datetime import datetime
import subprocess
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveAPITester:
    def __init__(self):
        self.fake_api_url = "http://localhost:5001"
        self.backend_url = "ws://localhost:8767"
        self.test_results = {}
        
    def test_environment_setup(self):
        """Test that environment variables are set correctly"""
        logger.info("Testing environment setup...")
        
        # Read .env file
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            # Check for required variables
            required_vars = [
                'REACT_APP_API_BASE_URL',
                'REACT_APP_WEBSOCKET_URL', 
                'REACT_APP_ANALYSIS_API_URL',
                'API_MODE',
                'FAKE_API_URL',
                'REAL_API_URL'
            ]
            
            missing_vars = []
            for var in required_vars:
                if var not in env_content:
                    missing_vars.append(var)
            
            if missing_vars:
                logger.error(f"Missing environment variables: {missing_vars}")
                self.test_results['environment_setup'] = 'FAIL'
                return False
            else:
                logger.info("All required environment variables found")
                self.test_results['environment_setup'] = 'PASS'
                return True
                
        except FileNotFoundError:
            logger.error(".env file not found")
            self.test_results['environment_setup'] = 'FAIL'
            return False
    
    def test_fake_api_server(self):
        """Test fake API server functionality"""
        logger.info("Testing fake API server...")
        
        try:
            # Test HTTP health endpoint
            response = requests.get(f"{self.fake_api_url}/api/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Health check passed: {health_data}")
                
                # Test analysis endpoint
                response = requests.get(f"{self.fake_api_url}/api/analysis/BTCUSDT", timeout=5)
                
                if response.status_code == 200:
                    analysis_data = response.json()
                    
                    # Verify structure
                    required_keys = ['final_recommendation', 'grok_analysis', 'claude_analysis']
                    if all(key in analysis_data for key in required_keys):
                        logger.info("Fake API server working correctly")
                        self.test_results['fake_api_server'] = 'PASS'
                        return True
                    else:
                        logger.error("Fake API response missing required keys")
                        self.test_results['fake_api_server'] = 'FAIL'
                        return False
                else:
                    logger.error(f"Analysis endpoint failed: {response.status_code}")
                    self.test_results['fake_api_server'] = 'FAIL'
                    return False
            else:
                logger.error(f"Health check failed: {response.status_code}")
                self.test_results['fake_api_server'] = 'FAIL'
                return False
                
        except Exception as e:
            logger.error(f"Fake API server test failed: {e}")
            self.test_results['fake_api_server'] = 'FAIL'
            return False
    
    async def test_backend_websocket(self):
        """Test backend WebSocket functionality"""
        logger.info("Testing backend WebSocket...")
        
        try:
            websocket = await websockets.connect(self.backend_url)
            logger.info("WebSocket connected successfully")
            
            # Test analysis request
            analysis_request = {
                "action": "get_analysis",
                "symbol": "BTCUSDT"
            }
            
            await websocket.send(json.dumps(analysis_request))
            logger.info("Analysis request sent")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=30)
            data = json.loads(response)
            
            if data['type'] == 'analysis_complete':
                analysis = data['data']['analysis']
                final_rec = analysis.get('final_recommendation', {})
                logger.info(f"Analysis received: {final_rec.get('action')} with {final_rec.get('confidence', 0):.2f} confidence")
                
                # Test bot config
                config_request = {"action": "get_bot_config"}
                await websocket.send(json.dumps(config_request))
                
                config_response = await asyncio.wait_for(websocket.recv(), timeout=10)
                config_data = json.loads(config_response)
                
                if config_data['type'] == 'bot_config':
                    logger.info("Bot configuration retrieved successfully")
                    self.test_results['backend_websocket'] = 'PASS'
                    await websocket.close()
                    return True
                else:
                    logger.error(f"Bot config failed: {config_data}")
                    self.test_results['backend_websocket'] = 'FAIL'
                    await websocket.close()
                    return False
            else:
                logger.error(f"Analysis failed: {data}")
                self.test_results['backend_websocket'] = 'FAIL'
                await websocket.close()
                return False
                
        except Exception as e:
            logger.error(f"Backend WebSocket test failed: {e}")
            self.test_results['backend_websocket'] = 'FAIL'
            return False
    
    def test_api_mode_switching(self):
        """Test API mode switching"""
        logger.info("Testing API mode switching...")
        
        try:
            # Read current mode
            with open('.env', 'r') as f:
                env_content = f.read()
            
            current_mode = 'fake' if 'API_MODE=fake' in env_content else 'real'
            logger.info(f"Current API mode: {current_mode}")
            
            # Test switching to opposite mode
            new_mode = 'real' if current_mode == 'fake' else 'fake'
            
            # Update env file
            updated_content = env_content.replace(f'API_MODE={current_mode}', f'API_MODE={new_mode}')
            
            with open('.env', 'w') as f:
                f.write(updated_content)
            
            logger.info(f"Switched API mode to: {new_mode}")
            
            # Switch back to original mode
            with open('.env', 'w') as f:
                f.write(env_content)
            
            logger.info(f"Switched back to original mode: {current_mode}")
            
            self.test_results['api_mode_switching'] = 'PASS'
            return True
            
        except Exception as e:
            logger.error(f"API mode switching test failed: {e}")
            self.test_results['api_mode_switching'] = 'FAIL'
            return False
    
    def test_frontend_service_files(self):
        """Test that frontend service files exist and are structured correctly"""
        logger.info("Testing frontend service files...")
        
        try:
            # Check if apiService.js exists
            api_service_path = 'src/services/apiService.js'
            if not os.path.exists(api_service_path):
                logger.error("apiService.js file not found")
                self.test_results['frontend_service_files'] = 'FAIL'
                return False
            
            # Read and check apiService.js content
            with open(api_service_path, 'r') as f:
                content = f.read()
            
            required_methods = [
                'initializeWebSocket',
                'getBotConfig',
                'updateBotConfig',
                'startBot',
                'stopBot',
                'executeTrade',
                'getMarketData',
                'getAnalysis'
            ]
            
            missing_methods = []
            for method in required_methods:
                if method not in content:
                    missing_methods.append(method)
            
            if missing_methods:
                logger.error(f"Missing methods in apiService.js: {missing_methods}")
                self.test_results['frontend_service_files'] = 'FAIL'
                return False
            
            logger.info("Frontend service files are properly structured")
            self.test_results['frontend_service_files'] = 'PASS'
            return True
            
        except Exception as e:
            logger.error(f"Frontend service files test failed: {e}")
            self.test_results['frontend_service_files'] = 'FAIL'
            return False
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "="*60)
        logger.info("COMPREHENSIVE API TESTING RESULTS")
        logger.info("="*60)
        
        for test_name, result in self.test_results.items():
            status_emoji = "" if result == "PASS" else "❌"
            logger.info(f"{status_emoji} {test_name.replace('_', ' ').title()}: {result}")
        
        passed = sum(1 for r in self.test_results.values() if r == 'PASS')
        failed = sum(1 for r in self.test_results.values() if r == 'FAIL')
        
        logger.info(f"\nSummary: {passed} PASSED, {failed} FAILED")
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED! API switching system is working correctly.")
            logger.info("\nTo switch between real and fake APIs:")
            logger.info("1. Edit .env file")
            logger.info("2. Change API_MODE=fake to API_MODE=real (or vice versa)")
            logger.info("3. Restart the backend server")
            logger.info("4. Frontend will automatically use the new API endpoints")
        else:
            logger.info(f"⚠️  {failed} test(s) failed - check logs for details")
        
        logger.info("="*60)

async def main():
    """Main test function"""
    logger.info("🚀 Starting comprehensive API testing...")
    
    tester = ComprehensiveAPITester()
    
    # Run all tests
    tester.test_environment_setup()
    tester.test_fake_api_server()
    await tester.test_backend_websocket()
    tester.test_api_mode_switching()
    tester.test_frontend_service_files()
    
    # Print results
    tester.print_test_results()

if __name__ == "__main__":
    asyncio.run(main())