#!/usr/bin/env python3
"""
Simple WebSocket Server for Crypto Trading Frontend Testing
This server sends fake trade data to test the frontend without the real backend.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Set

import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CryptoFakeServer:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.running = False
        
        # Sample crypto data
        self.crypto_symbols = ["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP"]
        self.base_prices = {
            "BTC": 45000.0,
            "ETH": 3000.0,
            "ADA": 1.20,
            "DOT": 25.0,
            "LINK": 18.0,
            "LTC": 150.0,
            "BCH": 400.0,
            "XRP": 0.80
        }
        
    async def generate_price_data(self, symbol: str) -> Dict:
        """Generate fake price data for a crypto symbol"""
        base_price = self.base_prices.get(symbol, 100.0)
        
        # Add some random movement
        change_percent = random.uniform(-2.0, 2.0)
        new_price = base_price * (1 + change_percent / 100)
        
        # Update base price for next iteration
        self.base_prices[symbol] = new_price
        
        return {
            "symbol": symbol,
            "price": round(new_price, 4),
            "change": round(change_percent, 2),
            "volume": random.randint(1000, 10000),
            "timestamp": datetime.now().isoformat()
        }
    
    async def generate_trade_data(self) -> Dict:
        """Generate fake trade data"""
        symbol = random.choice(self.crypto_symbols)
        price_data = await self.generate_price_data(symbol)
        
        return {
            "type": "trade_data",
            "data": price_data
        }
    
    async def generate_ai_analysis(self) -> Dict:
        """Generate fake AI analysis data"""
        symbol = random.choice(self.crypto_symbols)
        
        return {
            "type": "ai_analysis",
            "data": {
                "symbol": symbol,
                "sentiment": random.choice(["bullish", "bearish", "neutral"]),
                "confidence": round(random.uniform(0.6, 0.95), 2),
                "recommendation": random.choice(["buy", "sell", "hold"]),
                "analysis": f"AI analysis for {symbol}: Market shows {'positive' if random.random() > 0.5 else 'negative'} momentum.",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def handle_client(self, websocket, path):
        """
        Handle individual client connections.
        NOTE: The handler signature MUST be (websocket, path) for websockets.serve.
        """
        client_id = id(websocket)
        logger.info(f"New client connected: {client_id}")
        
        try:
            # Add client to set
            self.clients.add(websocket)
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection_status",
                "status": "connected",
                "message": "Connected to fake crypto trading server"
            }))
            
            # Keep connection alive and send periodic data
            while self.running:
                try:
                    # Send trade data every 2 seconds
                    trade_data = await self.generate_trade_data()
                    await websocket.send(json.dumps(trade_data))
                    
                    # Send AI analysis every 5 seconds
                    if random.random() < 0.4:  # 40% chance
                        ai_data = await self.generate_ai_analysis()
                        await websocket.send(json.dumps(ai_data))
                    
                    await asyncio.sleep(2)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"Client {client_id} disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error sending data to client {client_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} removed from active connections")
    
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting fake crypto trading server on ws://{self.host}:{self.port}")
        
        self.running = True
        
        try:
            # Start the server
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            
            logger.info(f"Server started successfully on ws://{self.host}:{self.port}")
            logger.info("Press Ctrl+C to stop the server")
            
            # Keep the server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
        finally:
            self.running = False
            logger.info("Server stopped")

async def main():
    """Main function to run the server"""
    server = CryptoFakeServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 