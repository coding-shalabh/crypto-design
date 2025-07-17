#!/usr/bin/env python3
import asyncio
import json
import time
import websockets
import logging

# Set up logging without emojis
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFakeDataGenerator:
    def __init__(self):
        self.websocket = None
        self.is_connected = False
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect("ws://localhost:8765")
            self.is_connected = True
            logger.info("Connected to WebSocket server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket")
    
    async def send_message(self, message_type, data):
        """Send a message to the WebSocket server"""
        if not self.is_connected:
            logger.error("Not connected to WebSocket")
            return
        
        message = {
            "type": message_type,
            "data": data
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"Sent {message_type} message")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_initial_data(self):
        """Send initial data"""
        initial_data = {
            "paper_balance": 10000.0,
            "positions": {},
            "recent_trades": [],
            "price_cache": {
                "BTC": {
                    "symbol": "BTC",
                    "price": 45000.0,
                    "change_24h": 2.5,
                    "volume_24h": 25000000,
                    "market_cap": 850000000000,
                    "timestamp": time.time()
                }
            },
            "crypto_data": {
                "bitcoin": {
                    "id": "bitcoin",
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "current_price": 45000.0,
                    "market_cap": 850000000000,
                    "market_cap_rank": 1
                }
            }
        }
        
        await self.send_message("initial_data", initial_data)
    
    async def send_trade_executed(self):
        """Send a fake trade execution"""
        trade_data = {
            "new_balance": 9950.0,
            "positions": {
                "BTC": {
                    "symbol": "BTC",
                    "amount": 0.1,
                    "entry_price": 45000.0,
                    "current_price": 45100.0,
                    "direction": "LONG",
                    "value": 4500.0,
                    "timestamp": time.time()
                }
            },
            "trade": {
                "trade_id": f"trade_{int(time.time())}",
                "symbol": "BTC",
                "direction": "BUY",
                "amount": 0.1,
                "price": 45000.0,
                "value": 4500.0,
                "timestamp": time.time(),
                "trade_type": "MANUAL",
                "status": "executed"
            }
        }
        
        await self.send_message("trade_executed", trade_data)
    
    async def send_price_update(self):
        """Send a price update"""
        price_data = {
            "symbol": "BTC",
            "price": 45100.0,
            "change_24h": 2.8,
            "volume_24h": 25000000,
            "market_cap": 850000000000,
            "timestamp": time.time()
        }
        
        await self.send_message("price_update", price_data)
    
    async def run_test(self):
        """Run a simple test"""
        if await self.connect():
            logger.info("Starting test...")
            
            # Send initial data
            await self.send_initial_data()
            await asyncio.sleep(1)
            
            # Send price update
            await self.send_price_update()
            await asyncio.sleep(1)
            
            # Send trade execution
            await self.send_trade_executed()
            await asyncio.sleep(1)
            
            # Send another trade
            await self.send_trade_executed()
            
            logger.info("Test completed!")
            await self.disconnect()

async def main():
    """Main function"""
    generator = SimpleFakeDataGenerator()
    await generator.run_test()

if __name__ == "__main__":
    asyncio.run(main()) 