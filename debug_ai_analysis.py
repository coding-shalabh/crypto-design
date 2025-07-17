#!/usr/bin/env python3
"""
Debug script for AI Analysis functionality
"""
import asyncio
import json
import time
import logging
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_analysis_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Import AI analysis components
from ai_analysis import AIAnalysisManager
from market_data import MarketDataManager
from config import Config

class AIAnalysisDebugger:
    """Debug class for AI analysis testing"""
    
    def __init__(self):
        logger.info("🔍 AI Analysis Debugger initialized")
        self.ai_manager = AIAnalysisManager()
        self.market_data = MarketDataManager()
        
    async def test_market_data_fetch(self, symbol: str = "BTCUSDT"):
        """Test market data fetching"""
        logger.info(f"🔍 Testing market data fetch for {symbol}")
        
        try:
            # Fetch market data
            market_data = await self.market_data.get_market_data(symbol)
            
            if market_data:
                logger.info(f"✅ Market data fetched successfully for {symbol}")
                logger.info(f"   Current price: ${market_data.get('current_price', 0):,.2f}")
                logger.info(f"   24h change: {market_data.get('change_24h', 0):.2f}%")
                logger.info(f"   Volume: {market_data.get('volume_24h', 0):,.0f}")
                logger.info(f"   Price data points: {len(market_data.get('prices', []))}")
                logger.info(f"   Candle data points: {len(market_data.get('candles', []))}")
                return market_data
            else:
                logger.error(f"❌ Failed to fetch market data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching market data for {symbol}: {e}")
            return None
    
    async def test_grok_analysis(self, symbol: str = "BTCUSDT"):
        """Test Grok sentiment analysis"""
        logger.info(f"🔍 Testing Grok sentiment analysis for {symbol}")
        
        try:
            # Get market data
            market_data = await self.test_market_data_fetch(symbol)
            if not market_data:
                logger.error(f"❌ Cannot test Grok analysis - no market data for {symbol}")
                return None
            
            # Run Grok analysis
            start_time = time.time()
            grok_result = await self.ai_manager.grok_sentiment_analysis(symbol, market_data)
            end_time = time.time()
            
            logger.info(f"✅ Grok analysis completed in {end_time - start_time:.2f} seconds")
            logger.info(f"   Sentiment: {grok_result.get('sentiment', 'unknown')}")
            logger.info(f"   Recommendation: {grok_result.get('recommendation', 'HOLD')}")
            logger.info(f"   Confidence: {grok_result.get('confidence_score', 0):.2f}")
            logger.info(f"   Source: {grok_result.get('source', 'unknown')}")
            
            return grok_result
            
        except Exception as e:
            logger.error(f"❌ Error in Grok analysis for {symbol}: {e}")
            return None
    
    async def test_claude_analysis(self, symbol: str = "BTCUSDT"):
        """Test Claude deep analysis"""
        logger.info(f"🔍 Testing Claude deep analysis for {symbol}")
        
        try:
            # Get market data
            market_data = await self.test_market_data_fetch(symbol)
            if not market_data:
                logger.error(f"❌ Cannot test Claude analysis - no market data for {symbol}")
                return None
            
            # Run Claude analysis
            start_time = time.time()
            claude_result = await self.ai_manager.claude_deep_analysis(market_data)
            end_time = time.time()
            
            logger.info(f"✅ Claude analysis completed in {end_time - start_time:.2f} seconds")
            logger.info(f"   Recommendation: {claude_result.get('recommendation', {}).get('action', 'HOLD')}")
            logger.info(f"   Confidence: {claude_result.get('recommendation', {}).get('confidence', 0):.2f}")
            logger.info(f"   Source: {claude_result.get('source', 'unknown')}")
            
            return claude_result
            
        except Exception as e:
            logger.error(f"❌ Error in Claude analysis for {symbol}: {e}")
            return None
    
    async def test_local_analysis(self, symbol: str = "BTCUSDT"):
        """Test local analysis fallback"""
        logger.info(f"🔍 Testing local analysis for {symbol}")
        
        try:
            # Get market data
            market_data = await self.test_market_data_fetch(symbol)
            if not market_data:
                logger.error(f"❌ Cannot test local analysis - no market data for {symbol}")
                return None
            
            # Run local analysis
            start_time = time.time()
            local_result = self.ai_manager.create_local_analysis_result(symbol, market_data)
            end_time = time.time()
            
            logger.info(f"✅ Local analysis completed in {end_time - start_time:.2f} seconds")
            logger.info(f"   Sentiment: {local_result.get('sentiment', 'unknown')}")
            logger.info(f"   Recommendation: {local_result.get('recommendation', 'HOLD')}")
            logger.info(f"   Confidence: {local_result.get('confidence_score', 0):.2f}")
            logger.info(f"   Source: {local_result.get('source', 'unknown')}")
            
            return local_result
            
        except Exception as e:
            logger.error(f"❌ Error in local analysis for {symbol}: {e}")
            return None
    
    async def test_full_pipeline(self, symbol: str = "BTCUSDT"):
        """Test complete AI analysis pipeline"""
        logger.info(f"🔍 Testing complete AI analysis pipeline for {symbol}")
        
        try:
            # Get market data
            market_data = await self.test_market_data_fetch(symbol)
            if not market_data:
                logger.error(f"❌ Cannot test pipeline - no market data for {symbol}")
                return None
            
            # Run full pipeline
            start_time = time.time()
            pipeline_result = await self.ai_manager.run_ai_analysis_pipeline(symbol, market_data)
            end_time = time.time()
            
            logger.info(f"✅ Full pipeline completed in {end_time - start_time:.2f} seconds")
            
            if pipeline_result:
                final_rec = pipeline_result.get('final_recommendation', {})
                logger.info(f"   Final Action: {final_rec.get('action', 'HOLD')}")
                logger.info(f"   Final Confidence: {final_rec.get('confidence', 0):.2f}")
                logger.info(f"   Combined Confidence: {pipeline_result.get('combined_confidence', 0):.2f}")
                logger.info(f"   Source: {pipeline_result.get('source', 'unknown')}")
                logger.info(f"   Timestamp: {pipeline_result.get('timestamp', 'unknown')}")
                
                # Log individual analysis results
                if 'grok_analysis' in pipeline_result:
                    grok = pipeline_result['grok_analysis']
                    logger.info(f"   Grok: {grok.get('recommendation', 'HOLD')} ({grok.get('confidence_score', 0):.2f})")
                
                if 'claude_analysis' in pipeline_result:
                    claude = pipeline_result['claude_analysis']
                    logger.info(f"   Claude: {claude.get('recommendation', {}).get('action', 'HOLD')} ({claude.get('recommendation', {}).get('confidence', 0):.2f})")
                
                if 'gpt_refinement' in pipeline_result and pipeline_result['gpt_refinement']:
                    gpt = pipeline_result['gpt_refinement']
                    logger.info(f"   GPT: {gpt.get('plan_type', 'N/A')}")
                
                return pipeline_result
            else:
                logger.error(f"❌ Pipeline returned no result for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in full pipeline for {symbol}: {e}")
            return None
    
    async def test_multiple_symbols(self, symbols: list = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]):
        """Test analysis on multiple symbols"""
        logger.info(f"🔍 Testing analysis on multiple symbols: {symbols}")
        
        results = {}
        
        for symbol in symbols:
            logger.info(f"🔍 Testing {symbol}...")
            try:
                result = await self.test_full_pipeline(symbol)
                results[symbol] = result
                
                # Small delay between symbols
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error testing {symbol}: {e}")
                results[symbol] = None
        
        # Summary
        logger.info("🔍 Multiple symbols test summary:")
        for symbol, result in results.items():
            if result:
                action = result.get('final_recommendation', {}).get('action', 'HOLD')
                confidence = result.get('combined_confidence', 0)
                logger.info(f"   {symbol}: {action} ({confidence:.2f})")
            else:
                logger.info(f"   {symbol}: FAILED")
        
        return results
    
    async def test_api_connectivity(self):
        """Test API connectivity"""
        logger.info("🔍 Testing API connectivity")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning("⚠️ No OpenRouter API key configured")
            return False
        
        logger.info("✅ OpenRouter API key is configured")
        
        # Test with a simple request
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'anthropic/claude-3.5-sonnet',
                    'messages': [{'role': 'user', 'content': 'Hello'}],
                    'max_tokens': 10
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ OpenRouter API connectivity test passed")
                        return True
                    else:
                        logger.error(f"❌ OpenRouter API test failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ API connectivity test error: {e}")
            return False

async def main():
    """Main debug function"""
    logger.info("🚀 Starting AI Analysis Debug Session")
    
    debugger = AIAnalysisDebugger()
    
    # Test 1: API Connectivity
    logger.info("\n" + "="*50)
    logger.info("TEST 1: API Connectivity")
    logger.info("="*50)
    api_ok = await debugger.test_api_connectivity()
    
    # Test 2: Market Data
    logger.info("\n" + "="*50)
    logger.info("TEST 2: Market Data Fetch")
    logger.info("="*50)
    await debugger.test_market_data_fetch("BTCUSDT")
    
    # Test 3: Individual Analysis Components
    logger.info("\n" + "="*50)
    logger.info("TEST 3: Individual Analysis Components")
    logger.info("="*50)
    
    if api_ok:
        await debugger.test_grok_analysis("BTCUSDT")
        await debugger.test_claude_analysis("BTCUSDT")
    else:
        logger.info("⏸ Skipping API-based analysis (no API key)")
    
    await debugger.test_local_analysis("BTCUSDT")
    
    # Test 4: Full Pipeline
    logger.info("\n" + "="*50)
    logger.info("TEST 4: Full Analysis Pipeline")
    logger.info("="*50)
    await debugger.test_full_pipeline("BTCUSDT")
    
    # Test 5: Multiple Symbols
    logger.info("\n" + "="*50)
    logger.info("TEST 5: Multiple Symbols")
    logger.info("="*50)
    await debugger.test_multiple_symbols(["BTCUSDT", "ETHUSDT"])
    
    logger.info("\n" + "="*50)
    logger.info("🎉 AI Analysis Debug Session Completed")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main()) 