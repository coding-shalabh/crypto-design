#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_registration():
    """Test user registration via WebSocket"""
    uri = "ws://localhost:8770"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Test registration
            register_data = {
                "type": "register",
                "data": {
                    "username": "testuser123",
                    "email": "test@example.com",
                    "password": "password123"
                }
            }
            
            print(f"Sending registration request: {register_data}")
            await websocket.send(json.dumps(register_data))
            
            # Wait for response (skip initial_data and wait for auth response)
            print("Waiting for response...")
            while True:
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Skip initial_data and price_updates, wait for auth response
                if response_data.get('type') in ['initial_data', 'price_updates_batch']:
                    continue
                    
                print(f"Registration response: {response_data}")
                
                if response_data.get('type') == 'register_success':
                    print("Registration successful!")
                    return True
                elif response_data.get('type') == 'auth_error':
                    print(f"Registration failed: {response_data.get('data', {}).get('message', 'Unknown error')}")
                    return False
                else:
                    print(f"Unexpected response: {response_data}")
                    return False
                
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

async def test_login():
    """Test user login via WebSocket"""
    uri = "ws://localhost:8770"
    
    try:
        print(f"Connecting to {uri} for login test...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Test login
            login_data = {
                "type": "login",
                "data": {
                    "username": "testuser123",
                    "password": "password123"
                }
            }
            
            print(f"Sending login request: {login_data}")
            await websocket.send(json.dumps(login_data))
            
            # Wait for response (skip initial_data and wait for auth response)
            print("Waiting for response...")
            while True:
                response = await websocket.recv()
                response_data = json.loads(response)
                
                # Skip initial_data and price_updates, wait for auth response
                if response_data.get('type') in ['initial_data', 'price_updates_batch']:
                    continue
                    
                print(f"Login response: {response_data}")
                
                if response_data.get('type') == 'login_success':
                    print("Login successful!")
                    return True
                elif response_data.get('type') == 'auth_error':
                    print(f"Login failed: {response_data.get('data', {}).get('message', 'Unknown error')}")
                    return False
                else:
                    print(f"Unexpected response: {response_data}")
                    return False
                
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

async def main():
    print("Testing Authentication System")
    print("=" * 50)
    
    # Test registration
    print("\n1. Testing Registration...")
    reg_success = await test_registration()
    
    if reg_success:
        print("\n2. Testing Login...")
        login_success = await test_login()
        
        if login_success:
            print("\nAll authentication tests passed!")
        else:
            print("\nLogin test failed!")
    else:
        print("\nRegistration test failed!")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main())