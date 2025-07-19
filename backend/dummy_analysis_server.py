"""
Dummy AI Analysis API Server for Testing
Creates fake analysis data matching the real API format
"""
import asyncio
import websockets
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, List
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DummyAnalysisServer:
    """Dummy analysis server that returns fake but realistic analysis data"""
    
    def __init__(self, port=8766):  # Changed to 8766 to avoid conflict
        self.port = port
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOGEUSDT']
        self.running = False
        
    def generate_fake_analysis(self, symbol: str) -> Dict:
        """Generate fake analysis data matching real API format"""
        
        # Generate realistic price data
        base_price = {
            'BTCUSDT': 45000 + random.uniform(-5000, 5000),
            'ETHUSDT': 2800 + random.uniform(-300, 300),
            'ADAUSDT': 0.45 + random.uniform(-0.1, 0.1),
            'SOLUSDT': 95 + random.uniform(-20, 20),
            'DOGEUSDT': 0.08 + random.uniform(-0.02, 0.02)
        }.get(symbol, 100 + random.uniform(-10, 10))
        
        # Generate fake technical indicators
        rsi = random.uniform(25, 75)
        macd = random.uniform(-0.5, 0.5)
        ema_20 = base_price * random.uniform(0.98, 1.02)
        volatility = random.uniform(0.02, 0.08)
        
        # Generate sentiment based on indicators
        sentiment_score = random.uniform(0.3, 0.8)
        if rsi > 70:
            sentiment = 'bearish'
            sentiment_score = random.uniform(0.2, 0.4)
        elif rsi < 30:
            sentiment = 'bullish'
            sentiment_score = random.uniform(0.6, 0.8)
        else:
            sentiment = 'neutral'
            sentiment_score = random.uniform(0.4, 0.6)
        
        # Generate recommendation based on sentiment
        recommendations = ['BUY', 'SELL', 'HOLD']
        if sentiment == 'bullish':
            recommendation = random.choice(['BUY', 'BUY', 'HOLD'])
            confidence = random.uniform(0.65, 0.85)
        elif sentiment == 'bearish':
            recommendation = random.choice(['SELL', 'SELL', 'HOLD'])
            confidence = random.uniform(0.65, 0.85)
        else:
            recommendation = random.choice(['HOLD', 'HOLD', 'BUY', 'SELL'])
            confidence = random.uniform(0.45, 0.65)
        
        # Generate support/resistance levels
        support_levels = [
            base_price * 0.95,
            base_price * 0.90
        ]
        resistance_levels = [
            base_price * 1.05,
            base_price * 1.10
        ]
        
        # Create Grok analysis
        grok_analysis = {
            'symbol': symbol,
            'source': 'grok_sentiment',
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'technical_summary': f'RSI: {rsi:.2f}, MACD: {macd:.4f}, Strong {sentiment} signals detected',
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'risk_level': random.choice(['low', 'medium', 'high']),
            'recommendation': recommendation,
            'confidence_score': confidence,
            'reasoning': f'Based on RSI ({rsi:.2f}) and MACD ({macd:.4f}), showing {sentiment} trend with {confidence:.2f} confidence',
            'timestamp': datetime.now().isoformat()
        }
        
        # Create Claude analysis (more detailed)
        claude_analysis = {
            'symbol': symbol,
            'source': 'claude_deep',
            'trend_analysis': {
                'short_term': f'{sentiment} trend with momentum indicators showing {sentiment} bias',
                'medium_term': f'Price action suggests {sentiment} continuation pattern',
                'long_term': f'Overall market structure remains {sentiment} leaning'
            },
            'momentum': {
                'rsi_interpretation': f'RSI at {rsi:.2f} indicates {"oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"} conditions',
                'macd_interpretation': f'MACD at {macd:.4f} shows {"bullish" if macd > 0 else "bearish"} momentum',
                'overall_momentum': sentiment
            },
            'volatility': {
                'current_level': 'medium' if volatility < 0.05 else 'high',
                'bollinger_position': random.choice(['above', 'below', 'within']) + ' bands',
                'atr_interpretation': f'ATR at {volatility:.4f} indicates {"low" if volatility < 0.03 else "high"} volatility'
            },
            'levels': {
                'support': support_levels,
                'resistance': resistance_levels
            },
            'risk_reward': {
                'risk_level': random.choice(['low', 'medium', 'high']),
                'reward_potential': random.choice(['low', 'medium', 'high']),
                'risk_reward_ratio': random.uniform(1.5, 3.0)
            },
            'recommendation': {
                'action': recommendation,
                'confidence': confidence,
                'reasoning': f'Technical analysis shows {sentiment} bias with {confidence:.2f} confidence',
                'entry_price': base_price,
                'stop_loss': base_price * (0.95 if recommendation == 'BUY' else 1.05),
                'take_profit': base_price * (1.08 if recommendation == 'BUY' else 0.92)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Create GPT analysis
        gpt_analysis = {
            'symbol': symbol,
            'source': 'gpt_analysis',
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'technical_summary': f'Comprehensive analysis shows {sentiment} trend with {confidence:.2f} confidence',
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'risk_level': random.choice(['low', 'medium', 'high']),
            'recommendation': recommendation,
            'confidence_score': confidence,
            'reasoning': f'Market structure analysis indicates {sentiment} bias with technical confluences',
            'timestamp': datetime.now().isoformat()
        }
        
        # Create news sentiment
        news_sentiment = {
            'symbol': symbol,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'news_count': random.randint(5, 25),
            'positive_mentions': random.randint(2, 12),
            'negative_mentions': random.randint(1, 8),
            'summary': f'Market sentiment for {symbol.replace("USDT", "")} shows {sentiment} bias based on recent news',
            'timestamp': time.time()
        }
        
        # Create final recommendation (GPT final decision)
        final_recommendation = {
            'action': recommendation,
            'confidence': confidence,
            'reasoning': f'Combined analysis from multiple AI models shows {sentiment} consensus with {confidence:.2f} confidence',
            'timeframe': '30 minutes'
        }
        
        # Create trade setup
        trade_setup = {
            'entry_strategy': {
                'order_type': 'market',
                'entry_price': base_price,
                'timing': 'immediate'
            },
            'position_sizing': {
                'percentage_of_balance': 0.1,
                'risk_per_trade': 0.02,
                'max_position_size': 1000
            },
            'risk_management': {
                'stop_loss': base_price * (0.95 if recommendation == 'BUY' else 1.05),
                'take_profit': base_price * (1.08 if recommendation == 'BUY' else 0.92),
                'trailing_stop': random.choice([True, False]),
                'max_loss_percent': 0.02
            },
            'key_levels': {
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'critical_levels': [base_price * 0.98, base_price * 1.02]
            },
            'exit_strategy': {
                'primary_exit': 'take_profit',
                'secondary_exits': ['trailing_stop', 'time_based'],
                'emergency_exit': 'market_order',
                'max_hold_time': '30 minutes'
            },
            'monitoring': {
                'check_frequency': 'every 5 minutes',
                'key_indicators': ['price', 'volume', 'momentum'],
                'alert_triggers': ['price_breakout', 'volume_spike', 'time_remaining']
            }
        }
        
        # Create AI consensus
        ai_consensus = {
            'grok_agreement': random.choice([True, False]),
            'claude_agreement': random.choice([True, False]),
            'gpt_agreement': random.choice([True, False]),
            'consensus_level': random.choice(['high', 'medium', 'low'])
        }
        
        # Return complete analysis matching real API format
        return {
            'symbol': symbol,
            'grok_analysis': grok_analysis,
            'claude_analysis': claude_analysis,
            'gpt_refinement': gpt_analysis,
            'news_sentiment': news_sentiment,
            'final_recommendation': final_recommendation,
            'trade_setup': trade_setup,
            'ai_consensus': ai_consensus,
            'combined_confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'source': 'dummy_api'
        }
    
    async def handle_request(self, websocket, path):
        """Handle incoming WebSocket requests"""
        logger.info(f"New connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    action = data.get('action')
                    
                    if action == 'get_analysis':
                        symbol = data.get('symbol', 'BTCUSDT')
                        logger.info(f"Generating fake analysis for {symbol}")
                        
                        # Simulate API delay
                        await asyncio.sleep(random.uniform(0.5, 2.0))
                        
                        analysis = self.generate_fake_analysis(symbol)
                        
                        response = {
                            'type': 'analysis_result',
                            'symbol': symbol,
                            'analysis': analysis,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps(response))
                        logger.info(f"Sent fake analysis for {symbol}: {analysis['final_recommendation']['action']} with {analysis['combined_confidence']:.2f} confidence")
                        
                    elif action == 'ping':
                        await websocket.send(json.dumps({'type': 'pong'}))
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received")
                    await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid JSON'}))
                except Exception as e:
                    logger.error(f"Error handling request: {e}")
                    await websocket.send(json.dumps({'type': 'error', 'message': str(e)}))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed from {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
    
    async def start_server(self):
        """Start the dummy analysis server with port conflict resolution"""
        self.running = True
        original_port = self.port
        max_port_attempts = 10
        
        for attempt in range(max_port_attempts):
            try:
                logger.info(f"Attempting to start dummy analysis server on port {self.port} (attempt {attempt + 1}/{max_port_attempts})")
                
                server = await websockets.serve(
                    self.handle_request,
                    "localhost",
                    self.port,
                    ping_interval=20,
                    ping_timeout=10
                )
                
                logger.info(f" Dummy analysis server running on ws://localhost:{self.port}")
                
                try:
                    await server.wait_closed()
                except Exception as e:
                    logger.error(f"Server error: {e}")
                    self.running = False
                break
                    
            except OSError as e:
                if e.errno == 10048:  # Port already in use
                    logger.warning(f"Port {self.port} is already in use, trying port {self.port + 1}")
                    self.port += 1
                    if attempt == max_port_attempts - 1:
                        logger.error(f"Failed to find available port after {max_port_attempts} attempts")
                        self.running = False
                        return
                    continue
                else:
                    logger.error(f"Failed to start server: {e}")
                    self.running = False
                    return
    
    def stop_server(self):
        """Stop the dummy analysis server"""
        self.running = False
        logger.info("Stopping dummy analysis server")

# Simple HTTP server for testing
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

class DummyHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith('/api/analysis/'):
                symbol = self.path.split('/')[-1].upper()
                dummy_server = DummyAnalysisServer()
                analysis = dummy_server.generate_fake_analysis(symbol)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(analysis).encode())
                
            elif self.path == '/api/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'healthy', 'server': 'dummy_analysis'}).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        logger.info(f"HTTP: {format % args}")

def run_http_server():
    """Run HTTP server in a separate thread with port conflict resolution"""
    port = 5001
    max_attempts = 10
    
    for attempt in range(max_attempts):
        try:
            server = HTTPServer(('localhost', port), DummyHTTPHandler)
            logger.info(f" HTTP server running on http://localhost:{port}")
            server.serve_forever()
            break
        except OSError as e:
            if e.errno == 10048:  # Port already in use
                logger.warning(f"Port {port} is in use, trying {port + 1}")
                port += 1
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to find available HTTP port after {max_attempts} attempts")
                    break
                continue
            else:
                logger.error(f"Failed to start HTTP server: {e}")
                break

if __name__ == "__main__":
    # Start HTTP server in background
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start WebSocket server
    asyncio.run(DummyAnalysisServer().start_server())