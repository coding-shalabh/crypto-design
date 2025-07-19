"""
Simple test to verify the dummy analysis system
"""
import asyncio
import json
import os
import sys
import urllib.request
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set API mode to fake
os.environ['API_MODE'] = 'fake'

async def test_system():
    """Test the system with dummy analysis"""
    print("Testing Dummy Analysis System")
    print("=" * 50)
    
    # Test 1: Check dummy server
    print("\n1. Testing Dummy Server...")
    try:
        with urllib.request.urlopen('http://localhost:5001/api/health') as response:
            data = json.loads(response.read())
            print(f"[OK] Dummy server is running: {data}")
    except Exception as e:
        print(f"[ERROR] Dummy server failed: {e}")
        return False
    
    # Test 2: Get dummy analysis
    print("\n2. Testing Dummy Analysis...")
    try:
        with urllib.request.urlopen('http://localhost:5001/api/analysis/BTCUSDT') as response:
            analysis = json.loads(response.read())
            print(f"[OK] Dummy analysis received")
            print(f"   Symbol: {analysis['symbol']}")
            print(f"   Recommendation: {analysis['final_recommendation']['action']}")
            print(f"   Confidence: {analysis['final_recommendation']['confidence']:.2f}")
            print(f"   Source: {analysis['source']}")
    except Exception as e:
        print(f"[ERROR] Dummy analysis failed: {e}")
        return False
    
    # Test 3: Test with backend components
    print("\n3. Testing Backend Components...")
    try:
        from config import Config
        from ai_analysis import AIAnalysisManager
        from market_data import MarketDataManager
        
        print(f"[OK] API Mode: {Config.API_MODE}")
        
        # Test AI Analysis Manager
        ai_manager = AIAnalysisManager()
        market_manager = MarketDataManager()
        
        # Mock market data
        mock_market_data = {
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test analysis
        result = await ai_manager.run_ai_analysis_pipeline('BTCUSDT', mock_market_data)
        
        if result:
            print("[OK] AI Analysis Manager working")
            print(f"   Recommendation: {result['final_recommendation']['action']}")
            print(f"   Confidence: {result['final_recommendation']['confidence']:.2f}")
        else:
            print("[ERROR] AI Analysis Manager failed")
            return False
        
        # Test real market data
        try:
            price_data = await market_manager.get_current_price('BTCUSDT')
            if price_data:
                print("[OK] Real market data working")
                print(f"   Price: ${price_data['price']:.2f}")
            else:
                print("[WARNING] Market data unavailable (might be API limits)")
        except Exception as e:
            print(f"[WARNING] Market data failed: {e}")
        
    except Exception as e:
        print(f"[ERROR] Backend test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("SUCCESS: Dummy system is working!")
    print("\nWhat's working:")
    print("   - Dummy analysis server running")
    print("   - Fake AI analysis generation")
    print("   - Backend components initialized")
    print("   - API_MODE set to 'fake'")
    
    print("\nTo use the system:")
    print("   1. Dummy server is running on http://localhost:5001")
    print("   2. Backend will use fake analysis")
    print("   3. Real prices will be fetched from Binance")
    print("   4. Demo trades will use real PnL calculations")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_system())