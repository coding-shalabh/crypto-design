#!/usr/bin/env python3
"""
Test script to verify authentication system
"""
import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_authentication():
    """Test the authentication flow"""
    uri = "ws://localhost:8768"
    
    try:
        logger.info("Connecting to WebSocket server...")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Test registration
            logger.info("Testing user registration...")
            register_message = {
                "type": "register",
                "username": "demo",
                "email": "demo@example.com",
                "password": "demo123"
            }
            
            await websocket.send(json.dumps(register_message))
            logger.info("📤 Sent registration message")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📨 Received response: {response_data}")
            
            if response_data.get('type') == 'register_response':
                if response_data['data']['success']:
                    logger.info("✅ Registration successful")
                else:
                    logger.info(f"❌ Registration failed: {response_data['data']['message']}")
            
            # Test login
            logger.info("Testing user login...")
            login_message = {
                "type": "login",
                "username": "demo",
                "password": "demo123"
            }
            
            await websocket.send(json.dumps(login_message))
            logger.info("📤 Sent login message")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📨 Received response: {response_data}")
            
            if response_data.get('type') == 'login_response':
                if response_data['data']['success']:
                    logger.info("✅ Login successful")
                    token = response_data['data']['token']
                    user = response_data['data']['user']
                    logger.info(f"User: {user['username']}, Balance: ${user['portfolio_balance']}")
                    
                    # Test getting positions
                    logger.info("Testing get positions...")
                    positions_message = {
                        "type": "get_positions"
                    }
                    
                    await websocket.send(json.dumps(positions_message))
                    logger.info("📤 Sent get_positions message")
                    
                    # Wait for response
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    logger.info(f"📨 Received positions response: {response_data}")
                    
                else:
                    logger.info(f"❌ Login failed: {response_data['data']['message']}")
            
            # Test crypto data
            logger.info("Testing get crypto data...")
            crypto_message = {
                "type": "get_crypto_data"
            }
            
            await websocket.send(json.dumps(crypto_message))
            logger.info("📤 Sent get_crypto_data message")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📨 Received crypto data response: {response_data.get('type')}")
            
            logger.info("✅ All tests completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_authentication()) 