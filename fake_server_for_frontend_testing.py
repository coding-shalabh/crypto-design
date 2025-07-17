#!/usr/bin/env python3
"""
Fake WebSocket Server for Frontend Testing
==========================================

This server simulates the exact backend behavior expected by the frontend,
sending properly formatted messages that match the frontend's expectations.

Based on FRONTEND_FLOW_DIAGRAM.txt analysis:
- Handles all expected message types
- Sends properly formatted JSON responses
- Simulates real-time data updates
- Matches frontend data structures exactly
"""

import asyncio
import json
import logging
import random
import time
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FakeTradingServer:
    def __init__(self):
        # WebSocket clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Simulated data state
        self.paper_balance = 100000.0
        self.positions = {}
        self.recent_trades = []
        self.price_cache = {}
        self.crypto_data = {}
        self.ai_insights = None
        
        # Bot state
        self.bot_enabled = False
        self.bot_start_time = None
        self.bot_config = {
            'max_trades_per_day': 10,
            'trade_amount_usdt': 50,
            'profit_target_usd': 2,
            'stop_loss_usd': 1,
            'trailing_enabled': True,
            'trailing_trigger_usd': 1,
            'trailing_distance_usd': 0.5,
            'trade_interval_secs': 60,
            'max_concurrent_trades': 3,
            'cooldown_secs': 300,
            'allowed_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            'ai_confidence_threshold': 0.75,
            'run_time_minutes': 180,
            'test_mode': False,
            'risk_per_trade_percent': 1.0,
            'slippage_tolerance_percent': 0.1,
            'signal_sources': ['gpt', 'claude'],
            'manual_approval_mode': False
        }
        
        # Crypto symbols for testing
        self.crypto_symbols = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC',
            'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'VET', 'FIL'
        ]
        
        # Initialize fake data
        self._initialize_fake_data()
        
        # Background tasks
        self.background_tasks = []
        self.running = False
        
    def _initialize_fake_data(self):
        """Initialize fake data structures"""
        # Initialize price cache
        base_prices = {
            'BTC': 45000, 'ETH': 3000, 'BNB': 400, 'ADA': 0.5,
            'SOL': 100, 'DOT': 7, 'AVAX': 25, 'MATIC': 0.8,
            'LINK': 15, 'UNI': 8, 'ATOM': 12, 'LTC': 150,
            'BCH': 250, 'XLM': 0.3, 'VET': 0.05, 'FIL': 5
        }
        
        for symbol in self.crypto_symbols:
            base_price = base_prices.get(symbol, 10)
            current_price = base_price * (1 + random.uniform(-0.1, 0.1))
            
            self.price_cache[symbol] = {
                'symbol': symbol,
                'price': round(current_price, 4),
                'change_24h': round(random.uniform(-15, 15), 2),
                'volume_24h': round(random.uniform(1000000, 100000000), 2),
                'market_cap': round(current_price * random.uniform(1000000, 100000000), 2),
                'timestamp': time.time()
            }
        
        # Initialize crypto data (matches frontend expectations)
        for symbol in self.crypto_symbols:
            price_data = self.price_cache[symbol]
            
            self.crypto_data[symbol.lower()] = {
                'id': symbol.lower(),
                'symbol': symbol,
                'name': f'{symbol} Token',
                'image': f'https://assets.coingecko.com/coins/images/1/large/{symbol.lower()}.png',
                'current_price': price_data['price'],
                'market_cap': price_data['market_cap'],
                'market_cap_rank': random.randint(1, 100),
                'fully_diluted_valuation': price_data['market_cap'] * 1.1,
                'total_volume': price_data['volume_24h'],
                'high_24h': price_data['price'] * 1.05,
                'low_24h': price_data['price'] * 0.95,
                'price_change_24h': price_data['change_24h'],
                'price_change_percentage_24h': price_data['change_24h'],
                'market_cap_change_24h': price_data['market_cap'] * 0.02,
                'market_cap_change_percentage_24h': 2.0,
                'circulating_supply': price_data['market_cap'] / price_data['price'],
                'total_supply': price_data['market_cap'] / price_data['price'] * 1.1,
                'max_supply': None,
                'ath': price_data['price'] * 2,
                'ath_change_percentage': -50.0,
                'ath_date': '2021-11-01T00:00:00.000Z',
                'atl': price_data['price'] * 0.1,
                'atl_change_percentage': 900.0,
                'atl_date': '2020-01-01T00:00:00.000Z',
                'roi': None,
                'last_updated': datetime.now().isoformat()
            }
        
        # Add some fake trades
        self._add_fake_trades()
        
        # Add some fake positions
        self._add_fake_positions()
        
        logger.info("✅ Fake data initialized successfully")
    
    def _add_fake_trades(self):
        """Add some fake trade history"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        for i in range(25):  # More trades for better history
            symbol = random.choice(symbols)
            direction = random.choice(['BUY', 'SELL'])
            amount = round(random.uniform(0.01, 0.5), 4)
            # Extract base symbol for price lookup
            base_symbol = symbol.replace('USDT', '')
            price = self.price_cache[base_symbol]['price']
            value = amount * price
            
            trade = {
                'trade_id': f"trade_{int(time.time() - i * 3600)}_{symbol}",
                'symbol': symbol,
                'direction': direction,
                'amount': amount,
                'price': price,
                'value': value,
                'timestamp': time.time() - i * 3600,
                'trade_type': random.choice(['MANUAL', 'BOT']),
                'status': 'executed',
                'pnl': round(random.uniform(-100, 200), 2) if direction == 'SELL' else 0
            }
            self.recent_trades.append(trade)
    
    def _add_fake_positions(self):
        """Add some fake open positions"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        for symbol in symbols:
            # Extract base symbol for price lookup
            base_symbol = symbol.replace('USDT', '')
            amount = round(random.uniform(0.01, 0.2), 4)
            entry_price = self.price_cache[base_symbol]['price'] * 0.95
            current_price = self.price_cache[base_symbol]['price']
            
            self.positions[symbol] = {
                'symbol': symbol,
                'amount': amount,
                'entry_price': entry_price,
                'current_price': current_price,
                'unrealized_pnl': (current_price - entry_price) * amount,
                'direction': 'long' if amount > 0 else 'short'
            }
    
    async def handle_client(self, websocket):
        """Handle individual client connections"""
        try:
            # Add client to set
            self.clients.add(websocket)
            logger.info(f"🔌 Client connected. Total clients: {len(self.clients)}")
            
            # Send initial data (matches frontend expectations)
            await self.send_initial_data(websocket)
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error("❌ Invalid JSON message received")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'data': {'message': 'Invalid JSON format'}
                    }))
                except Exception as e:
                    logger.error(f"❌ Error handling message: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'data': {'message': str(e)}
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 Client disconnected")
        except Exception as e:
            logger.error(f"❌ Error handling client: {e}")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            logger.info(f"🔌 Client removed. Total clients: {len(self.clients)}")
    
    async def send_initial_data(self, websocket):
        """Send initial data to new client (matches frontend expectations)"""
        try:
            # Send comprehensive initial data that matches frontend expectations
            initial_data = {
                'type': 'initial_data',
                'data': {
                    'paper_balance': self.paper_balance,
                    'positions': self.positions,
                    'recent_trades': self.recent_trades,
                    'price_cache': self.price_cache,
                    'crypto_data': self.crypto_data,
                    'ai_insights': None
                }
            }
            await websocket.send(json.dumps(initial_data))
            
            # Also send individual responses for compatibility
            # Send positions
            await websocket.send(json.dumps({
                'type': 'positions_response',
                'data': {
                    'balance': self.paper_balance,
                    'positions': self.positions
                }
            }))
            
            # Send trade history
            await websocket.send(json.dumps({
                'type': 'trade_history_response',
                'data': {
                    'trades': self.recent_trades
                }
            }))
            
            # Send crypto data
            await websocket.send(json.dumps({
                'type': 'crypto_data_response',
                'data': self.crypto_data
            }))
            
            # Send bot status
            await websocket.send(json.dumps({
                'type': 'bot_status_response',
                'data': {
                    'enabled': self.bot_enabled,
                    'start_time': self.bot_start_time,
                    'active_trades': len(self.positions),
                    'trades_today': len([t for t in self.recent_trades if time.time() - t['timestamp'] < 86400]),
                    'total_profit': sum(p.get('unrealized_pnl', 0) for p in self.positions.values()),
                    'total_trades': len(self.recent_trades),
                    'winning_trades': len([t for t in self.recent_trades if t['direction'] == 'SELL']),
                    'win_rate': 0.65,
                    'pair_status': {symbol: 'idle' for symbol in self.bot_config['allowed_pairs']},
                    'running_duration': 0
                }
            }))
            
            # Send some fake analysis logs
            await websocket.send(json.dumps({
                'type': 'analysis_log',
                'data': {
                    'timestamp': time.time(),
                    'level': 'info',
                    'message': 'AI analysis completed for BTCUSDT - BULLISH signal detected',
                    'confidence_score': 0.85,
                    'entry_price': 45000.0
                }
            }))
            
            # Send some fake trade logs
            await websocket.send(json.dumps({
                'type': 'trade_log',
                'data': {
                    'timestamp': time.time(),
                    'level': 'success',
                    'message': 'Bot trade executed: BUY 0.1 BTCUSDT @ $45000',
                    'profit': 150.25
                }
            }))
            
            # Send some fake active bot trades
            await websocket.send(json.dumps({
                'type': 'bot_trade_executed',
                'data': {
                    'symbol': 'BTCUSDT',
                    'trade_data': {
                        'direction': 'LONG',
                        'price': 45000.0,
                        'take_profit': 46000.0,
                        'stop_loss': 44000.0,
                        'amount': 0.1,
                        'confidence_score': 0.85
                    }
                }
            }))
            
            await websocket.send(json.dumps({
                'type': 'bot_trade_executed',
                'data': {
                    'symbol': 'ETHUSDT',
                    'trade_data': {
                        'direction': 'SHORT',
                        'price': 3000.0,
                        'take_profit': 2900.0,
                        'stop_loss': 3100.0,
                        'amount': 1.5,
                        'confidence_score': 0.72
                    }
                }
            }))
            
            # Send some fake closed bot trades for trade history
            await websocket.send(json.dumps({
                'type': 'bot_trade_closed',
                'data': {
                    'symbol': 'SOLUSDT',
                    'trade_record': {
                        'symbol': 'SOLUSDT',
                        'direction': 'LONG',
                        'entry_price': 95.0,
                        'exit_price': 102.5,
                        'profit_loss': 75.0,
                        'exit_reason': 'Take Profit'
                    }
                }
            }))
            
            await websocket.send(json.dumps({
                'type': 'bot_trade_closed',
                'data': {
                    'symbol': 'ADAUSDT',
                    'trade_record': {
                        'symbol': 'ADAUSDT',
                        'direction': 'SHORT',
                        'entry_price': 0.55,
                        'exit_price': 0.52,
                        'profit_loss': 45.0,
                        'exit_reason': 'Stop Loss'
                    }
                }
            }))
            
            logger.info("✅ Initial data sent to client")
            
        except Exception as e:
            logger.error(f"❌ Error sending initial data: {e}")
    
    async def handle_message(self, websocket, data):
        """Handle incoming WebSocket messages (matches frontend expectations)"""
        try:
            message_type = data.get('type')
            logger.info(f"📨 Received message: {message_type}")
            
            if message_type == 'get_positions':
                await websocket.send(json.dumps({
                    'type': 'positions_response',
                    'data': {
                        'balance': self.paper_balance,
                        'positions': self.positions
                    }
                }))
                
            elif message_type == 'get_trade_history':
                limit = data.get('limit', 50)
                symbol = data.get('symbol')
                
                trades = self.recent_trades
                if symbol:
                    trades = [t for t in trades if t['symbol'] == symbol]
                
                trades = trades[:limit]
                
                await websocket.send(json.dumps({
                    'type': 'trade_history_response',
                    'data': {
                        'trades': trades
                    }
                }))
                
            elif message_type == 'get_crypto_data':
                symbol = data.get('symbol')
                if symbol:
                    response_data = {symbol.lower(): self.crypto_data.get(symbol.lower(), {})}
                else:
                    response_data = self.crypto_data
                
                await websocket.send(json.dumps({
                    'type': 'crypto_data_response',
                    'data': response_data
                }))
                
            elif message_type == 'execute_trade':
                await self.execute_fake_trade(websocket, data)
                
            elif message_type == 'paper_trade':
                await self.execute_fake_trade(websocket, data)
                
            elif message_type == 'close_position':
                symbol = data.get('symbol')
                await self.close_fake_position(websocket, symbol)
                
            elif message_type == 'start_bot':
                config = data.get('config', {})
                await self.start_fake_bot(websocket, config)
                
            elif message_type == 'stop_bot':
                await self.stop_fake_bot(websocket)
                
            elif message_type == 'get_bot_status':
                await self.send_bot_status(websocket)
                
            elif message_type == 'update_bot_config':
                config = data.get('config', {})
                await self.update_bot_config(websocket, config)
                
            elif message_type == 'get_ai_analysis':
                symbol = data.get('symbol', 'BTC')
                await self.send_ai_analysis(websocket, symbol)
                
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': f'Unknown message type: {message_type}'}
                }))
                
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
    
    async def execute_fake_trade(self, websocket, data):
        """Execute a fake trade (matches frontend expectations)"""
        try:
            symbol = data.get('symbol')
            direction = data.get('direction')
            amount = data.get('amount')
            price = data.get('price')
            
            if not all([symbol, direction, amount, price]):
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': 'Missing trade parameters'}
                }))
                return
            
            # Calculate trade value
            trade_value = amount * price
            
            # Check if we have enough balance for BUY
            if direction == 'BUY' and trade_value > self.paper_balance:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': 'Insufficient balance'}
                }))
                return
            
            # Create trade record
            trade = {
                'trade_id': f"trade_{int(time.time())}_{symbol}",
                'symbol': symbol,
                'direction': direction,
                'amount': amount,
                'price': price,
                'value': trade_value,
                'timestamp': time.time(),
                'trade_type': 'MANUAL',
                'status': 'executed'
            }
            
            # Update balance and positions
            if direction == 'BUY':
                self.paper_balance -= trade_value
                if symbol in self.positions:
                    # Add to existing position
                    pos = self.positions[symbol]
                    total_amount = pos['amount'] + amount
                    avg_price = ((pos['amount'] * pos['entry_price']) + (amount * price)) / total_amount
                    pos['amount'] = total_amount
                    pos['entry_price'] = avg_price
                    pos['current_price'] = price
                    pos['unrealized_pnl'] = (price - avg_price) * total_amount
                else:
                    # Create new position
                    self.positions[symbol] = {
                        'symbol': symbol,
                        'amount': amount,
                        'entry_price': price,
                        'current_price': price,
                        'unrealized_pnl': 0.0
                    }
            else:  # SELL
                self.paper_balance += trade_value
                if symbol in self.positions:
                    # Reduce or close position
                    pos = self.positions[symbol]
                    if amount >= pos['amount']:
                        # Close position
                        del self.positions[symbol]
                    else:
                        # Reduce position
                        pos['amount'] -= amount
                        pos['current_price'] = price
                        pos['unrealized_pnl'] = (price - pos['entry_price']) * pos['amount']
            
            # Add to trade history
            self.recent_trades.insert(0, trade)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]
            
            # Send trade executed response (matches frontend expectations)
            await websocket.send(json.dumps({
                'type': 'trade_executed',
                'data': {
                    'trade': trade,
                    'new_balance': self.paper_balance,
                    'positions': self.positions
                }
            }))
            
            # Also send paper_trade_response for frontend compatibility
            await websocket.send(json.dumps({
                'type': 'paper_trade_response',
                'data': {
                    'success': True,
                    'trade': trade,
                    'new_balance': self.paper_balance,
                    'positions': self.positions
                }
            }))
            
            # Broadcast position update to all clients
            await self.broadcast_message('position_update', {
                'balance': self.paper_balance,
                'positions': self.positions
            })
            
            logger.info(f"💰 Fake trade executed: {direction} {amount} {symbol} @ {price}")
            
        except Exception as e:
            logger.error(f"❌ Error executing fake trade: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
    
    async def close_fake_position(self, websocket, symbol):
        """Close a fake position (matches frontend expectations)"""
        try:
            if symbol not in self.positions:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': f'No position found for {symbol}'}
                }))
                return
            
            position = self.positions[symbol]
            # Extract base symbol for price lookup
            base_symbol = symbol.replace('USDT', '')
            current_price = self.price_cache[base_symbol]['price']
            
            # Create closing trade
            trade = {
                'trade_id': f"trade_{int(time.time())}_{symbol}_close",
                'symbol': symbol,
                'direction': 'SELL',
                'amount': position['amount'],
                'price': current_price,
                'value': position['amount'] * current_price,
                'timestamp': time.time(),
                'trade_type': 'MANUAL',
                'status': 'executed'
            }
            
            # Update balance
            self.paper_balance += trade['value']
            
            # Calculate realized P&L
            realized_pnl = (current_price - position['entry_price']) * position['amount']
            
            # Remove position
            del self.positions[symbol]
            
            # Add to trade history
            self.recent_trades.insert(0, trade)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]
            
            # Send position closed response (matches frontend expectations)
            await websocket.send(json.dumps({
                'type': 'position_closed',
                'data': {
                    'trade': trade,
                    'new_balance': self.paper_balance,
                    'positions': self.positions,
                    'realized_pnl': realized_pnl
                }
            }))
            
            # Broadcast position update to all clients
            await self.broadcast_message('position_update', {
                'balance': self.paper_balance,
                'positions': self.positions
            })
            
            logger.info(f"💰 Fake position closed: {symbol}, P&L: {realized_pnl}")
            
        except Exception as e:
            logger.error(f"❌ Error closing fake position: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
    
    async def start_fake_bot(self, websocket, config):
        """Start fake trading bot (matches frontend expectations)"""
        try:
            if self.bot_enabled:
                await websocket.send(json.dumps({
                    'type': 'start_bot_response',
                    'data': {
                        'success': False,
                        'error': 'Bot is already running'
                    }
                }))
                return
            
            # Update config
            if config:
                self.bot_config.update(config)
            
            self.bot_enabled = True
            self.bot_start_time = time.time()
            
            await websocket.send(json.dumps({
                'type': 'start_bot_response',
                'data': {
                    'success': True,
                    'message': 'Trading bot started successfully',
                    'config': self.bot_config
                }
            }))
            
            # Broadcast bot status update
            await self.broadcast_message('bot_status_update', {
                'enabled': True,
                'start_time': self.bot_start_time,
                'config': self.bot_config,
                'message': 'Trading bot started successfully'
            })
            
            logger.info("🤖 Fake trading bot started")
            
        except Exception as e:
            logger.error(f"❌ Error starting fake bot: {e}")
            await websocket.send(json.dumps({
                'type': 'start_bot_response',
                'data': {
                    'success': False,
                    'error': str(e)
                }
            }))
    
    async def stop_fake_bot(self, websocket):
        """Stop fake trading bot (matches frontend expectations)"""
        try:
            self.bot_enabled = False
            self.bot_start_time = None
            
            await websocket.send(json.dumps({
                'type': 'stop_bot_response',
                'data': {
                    'success': True,
                    'message': 'Trading bot stopped successfully'
                }
            }))
            
            # Broadcast bot status update
            await self.broadcast_message('bot_status_update', {
                'enabled': False,
                'message': 'Trading bot stopped successfully'
            })
            
            logger.info("🤖 Fake trading bot stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping fake bot: {e}")
            await websocket.send(json.dumps({
                'type': 'stop_bot_response',
                'data': {
                    'success': False,
                    'error': str(e)
                }
            }))
    
    async def send_bot_status(self, websocket):
        """Send bot status (matches frontend expectations)"""
        try:
            trades_today = len([t for t in self.recent_trades if time.time() - t['timestamp'] < 86400])
            winning_trades = len([t for t in self.recent_trades if t['direction'] == 'SELL'])
            total_trades = len(self.recent_trades)
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            status = {
                'enabled': self.bot_enabled,
                'start_time': self.bot_start_time,
                'active_trades': len(self.positions),
                'trades_today': trades_today,
                'total_profit': sum(p['unrealized_pnl'] for p in self.positions.values()),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 2),
                'pair_status': {symbol: 'idle' for symbol in self.bot_config['allowed_pairs']}
            }
            
            await websocket.send(json.dumps({
                'type': 'bot_status_response',
                'data': status
            }))
            
        except Exception as e:
            logger.error(f"❌ Error sending bot status: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
    
    async def update_bot_config(self, websocket, config):
        """Update bot configuration (matches frontend expectations)"""
        try:
            self.bot_config.update(config)
            
            await websocket.send(json.dumps({
                'type': 'bot_config_update_result',
                'data': {
                    'success': True,
                    'message': 'Bot configuration updated successfully',
                    'config': self.bot_config
                }
            }))
            
            logger.info("⚙️ Bot configuration updated")
            
        except Exception as e:
            logger.error(f"❌ Error updating bot config: {e}")
            await websocket.send(json.dumps({
                'type': 'bot_config_update_result',
                'data': {
                    'success': False,
                    'error': str(e)
                }
            }))
    
    async def send_ai_analysis(self, websocket, symbol):
        """Send fake AI analysis (matches frontend expectations)"""
        try:
            analysis = {
                'symbol': symbol,
                'claude_analysis': f"Claude analysis for {symbol}: Strong bullish momentum with support at key levels.",
                'gpt_refinement': f"GPT refinement for {symbol}: Technical indicators suggest continued upward movement.",
                'timestamp': time.time(),
                'confidence_score': round(random.uniform(0.6, 0.9), 2)
            }
            
            await websocket.send(json.dumps({
                'type': 'ai_insights',
                'data': analysis
            }))
            
            logger.info(f"🤖 Fake AI analysis sent for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error sending AI analysis: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'data': {'message': str(e)}
            }))
    
    async def broadcast_message(self, message_type: str, data: Dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        message = {
            'type': message_type,
            'data': data
        }
        
        try:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
            logger.info(f"📡 Broadcasted {message_type} to {len(self.clients)} clients")
        except Exception as e:
            logger.error(f"❌ Error broadcasting message: {e}")
    
    async def update_prices(self):
        """Update fake prices periodically"""
        while self.running:
            try:
                for symbol in self.crypto_symbols:
                    current_price = self.price_cache[symbol]['price']
                    change_percent = random.uniform(-0.02, 0.02)  # ±2% change
                    new_price = current_price * (1 + change_percent)
                    
                    self.price_cache[symbol].update({
                        'price': round(new_price, 4),
                        'change_24h': round(random.uniform(-15, 15), 2),
                        'timestamp': time.time()
                    })
                    
                    # Update crypto data
                    if symbol.lower() in self.crypto_data:
                        self.crypto_data[symbol.lower()]['current_price'] = new_price
                    
                    # Update position P&L if exists
                    if symbol in self.positions:
                        self.positions[symbol]['current_price'] = new_price
                        entry_price = self.positions[symbol]['entry_price']
                        amount = self.positions[symbol]['amount']
                        self.positions[symbol]['unrealized_pnl'] = (new_price - entry_price) * amount
                
                # Broadcast price updates
                for symbol in self.crypto_symbols:
                    await self.broadcast_message('price_update', self.price_cache[symbol])
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"❌ Error updating prices: {e}")
                await asyncio.sleep(5)
    
    async def simulate_bot_trades(self):
        """Simulate bot trading activity"""
        while self.running and self.bot_enabled:
            try:
                # Simulate bot trade every 30 seconds
                await asyncio.sleep(30)
                
                if not self.bot_enabled:
                    continue
                
                # Randomly execute a bot trade
                if random.random() < 0.3:  # 30% chance
                    symbol = random.choice(self.bot_config['allowed_pairs'])
                    direction = random.choice(['BUY', 'SELL'])
                    amount = round(random.uniform(0.01, 0.1), 4)
                    price = self.price_cache[symbol]['price']
                    
                    # Create bot trade
                    trade = {
                        'trade_id': f"bot_trade_{int(time.time())}_{symbol}",
                        'symbol': symbol,
                        'direction': direction,
                        'amount': amount,
                        'price': price,
                        'value': amount * price,
                        'timestamp': time.time(),
                        'trade_type': 'BOT',
                        'status': 'executed'
                    }
                    
                    # Broadcast bot trade
                    await self.broadcast_message('bot_trade_executed', {
                        'trade': trade,
                        'bot_status': {
                            'enabled': self.bot_enabled,
                            'active_trades': len(self.positions),
                            'total_profit': sum(p['unrealized_pnl'] for p in self.positions.values())
                        }
                    })
                    
                    logger.info(f"🤖 Simulated bot trade: {direction} {amount} {symbol}")
                
            except Exception as e:
                logger.error(f"❌ Error simulating bot trades: {e}")
                await asyncio.sleep(30)
    
    async def start_server(self, host='localhost', port=8765):
        """Start the fake WebSocket server"""
        self.running = True
        
        # Start background tasks
        self.background_tasks.append(asyncio.create_task(self.update_prices()))
        self.background_tasks.append(asyncio.create_task(self.simulate_bot_trades()))
        
        logger.info(f"🚀 Starting fake WebSocket server on ws://{host}:{port}")
        logger.info("📊 Server will send fake data to frontend")
        logger.info("💰 Simulate trades, bot operations, and real-time updates")
        logger.info("🛑 Press Ctrl+C to stop")
        
        # Start the server - pass the handle_client method directly
        # The websockets library will automatically pass only the websocket to it
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever
    
    async def shutdown(self):
        """Shutdown the server"""
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close all client connections
        for client in self.clients:
            await client.close()
        
        logger.info("🛑 Fake server shutdown complete")

async def main():
    """Main function"""
    server = FakeTradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")