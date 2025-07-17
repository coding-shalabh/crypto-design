#!/usr/bin/env python3
"""
Fake Trade Data Generator for Frontend Testing
==============================================

This script generates fake trade data in the exact format expected by the frontend
to test data flow without running the actual backend server.

Features:
- Generates realistic crypto price data
- Simulates trade executions and position updates
- Creates AI analysis responses
- Tests all WebSocket message types
- Provides detailed logging of data flow
"""

import json
import time
import random
import asyncio
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fake_data_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FakeTradeDataGenerator:
    def __init__(self, websocket_url: str = "ws://localhost:3000"):
        self.websocket_url = websocket_url
        self.websocket = None
        self.is_connected = False
        
        # Initialize fake data structures
        self.paper_balance = 10000.0  # Starting balance
        self.positions = {}
        self.recent_trades = []
        self.price_cache = {}
        self.crypto_data = {}
        self.bot_status = {
            'is_active': False,
            'pairs': {},
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0.0
        }
        
        # Crypto symbols for testing
        self.crypto_symbols = [
            'BTC', 'ETH', 'BNB', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC',
            'LINK', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'VET', 'FIL'
        ]
        
        # Initialize price cache with realistic data
        self._initialize_price_cache()
        self._initialize_crypto_data()
        
    def _initialize_price_cache(self):
        """Initialize price cache with realistic crypto prices"""
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
    
    def _initialize_crypto_data(self):
        """Initialize comprehensive crypto data"""
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
    
    async def connect(self):
        """Connect to the frontend WebSocket"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            logger.info(f"✅ Connected to {self.websocket_url}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("🔌 Disconnected from WebSocket")
    
    async def send_message(self, message_type: str, data: Dict[str, Any]):
        """Send a message to the frontend"""
        if not self.is_connected:
            logger.error("❌ Not connected to WebSocket")
            return
        
        message = {
            'type': message_type,
            'data': data
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Sent {message_type}: {json.dumps(message, indent=2)}")
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    def generate_fake_trade(self, symbol: str, direction: str = None) -> Dict[str, Any]:
        """Generate a fake trade"""
        if not direction:
            direction = random.choice(['BUY', 'SELL'])
        
        current_price = self.price_cache[symbol]['price']
        quantity = round(random.uniform(0.1, 2.0), 4)
        trade_amount = quantity * current_price
        
        trade = {
            'trade_id': f"trade_{int(time.time())}_{symbol}",
            'symbol': symbol,
            'direction': direction,
            'amount': quantity,
            'price': current_price,
            'value': trade_amount,
            'timestamp': time.time(),
            'trade_type': 'MANUAL',
            'status': 'executed'
        }
        
        return trade
    
    def update_price_cache(self, symbol: str):
        """Update price with realistic movement"""
        current_price = self.price_cache[symbol]['price']
        change_percent = random.uniform(-0.02, 0.02)  # ±2% change
        new_price = current_price * (1 + change_percent)
        
        self.price_cache[symbol].update({
            'price': round(new_price, 4),
            'change_24h': round(random.uniform(-15, 15), 2),
            'timestamp': time.time()
        })
        
        # Update crypto data as well
        if symbol.lower() in self.crypto_data:
            self.crypto_data[symbol.lower()]['current_price'] = new_price
    
    async def send_initial_data(self):
        """Send initial data to frontend"""
        initial_data = {
            'paper_balance': self.paper_balance,
            'positions': self.positions,
            'recent_trades': self.recent_trades[:20],
            'price_cache': self.price_cache,
            'crypto_data': self.crypto_data
        }
        
        await self.send_message('initial_data', initial_data)
        logger.info("📊 Sent initial data")
    
    async def send_price_update(self, symbol: str = None):
        """Send price update"""
        if symbol:
            self.update_price_cache(symbol)
            await self.send_message('price_update', self.price_cache[symbol])
        else:
            # Update all prices
            for sym in self.crypto_symbols[:5]:  # Update first 5 symbols
                self.update_price_cache(sym)
                await self.send_message('price_update', self.price_cache[sym])
                await asyncio.sleep(0.1)
    
    async def send_trade_executed(self, symbol: str = None):
        """Send trade executed message"""
        if not symbol:
            symbol = random.choice(self.crypto_symbols)
        
        trade = self.generate_fake_trade(symbol)
        self.recent_trades.insert(0, trade)
        
        # Update balance and positions
        if trade['direction'] == 'BUY':
            self.paper_balance -= trade['value']
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'symbol': symbol,
                    'amount': trade['amount'],
                    'entry_price': trade['price'],
                    'current_price': trade['price'],
                    'direction': 'LONG',
                    'value': trade['value'],
                    'timestamp': trade['timestamp']
                }
            else:
                self.positions[symbol]['amount'] += trade['amount']
                self.positions[symbol]['value'] += trade['value']
        else:
            self.paper_balance += trade['value']
            if symbol in self.positions:
                self.positions[symbol]['amount'] -= trade['amount']
                if self.positions[symbol]['amount'] <= 0:
                    del self.positions[symbol]
        
        trade_data = {
            'new_balance': self.paper_balance,
            'positions': self.positions,
            'trade': trade
        }
        
        await self.send_message('trade_executed', trade_data)
        logger.info(f"💰 Trade executed: {symbol} {trade['direction']} {trade['amount']}")
    
    async def send_position_update(self):
        """Send position update"""
        position_data = {
            'balance': self.paper_balance,
            'positions': self.positions
        }
        
        await self.send_message('position_update', position_data)
        logger.info("📈 Sent position update")
    
    async def send_ai_insights(self, symbol: str = None):
        """Send AI insights"""
        if not symbol:
            symbol = random.choice(self.crypto_symbols)
        
        ai_data = {
            'symbol': symbol,
            'claude_analysis': {
                'sentiment': random.choice(['bullish', 'bearish', 'neutral']),
                'confidence': round(random.uniform(0.6, 0.95), 2),
                'recommendation': {
                    'action': random.choice(['BUY', 'SELL', 'HOLD']),
                    'reasoning': f'AI analysis suggests {symbol} shows strong technical indicators'
                }
            },
            'gpt_refinement': {
                'summary': f'Refined analysis for {symbol} indicates potential movement',
                'risk_level': random.choice(['low', 'medium', 'high']),
                'timeframe': random.choice(['short', 'medium', 'long'])
            },
            'timestamp': time.time()
        }
        
        await self.send_message('ai_insights', ai_data)
        logger.info(f"🤖 Sent AI insights for {symbol}")
    
    async def send_bot_status(self):
        """Send bot status update"""
        self.bot_status['is_active'] = random.choice([True, False])
        self.bot_status['total_trades'] += random.randint(0, 2)
        self.bot_status['total_profit'] += random.uniform(-100, 200)
        
        await self.send_message('bot_status_response', self.bot_status)
        logger.info("🤖 Sent bot status update")
    
    async def send_bot_trade_executed(self, symbol: str = None):
        """Send bot trade executed message"""
        if not symbol:
            symbol = random.choice(self.crypto_symbols)
        
        trade = self.generate_fake_trade(symbol)
        trade['trade_type'] = 'BOT'
        
        bot_trade_data = {
            'symbol': symbol,
            'trade': trade,
            'bot_status': self.bot_status,
            'analysis_id': f"analysis_{int(time.time())}",
            'confidence_score': round(random.uniform(0.7, 0.95), 2)
        }
        
        await self.send_message('bot_trade_executed', bot_trade_data)
        logger.info(f"🤖 Bot trade executed: {symbol}")
    
    async def run_test_scenario(self, scenario_name: str):
        """Run a specific test scenario"""
        logger.info(f"🚀 Starting test scenario: {scenario_name}")
        
        if scenario_name == "initial_connection":
            await self.send_initial_data()
            
        elif scenario_name == "price_updates":
            for _ in range(3):
                await self.send_price_update()
                await asyncio.sleep(1)
                
        elif scenario_name == "trade_execution":
            for symbol in ['BTC', 'ETH', 'SOL']:
                await self.send_trade_executed(symbol)
                await asyncio.sleep(0.5)
                
        elif scenario_name == "ai_analysis":
            for symbol in ['BTC', 'ETH', 'ADA']:
                await self.send_ai_insights(symbol)
                await asyncio.sleep(0.5)
                
        elif scenario_name == "bot_operations":
            await self.send_bot_status()
            await asyncio.sleep(0.5)
            await self.send_bot_trade_executed('BTC')
            await asyncio.sleep(0.5)
            await self.send_bot_trade_executed('ETH')
            
        elif scenario_name == "comprehensive":
            # Run all scenarios
            await self.send_initial_data()
            await asyncio.sleep(1)
            
            for _ in range(5):
                await self.send_price_update()
                await asyncio.sleep(0.5)
            
            for symbol in ['BTC', 'ETH', 'SOL', 'ADA']:
                await self.send_trade_executed(symbol)
                await asyncio.sleep(0.3)
            
            for symbol in ['BTC', 'ETH']:
                await self.send_ai_insights(symbol)
                await asyncio.sleep(0.3)
            
            await self.send_bot_status()
            await self.send_bot_trade_executed('BTC')
            
        logger.info(f"✅ Completed test scenario: {scenario_name}")

async def main():
    """Main function to run the fake data generator"""
    generator = FakeTradeDataGenerator()
    
    # Test scenarios
    scenarios = [
        "initial_connection",
        "price_updates", 
        "trade_execution",
        "ai_analysis",
        "bot_operations",
        "comprehensive"
    ]
    
    print("🎯 Fake Trade Data Generator")
    print("=" * 50)
    print("Available test scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario}")
    print("0. Run all scenarios")
    print("-1. Exit")
    
    while True:
        try:
            choice = input("\nSelect scenario (0-6, -1 to exit): ").strip()
            
            if choice == "-1":
                break
            elif choice == "0":
                # Run all scenarios
                if await generator.connect():
                    for scenario in scenarios:
                        await generator.run_test_scenario(scenario)
                        await asyncio.sleep(2)
                    await generator.disconnect()
            elif choice.isdigit() and 1 <= int(choice) <= len(scenarios):
                scenario_index = int(choice) - 1
                scenario_name = scenarios[scenario_index]
                
                if await generator.connect():
                    await generator.run_test_scenario(scenario_name)
                    await asyncio.sleep(2)
                    await generator.disconnect()
            else:
                print("❌ Invalid choice. Please select 0-6 or -1.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 