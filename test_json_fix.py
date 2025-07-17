#!/usr/bin/env python3
"""
Test script to verify JSON serialization fixes
"""
import asyncio
import websockets
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_websocket_connection():
    """Test WebSocket connection and message handling"""
    try:
        print("🔌 Testing WebSocket connection...")
        
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            print("  Connected to WebSocket server")
            
            # Wait for initial data
            print("📥 Waiting for initial data...")
            initial_message = await websocket.recv()
            initial_data = json.loads(initial_message)
            print(f"  Received initial data: {initial_data['type']}")
            
            # Test get_positions
            print("📊 Testing get_positions...")
            await websocket.send(json.dumps({'type': 'get_positions'}))
            response = await websocket.recv()
            positions_data = json.loads(response)
            print(f"  Received positions: {positions_data['type']}")
            
            # Test get_trade_history
            print("📈 Testing get_trade_history...")
            await websocket.send(json.dumps({'type': 'get_trade_history'}))
            response = await websocket.recv()
            history_data = json.loads(response)
            print(f"  Received trade history: {history_data['type']}")
            
            # Test get_crypto_data
            print("💰 Testing get_crypto_data...")
            await websocket.send(json.dumps({'type': 'get_crypto_data'}))
            response = await websocket.recv()
            crypto_data = json.loads(response)
            print(f"  Received crypto data: {crypto_data['type']}")
            
            print("🎉 All tests passed! JSON serialization is working correctly.")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing JSON Serialization Fixes")
    print("=" * 50)
    
    success = asyncio.run(test_websocket_connection())
    
    if success:
        print("\n  All tests passed! The JSON serialization issues have been fixed.")
    else:
        print("\n❌ Tests failed. There may still be issues to resolve.") 