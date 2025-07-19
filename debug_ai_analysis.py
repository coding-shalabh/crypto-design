#!/usr/bin/env python3
"""
Debug script to test AI analysis system
"""
import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.ai_analysis import AIAnalysisManager
from backend.market_data import MarketDataManager
from backend.config import Config
from backend.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_ai_analysis():
    """Test the AI analysis system"""
    
    print("🔍 Testing AI Analysis System")
    print("=" * 50)
    
    # Check configuration
    print(f"📋 Config Check:")
    print(f"   API_MODE: {Config.API_MODE}")
    print(f"   OPENROUTER_API_KEY: {'SET' if Config.OPENROUTER_API_KEY else 'NOT SET'}")
    print(f"   TARGET_PAIRS: {Config.TARGET_PAIRS}")
    print()
    
    # Initialize components
    print("🔧 Initializing components...")
    market_data = MarketDataManager()
    ai_analysis = AIAnalysisManager()
    db = DatabaseManager()
    
    # Test market data
    print("📊 Testing market data...")
    crypto_data = await market_data.fetch_crypto_data()
    print(f"   Fetched data for {len(crypto_data)} symbols")
    
    if not crypto_data:
        print("❌ No market data available!")
        return
    
    # Test AI analysis for each symbol
    test_symbol = Config.TARGET_PAIRS[0] if Config.TARGET_PAIRS else 'BTCUSDT'
    symbol_key = test_symbol.replace('USDT', '').lower()
    
    print(f"🤖 Testing AI analysis for {test_symbol}...")
    
    if symbol_key in crypto_data:
        market_data_for_symbol = crypto_data[symbol_key]
        
        print(f"   Market data available: {symbol_key}")
        print(f"   Current price: ${market_data_for_symbol.get('current_price', 0):.2f}")
        
        # Test AI analysis pipeline
        print("🧠 Running AI analysis pipeline...")
        result = await ai_analysis.run_ai_analysis_pipeline(test_symbol, market_data_for_symbol)
        
        if result:
            print("✅ AI analysis completed!")
            print(f"   Source: {result.get('source', 'unknown')}")
            
            final_rec = result.get('final_recommendation', {})
            if final_rec:
                action = final_rec.get('action', 'HOLD')
                confidence = final_rec.get('confidence', 0)
                reasoning = final_rec.get('reasoning', 'No reasoning')
                
                print(f"   Final recommendation: {action}")
                print(f"   Confidence: {confidence:.2f}")
                print(f"   Reasoning: {reasoning[:100]}...")
            else:
                print("   No final recommendation found")
            
            # Test database logging
            print("💾 Testing database logging...")
            analysis_log = {
                'symbol': test_symbol,
                'analysis_type': 'debug_test',
                'result': result,
                'source': 'debug_script',
                'timestamp': asyncio.get_event_loop().time()
            }
            
            log_success = await db.log_analysis(analysis_log, user_id=28)
            if log_success:
                print("✅ Analysis logged to database")
            else:
                print("❌ Failed to log analysis to database")
        else:
            print("❌ AI analysis failed!")
    else:
        print(f"❌ Symbol {symbol_key} not found in market data")
        print(f"   Available symbols: {list(crypto_data.keys())}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print(f"   Market data: {'✅' if crypto_data else '❌'}")
    print(f"   AI analysis: {'✅' if result else '❌'}")
    print(f"   Database logging: {'✅' if log_success else '❌'}")
    
    # Test different API modes
    print("\n🔄 Testing API modes...")
    
    # Test fake mode
    original_mode = Config.API_MODE
    Config.API_MODE = 'fake'
    print(f"   Testing FAKE mode...")
    
    fake_result = await ai_analysis.run_ai_analysis_pipeline(test_symbol, market_data_for_symbol)
    fake_success = fake_result is not None
    print(f"   Fake mode result: {'✅' if fake_success else '❌'}")
    
    if fake_success:
        fake_final = fake_result.get('final_recommendation', {})
        print(f"   Fake recommendation: {fake_final.get('action', 'HOLD')} ({fake_final.get('confidence', 0):.2f})")
    
    # Test real mode (if API key is available)
    if Config.OPENROUTER_API_KEY:
        Config.API_MODE = 'real'
        print(f"   Testing REAL mode...")
        
        real_result = await ai_analysis.run_ai_analysis_pipeline(test_symbol, market_data_for_symbol)
        real_success = real_result is not None
        print(f"   Real mode result: {'✅' if real_success else '❌'}")
        
        if real_success:
            real_final = real_result.get('final_recommendation', {})
            print(f"   Real recommendation: {real_final.get('action', 'HOLD')} ({real_final.get('confidence', 0):.2f})")
    else:
        print("   Skipping REAL mode (no API key)")
    
    # Restore original mode
    Config.API_MODE = original_mode
    
    print("\n🎉 Debug test completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_analysis())