#!/usr/bin/env python3
"""
Test script to check API keys and AI analysis pipeline
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_api_keys():
    """Test if API keys are available"""
    print("🔍 Checking API keys...")
    
    # Check OpenRouter API key
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    if openrouter_key:
        print(f"✅ OpenRouter API key found: {openrouter_key[:10]}...")
    else:
        print("❌ OpenRouter API key not found")
    
    # Check CryptoPanic API key
    cryptopanic_key = os.getenv('CRYPTOPANIC_API_KEY')
    if cryptopanic_key:
        print(f"✅ CryptoPanic API key found: {cryptopanic_key[:10]}...")
    else:
        print("❌ CryptoPanic API key not found")
    
    # Test AI analysis manager
    print("\n🔍 Testing AI analysis manager...")
    try:
        from backend.ai_analysis import AIAnalysisManager
        from backend.market_data import MarketDataManager
        
        ai_manager = AIAnalysisManager()
        market_manager = MarketDataManager()
        
        print("✅ AI analysis manager initialized")
        
        # Test market data collection
        print("🔍 Testing market data collection...")
        market_data = await market_manager.collect_market_data('BTCUSDT')
        if market_data:
            print(f"✅ Market data collected: Price ${market_data.get('current_price', 0)}")
            print(f"   Data keys: {list(market_data.keys())}")
        else:
            print("❌ Failed to collect market data")
            return
        
        # Test AI analysis pipeline
        print("🔍 Testing AI analysis pipeline...")
        analysis = await ai_manager.run_ai_analysis_pipeline('BTCUSDT', market_data)
        if analysis:
            print("✅ AI analysis completed")
            print(f"   Analysis keys: {list(analysis.keys())}")
            print(f"   Combined confidence: {analysis.get('combined_confidence', 0)}")
        else:
            print("❌ AI analysis failed")
            
    except Exception as e:
        print(f"❌ Error testing AI analysis: {e}")

if __name__ == "__main__":
    print("🧪 Starting API key and AI analysis test...")
    asyncio.run(test_api_keys()) 