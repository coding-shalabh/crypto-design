#!/usr/bin/env python3
"""
Test script to verify local AI analysis is working
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_local_analysis():
    """Test local AI analysis functionality"""
    try:
        from ai_analysis import AIAnalysisManager
        from market_data import MarketDataManager
        
        print("🔍 Testing local AI analysis...")
        
        # Initialize managers
        ai_manager = AIAnalysisManager()
        market_manager = MarketDataManager()
        
        print("✅ Managers initialized")
        
        # Fetch market data
        print("🔍 Fetching market data...")
        await market_manager.fetch_crypto_data()
        
        # Collect market data for BTCUSDT
        market_data = await market_manager.collect_market_data('BTCUSDT')
        if market_data:
            print(f"✅ Market data collected: Price ${market_data.get('current_price', 0)}")
            print(f"   Data keys: {list(market_data.keys())}")
        else:
            print("❌ Failed to collect market data")
            return
        
        # Test local analysis
        print("🔍 Testing local analysis...")
        local_result = ai_manager.create_local_analysis_result('BTCUSDT', market_data)
        if local_result:
            print("✅ Local analysis completed")
            print(f"   Symbol: {local_result['symbol']}")
            print(f"   Sentiment: {local_result['sentiment']}")
            print(f"   Recommendation: {local_result['recommendation']}")
            print(f"   Confidence: {local_result['confidence_score']}")
            print(f"   Reasoning: {local_result['reasoning']}")
        else:
            print("❌ Local analysis failed")
        
        # Test full AI pipeline
        print("🔍 Testing full AI pipeline...")
        analysis = await ai_manager.run_ai_analysis_pipeline('BTCUSDT', market_data)
        if analysis:
            print("✅ Full AI pipeline completed")
            print(f"   Combined confidence: {analysis.get('combined_confidence', 0)}")
            print(f"   Final recommendation: {analysis.get('final_recommendation', {}).get('action', 'HOLD')}")
        else:
            print("❌ Full AI pipeline failed")
            
    except Exception as e:
        print(f"❌ Error testing local analysis: {e}")

if __name__ == "__main__":
    print("🧪 Starting local AI analysis test...")
    asyncio.run(test_local_analysis()) 