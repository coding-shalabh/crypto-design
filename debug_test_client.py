#!/usr/bin/env python3
"""
Debug Test Client for Enhanced Fake Trading Server
==================================================

This client connects to the fake trading server and provides detailed debugging
to help identify any issues with the frontend connection and data flow.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List

import websockets

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DebugTestClient:
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.message_count = 0
        self.start_time = None
        
        # Track different message types
        self.message_types = {
            'price_update': 0,
            'trade_executed': 0,
            'ai_analysis': 0,
            'positions_update': 0,
            'bot_status': 0,
            'connection_status': 0,
            'other': 0
        }
        
    async def debug_log(self, message: str, emoji: str = "🔍"):
        """Log debug message with emoji and markers"""
        logger.info(f"-----{emoji} {message} -----")
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            await self.debug_log(f"CONNECTING TO SERVER: {self.uri}", "🔌")
            
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            self.start_time = time.time()
            
            await self.debug_log("CONNECTION ESTABLISHED SUCCESSFULLY", "✅")
            await self.debug_log("READY TO RECEIVE MESSAGES", "📡")
            
        except websockets.exceptions.ConnectionRefused:
            await self.debug_log("CONNECTION REFUSED - SERVER NOT RUNNING", "❌")
            raise
        except Exception as e:
            await self.debug_log(f"CONNECTION ERROR: {e}", "💥")
            raise
    
    async def receive_messages(self, duration: int = 60):
        """Receive and analyze messages for specified duration"""
        if not self.connected:
            await self.debug_log("NOT CONNECTED - CANNOT RECEIVE MESSAGES", "❌")
            return
        
        await self.debug_log(f"STARTING MESSAGE RECEPTION FOR {duration} SECONDS", "📥")
        
        try:
            while self.connected and (time.time() - self.start_time) < duration:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    
                    # Parse and analyze message
                    await self.analyze_message(message)
                    
                except asyncio.TimeoutError:
                    # No message received within timeout, continue
                    continue
                except websockets.exceptions.ConnectionClosed:
                    await self.debug_log("CONNECTION CLOSED BY SERVER", "🔌")
                    break
                except Exception as e:
                    await self.debug_log(f"ERROR RECEIVING MESSAGE: {e}", "❌")
                    break
            
            await self.debug_log("MESSAGE RECEPTION COMPLETED", "✅")
            
        except Exception as e:
            await self.debug_log(f"ERROR IN MESSAGE RECEPTION: {e}", "💥")
    
    async def analyze_message(self, message: str):
        """Analyze received message and log details"""
        self.message_count += 1
        
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            # Track message types
            if message_type in self.message_types:
                self.message_types[message_type] += 1
            else:
                self.message_types['other'] += 1
            
            # Log message details based on type
            await self.log_message_details(message_type, data)
            
        except json.JSONDecodeError as e:
            await self.debug_log(f"INVALID JSON RECEIVED: {e}", "⚠️")
            await self.debug_log(f"RAW MESSAGE: {message[:200]}...", "📄")
        except Exception as e:
            await self.debug_log(f"ERROR ANALYZING MESSAGE: {e}", "❌")
    
    async def log_message_details(self, message_type: str, data: Dict):
        """Log specific details for different message types"""
        if message_type == 'connection_status':
            await self.debug_log(f"CONNECTION STATUS: {data.get('status', 'unknown')}", "🔗")
            await self.debug_log(f"SERVER INFO: {data.get('server_info', {})}", "ℹ️")
            
        elif message_type == 'price_update':
            price_data = data.get('data', {})
            symbol = price_data.get('symbol', 'unknown')
            price = price_data.get('price', 0)
            change = price_data.get('change_24h', 0)
            await self.debug_log(f"PRICE UPDATE: {symbol} = ${price:.4f} ({change:+.2f}%)", "📈")
            
        elif message_type == 'trade_executed':
            trade_data = data.get('data', {})
            symbol = trade_data.get('symbol', 'unknown')
            direction = trade_data.get('direction', 'unknown')
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            await self.debug_log(f"TRADE EXECUTED: {direction} {amount} {symbol} @ ${price:.4f}", "💼")
            
        elif message_type == 'ai_analysis':
            ai_data = data.get('data', {})
            symbol = ai_data.get('symbol', 'unknown')
            sentiment = ai_data.get('sentiment', 'unknown')
            confidence = ai_data.get('confidence', 0)
            await self.debug_log(f"AI ANALYSIS: {symbol} - {sentiment.upper()} ({confidence*100:.0f}%)", "🤖")
            
        elif message_type == 'positions_update':
            pos_data = data.get('data', {})
            total_positions = pos_data.get('total_positions', 0)
            total_pnl = pos_data.get('total_pnl', 0)
            await self.debug_log(f"POSITIONS UPDATE: {total_positions} positions, P&L: ${total_pnl:.2f}", "📊")
            
        elif message_type == 'bot_status':
            bot_data = data.get('data', {})
            enabled = bot_data.get('enabled', False)
            strategy = bot_data.get('strategy', 'unknown')
            await self.debug_log(f"BOT STATUS: {'🟢 ENABLED' if enabled else '🔴 DISABLED'} - {strategy}", "🤖")
            
        else:
            await self.debug_log(f"UNKNOWN MESSAGE TYPE: {message_type}", "❓")
            await self.debug_log(f"MESSAGE DATA: {json.dumps(data, indent=2)}", "📄")
    
    async def send_test_message(self, message_type: str = "ping", data: Dict = None):
        """Send a test message to the server"""
        if not self.connected:
            await self.debug_log("NOT CONNECTED - CANNOT SEND MESSAGE", "❌")
            return
        
        test_message = {
            "type": message_type,
            "data": data or {"message": "Test from debug client"},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket.send(json.dumps(test_message))
            await self.debug_log(f"TEST MESSAGE SENT: {message_type}", "📤")
        except Exception as e:
            await self.debug_log(f"ERROR SENDING TEST MESSAGE: {e}", "❌")
    
    async def print_statistics(self):
        """Print message statistics"""
        duration = time.time() - self.start_time if self.start_time else 0
        
        await self.debug_log("MESSAGE STATISTICS", "📊")
        await self.debug_log(f"TOTAL MESSAGES RECEIVED: {self.message_count}", "📈")
        await self.debug_log(f"TEST DURATION: {duration:.1f} seconds", "⏱️")
        await self.debug_log(f"MESSAGES PER SECOND: {self.message_count/duration:.2f}" if duration > 0 else "N/A", "📊")
        
        await self.debug_log("MESSAGE TYPE BREAKDOWN:", "📋")
        for msg_type, count in self.message_types.items():
            if count > 0:
                percentage = (count / self.message_count * 100) if self.message_count > 0 else 0
                await self.debug_log(f"  {msg_type}: {count} ({percentage:.1f}%)", "📊")
    
    async def close(self):
        """Close the connection"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            await self.debug_log("CONNECTION CLOSED", "🔌")

async def main():
    """Main function to run the debug test client"""
    client = DebugTestClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Send a test message
        await client.send_test_message("ping", {"client": "debug_test"})
        
        # Receive messages for 30 seconds
        await client.receive_messages(duration=30)
        
        # Print statistics
        await client.print_statistics()
        
    except Exception as e:
        logger.error(f"-----💥 CLIENT ERROR: {e} -----")
    finally:
        await client.close()
        logger.info("-----👋 DEBUG TEST CLIENT SHUTDOWN COMPLETE -----")

if __name__ == "__main__":
    asyncio.run(main()) 