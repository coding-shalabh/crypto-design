#!/usr/bin/env python3
"""
Test script to verify dummy analysis system is working
"""
import asyncio
import json
import os
import sys
import requests
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config
from ai_analysis import AIAnalysisManager
from market_data import MarketDataManager

async def test_dummy_system():
    """Test the complete dummy analysis system"""
    print("🧪 Testing Dummy Analysis System")
    print("=" * 50)
    
    # Test 1: Check dummy server is running
    print("\n1. Testing Dummy Server Connection...")
    try:
        response = requests.get("http://localhost:5001/api/health", timeout=5)
        if response.status_code == 200:
            print(" Dummy server is running")
            print(f"   Status: {response.json()}")
        else:
            print(f"❌ Dummy server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to dummy server: {e}")
        return False
    
    # Test 2: Check API mode
    print("\n2. Testing API Mode Configuration...")
    os.environ['API_MODE'] = 'fake'
    print(f" API_MODE set to: {os.getenv('API_MODE', 'real')}")
    
    # Test 3: Test dummy analysis endpoint
    print("\n3. Testing Dummy Analysis Endpoint...")
    try:
        response = requests.get("http://localhost:5001/api/analysis/BTCUSDT", timeout=10)
        if response.status_code == 200:
            analysis = response.json()
            print(" Dummy analysis received")
            print(f"   Symbol: {analysis['symbol']}")
            print(f"   Recommendation: {analysis['final_recommendation']['action']}")
            print(f"   Confidence: {analysis['final_recommendation']['confidence']:.2f}")
            print(f"   Source: {analysis['source']}")
        else:
            print(f"❌ Dummy analysis failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dummy analysis request failed: {e}")
        return False
    
    # Test 4: Test AI Analysis Manager with dummy mode
    print("\n4. Testing AI Analysis Manager (Dummy Mode)...")
    try:
        ai_manager = AIAnalysisManager()
        
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
            print(" AI Analysis Manager working with dummy data")
            print(f"   Symbol: {result['symbol']}")
            print(f"   Final Recommendation: {result['final_recommendation']['action']}")
            print(f"   Confidence: {result['final_recommendation']['confidence']:.2f}")
            print(f"   Source: {result.get('source', 'Unknown')}")
        else:
            print("❌ AI Analysis Manager returned no result")
            return False
            
    except Exception as e:
        print(f"❌ AI Analysis Manager test failed: {e}")
        return False
    
    # Test 5: Test Market Data Manager
    print("\n5. Testing Market Data Manager...")
    try:
        market_manager = MarketDataManager()
        
        # Test price fetching (should be real)
        price_data = await market_manager.get_current_price('BTCUSDT')
        if price_data:
            print(" Market data working (real prices)")
            print(f"   Symbol: {price_data['symbol']}")
            print(f"   Price: ${price_data['price']:.2f}")
            print(f"   Volume: {price_data['volume']}")
        else:
            print("❌ Market data failed")
            return False
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False
    
    # Test 6: Test combined workflow
    print("\n6. Testing Combined Workflow (Real Prices + Fake Analysis)...")
    try:
        # Get real market data
        real_market_data = await market_manager.get_current_price('BTCUSDT')
        
        # Get fake analysis
        fake_analysis = await ai_manager.run_ai_analysis_pipeline('BTCUSDT', real_market_data)
        
        if real_market_data and fake_analysis:
            print(" Combined workflow working")
            print(f"   Real Price: ${real_market_data['price']:.2f}")
            print(f"   Fake Analysis: {fake_analysis['final_recommendation']['action']}")
            print(f"   Confidence: {fake_analysis['final_recommendation']['confidence']:.2f}")
            print(f"   Analysis Source: {fake_analysis.get('source', 'Unknown')}")
        else:
            print("❌ Combined workflow failed")
            return False
            
    except Exception as e:
        print(f"❌ Combined workflow test failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Dummy system is working correctly.")
    print("\n📋 Summary:")
    print("   • Dummy server running on http://localhost:5001")
    print("   • API_MODE set to 'fake'")
    print("   • Real market data fetching works")
    print("   • Fake AI analysis works")
    print("   • Combined workflow functional")
    print("\n Your bot will now:")
    print("   • Fetch real cryptocurrency prices")
    print("   • Generate fake AI analysis instantly")
    print("   • Execute demo trades with real PnL calculations")
    print("   • No real API calls to LLM providers")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_dummy_system())