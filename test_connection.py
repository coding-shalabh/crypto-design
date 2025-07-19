#!/usr/bin/env python3
"""
Test WebSocket connection to verify the port fix
"""
import asyncio
import websockets
import json
import time

async def test_connection():
    """Test connection to the fixed WebSocket port"""
    try:
        # Test the correct port
        uri = "ws://localhost:8768"
        print(f"🔍 Testing connection to {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Consume initial data
            initial_response = await asyncio.wait_for(websocket.recv(), timeout=5)
            initial_data = json.loads(initial_response)
            print(f"📥 Received initial data: {initial_data.get('type')}")
            
            # Test a simple status request
            await websocket.send(json.dumps({'type': 'get_bot_status'}))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            print(f"📥 Bot status response: {data.get('type')}")
            
            if data.get('type') == 'bot_status_response':
                bot_data = data.get('data', {})
                config = bot_data.get('config', {})
                print(f"✅ Bot Status:")
                print(f"   Enabled: {bot_data.get('enabled', False)}")
                print(f"   Config keys: {len(config)} items")
                if 'profit_target_min' in config:
                    print(f"   Profit Target: ${config.get('profit_target_min')}")
                else:
                    print(f"   Profit Target: Not configured")
            
            print("\n🎉 Connection test successful!")
            print("Frontend should now be able to connect properly.")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure the backend server is running on port 8768")

if __name__ == "__main__":
    asyncio.run(test_connection()) 