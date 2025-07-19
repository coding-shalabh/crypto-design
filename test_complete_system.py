#!/usr/bin/env python3
"""
Complete system test - Tests the full trading bot workflow with dummy analysis
"""
import asyncio
import json
import os
import sys
import urllib.request
from datetime import datetime
import websockets

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set API mode to fake
os.environ['API_MODE'] = 'fake'

async def test_websocket_connection():
    """Test WebSocket connection to backend"""
    try:
        print("Testing WebSocket connection to backend...")
        
        # Connect to WebSocket
        websocket = await websockets.connect("ws://localhost:8767")
        print("[OK] Connected to WebSocket backend")
        
        # Test 1: Get analysis
        print("\nTesting analysis request...")
        analysis_request = {
            "action": "get_analysis",
            "symbol": "BTCUSDT"
        }
        
        await websocket.send(json.dumps(analysis_request))
        
        # Wait for response
        response = await asyncio.wait_for(websocket.recv(), timeout=30)
        data = json.loads(response)
        
        if data.get('type') == 'analysis_complete':
            analysis = data.get('data', {}).get('analysis', {})
            final_rec = analysis.get('final_recommendation', {})
            print(f"[OK] Analysis received: {final_rec.get('action')} with {final_rec.get('confidence'):.2f} confidence")
        else:
            print(f"[INFO] Response: {data}")
        
        # Test 2: Get bot status
        print("\nTesting bot status request...")
        status_request = {"action": "get_bot_status"}
        await websocket.send(json.dumps(status_request))
        
        status_response = await asyncio.wait_for(websocket.recv(), timeout=10)
        status_data = json.loads(status_response)
        
        if status_data.get('type') == 'bot_status':
            bot_status = status_data.get('data', {})
            print(f"[OK] Bot status: {bot_status.get('status', 'unknown')}")
        else:
            print(f"[INFO] Status response: {status_data}")
        
        # Test 3: Start bot
        print("\nTesting bot start...")
        start_request = {"action": "start_bot"}
        await websocket.send(json.dumps(start_request))
        
        start_response = await asyncio.wait_for(websocket.recv(), timeout=10)
        start_data = json.loads(start_response)
        print(f"[INFO] Bot start response: {start_data}")
        
        # Listen for bot messages for a bit
        print("\nListening for bot messages (10 seconds)...")
        try:
            for i in range(10):
                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                msg_data = json.loads(message)
                msg_type = msg_data.get('type', 'unknown')
                
                if msg_type == 'price_update':
                    price_data = msg_data.get('data', {})
                    print(f"[PRICE] {price_data.get('symbol')}: ${price_data.get('price'):.2f}")
                elif msg_type == 'analysis_complete':
                    analysis = msg_data.get('data', {}).get('analysis', {})
                    final_rec = analysis.get('final_recommendation', {})
                    print(f"[ANALYSIS] {analysis.get('symbol')}: {final_rec.get('action')} ({final_rec.get('confidence'):.2f})")
                elif msg_type == 'trade_executed':
                    trade = msg_data.get('data', {})
                    print(f"[TRADE] {trade.get('symbol')}: {trade.get('side')} at ${trade.get('price'):.2f}")
                else:
                    print(f"[MESSAGE] {msg_type}: {msg_data}")
        except asyncio.TimeoutError:
            print("[INFO] No more messages received")
        
        await websocket.close()
        print("[OK] WebSocket connection closed")
        return True
        
    except Exception as e:
        print(f"[ERROR] WebSocket test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Complete System Test - Dummy Analysis Mode")
    print("=" * 60)
    
    # Test 1: Dummy server
    print("\n1. Testing Dummy Server...")
    try:
        with urllib.request.urlopen('http://localhost:5001/api/health') as response:
            data = json.loads(response.read())
            print(f"[OK] Dummy server running: {data}")
    except Exception as e:
        print(f"[ERROR] Dummy server failed: {e}")
        return False
    
    # Test 2: Backend components
    print("\n2. Testing Backend Components...")
    try:
        from config import Config
        print(f"[OK] API Mode: {Config.API_MODE}")
        
        if Config.API_MODE != 'fake':
            print(f"[WARNING] API_MODE is '{Config.API_MODE}', expected 'fake'")
    except Exception as e:
        print(f"[ERROR] Backend test failed: {e}")
        return False
    
    # Test 3: WebSocket connection
    print("\n3. Testing WebSocket Connection...")
    websocket_ok = await test_websocket_connection()
    
    if websocket_ok:
        print("\n" + "=" * 60)
        print("SUCCESS: Complete system test passed!")
        print("\nSystem Status:")
        print("   - Dummy analysis server: RUNNING")
        print("   - Backend API mode: FAKE")
        print("   - WebSocket connection: WORKING")
        print("   - Bot functionality: TESTED")
        
        print("\nHow to use:")
        print("   1. Frontend: http://localhost:3000")
        print("   2. Backend: ws://localhost:8767")
        print("   3. Dummy server: http://localhost:5001")
        print("   4. Bot will use fake analysis with real prices")
        print("   5. Demo trades will show real PnL calculations")
        
        return True
    else:
        print("\n[ERROR] WebSocket test failed")
        return False

if __name__ == "__main__":
    asyncio.run(main())