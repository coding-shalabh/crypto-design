"""
Main WebSocket server for crypto trading bot - FIXED VERSION
Addresses frequent disconnection issues
"""
import asyncio
import websockets
import json
import logging
import time
import weakref
from typing import Dict, Set
from weakref import WeakSet
from datetime import datetime
import signal

from config import Config
from database import DatabaseManager
from market_data import MarketDataManager
from news_analysis import NewsAnalysisManager
from ai_analysis import AIAnalysisManager
from trading_bot import TradingBot
from trade_execution import TradeExecutionManager
from bson import ObjectId

def safe_json_serialize(obj):
    """Safely serialize objects to JSON, handling ObjectId and other types"""
    def json_serializer(obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return str(obj)
    
    return json.dumps(obj, default=json_serializer)

# Configure logging with reduced output - only essential events
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trading_server.log')
    ]
)
logger = logging.getLogger(__name__)

class TradingServer:
    """Main trading server that orchestrates all components - FIXED VERSION"""
    
    def __init__(self):
        logger.info("Initializing Trading Server...")
        
        # Initialize all managers
        self.db = DatabaseManager()
        self.market_data = MarketDataManager()
        self.news_analysis = NewsAnalysisManager()
        self.ai_analysis = AIAnalysisManager()
        self.trading_bot = TradingBot()
        self.trade_execution = TradeExecutionManager(self.db)
        
        # 🔧 FIXED: Use WeakSet for automatic cleanup of dead connections
        self.clients = weakref.WeakSet()
        self._client_tasks = {}  # Track tasks per client
        
        # Analysis control
        self.analysis_enabled = False
        self.analysis_start_time = None
        
        # Background tasks
        self.background_tasks = []
        self._server_running = False
        self._shutdown_event = asyncio.Event()
        
        # 🔧 FIXED: Connection statistics for monitoring
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_handshakes': 0,
            'clean_disconnects': 0,
            'unexpected_disconnects': 0
        }
        
        logger.info("Trading Server initialization complete!")
        
    async def start_server(self):
        """Start the WebSocket server with proper signal handling"""
        try:
            logger.info(f"Starting WebSocket server on {Config.HOST}:{Config.PORT}")
            
            # 🔧 FIXED: Proper server configuration with ping/pong settings
            server = await websockets.serve(
                self.handle_client,
                Config.HOST,
                Config.PORT,
                ping_interval=20,      # Send ping every 20 seconds
                ping_timeout=10,       # Wait 10 seconds for pong
                close_timeout=10,      # Wait 10 seconds for close
                max_size=2**20,        # 1MB max message size
                max_queue=32,          # Max queue size
                compression=None       # Disable compression for speed
            )
            
            logger.info(f"WebSocket server started successfully")
            self._server_running = True
            
            # 🔧 FIXED: Set up signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in [signal.SIGTERM, signal.SIGINT]:
                loop.add_signal_handler(sig, self._signal_handler)
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.info("Server is ready! Waiting for client connections...")
            
            # 🔧 FIXED: Use shutdown event instead of wait_closed
            await self._shutdown_event.wait()
            
            # Graceful shutdown
            logger.info("Shutting down server...")
            server.close()
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise
        finally:
            self._server_running = False
    
    def _signal_handler(self):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal")
        self._shutdown_event.set()
    
    async def start_background_tasks(self):
        """Start background monitoring tasks with proper error handling"""
        try:
            # 🔧 FIXED: Create tasks with proper exception handling
            tasks = [
                ('market_data_updates', self.continuous_market_data_updates()),
                ('price_broadcasts', self.broadcast_price_updates()),
                ('connection_monitor', self.monitor_connections()),
                ('health_check', self.health_check_loop())
            ]
            
            for task_name, coro in tasks:
                task = asyncio.create_task(coro, name=task_name)
                # 🔧 FIXED: Add exception callback for background tasks
                task.add_done_callback(lambda t, name=task_name: self._handle_task_exception(t, name))
                self.background_tasks.append(task)
            
            # Start bot monitoring if enabled
            if self.trading_bot.bot_enabled:
                bot_task = asyncio.create_task(self.continuous_bot_monitoring(), name='bot_monitoring')
                bot_task.add_done_callback(lambda t: self._handle_task_exception(t, 'bot_monitoring'))
                self.background_tasks.append(bot_task)
            
            logger.info(f"Started {len(self.background_tasks)} background tasks")
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")
    
    def _handle_task_exception(self, task, task_name):
        """Handle exceptions in background tasks"""
        if task.cancelled():
            logger.info(f"Task {task_name} was cancelled")
            return
        
        try:
            task.result()
        except Exception as e:
            logger.error(f"Task {task_name} failed with exception: {e}")
            # 🔧 FIXED: Restart critical tasks
            if task_name in ['market_data_updates', 'price_broadcasts']:
                logger.info(f"Restarting critical task: {task_name}")
                # Restart the task after a delay
                asyncio.create_task(self._restart_task_after_delay(task_name, 5))
    
    async def _restart_task_after_delay(self, task_name, delay):
        """Restart a failed task after a delay"""
        await asyncio.sleep(delay)
        if not self._server_running:
            return
        
        try:
            if task_name == 'market_data_updates':
                task = asyncio.create_task(self.continuous_market_data_updates(), name=task_name)
            elif task_name == 'price_broadcasts':
                task = asyncio.create_task(self.broadcast_price_updates(), name=task_name)
            else:
                return
            
            task.add_done_callback(lambda t: self._handle_task_exception(t, task_name))
            self.background_tasks.append(task)
            logger.info(f"Restarted task: {task_name}")
        except Exception as e:
            logger.error(f"Failed to restart task {task_name}: {e}")
    
    async def monitor_connections(self):
        """Monitor connection health and cleanup dead connections"""
        while self._server_running:
            try:
                # 🔧 FIXED: Update connection statistics
                self.connection_stats['active_connections'] = len(self.clients)
                
                # Clean up dead client tasks
                dead_clients = []
                for client_id, tasks in self._client_tasks.items():
                    if not any(not task.done() for task in tasks):
                        dead_clients.append(client_id)
                
                for client_id in dead_clients:
                    del self._client_tasks[client_id]
                
                # Log connection stats every 5 minutes
                if int(time.time()) % 300 == 0:
                    logger.info(f"Connection stats: {self.connection_stats}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(60)
    
    async def health_check_loop(self):
        """Periodic health check for server components"""
        while self._server_running:
            try:
                # Check if critical components are responsive
                await asyncio.sleep(60)  # Health check every minute
                
                # Log system status
                logger.debug(f"Health check: Server running, {len(self.clients)} active clients")
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(120)
    
    async def handle_client(self, websocket, path="/"):
        """Handle WebSocket client connection with improved error handling"""
        client_id = id(websocket)
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        
        # 🔧 FIXED: Check connection limit early
        if len(self.clients) >= 50:
            logger.warning(f"Connection limit reached, rejecting client {client_id} from {client_ip}")
            await websocket.close(1013, "Too many connections")
            self.connection_stats['failed_handshakes'] += 1
            return
        
        try:
            # 🔧 FIXED: Add client to set early
            self.clients.add(websocket)
            self._client_tasks[client_id] = []
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] = len(self.clients)
            
            logger.info(f"Client {client_id} from {client_ip} connected. Total clients: {len(self.clients)}")
            
            # 🔧 FIXED: Send initial data with timeout
            try:
                await asyncio.wait_for(self.send_initial_data(websocket), timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"Initial data send timeout for client {client_id}")
                raise
            except Exception as e:
                logger.error(f"Error sending initial data to client {client_id}: {e}")
                raise
            
            # 🔧 FIXED: Improved message handling loop
            await self._handle_client_messages(websocket, client_id)
            
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"Client {client_id} disconnected normally")
            self.connection_stats['clean_disconnects'] += 1
        except websockets.exceptions.ConnectionClosedError as e:
            logger.info(f"Client {client_id} connection closed with error: {e}")
            self.connection_stats['unexpected_disconnects'] += 1
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} connection closed")
            self.connection_stats['clean_disconnects'] += 1
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            self.connection_stats['unexpected_disconnects'] += 1
        finally:
            # 🔧 FIXED: Comprehensive cleanup
            await self._cleanup_client(websocket, client_id)
    
    async def _handle_client_messages(self, websocket, client_id):
        """Handle messages from a client with proper error handling"""
        try:
            async for message in websocket:
                try:
                    # 🔧 FIXED: Add message size limit
                    if len(message) > 1024 * 1024:  # 1MB limit
                        logger.warning(f"Message too large from client {client_id}")
                        continue
                    
                    data = json.loads(message)
                    
                    # 🔧 FIXED: Process message in separate task to avoid blocking
                    task = asyncio.create_task(
                        self.handle_message(websocket, data, client_id),
                        name=f"message_handler_{client_id}"
                    )
                    self._client_tasks[client_id].append(task)
                    
                    # 🔧 FIXED: Limit number of concurrent tasks per client
                    if len(self._client_tasks[client_id]) > 10:
                        # Cancel oldest task if too many
                        oldest_task = self._client_tasks[client_id].pop(0)
                        if not oldest_task.done():
                            oldest_task.cancel()
                    
                    # 🔧 FIXED: Yield control to prevent blocking
                    await asyncio.sleep(0)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Client {client_id} sent invalid JSON")
                    try:
                        await websocket.send(safe_json_serialize({
                            'type': 'error',
                            'data': {'message': 'Invalid JSON format'}
                        }))
                    except:
                        break
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
                    try:
                        await websocket.send(safe_json_serialize({
                            'type': 'error',
                            'data': {'message': f'Error processing message: {str(e)}'}
                        }))
                    except:
                        break
                        
        except websockets.exceptions.ConnectionClosed:
            # Connection closed normally, let it bubble up
            raise
        except Exception as e:
            logger.error(f"Error in message handling loop for client {client_id}: {e}")
            raise

    async def handle_message(self, websocket, data, client_id=None):
        """Handle incoming WebSocket messages with improved error handling and yielding"""
        try:
            message_type = data.get('type')
            
            # 🔧 FIXED: Handle heartbeat messages
            if message_type == 'ping':
                try:
                    await websocket.send(safe_json_serialize({
                        'type': 'pong',
                        'timestamp': data.get('timestamp', time.time())
                    }))
                    return
                except:
                    pass  # If pong fails, connection will be closed anyway
            
            # 🔧 FIXED: Add yielding between message handling to prevent blocking
            await asyncio.sleep(0)
            
            if message_type == 'get_positions':
                positions = self.trade_execution.get_positions()
                balance = self.trade_execution.get_balance()
                await websocket.send(safe_json_serialize({
                    'type': 'positions_response',
                    'data': {
                        'balance': balance,
                        'positions': positions
                    }
                }))
                
            elif message_type == 'get_trade_history':
                limit = data.get('limit', 50)
                symbol = data.get('symbol')
                
                trades = self.trade_execution.get_recent_trades(limit)
                if symbol:
                    trades = [t for t in trades if t.get('symbol') == symbol]
                
                await websocket.send(safe_json_serialize({
                    'type': 'trade_history_response',
                    'data': {
                        'trades': trades
                    }
                }))
                
            elif message_type == 'get_crypto_data':
                symbol = data.get('symbol')
                if symbol:
                    crypto_data = self.market_data.get_all_crypto_data()
                    response_data = {symbol: crypto_data.get(symbol, {})}
                else:
                    response_data = self.market_data.get_all_crypto_data()
                
                await websocket.send(safe_json_serialize({
                    'type': 'crypto_data_response',
                    'data': response_data
                }))
                
            elif message_type == 'execute_trade':
                trade_data = data.get('trade_data', {})
                
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trade_execution.execute_paper_trade(trade_data)
                
                if result['success']:
                    logger.info(f"Trade executed successfully")
                    # Send trade executed response
                    await websocket.send(safe_json_serialize({
                        'type': 'trade_executed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions()
                        }
                    }))
                    
                    # Also send paper_trade_response for frontend compatibility
                    await websocket.send(safe_json_serialize({
                        'type': 'paper_trade_response',
                        'data': result
                    }))
                    
                    # 🔧 FIXED: Broadcast update asynchronously
                    asyncio.create_task(self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    }))
                else:
                    logger.error(f"Trade execution failed: {result['message']}")
                    await websocket.send(safe_json_serialize({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'paper_trade':
                trade_data = data.get('trade_data', {})
                logger.info(f"Received paper trade request: {trade_data}")
                
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trade_execution.execute_paper_trade(trade_data)
                
                if result['success']:
                    logger.info(f"Paper trade executed successfully")
                    # Send trade executed response
                    await websocket.send(safe_json_serialize({
                        'type': 'trade_executed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions()
                        }
                    }))
                    
                    # Also send paper_trade_response for frontend compatibility
                    await websocket.send(safe_json_serialize({
                        'type': 'paper_trade_response',
                        'data': result
                    }))
                    
                    # 🔧 FIXED: Broadcast update asynchronously
                    asyncio.create_task(self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    }))
                else:
                    logger.error(f"Paper trade execution failed: {result['message']}")
                    logger.error(f"Trade data received: {trade_data}")
                    await websocket.send(safe_json_serialize({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'close_position':
                symbol = data.get('symbol')
                
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trade_execution.close_position(symbol)
                
                if result['success']:
                    logger.info(f"Position closed successfully")
                    # Send position closed response
                    await websocket.send(safe_json_serialize({
                        'type': 'position_closed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions(),
                            'realized_pnl': result.get('profit_loss', 0)
                        }
                    }))
                    
                    # 🔧 FIXED: Broadcast update asynchronously
                    asyncio.create_task(self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    }))
                else:
                    logger.error(f"Position close failed: {result['message']}")
                    await websocket.send(safe_json_serialize({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'start_bot':
                config = data.get('config', {})
                
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trading_bot.start_bot(config)
                
                await websocket.send(safe_json_serialize({
                    'type': 'start_bot_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot started successfully")
                    
                    # Automatically start AI analysis when bot starts
                    if not self.analysis_enabled:
                        await self.start_analysis()
                    
                    # 🔧 FIXED: Broadcast update asynchronously
                    bot_status = await self.trading_bot.get_bot_status()
                    asyncio.create_task(self.broadcast_message('bot_status_update', {
                        'enabled': True,
                        'start_time': self.trading_bot.bot_start_time,
                        'config': self.trading_bot.bot_config,
                        'message': 'Trading bot started successfully'
                    }))
                else:
                    logger.error(f"Bot start failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'stop_bot':
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trading_bot.stop_bot()
                
                await websocket.send(safe_json_serialize({
                    'type': 'stop_bot_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot stopped successfully")
                    # 🔧 FIXED: Broadcast update asynchronously
                    asyncio.create_task(self.broadcast_message('bot_status_update', {
                        'enabled': False,
                        'message': 'Trading bot stopped'
                    }))
                else:
                    logger.error(f"Bot stop failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'get_bot_status':
                bot_status = await self.trading_bot.get_bot_status()
                
                await websocket.send(safe_json_serialize({
                    'type': 'bot_status_response',
                    'data': bot_status
                }))
                
            elif message_type == 'update_bot_config':
                new_config = data.get('config', {})
                
                # 🔧 FIXED: Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trading_bot.update_bot_config(new_config)
                
                await websocket.send(safe_json_serialize({
                    'type': 'update_bot_config_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot config updated successfully")
                else:
                    logger.error(f"Bot config update failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'start_analysis':
                result = await self.start_analysis()
                
                await websocket.send(safe_json_serialize({
                    'type': 'start_analysis_response',
                    'data': result
                }))
                
            elif message_type == 'stop_analysis':
                result = await self.stop_analysis()
                
                await websocket.send(safe_json_serialize({
                    'type': 'stop_analysis_response',
                    'data': result
                }))
                
            elif message_type == 'get_analysis_status':
                status = await self.get_analysis_status()
                
                await websocket.send(safe_json_serialize({
                    'type': 'analysis_status_response',
                    'data': status
                }))
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send(safe_json_serialize({
                    'type': 'error',
                    'data': {'message': f'Unknown message type: {message_type}'}
                }))
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await websocket.send(safe_json_serialize({
                    'type': 'error',
                    'data': {'message': str(e)}
                }))
            except:
                pass  # If we can't send error, connection is probably dead

    async def _cleanup_client(self, websocket, client_id):
        """Clean up client resources"""
        try:
            # Remove from clients set (WeakSet handles this automatically but let's be explicit)
            try:
                self.clients.discard(websocket)
            except:
                pass
            
            # Cancel and clean up client tasks
            if client_id in self._client_tasks:
                for task in self._client_tasks[client_id]:
                    if not task.done():
                        task.cancel()
                del self._client_tasks[client_id]
            
            # Update connection count
            self.connection_stats['active_connections'] = len(self.clients)
            
            logger.info(f"Client {client_id} cleanup complete. Active clients: {len(self.clients)}")
            
        except Exception as e:
            logger.error(f"Error during client cleanup for {client_id}: {e}")
    
    # 🔧 FIXED: Improved background task methods with proper yielding
    async def continuous_market_data_updates(self):
        """Continuously update market data with proper error handling"""
        while self._server_running:
            try:
                await self.market_data.fetch_crypto_data()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def broadcast_price_updates(self):
        """Broadcast price updates to all clients with throttling"""
        last_broadcast = 0
        while self._server_running:
            try:
                current_time = time.time()
                # 🔧 FIXED: Throttle broadcasts to every 5 seconds
                if current_time - last_broadcast < 5:
                    await asyncio.sleep(1)
                    continue
                
                # Get current prices
                prices = self.market_data.get_all_prices()
                
                if not prices:
                    await asyncio.sleep(10)
                    continue
                
                # 🔧 FIXED: Batch multiple updates into single message
                price_updates = []
                for symbol, price_data in prices.items():
                    price_value = price_data.get('price', 0) if isinstance(price_data, dict) else price_data
                    
                    crypto_data = self.market_data.get_all_crypto_data()
                    symbol_data = crypto_data.get(symbol, {})
                    
                    price_updates.append({
                        'symbol': symbol,
                        'price': price_value,
                        'change_24h': symbol_data.get('change_24h', 0),
                        'volume_24h': symbol_data.get('volume_24h', 0),
                        'timestamp': current_time
                    })
                
                # Send batched update
                if price_updates:
                    await self.broadcast_message('price_updates_batch', {
                        'updates': price_updates,
                        'timestamp': current_time
                    })
                
                last_broadcast = current_time
                await asyncio.sleep(5)  # 🔧 FIXED: Consistent 5-second intervals
                
            except Exception as e:
                logger.error(f"Error broadcasting price updates: {e}")
                await asyncio.sleep(10)  # Error recovery delay
    
    async def broadcast_message(self, message_type: str, data: Dict):
        """Broadcast message to all connected clients with improved error handling"""
        if not self.clients:
            return
        
        message = {
            'type': message_type,
            'data': data
        }
        
        try:
            # 🔧 FIXED: Create a list copy to avoid modification during iteration
            clients_copy = list(self.clients)
            if not clients_copy:
                return
            
            # 🔧 FIXED: Use safe JSON serialization
            serialized_message = safe_json_serialize(message)
            
            # 🔧 FIXED: Send messages concurrently with timeout
            send_tasks = []
            for client in clients_copy:
                task = asyncio.create_task(self._safe_send(client, serialized_message))
                send_tasks.append(task)
            
            # Wait for all sends to complete with timeout
            if send_tasks:
                await asyncio.wait(send_tasks, timeout=5, return_when=asyncio.ALL_COMPLETED)
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    
    async def _safe_send(self, client, message):
        """Safely send message to a client"""
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            # Client disconnected, remove from set
            self.clients.discard(client)
        except Exception as e:
            logger.warning(f"Error sending to client: {e}")
            self.clients.discard(client)
    
    async def send_initial_data(self, websocket):
        """Send initial data to new client with timeout"""
        try:
            # Get current data
            positions = self.trade_execution.get_positions()
            balance = self.trade_execution.get_balance()
            recent_trades = self.trade_execution.get_recent_trades(50)
            crypto_data = self.market_data.get_all_crypto_data()
            price_cache = self.market_data.get_all_prices()
            
            # Send comprehensive initial data
            initial_data = {
                'type': 'initial_data',
                'data': {
                    'paper_balance': balance,
                    'positions': positions,
                    'recent_trades': recent_trades,
                    'price_cache': price_cache,
                    'crypto_data': crypto_data,
                    'ai_insights': None
                }
            }
            await websocket.send(safe_json_serialize(initial_data))
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the server gracefully"""
        logger.info("Shutting down server...")
        self._server_running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close all client connections
        try:
            clients_copy = list(self.clients)
            for client in clients_copy:
                try:
                    await client.close()
                except:
                    pass
        except Exception as e:
            logger.warning(f"Error during client cleanup: {e}")
        
        logger.info("Server shutdown complete")

async def main():
    """Main function with proper signal handling"""
    logger.info("Trading Server v1.0 starting...")
    server = TradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")