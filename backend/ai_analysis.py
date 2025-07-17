"""
AI-powered trading analysis using multiple LLM models
"""
import aiohttp
import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from config import Config
from technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class AIAnalysisManager:
    """Manages AI-powered trading analysis"""
    
    def __init__(self):
        logger.info("Initializing AI Analysis Manager...")
        
        self.ai_analysis_cache = {}
        self.last_analysis_time = {}
        self.analysis_status = {}
        self.analysis_progress = {}
        
        logger.info(" AI Analysis Manager initialization complete!")
        
    async def grok_sentiment_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """Perform sentiment analysis using Grok"""
        logger.info(f"Starting Grok sentiment analysis for {symbol}")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for Grok analysis")
            return self.create_empty_analysis_result(symbol, "grok_sentiment")
        
        try:
            # Prepare market data for analysis
            current_price = market_data.get('current_price', 0)
            change_24h = market_data.get('change_24h', 0)
            volume_24h = market_data.get('volume_24h', 0)
            
            logger.info(f" Market data for {symbol}: Price=${current_price}, Change={change_24h:.2f}%, Volume={volume_24h:,.0f}")
            
            # Calculate technical indicators
            prices = market_data.get('prices', [])
            candles = market_data.get('candles', [])
            
            if len(prices) < 20:
                logger.warning(f" Insufficient price data for {symbol} analysis ({len(prices)} points)")
                return self.create_empty_analysis_result(symbol, "grok_sentiment")
            
            # Calculate indicators
            logger.info(f" Calculating technical indicators for {symbol}")
            rsi = TechnicalIndicators.calculate_rsi(prices)
            ema_20 = TechnicalIndicators.calculate_ema(prices, 20)
            macd = TechnicalIndicators.calculate_macd(prices)
            volatility = TechnicalIndicators.calculate_volatility(prices)
            
            logger.info(f" Technical indicators for {symbol}: RSI={rsi:.2f}, EMA20=${ema_20:.2f}, MACD={macd['macd']:.4f}, Vol={volatility:.4f}")
            
            analysis_prompt = f"""
            Analyze the current market conditions for {symbol} cryptocurrency.
            
            Current Data:
            - Current Price: ${current_price:,.2f}
            - 24h Change: {change_24h:.2f}%
            - 24h Volume: {volume_24h:,.0f}
            - RSI: {rsi:.2f}
            - EMA(20): ${ema_20:,.2f}
            - MACD: {macd['macd']:.4f}
            - Volatility: {volatility:.4f}
            
            Provide a comprehensive analysis including:
            1. Current market sentiment (bullish/bearish/neutral)
            2. Technical analysis summary
            3. Key support and resistance levels
            4. Risk assessment
            5. Trading recommendation with confidence score (0-1)
            
            Format your response as JSON with these fields:
            {{
                "sentiment": "bullish/bearish/neutral",
                "sentiment_score": 0.0-1.0,
                "technical_summary": "brief technical analysis",
                "support_levels": [price1, price2],
                "resistance_levels": [price1, price2],
                "risk_level": "low/medium/high",
                "recommendation": "BUY/SELL/HOLD",
                "confidence_score": 0.0-1.0,
                "reasoning": "detailed explanation"
            }}
            """
            
            logger.info(f" Sending Grok API request for {symbol}")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://crypto-trading-bot.com',
                    'X-Title': 'Crypto Trading Bot'
                }
                
                payload = {
                    'model': 'x-ai/grok-3',
                    'messages': [
                        {
                            'role': 'user',
                            'content': analysis_prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1000
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            logger.info(f" Received Grok response for {symbol}")
                            
                            # Parse JSON response
                            try:
                                analysis_result = self.parse_analysis_response(content)
                                analysis_result['source'] = 'grok_sentiment'
                                analysis_result['timestamp'] = datetime.now().isoformat()
                                
                                logger.info(f" Grok analysis completed for {symbol}: {analysis_result.get('sentiment', 'unknown')} sentiment, {analysis_result.get('recommendation', 'HOLD')} recommendation")
                                return analysis_result
                                
                            except Exception as e:
                                logger.error(f" Error parsing Grok response for {symbol}: {e}")
                                return self.create_empty_analysis_result(symbol, "grok_sentiment")
                        else:
                            logger.warning(f" Empty Grok response for {symbol}")
                            return self.create_empty_analysis_result(symbol, "grok_sentiment")
                    else:
                        logger.error(f" Grok API error for {symbol}: {response.status}")
                        return self.create_empty_analysis_result(symbol, "grok_sentiment")
                        
        except Exception as e:
            logger.error(f" Grok analysis error for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "grok_sentiment")
    
    async def claude_deep_analysis(self, market_data: Dict) -> Dict:
        """Perform deep analysis using Claude"""
        symbol = market_data.get('symbol', 'UNKNOWN')
        logger.info(f"Starting Claude deep analysis for {symbol}")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for Claude analysis")
            return self.create_empty_analysis_result(symbol, "claude_deep")
        
        try:
            current_price = market_data.get('current_price', 0)
            prices = market_data.get('prices', [])
            candles = market_data.get('candles', [])
            
            logger.info(f" Market data for {symbol}: Price=${current_price}, Data points={len(prices)}")
            
            if len(prices) < 50:
                logger.warning(f" Insufficient data for Claude analysis of {symbol} ({len(prices)} points)")
                return self.create_empty_analysis_result(symbol, "claude_deep")
            
            # Calculate comprehensive indicators
            logger.info(f" Calculating comprehensive indicators for {symbol}")
            rsi = TechnicalIndicators.calculate_rsi(prices)
            ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
            ema_26 = TechnicalIndicators.calculate_ema(prices, 26)
            macd = TechnicalIndicators.calculate_macd(prices)
            bb = TechnicalIndicators.calculate_bollinger_bands(prices)
            atr = TechnicalIndicators.calculate_atr(candles)
            
            logger.info(f" Indicators for {symbol}: RSI={rsi:.2f}, EMA12=${ema_12:.2f}, EMA26=${ema_26:.2f}, MACD={macd['macd']:.4f}")
            
            analysis_prompt = f"""
            Perform a comprehensive technical and fundamental analysis for {symbol}.
            
            Market Data:
            - Current Price: ${current_price:,.2f}
            - RSI: {rsi:.2f}
            - EMA(12): ${ema_12:,.2f}
            - EMA(26): ${ema_26:,.2f}
            - MACD: {macd['macd']:.4f}
            - Bollinger Bands: Upper=${bb['upper']:.2f}, Middle=${bb['middle']:.2f}, Lower=${bb['lower']:.2f}
            - ATR: {atr:.4f}
            
            Provide detailed analysis including:
            1. Trend analysis (short, medium, long term)
            2. Momentum indicators interpretation
            3. Volatility assessment
            4. Support/resistance identification
            5. Risk-reward analysis
            6. Trading strategy recommendation
            
            Return JSON format:
            {{
                "trend_analysis": {{
                    "short_term": "trend description",
                    "medium_term": "trend description",
                    "long_term": "trend description"
                }},
                "momentum": {{
                    "rsi_interpretation": "RSI analysis",
                    "macd_interpretation": "MACD analysis",
                    "overall_momentum": "bullish/bearish/neutral"
                }},
                "volatility": {{
                    "current_level": "low/medium/high",
                    "bollinger_position": "above/below/within bands",
                    "atr_interpretation": "volatility analysis"
                }},
                "levels": {{
                    "support": [price1, price2],
                    "resistance": [price1, price2]
                }},
                "risk_reward": {{
                    "risk_level": "low/medium/high",
                    "reward_potential": "low/medium/high",
                    "risk_reward_ratio": 0.0-5.0
                }},
                "recommendation": {{
                    "action": "BUY/SELL/HOLD",
                    "confidence": 0.0-1.0,
                    "reasoning": "detailed explanation",
                    "entry_price": {current_price},
                    "stop_loss": price,
                    "take_profit": price
                }}
            }}
            """
            
            logger.info(f" Sending Claude API request for {symbol}")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://crypto-trading-bot.com',
                    'X-Title': 'Crypto Trading Bot'
                }
                
                payload = {
                    'model': 'anthropic/claude-3.5-sonnet',
                    'messages': [
                        {
                            'role': 'user',
                            'content': analysis_prompt
                        }
                    ],
                    'temperature': 0.2,
                    'max_tokens': 1500
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            logger.info(f" Received Claude response for {symbol}")
                            
                            # Parse JSON response
                            try:
                                analysis_result = self.parse_claude_response(content)
                                analysis_result['source'] = 'claude_deep'
                                analysis_result['timestamp'] = datetime.now().isoformat()
                                
                                recommendation = analysis_result.get('recommendation', {})
                                action = recommendation.get('action', 'HOLD')
                                confidence = recommendation.get('confidence', 0)
                                
                                logger.info(f" Claude analysis completed for {symbol}: {action} recommendation with {confidence:.2f} confidence")
                                return analysis_result
                                
                            except Exception as e:
                                logger.error(f" Error parsing Claude response for {symbol}: {e}")
                                return self.create_empty_analysis_result(symbol, "claude_deep")
                        else:
                            logger.warning(f" Empty Claude response for {symbol}")
                            return self.create_empty_analysis_result(symbol, "claude_deep")
                    else:
                        logger.error(f" Claude API error for {symbol}: {response.status}")
                        return self.create_empty_analysis_result(symbol, "claude_deep")
                        
        except Exception as e:
            logger.error(f" Claude analysis error for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "claude_deep")
    
    async def gpt_trade_plan_generator(self, market_data: Dict, claude_analysis: Dict) -> Dict:
        """Generate trade plan using GPT"""
        symbol = market_data.get('symbol', 'UNKNOWN')
        logger.info(f"Starting GPT trade plan generation for {symbol}")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for GPT analysis")
            return self.create_empty_analysis_result(symbol, "gpt_plan")
        
        try:
            current_price = market_data.get('current_price', 0)
            claude_recommendation = claude_analysis.get('recommendation', {})
            
            logger.info(f" Using Claude recommendation for {symbol}: {claude_recommendation.get('action', 'HOLD')}")
            
            plan_prompt = f"""
            Generate a detailed trade execution plan for {symbol} based on the following analysis:
            
            Current Price: ${current_price:,.2f}
            Claude Recommendation: {claude_recommendation.get('action', 'HOLD')}
            Confidence: {claude_recommendation.get('confidence', 0):.2f}
            Reasoning: {claude_recommendation.get('reasoning', 'No reasoning provided')}
            
            Create a comprehensive trade plan including:
            1. Entry strategy (market order, limit order, etc.)
            2. Position sizing recommendations
            3. Risk management (stop loss, take profit)
            4. Trade management rules
            5. Exit strategy
            6. Contingency plans
            
            Return JSON format:
            {{
                "entry_strategy": {{
                    "order_type": "market/limit",
                    "entry_price": price,
                    "timing": "immediate/wait for pullback"
                }},
                "position_sizing": {{
                    "percentage_of_balance": 0.0-1.0,
                    "risk_per_trade": 0.0-1.0,
                    "max_position_size": amount
                }},
                "risk_management": {{
                    "stop_loss": price,
                    "take_profit": price,
                    "trailing_stop": true/false,
                    "max_loss_percent": 0.0-1.0
                }},
                "trade_management": {{
                    "monitoring_frequency": "continuous/5min/15min",
                    "adjustment_triggers": ["price_change", "time_based"],
                    "partial_exit_rules": [{{"profit_percent": 1.0, "exit_percent": 0.5}}]
                }},
                "exit_strategy": {{
                    "primary_exit": "take_profit/stop_loss",
                    "secondary_exits": ["trailing_stop", "time_based"],
                    "emergency_exit": "market_order"
                }},
                "contingency_plans": {{
                    "if_trend_reverses": "action",
                    "if_volume_drops": "action",
                    "if_news_breaks": "action"
                }},
                "confidence_boost": 0.0-1.0,
                "plan_quality": "low/medium/high"
            }}
            """
            
            logger.info(f" Sending GPT API request for {symbol}")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {Config.OPENROUTER_API_KEY}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://crypto-trading-bot.com',
                    'X-Title': 'Crypto Trading Bot'
                }
                
                payload = {
                    'model': 'openai/gpt-4o',
                    'messages': [
                        {
                            'role': 'user',
                            'content': plan_prompt
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1200
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=40)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if 'choices' in result and len(result['choices']) > 0:
                            content = result['choices'][0]['message']['content']
                            
                            logger.info(f" Received GPT response for {symbol}")
                            
                            # Parse JSON response
                            try:
                                plan_result = self.parse_plan_response(content)
                                plan_result['source'] = 'gpt_plan'
                                plan_result['timestamp'] = datetime.now().isoformat()
                                
                                confidence_boost = plan_result.get('confidence_boost', 0)
                                plan_quality = plan_result.get('plan_quality', 'low')
                                
                                logger.info(f" GPT plan generated for {symbol}: {plan_quality} quality, {confidence_boost:.2f} confidence boost")
                                return plan_result
                                
                            except Exception as e:
                                logger.error(f" Error parsing GPT response for {symbol}: {e}")
                                return self.create_empty_analysis_result(symbol, "gpt_plan")
                        else:
                            logger.warning(f" Empty GPT response for {symbol}")
                            return self.create_empty_analysis_result(symbol, "gpt_plan")
                    else:
                        logger.error(f" GPT API error for {symbol}: {response.status}")
                        return self.create_empty_analysis_result(symbol, "gpt_plan")
                        
        except Exception as e:
            logger.error(f" GPT analysis error for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "gpt_plan")
    
    def parse_analysis_response(self, content: str) -> Dict:
        """Parse Grok analysis response"""
        try:
            # Extract JSON from response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self.create_empty_analysis_result("UNKNOWN", "grok_sentiment")
        except Exception as e:
            logger.error(f" Error parsing analysis response: {e}")
            return self.create_empty_analysis_result("UNKNOWN", "grok_sentiment")
    
    def parse_claude_response(self, content: str) -> Dict:
        """Parse Claude analysis response"""
        return self.parse_analysis_response(content)
    
    def parse_plan_response(self, content: str) -> Dict:
        """Parse GPT plan response"""
        return self.parse_analysis_response(content)
    
    def create_empty_analysis_result(self, symbol: str, source: str) -> Dict:
        """Create empty analysis result when API fails"""
        logger.warning(f" Creating empty analysis result for {symbol} ({source})")
        return {
            'symbol': symbol,
            'source': source,
            'sentiment': 'neutral',
            'sentiment_score': 0.5,
            'technical_summary': 'Analysis not available',
            'support_levels': [],
            'resistance_levels': [],
            'risk_level': 'medium',
            'recommendation': 'HOLD',
            'confidence_score': 0.5,
            'reasoning': 'Analysis failed or not available',
            'timestamp': datetime.now().isoformat()
        }
    
    def create_local_analysis_result(self, symbol: str, market_data: Dict) -> Dict:
        """Create local analysis result when APIs are not available"""
        logger.info(f" Creating local analysis for {symbol}")
        
        try:
            current_price = market_data.get('current_price', 0)
            change_24h = market_data.get('change_24h', 0)
            prices = market_data.get('prices', [])
            
            if len(prices) < 20:
                logger.warning(f" Insufficient data for local analysis of {symbol}")
                return self.create_empty_analysis_result(symbol, "local")
            
            # Calculate basic indicators
            rsi = TechnicalIndicators.calculate_rsi(prices)
            ema_20 = TechnicalIndicators.calculate_ema(prices, 20)
            
            # Simple sentiment based on price action
            if change_24h > 2:
                sentiment = 'bullish'
                sentiment_score = 0.7
            elif change_24h < -2:
                sentiment = 'bearish'
                sentiment_score = 0.3
            else:
                sentiment = 'neutral'
                sentiment_score = 0.5
            
            # Simple recommendation based on RSI and trend
            if rsi < 30 and change_24h > 0:
                recommendation = 'BUY'
                confidence = 0.6
            elif rsi > 70 and change_24h < 0:
                recommendation = 'SELL'
                confidence = 0.6
            else:
                recommendation = 'HOLD'
                confidence = 0.5
            
            logger.info(f" Local analysis for {symbol}: {sentiment} sentiment, {recommendation} recommendation")
            
            return {
                'symbol': symbol,
                'source': 'local',
                'sentiment': sentiment,
                'sentiment_score': sentiment_score,
                'technical_summary': f'RSI: {rsi:.2f}, EMA20: ${ema_20:.2f}, 24h Change: {change_24h:.2f}%',
                'support_levels': [current_price * 0.95, current_price * 0.90],
                'resistance_levels': [current_price * 1.05, current_price * 1.10],
                'risk_level': 'medium',
                'recommendation': recommendation,
                'confidence_score': confidence,
                'reasoning': f'Local analysis based on RSI ({rsi:.2f}) and 24h change ({change_24h:.2f}%)',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f" Error in local analysis for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "local")
    
    async def run_ai_analysis_pipeline(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Run complete AI analysis pipeline"""
        logger.info(f" Starting AI analysis pipeline for {symbol}")
        
        try:
            # Check cache first
            cache_key = f"{symbol}_{int(time.time() / 300)}"  # 5-minute cache
            if cache_key in self.ai_analysis_cache:
                logger.info(f" Using cached analysis for {symbol}")
                return self.ai_analysis_cache[cache_key]
            
            # Step 1: Grok sentiment analysis
            logger.info(f"Step 1: Grok sentiment analysis for {symbol}")
            grok_result = await self.grok_sentiment_analysis(symbol, market_data)
            
            # Step 2: Claude deep analysis
            logger.info(f"Step 2: Claude deep analysis for {symbol}")
            claude_result = await self.claude_deep_analysis(market_data)
            
            # Step 3: GPT trade plan (if Claude analysis is good)
            gpt_result = None
            if claude_result.get('recommendation', {}).get('action') != 'HOLD':
                logger.info(f"Step 3: GPT trade plan for {symbol}")
                gpt_result = await self.gpt_trade_plan_generator(market_data, claude_result)
            else:
                logger.info(f"⏸ Skipping GPT plan for {symbol} (HOLD recommendation)")
            
            # Combine results
            logger.info(f" Combining analysis results for {symbol}")
            final_result = self.get_final_recommendation(grok_result, claude_result, gpt_result)
            
            # Cache the result
            self.ai_analysis_cache[cache_key] = final_result
            self.last_analysis_time[symbol] = time.time()
            
            logger.info(f" AI analysis pipeline completed for {symbol}")
            logger.info(f" Final recommendation: {final_result.get('final_recommendation', {}).get('action', 'HOLD')} with {final_result.get('combined_confidence', 0):.2f} confidence")
            
            return final_result
            
        except Exception as e:
            logger.error(f" Error in AI analysis pipeline for {symbol}: {e}")
            
            # Fallback to local analysis
            logger.info(f" Falling back to local analysis for {symbol}")
            local_result = self.create_local_analysis_result(symbol, market_data)
            
            return {
                'symbol': symbol,
                'grok_analysis': local_result,
                'claude_analysis': local_result,
                'gpt_refinement': None,
                'final_recommendation': {
                    'action': local_result['recommendation'],
                    'confidence': local_result['confidence_score'],
                    'reasoning': local_result['reasoning']
                },
                'combined_confidence': local_result['confidence_score'],
                'timestamp': datetime.now().isoformat(),
                'source': 'local_fallback'
            }
    
    def get_final_recommendation(self, grok_result: Dict, claude_result: Dict, gpt_result: Dict) -> Dict:
        """Combine all analysis results into final recommendation"""
        try:
            logger.info(" Combining analysis results into final recommendation")
            
            # Extract recommendations
            grok_action = grok_result.get('recommendation', 'HOLD')
            grok_confidence = grok_result.get('confidence_score', 0.5)
            
            claude_action = claude_result.get('recommendation', {}).get('action', 'HOLD')
            claude_confidence = claude_result.get('recommendation', {}).get('confidence', 0.5)
            
            # Weight the recommendations (Claude gets higher weight)
            grok_weight = 0.3
            claude_weight = 0.7
            
            # Calculate weighted confidence
            weighted_confidence = (grok_confidence * grok_weight) + (claude_confidence * claude_weight)
            
            # Determine final action (majority vote with confidence threshold)
            actions = [grok_action, claude_action]
            buy_count = actions.count('BUY')
            sell_count = actions.count('SELL')
            hold_count = actions.count('HOLD')
            
            if buy_count > sell_count and buy_count > hold_count and weighted_confidence > 0.6:
                final_action = 'BUY'
            elif sell_count > buy_count and sell_count > hold_count and weighted_confidence > 0.6:
                final_action = 'SELL'
            else:
                final_action = 'HOLD'
            
            # Create final recommendation
            final_recommendation = {
                'action': final_action,
                'confidence': weighted_confidence,
                'reasoning': f'Combined analysis: Grok ({grok_action}, {grok_confidence:.2f}), Claude ({claude_action}, {claude_confidence:.2f})'
            }
            
            logger.info(f" Final recommendation: {final_action} with {weighted_confidence:.2f} confidence")
            
            return {
                'symbol': grok_result.get('symbol', 'UNKNOWN'),
                'grok_analysis': grok_result,
                'claude_analysis': claude_result,
                'gpt_refinement': gpt_result,
                'final_recommendation': final_recommendation,
                'combined_confidence': weighted_confidence,
                'timestamp': datetime.now().isoformat(),
                'source': 'combined_ai'
            }
            
        except Exception as e:
            logger.error(f" Error combining analysis results: {e}")
            return {
                'symbol': 'UNKNOWN',
                'grok_analysis': grok_result,
                'claude_analysis': claude_result,
                'gpt_refinement': gpt_result,
                'final_recommendation': {
                    'action': 'HOLD',
                    'confidence': 0.5,
                    'reasoning': 'Error combining analysis results'
                },
                'combined_confidence': 0.5,
                'timestamp': datetime.now().isoformat(),
                'source': 'error'
            }
    
    def get_analysis_status(self, symbol: str) -> Dict:
        """Get analysis status for a symbol"""
        return {
            'symbol': symbol,
            'last_analysis': self.last_analysis_time.get(symbol),
            'cached': symbol in self.ai_analysis_cache,
            'status': self.analysis_status.get(symbol, 'idle')
        }
    
    def get_cached_analysis(self, symbol: str) -> Optional[Dict]:
        """Get cached analysis for a symbol"""
        return self.ai_analysis_cache.get(symbol)
    
    def clear_analysis_cache(self):
        """Clear the analysis cache"""
        logger.info(" Clearing AI analysis cache")
        self.ai_analysis_cache.clear()
        logger.info(" AI analysis cache cleared") 