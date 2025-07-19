"""
AI-powered trading analysis using multiple LLM models
"""
import aiohttp
import asyncio
import logging
import re
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
        self.news_sentiment_cache = {}  # Cache for news sentiment
        self.analysis_progress = {}
        
        logger.info(" AI Analysis Manager initialization complete!")
    
    async def get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for a symbol"""
        try:
            # Check cache first (cache for 15 minutes)
            cache_key = f"{symbol}_{int(time.time() / 900)}"
            if cache_key in self.news_sentiment_cache:
                return self.news_sentiment_cache[cache_key]
            
            # For now, return a simple news sentiment analysis
            # In a real implementation, this would fetch from news APIs
            coin_name = symbol.replace('USDT', '').lower()
            
            # Simulate news sentiment analysis
            import random
            sentiment_score = random.uniform(0.3, 0.7)  # Random sentiment between 0.3-0.7
            
            news_data = {
                'symbol': symbol,
                'sentiment': 'neutral',
                'sentiment_score': sentiment_score,
                'news_count': random.randint(5, 20),
                'positive_mentions': random.randint(0, 10),
                'negative_mentions': random.randint(0, 8),
                'summary': f"Mixed sentiment for {coin_name.upper()} with moderate trading activity",
                'timestamp': time.time()
            }
            
            # Determine sentiment based on score
            if sentiment_score > 0.6:
                news_data['sentiment'] = 'bullish'
            elif sentiment_score < 0.4:
                news_data['sentiment'] = 'bearish'
            
            # Cache the result
            self.news_sentiment_cache[cache_key] = news_data
            
            logger.info(f" News sentiment for {symbol}: {news_data['sentiment']} ({sentiment_score:.2f})")
            return news_data
            
        except Exception as e:
            logger.error(f" Error getting news sentiment for {symbol}: {e}")
            return {
                'symbol': symbol,
                'sentiment': 'neutral',
                'sentiment_score': 0.5,
                'news_count': 0,
                'summary': 'No news data available',
                'timestamp': time.time()
            }
        
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
    
    async def gpt_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """Perform independent analysis using GPT"""
        logger.info(f"Starting GPT analysis for {symbol}")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for GPT analysis")
            return self.create_empty_analysis_result(symbol, "gpt_analysis")
        
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
                return self.create_empty_analysis_result(symbol, "gpt_analysis")
            
            # Calculate indicators
            logger.info(f" Calculating technical indicators for {symbol}")
            rsi = TechnicalIndicators.calculate_rsi(prices)
            ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
            ema_26 = TechnicalIndicators.calculate_ema(prices, 26)
            macd = TechnicalIndicators.calculate_macd(prices)
            
            logger.info(f" Technical indicators for {symbol}: RSI={rsi:.2f}, EMA12=${ema_12:.2f}, EMA26=${ema_26:.2f}, MACD={macd['macd']:.4f}")
            
            analysis_prompt = f"""
            Perform a comprehensive trading analysis for {symbol} cryptocurrency.
            
            Current Market Data:
            - Current Price: ${current_price:,.2f}
            - 24h Change: {change_24h:.2f}%
            - 24h Volume: {volume_24h:,.0f}
            - RSI: {rsi:.2f}
            - EMA(12): ${ema_12:,.2f}
            - EMA(26): ${ema_26:,.2f}
            - MACD: {macd['macd']:.4f}
            
            Provide a detailed analysis including:
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
                            
                            logger.info(f" Received GPT response for {symbol}")
                            
                            # Parse JSON response
                            try:
                                analysis_result = self.parse_analysis_response(content)
                                analysis_result['source'] = 'gpt_analysis'
                                analysis_result['timestamp'] = datetime.now().isoformat()
                                
                                logger.info(f" GPT analysis completed for {symbol}: {analysis_result.get('sentiment', 'unknown')} sentiment, {analysis_result.get('recommendation', 'HOLD')} recommendation")
                                return analysis_result
                                
                            except Exception as e:
                                logger.error(f" Error parsing GPT response for {symbol}: {e}")
                                return self.create_empty_analysis_result(symbol, "gpt_analysis")
                        else:
                            logger.warning(f" Empty GPT response for {symbol}")
                            return self.create_empty_analysis_result(symbol, "gpt_analysis")
                    else:
                        logger.error(f" GPT API error for {symbol}: {response.status}")
                        return self.create_empty_analysis_result(symbol, "gpt_analysis")
                        
        except Exception as e:
            logger.error(f" GPT analysis error for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "gpt_analysis")
    
    async def gpt_final_recommendation(self, symbol: str, market_data: Dict, grok_result: Dict, claude_result: Dict, gpt_result: Dict, news_sentiment: Dict) -> Dict:
        """GPT makes final recommendation based on all three AI analyses and creates 30-minute trade setup"""
        logger.info(f"Starting GPT final recommendation for {symbol}")
        
        if not Config.OPENROUTER_API_KEY:
            logger.warning(" No OpenRouter API key available for GPT final recommendation")
            return self.create_empty_analysis_result(symbol, "gpt_final")
        
        try:
            current_price = market_data.get('current_price', 0)
            
            # Extract recommendations from all three AI models
            grok_action = grok_result.get('recommendation', 'HOLD')
            grok_confidence = float(grok_result.get('confidence_score', 0.5))
            grok_reasoning = grok_result.get('reasoning', 'No reasoning provided')
            
            claude_rec = claude_result.get('recommendation', {})
            if isinstance(claude_rec, dict):
                claude_action = claude_rec.get('action', 'HOLD')
                claude_confidence = float(claude_rec.get('confidence', 0.5))
                claude_reasoning = claude_rec.get('reasoning', 'No reasoning provided')
            else:
                claude_action = claude_rec if claude_rec in ['BUY', 'SELL', 'HOLD'] else 'HOLD'
                claude_confidence = 0.5
                claude_reasoning = 'No reasoning provided'
            
            gpt_action = gpt_result.get('recommendation', 'HOLD')
            gpt_confidence = float(gpt_result.get('confidence_score', 0.5))
            gpt_reasoning = gpt_result.get('reasoning', 'No reasoning provided')
            
            # News sentiment
            news_sentiment_text = news_sentiment.get('sentiment', 'neutral')
            news_sentiment_score = float(news_sentiment.get('sentiment_score', 0.5))
            
            final_prompt = f"""
            You are the final decision maker for {symbol} cryptocurrency trading. You have received analysis from three AI models and need to make a final recommendation for the next 30 minutes.
            
            Current Price: ${current_price:,.2f}
            
            AI Model Analyses:
            
            1. GROK Analysis:
               - Recommendation: {grok_action}
               - Confidence: {grok_confidence:.2f}
               - Reasoning: {grok_reasoning}
            
            2. CLAUDE Analysis:
               - Recommendation: {claude_action}
               - Confidence: {claude_confidence:.2f}
               - Reasoning: {claude_reasoning}
            
            3. GPT Analysis:
               - Recommendation: {gpt_action}
               - Confidence: {gpt_confidence:.2f}
               - Reasoning: {gpt_reasoning}
            
            4. News Sentiment:
               - Sentiment: {news_sentiment_text}
               - Score: {news_sentiment_score:.2f}
            
            IMPORTANT DECISION RULES:
            1. If ANY AI model has confidence >= 0.70 and recommends BUY/SELL, strongly consider that recommendation
            2. If multiple AIs agree on BUY/SELL with confidence >= 0.65, prioritize their consensus
            3. Only recommend HOLD if all AIs have low confidence (< 0.60) or disagree significantly
            4. News sentiment should support, not override, strong AI signals
            5. Be decisive - avoid defaulting to HOLD when there are clear signals
            
            Based on all three AI analyses and news sentiment, provide:
            
            1. Final trading recommendation for the next 30 minutes
            2. Confidence level in your decision
            3. Detailed reasoning for your choice
            4. Specific trade setup for the next 30 minutes including:
               - Entry strategy (market/limit order, timing)
               - Position sizing
               - Risk management (stop loss, take profit)
               - Key levels to watch
               - Exit strategy within 30 minutes
            
            Return JSON format:
            {{
                "final_recommendation": {{
                    "action": "BUY/SELL/HOLD",
                    "confidence": 0.0-1.0,
                    "reasoning": "detailed explanation of final decision",
                    "timeframe": "30 minutes"
                }},
                "trade_setup": {{
                    "entry_strategy": {{
                        "order_type": "market/limit",
                        "entry_price": price,
                        "timing": "immediate/wait for pullback/specific condition"
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
                    "key_levels": {{
                        "support_levels": [price1, price2],
                        "resistance_levels": [price1, price2],
                        "critical_levels": [price1, price2]
                    }},
                    "exit_strategy": {{
                        "primary_exit": "take_profit/stop_loss/time_based",
                        "secondary_exits": ["trailing_stop", "time_based"],
                        "emergency_exit": "market_order",
                        "max_hold_time": "30 minutes"
                    }},
                    "monitoring": {{
                        "check_frequency": "every 5 minutes",
                        "key_indicators": ["price", "volume", "momentum"],
                        "alert_triggers": ["price_breakout", "volume_spike", "time_remaining"]
                    }}
                }},
                "ai_consensus": {{
                    "grok_agreement": true/false,
                    "claude_agreement": true/false,
                    "gpt_agreement": true/false,
                    "consensus_level": "high/medium/low"
                }}
            }}
            """
            
            logger.info(f" Sending GPT final recommendation request for {symbol}")
            
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
                            'content': final_prompt
                        }
                    ],
                    'temperature': 0.1,
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
                            
                            logger.info(f" Received GPT final recommendation for {symbol}")
                            
                            # Parse JSON response
                            try:
                                final_result = self.parse_analysis_response(content)
                                final_result['source'] = 'gpt_final'
                                final_result['timestamp'] = datetime.now().isoformat()
                                
                                # Extract final recommendation
                                final_rec = final_result.get('final_recommendation', {})
                                action = final_rec.get('action', 'HOLD')
                                confidence = float(final_rec.get('confidence', 0.5))
                                
                                logger.info(f" GPT final recommendation for {symbol}: {action} with {confidence:.2f} confidence (30min timeframe)")
                                return final_result
                                
                            except Exception as e:
                                logger.error(f" Error parsing GPT final recommendation for {symbol}: {e}")
                                return self.create_empty_analysis_result(symbol, "gpt_final")
                        else:
                            logger.warning(f" Empty GPT final recommendation for {symbol}")
                            return self.create_empty_analysis_result(symbol, "gpt_final")
                    else:
                        logger.error(f" GPT final recommendation API error for {symbol}: {response.status}")
                        return self.create_empty_analysis_result(symbol, "gpt_final")
                        
        except asyncio.TimeoutError:
            logger.error(f" GPT final recommendation timeout for {symbol}")
            return self.create_empty_analysis_result(symbol, "gpt_final")
        except Exception as e:
            logger.error(f" GPT final recommendation error for {symbol}: {e}")
            return self.create_empty_analysis_result(symbol, "gpt_final")
    
    def parse_analysis_response(self, content: str) -> Dict:
        """Parse Grok analysis response"""
        try:
            # Extract JSON from response
            import json
            import re
            
            # Log the raw content for debugging
            logger.debug(f" Raw AI response content: {content[:200]}...")
            
            # Try to find JSON within a markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug(f" Extracted JSON from markdown: {json_str[:200]}...")
                return self._clean_and_parse_json(json_str)
            
            # If not in a markdown block, try to find a standalone JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f" Extracted standalone JSON: {json_str[:200]}...")
                return self._clean_and_parse_json(json_str)
            else:
                logger.warning(f" No JSON found in response: {content[:200]}...")
                return self.create_empty_analysis_result("UNKNOWN", "grok_sentiment")
        except Exception as e:
            logger.error(f" Error parsing analysis response: {e}")
            logger.error(f" Raw content that failed to parse: {content[:500]}...")
            return self.create_empty_analysis_result("UNKNOWN", "grok_sentiment")
    
    def _clean_and_parse_json(self, json_str: str) -> Dict:
        """Clean and parse JSON string, handling common AI response issues"""
        import json
        
        try:
            # First, try to parse as-is
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f" Initial JSON parsing failed, attempting to clean: {e}")
            logger.debug(f" Raw JSON content that failed: {json_str[:500]}...")
            
            # Clean up common issues in AI-generated JSON
            cleaned_json = json_str
            
            # Remove commas from numbers (e.g., 118,000.00 -> 118000.00)
            cleaned_json = re.sub(r'(\d+),(\d{3})', r'\1\2', cleaned_json)
            
            # Fix unquoted property names (e.g., {key: value} -> {"key": value})
            cleaned_json = re.sub(r'(\s*)(\w+)(\s*):(\s*)', r'\1"\2"\3:\4', cleaned_json)
            
            # Fix trailing commas in objects and arrays
            cleaned_json = re.sub(r',(\s*[}\]])', r'\1', cleaned_json)
            
            # Fix single quotes to double quotes
            cleaned_json = cleaned_json.replace("'", '"')
            
            # Fix missing commas between properties
            cleaned_json = re.sub(r'"\s*\n\s*"', '",\n"', cleaned_json)
            
            # Fix missing commas between object properties
            cleaned_json = re.sub(r'}\s*\n\s*"', '},\n"', cleaned_json)
            
            # Remove any non-printable characters
            cleaned_json = ''.join(char for char in cleaned_json if char.isprintable() or char in '\n\r\t')
            
            try:
                logger.debug(f" Attempting to parse cleaned JSON: {cleaned_json[:200]}...")
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e2:
                logger.error(f" Failed to parse even after cleaning: {e2}")
                logger.error(f" Cleaned JSON: {cleaned_json[:500]}...")
                # Return a fallback result instead of crashing
                return {
                    'recommendation': 'HOLD',
                    'confidence_score': 0.5,
                    'sentiment': 'neutral',
                    'reasoning': 'Unable to parse AI response - using fallback recommendation'
                }
    
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
    
    async def get_dummy_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """Get analysis from dummy server for testing purposes"""
        import aiohttp
        import random
        
        try:
            logger.info(f" Fetching dummy analysis for {symbol}")
            
            # Try to get from dummy HTTP server first
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'http://localhost:5001/api/analysis/{symbol}', timeout=5) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f" Retrieved dummy analysis from HTTP server for {symbol}")
                            return result
            except Exception as e:
                logger.warning(f" Could not connect to dummy HTTP server: {e}")
            
            # Fallback to inline dummy data generation
            logger.info(f" Generating inline dummy analysis for {symbol}")
            return self.generate_inline_dummy_analysis(symbol, market_data)
            
        except Exception as e:
            logger.error(f" Error getting dummy analysis for {symbol}: {e}")
            return self.create_local_analysis_result(symbol, market_data)
    
    def generate_inline_dummy_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """Generate dummy analysis data inline"""
        import random
        
        current_price = market_data.get('current_price', 50000)
        
        # Generate fake analysis data
        sentiment_score = random.uniform(0.3, 0.8)
        rsi = random.uniform(25, 75)
        
        if rsi > 70:
            sentiment = 'bearish'
            recommendation = random.choice(['SELL', 'HOLD'])
            confidence = random.uniform(0.6, 0.8)
        elif rsi < 30:
            sentiment = 'bullish'
            recommendation = random.choice(['BUY', 'HOLD'])
            confidence = random.uniform(0.6, 0.8)
        else:
            sentiment = 'neutral'
            recommendation = random.choice(['HOLD', 'BUY', 'SELL'])
            confidence = random.uniform(0.5, 0.7)
        
        return {
            'symbol': symbol,
            'grok_analysis': {
                'sentiment': sentiment,
                'recommendation': recommendation,
                'confidence_score': confidence,
                'reasoning': f'Dummy analysis shows {sentiment} trend for {symbol}'
            },
            'claude_analysis': {
                'recommendation': {
                    'action': recommendation,
                    'confidence': confidence,
                    'reasoning': f'Dummy Claude analysis for {symbol}'
                }
            },
            'gpt_refinement': {
                'recommendation': recommendation,
                'confidence_score': confidence
            },
            'final_recommendation': {
                'action': recommendation,
                'confidence': confidence,
                'reasoning': f'DUMMY: Combined analysis shows {sentiment} bias for {symbol}',
                'timeframe': '30 minutes'
            },
            'combined_confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'source': 'dummy_inline'
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
        """Run the complete AI analysis pipeline for a symbol - SUPPORTS REAL/FAKE API SWITCHING"""
        try:
            api_mode = Config.API_MODE
            logger.info(f" Starting AI analysis pipeline for {symbol} (Mode: {api_mode.upper()})")
            
            # Check if we have recent analysis (within cache time)
            current_time = datetime.now()
            last_analysis = self.last_analysis_time.get(symbol)
            cache_time = 30 if api_mode == 'fake' else 60  # Shorter cache for fake mode
            
            if last_analysis:
                time_diff = (current_time - last_analysis).total_seconds()
                if time_diff < cache_time:
                    logger.info(f" Using cached analysis for {symbol}")
                    cached_result = self.ai_analysis_cache.get(symbol)
                    if cached_result:
                        # Return cached result but ensure confidence is preserved
                        final_rec = cached_result.get('final_recommendation', {})
                        if final_rec:
                            action = final_rec.get('action', 'HOLD')
                            confidence = float(final_rec.get('confidence', 0.5))
                            logger.info(f" Cached final recommendation: {action} with {confidence:.2f} confidence")
                        return cached_result
            
            # Choose API based on mode
            if api_mode == 'fake':
                logger.info(f" Using fake analysis server for {symbol}")
                result = await self.get_dummy_analysis(symbol, market_data)
            else:
                logger.info(f" Using real AI analysis pipeline for {symbol}")
                result = await self.run_real_ai_analysis(symbol, market_data)
            
            # Update cache and timestamp
            self.ai_analysis_cache[symbol] = result
            self.last_analysis_time[symbol] = current_time
            
            # Log final result
            final_rec = result.get('final_recommendation', {})
            action = final_rec.get('action', 'HOLD')
            confidence = float(final_rec.get('confidence', 0.5))
            logger.info(f" {api_mode.upper()} Final recommendation: {action} with {confidence:.2f} confidence")
            
            return result
            
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
    
    async def run_real_ai_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """Run the real AI analysis pipeline using actual APIs"""
        try:
            # Step 0: News sentiment analysis
            logger.info(f"Step 0: Running news sentiment analysis for {symbol}")
            news_sentiment = await self.get_news_sentiment(symbol)
            
            # Step 1: Grok sentiment analysis
            logger.info(f"Step 1: Running Grok sentiment analysis for {symbol}")
            grok_result = await self.grok_sentiment_analysis(symbol, market_data)
            
            # Step 2: Claude deep analysis
            logger.info(f"Step 2: Running Claude deep analysis for {symbol}")
            claude_result = await self.claude_deep_analysis(market_data)
            
            # Step 3: GPT independent analysis
            logger.info(f"Step 3: Running GPT independent analysis for {symbol}")
            gpt_result = await self.gpt_analysis(symbol, market_data)
            
            # Step 4: GPT final recommendation
            logger.info(f"Step 4: Running GPT final recommendation for {symbol}")
            final_result = await self.gpt_final_recommendation(symbol, market_data, grok_result, claude_result, gpt_result, news_sentiment)
            
            return final_result
            
        except Exception as e:
            logger.error(f" Error in real AI analysis for {symbol}: {e}")
            # Fall back to local analysis
            return self.create_local_analysis_result(symbol, market_data)
    
    def get_final_recommendation(self, grok_result: Dict, claude_result: Dict, gpt_result: Dict, news_sentiment: Dict) -> Dict:
        """Combine all analysis results into final recommendation"""
        try:
            logger.info(" Combining analysis results into final recommendation")
            
            # Ensure all results are dictionaries, handle None values
            if grok_result is None or not isinstance(grok_result, dict):
                grok_result = {'recommendation': 'HOLD', 'confidence_score': 0.5}
            if claude_result is None or not isinstance(claude_result, dict):
                claude_result = {'recommendation': {'action': 'HOLD', 'confidence': 0.5}}
            if gpt_result is None or not isinstance(gpt_result, dict):
                gpt_result = {'recommendation': 'HOLD', 'confidence_score': 0.5}
            if news_sentiment is None or not isinstance(news_sentiment, dict):
                news_sentiment = {'sentiment': 'neutral', 'sentiment_score': 0.5}
            
            # Extract recommendations
            grok_action = grok_result.get('recommendation', 'HOLD')
            grok_confidence = float(grok_result.get('confidence_score', 0.5))
            
            claude_rec = claude_result.get('recommendation', {})
            if isinstance(claude_rec, dict):
                claude_action = claude_rec.get('action', 'HOLD')
                claude_confidence = float(claude_rec.get('confidence', 0.5))
            else:
                claude_action = claude_rec if claude_rec in ['BUY', 'SELL', 'HOLD'] else 'HOLD'
                claude_confidence = 0.5
            
            # Extract news sentiment info
            news_sentiment_score = float(news_sentiment.get('sentiment_score', 0.5))
            news_sentiment_text = news_sentiment.get('sentiment', 'neutral')
            
            # Weight the recommendations (Claude gets higher weight, news sentiment provides boost/reduction)
            grok_weight = 0.25
            claude_weight = 0.65
            news_weight = 0.1
            
            # Calculate weighted confidence with news sentiment factor
            weighted_confidence = (grok_confidence * grok_weight) + (claude_confidence * claude_weight) + (news_sentiment_score * news_weight)
            
            # Determine final action (prioritize high-confidence signals over majority vote)
            actions = [grok_action, claude_action]
            buy_count = actions.count('BUY')
            sell_count = actions.count('SELL')
            hold_count = actions.count('HOLD')
            
            # Apply news sentiment influence
            sentiment_boost = 0
            if news_sentiment_text == 'bullish' and news_sentiment_score > 0.6:
                sentiment_boost = 0.1  # Boost BUY signals
            elif news_sentiment_text == 'bearish' and news_sentiment_score < 0.4:
                sentiment_boost = -0.1  # Boost SELL signals
            
            final_confidence = weighted_confidence + sentiment_boost
            
            # NEW LOGIC: Prioritize high-confidence signals
            # Debug logging to understand the decision
            logger.info(f" Decision factors - Claude: {claude_action} ({claude_confidence:.2f}), Grok: {grok_action} ({grok_confidence:.2f}), Final confidence: {final_confidence:.2f}")
            
            # If Claude has high confidence (>0.7) and recommends BUY/SELL, use that
            if claude_confidence > 0.7 and claude_action in ['BUY', 'SELL'] and final_confidence > 0.65:
                final_action = claude_action
                logger.info(f" Using Claude's high-confidence recommendation: {claude_action} ({claude_confidence:.2f})")
            # If Grok has high confidence (>0.7) and recommends BUY/SELL, use that  
            elif grok_confidence > 0.7 and grok_action in ['BUY', 'SELL'] and final_confidence > 0.65:
                final_action = grok_action
                logger.info(f" Using Grok's high-confidence recommendation: {grok_action} ({grok_confidence:.2f})")
            # Otherwise, use majority vote with confidence threshold
            elif buy_count > sell_count and buy_count > hold_count and final_confidence > 0.65:
                final_action = 'BUY'
                logger.info(f" Using majority vote: BUY (count: {buy_count})")
            elif sell_count > buy_count and sell_count > hold_count and final_confidence > 0.65:
                final_action = 'SELL'
                logger.info(f" Using majority vote: SELL (count: {sell_count})")
            else:
                final_action = 'HOLD'
                logger.info(f" Defaulting to HOLD (confidence: {final_confidence:.2f}, buy: {buy_count}, sell: {sell_count}, hold: {hold_count})")
            
            # Create final recommendation
            final_recommendation = {
                'action': final_action,
                'confidence': final_confidence,
                'reasoning': f'Combined analysis: Grok ({grok_action}, {grok_confidence:.2f}), Claude ({claude_action}, {claude_confidence:.2f}), News ({news_sentiment_text}, {news_sentiment_score:.2f})'
            }
            
            logger.info(f" Final recommendation: {final_action} with {final_confidence:.2f} confidence (News: {news_sentiment_text})")
            
            return {
                'symbol': grok_result.get('symbol', 'UNKNOWN'),
                'grok_analysis': grok_result,
                'claude_analysis': claude_result,
                'gpt_refinement': gpt_result,
                'news_sentiment': news_sentiment,
                'final_recommendation': final_recommendation,
                'combined_confidence': final_confidence,
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
                'news_sentiment': news_sentiment or {'sentiment': 'neutral', 'sentiment_score': 0.5},
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