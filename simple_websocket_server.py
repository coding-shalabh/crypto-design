#!/usr/bin/env python3
"""
Enhanced Fake Trading WebSocket Server with Comprehensive Debugging
==================================================================

This server simulates a complete crypto trading system with:
- Real-time price updates
- Trade execution simulation
- AI analysis generation
- Bot status updates
- Position management
- Comprehensive debugging with emojis and markers
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Set

import websockets

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedFakeTradingServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
        # Trading state
        self.positions = {}
        self.trade_history = []
        self.bot_enabled = False
        self.bot_config = {
            'strategy': 'momentum',
            'risk_level': 'medium',
            'max_positions': 3
        }
        
        # Crypto symbols and initial prices - use USDT format to match frontend
        self.crypto_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "XRPUSDT"]
        self.base_prices = {
            "BTCUSDT": 45000.0,
            "ETHUSDT": 3000.0,
            "ADAUSDT": 1.20,
            "DOTUSDT": 25.0,
            "LINKUSDT": 18.0,
            "LTCUSDT": 150.0,
            "BCHUSDT": 400.0,
            "XRPUSDT": 0.80
        }
        
        # Price cache for tracking changes
        self.price_cache = {symbol: {
            'price': self.base_prices[symbol],
            'change_24h': 0.0,
            'volume': random.randint(1000, 10000),
            'high_24h': self.base_prices[symbol] * 1.05,
            'low_24h': self.base_prices[symbol] * 0.95
        } for symbol in self.crypto_symbols}
        
        # Initialize crypto data structure that frontend expects
        self.crypto_data = {}
        for symbol in self.crypto_symbols:
            base_symbol = symbol.replace('USDT', '')
            self.crypto_data[symbol] = {
                'id': symbol.lower(),
                'symbol': symbol,
                'name': base_symbol,
                'current_price': self.base_prices[symbol],
                'market_cap': random.randint(1000000, 1000000000),
                'volume_24h': random.randint(100000, 10000000),
                'price_change_24h': 0.0,
                'price_change_percentage_24h': 0.0,
                'market_cap_rank': random.randint(1, 100),
                'last_updated': datetime.now().isoformat()
            }
        
        logger.info("-----🚀 ENHANCED FAKE TRADING SERVER INITIALIZED -----")
        logger.info("-----📊 Trading symbols: " + ", ".join(self.crypto_symbols) + " -----")
        logger.info("-----💰 Initial prices loaded -----")
        
    async def debug_log(self, message: str, emoji: str = "🔍"):
        """Log debug message with emoji and markers"""
        logger.info(f"-----{emoji} {message} -----")
    
    async def generate_price_update(self, symbol: str) -> Dict:
        """Generate realistic price update with debugging"""
        old_price = self.price_cache[symbol]['price']
        
        # Generate realistic price movement
        change_percent = random.uniform(-1.5, 1.5)  # ±1.5% max change
        new_price = old_price * (1 + change_percent / 100)
        
        # Update price cache
        self.price_cache[symbol].update({
            'price': round(new_price, 4),
            'change_24h': round(random.uniform(-15, 15), 2),
            'volume': random.randint(1000, 10000),
            'high_24h': max(self.price_cache[symbol]['high_24h'], new_price),
            'low_24h': min(self.price_cache[symbol]['low_24h'], new_price),
            'timestamp': time.time()
        })
        
        # Update crypto data structure
        if symbol in self.crypto_data:
            self.crypto_data[symbol].update({
                'current_price': round(new_price, 4),
                'price_change_24h': self.price_cache[symbol]['change_24h'],
                'price_change_percentage_24h': self.price_cache[symbol]['change_24h'],
                'volume_24h': self.price_cache[symbol]['volume'],
                'last_updated': datetime.now().isoformat()
            })
        
        await self.debug_log(f"PRICE UPDATE: {symbol} ${old_price:.4f} → ${new_price:.4f} ({change_percent:+.2f}%)", "📈")
        
        return {
            "type": "price_update",
            "data": {
                "symbol": symbol,
                "price": round(new_price, 4),
                "change_24h": self.price_cache[symbol]['change_24h'],
                "volume": self.price_cache[symbol]['volume'],
                "high_24h": self.price_cache[symbol]['high_24h'],
                "low_24h": self.price_cache[symbol]['low_24h'],
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def generate_trade_execution(self) -> Dict:
        """Generate fake trade execution"""
        symbol = random.choice(self.crypto_symbols)
        direction = random.choice(['BUY', 'SELL'])
        amount = round(random.uniform(0.01, 0.5), 4)
        price = self.price_cache[symbol]['price']
        trade_id = f"trade_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Update positions if it's a BUY
        if direction == 'BUY':
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'amount': amount,
                    'entry_price': price,
                    'current_price': price,
                    'unrealized_pnl': 0.0
                }
            else:
                # Average down/up existing position
                current_amount = self.positions[symbol]['amount']
                current_entry = self.positions[symbol]['entry_price']
                new_amount = current_amount + amount
                new_entry = ((current_amount * current_entry) + (amount * price)) / new_amount
                self.positions[symbol].update({
                    'amount': new_amount,
                    'entry_price': new_entry,
                    'current_price': price
                })
        # Remove position on SELL if it exists
        elif direction == 'SELL':
            if symbol in self.positions:
                del self.positions[symbol]
        
        trade_data = {
            "type": "trade_executed",
            "data": {
                "trade_id": trade_id,
                "symbol": symbol,
                "direction": direction,
                "amount": amount,
                "price": price,
                "value": amount * price,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
        }
        
        await self.debug_log(f"TRADE EXECUTED: {direction} {amount} {symbol} @ ${price:.4f} (ID: {trade_id})", "💼")
        
        # Add to trade history
        self.trade_history.append(trade_data['data'])
        if len(self.trade_history) > 100:  # Keep last 100 trades
            self.trade_history.pop(0)
        
        return trade_data
    
    async def generate_ai_analysis(self) -> Dict:
        """Generate fake AI analysis"""
        symbol = random.choice(self.crypto_symbols)
        sentiment = random.choice(["bullish", "bearish", "neutral"])
        confidence = round(random.uniform(0.65, 0.95), 2)
        recommendation = random.choice(["buy", "sell", "hold"])
        
        analysis_texts = {
            "bullish": [
                f"Strong upward momentum detected for {symbol}. Technical indicators suggest continued growth.",
                f"{symbol} showing bullish patterns with support at key levels. Consider accumulation.",
                f"Positive market sentiment for {symbol} with increasing volume and price action."
            ],
            "bearish": [
                f"Downward pressure building on {symbol}. Consider reducing exposure.",
                f"{symbol} showing bearish signals with resistance at current levels.",
                f"Negative momentum detected for {symbol}. Technical analysis suggests caution."
            ],
            "neutral": [
                f"{symbol} trading sideways with mixed signals. Monitor for breakout.",
                f"Consolidation phase for {symbol}. Wait for clearer direction.",
                f"Neutral stance on {symbol}. Market conditions are uncertain."
            ]
        }
        
        analysis_data = {
            "type": "ai_analysis",
            "data": {
                "symbol": symbol,
                "sentiment": sentiment,
                "confidence": confidence,
                "recommendation": recommendation,
                "analysis": random.choice(analysis_texts[sentiment]),
                "timestamp": datetime.now().isoformat(),
                "indicators": {
                    "rsi": round(random.uniform(20, 80), 1),
                    "macd": round(random.uniform(-2, 2), 3),
                    "volume": "increasing" if random.random() > 0.5 else "decreasing"
                }
            }
        }
        
        await self.debug_log(f"AI ANALYSIS: {symbol} - {sentiment.upper()} ({confidence*100:.0f}% confidence) - {recommendation.upper()}", "🤖")
        
        return analysis_data
    
    async def generate_position_update(self) -> Dict:
        """Generate position update with P&L calculations"""
        if not self.positions:
            return None
        
        # Update P&L for all positions
        for symbol, position in self.positions.items():
            current_price = self.price_cache[symbol]['price']
            entry_price = position['entry_price']
            amount = position['amount']
            
            unrealized_pnl = (current_price - entry_price) * amount
            pnl_percent = ((current_price - entry_price) / entry_price) * 100
            
            position.update({
                'current_price': current_price,
                'unrealized_pnl': round(unrealized_pnl, 2),
                'pnl_percent': round(pnl_percent, 2)
            })
        
        position_data = {
            "type": "positions_update",
            "data": {
                "positions": self.positions,
                "total_pnl": sum(p['unrealized_pnl'] for p in self.positions.values()),
                "total_positions": len(self.positions),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.debug_log(f"POSITIONS UPDATE: {len(self.positions)} positions, Total P&L: ${sum(p['unrealized_pnl'] for p in self.positions.values()):.2f}", "📊")
        
        return position_data
    
    async def generate_bot_status(self) -> Dict:
        """Generate bot status update"""
        status_data = {
            "type": "bot_status",
            "data": {
                "enabled": self.bot_enabled,
                "strategy": self.bot_config['strategy'],
                "risk_level": self.bot_config['risk_level'],
                "active_positions": len(self.positions),
                "total_trades": len(self.trade_history),
                "performance": {
                    "total_pnl": sum(p['unrealized_pnl'] for p in self.positions.values()),
                    "win_rate": round(random.uniform(0.4, 0.8), 2),
                    "avg_trade_size": round(random.uniform(0.05, 0.2), 4)
                },
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.debug_log(f"BOT STATUS: {'🟢 ENABLED' if self.bot_enabled else '🔴 DISABLED'} - {len(self.positions)} positions", "🤖")
        
        return status_data
    
    async def handle_client(self, websocket):
        """Handle individual client connections"""
        client_id = id(websocket)
        await self.debug_log(f"NEW CLIENT CONNECTED: {client_id}", "🔌")
        
        try:
            # Add client to set
            self.clients.add(websocket)
            await self.debug_log(f"CLIENT ADDED: Total clients: {len(self.clients)}", "👥")
            
            # Send initial connection message
            welcome_msg = {
                "type": "connection_status",
                "status": "connected",
                "message": "Connected to Enhanced Fake Trading Server",
                "server_info": {
                    "version": "1.0.0",
                    "features": ["price_updates", "trade_simulation", "ai_analysis", "bot_status"],
                    "symbols": self.crypto_symbols
                },
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(welcome_msg))
            await self.debug_log(f"WELCOME MESSAGE SENT TO CLIENT {client_id}", "👋")
            
            # Send initial data
            await self.send_initial_data(websocket)
            
            # Keep connection alive and send periodic data
            while self.running:
                try:
                    # Wait for messages from client
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    
                    try:
                        data = json.loads(message)
                        await self.handle_client_message(websocket, data)
                    except json.JSONDecodeError:
                        await self.debug_log(f"INVALID JSON FROM CLIENT {client_id}: {message}", "⚠️")
                    
                    # Send periodic data
                    await self.send_periodic_data(websocket)
                    
                except asyncio.TimeoutError:
                    # No message received, just send periodic data
                    await self.send_periodic_data(websocket)
                except websockets.exceptions.ConnectionClosed:
                    await self.debug_log(f"CLIENT DISCONNECTED: {client_id}", "🔌")
                    break
                except Exception as e:
                    await self.debug_log(f"ERROR SENDING DATA TO CLIENT {client_id}: {e}", "❌")
                    break
                    
        except Exception as e:
            await self.debug_log(f"ERROR HANDLING CLIENT {client_id}: {e}", "💥")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            await self.debug_log(f"CLIENT REMOVED: {client_id} - Total clients: {len(self.clients)}", "👥")
    
    async def handle_client_message(self, websocket, data):
        """Handle messages from client"""
        message_type = data.get('type', 'unknown')
        
        if message_type == 'get_positions':
            await self.send_positions_response(websocket)
        elif message_type == 'get_trade_history':
            await self.send_trade_history_response(websocket, data.get('limit', 50))
        elif message_type == 'get_crypto_data':
            await self.send_crypto_data_response(websocket)
        elif message_type == 'paper_trade':
            await self.handle_paper_trade(websocket, data)
        elif message_type == 'close_position':
            await self.handle_close_position(websocket, data.get('symbol'))
        else:
            await self.debug_log(f"UNKNOWN MESSAGE TYPE: {message_type}", "❓")
    
    async def send_positions_response(self, websocket):
        """Send positions response in the format frontend expects"""
        positions_response = {
            "type": "positions_response",
            "data": {
                "balance": 100000.0,  # Fixed paper balance
                "positions": self.positions
            }
        }
        await websocket.send(json.dumps(positions_response))
        await self.debug_log(f"POSITIONS RESPONSE SENT: {len(self.positions)} positions", "📊")
    
    async def send_trade_history_response(self, websocket, limit=50):
        """Send trade history response"""
        trade_history_response = {
            "type": "trade_history_response",
            "data": {
                "trades": self.trade_history[-limit:] if self.trade_history else []
            }
        }
        await websocket.send(json.dumps(trade_history_response))
        await self.debug_log(f"TRADE HISTORY RESPONSE SENT: {len(self.trade_history)} trades", "📋")
    
    async def send_crypto_data_response(self, websocket):
        """Send crypto data response"""
        crypto_data_response = {
            "type": "crypto_data_response",
            "data": self.crypto_data
        }
        await websocket.send(json.dumps(crypto_data_response))
        await self.debug_log(f"CRYPTO DATA RESPONSE SENT: {len(self.crypto_data)} symbols", "📊")
    
    async def handle_paper_trade(self, websocket, data):
        """Handle paper trade request"""
        # Simulate trade execution
        trade_data = await self.generate_trade_execution()
        
        # Send trade response
        trade_response = {
            "type": "paper_trade_response",
            "data": {
                "success": True,
                "new_balance": 100000.0,
                "positions": self.positions,
                "trade": trade_data['data']
            }
        }
        await websocket.send(json.dumps(trade_response))
        await self.debug_log(f"PAPER TRADE RESPONSE SENT", "💼")
    
    async def handle_close_position(self, websocket, symbol):
        """Handle close position request"""
        if symbol in self.positions:
            del self.positions[symbol]
            
            close_response = {
                "type": "position_closed",
                "data": {
                    "new_balance": 100000.0,
                    "positions": self.positions,
                    "trade": {
                        "symbol": symbol,
                        "action": "closed",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }
            await websocket.send(json.dumps(close_response))
            await self.debug_log(f"POSITION CLOSED: {symbol}", "📊")
    
    async def send_periodic_data(self, websocket):
        """Send periodic data updates"""
        # Send price updates every 3 seconds
        for symbol in random.sample(self.crypto_symbols, 3):  # Send 3 random symbols
            price_data = await self.generate_price_update(symbol)
            await websocket.send(json.dumps(price_data))
            await asyncio.sleep(0.5)  # Small delay between messages
        
        # Send trade execution every 8 seconds (30% chance)
        if random.random() < 0.3:
            trade_data = await self.generate_trade_execution()
            await websocket.send(json.dumps(trade_data))
        
        # Send AI analysis every 10 seconds (40% chance)
        if random.random() < 0.4:
            ai_data = await self.generate_ai_analysis()
            await websocket.send(json.dumps(ai_data))
        
        # Send position updates every 15 seconds
        if self.positions:
            position_data = await self.generate_position_update()
            if position_data:
                await websocket.send(json.dumps(position_data))
        
        # Send bot status every 20 seconds
        bot_data = await self.generate_bot_status()
        await websocket.send(json.dumps(bot_data))
        
        # Send crypto data updates every 25 seconds
        crypto_data_message = {
            "type": "crypto_data",
            "data": self.crypto_data
        }
        await websocket.send(json.dumps(crypto_data_message))
    
    async def send_initial_data(self, websocket):
        """Send initial data to new client"""
        await self.debug_log("SENDING INITIAL DATA TO NEW CLIENT", "📤")
        
        # Send current prices for all symbols
        for symbol in self.crypto_symbols:
            price_data = await self.generate_price_update(symbol)
            await websocket.send(json.dumps(price_data))
            await asyncio.sleep(0.1)
        
        # Send crypto data structure that frontend expects
        crypto_data_message = {
            "type": "crypto_data",
            "data": self.crypto_data
        }
        await websocket.send(json.dumps(crypto_data_message))
        await self.debug_log(f"SENT CRYPTO DATA FOR {len(self.crypto_data)} SYMBOLS", "📊")
        
        # Send current positions if any
        if self.positions:
            position_data = await self.generate_position_update()
            if position_data:
                await websocket.send(json.dumps(position_data))
        
        # Send bot status
        bot_data = await self.generate_bot_status()
        await websocket.send(json.dumps(bot_data))
        
        await self.debug_log("INITIAL DATA SENT SUCCESSFULLY", "✅")
    
    async def start_server(self):
        """Start the WebSocket server"""
        await self.debug_log(f"STARTING ENHANCED FAKE TRADING SERVER ON ws://{self.host}:{self.port}", "🚀")
        
        self.running = True
        
        try:
            # Start the server - pass the handle_client method directly
            # The websockets library will automatically pass (websocket, path) to it
            server = await websockets.serve(
                self.handle_client,  # Pass the method directly
                self.host,
                self.port
            )
            
            await self.debug_log(f"SERVER STARTED SUCCESSFULLY ON ws://{self.host}:{self.port}", "✅")
            await self.debug_log("READY TO ACCEPT CLIENT CONNECTIONS", "🎯")
            await self.debug_log("PRESS CTRL+C TO STOP THE SERVER", "⏹️")
            
            # Keep the server running
            await server.wait_closed()
            
        except Exception as e:
            await self.debug_log(f"ERROR STARTING SERVER: {e}", "💥")
        finally:
            self.running = False
            await self.debug_log("SERVER STOPPED", "🛑")

async def main():
    """Main function to run the server"""
    server = EnhancedFakeTradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("-----🛑 SERVER INTERRUPTED BY USER -----")
    except Exception as e:
        logger.error(f"-----💥 SERVER ERROR: {e} -----")

if __name__ == "__main__":
    asyncio.run(main())