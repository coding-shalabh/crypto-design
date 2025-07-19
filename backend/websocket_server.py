"""
Fixed WebSocket server for crypto trading bot
Addresses the process_limit and server startup issues
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
        
        # Use WeakSet for automatic cleanup of dead connections
        self.clients = weakref.WeakSet()
        
        # Analysis control
        self.analysis_enabled = False
        self.analysis_start_time = None
        
        # Background tasks
        self.background_tasks = []
        self._server_running = False
        self._shutdown_event = asyncio.Event()
        
        # Connection statistics for monitoring
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'failed_handshakes': 0,
            'clean_disconnects': 0,
            'unexpected_disconnects': 0
        }
        
        # Load persisted state on startup
        asyncio.create_task(self.load_persisted_state())
        
        logger.info("Trading Server initialization complete!")
        
    async def start_server(self):
        """Start the WebSocket server with proper signal handling and port conflict resolution"""
        server = None
        port = Config.PORT
        max_port_attempts = 10
        
        for attempt in range(max_port_attempts):
            try:
                logger.info(f"Attempting to start WebSocket server on {Config.HOST}:{port} (attempt {attempt + 1}/{max_port_attempts})")
                
                # FIXED: Simplified server configuration without unsupported parameters
                server = await websockets.serve(
                    self.handle_client,
                    Config.HOST,
                    port,
                    ping_interval=20,      # Send ping every 20 seconds
                    ping_timeout=10,       # Wait 10 seconds for pong
                    close_timeout=10,      # Wait 10 seconds for close
                    max_size=2**20,        # 1MB max message size
                    max_queue=32,          # Max queue size
                    compression=None       # Disable compression for speed
                    # REMOVED: process_limit - not supported in websockets library
                )
                
                logger.info(f" WebSocket server started successfully on port {port}")
                self._server_running = True
                
                # Start background tasks
                await self.start_background_tasks()
                
                logger.info(f" Server is ready on ws://{Config.HOST}:{port}! Waiting for client connections...")
                
                # Use shutdown event instead of wait_closed
                await self._shutdown_event.wait()
                break
                
            except OSError as e:
                if e.errno == 10048:  # Port already in use
                    logger.warning(f"Port {port} is already in use, trying port {port + 1}")
                    port += 1
                    if attempt == max_port_attempts - 1:
                        logger.error(f"Failed to find available port after {max_port_attempts} attempts")
                        raise
                    continue
                else:
                    logger.error(f"Error starting server: {e}")
                    logger.exception("Server startup error details:")
                    raise
            except Exception as e:
                logger.error(f"Error starting server: {e}")
                logger.exception("Server startup error details:")
                raise
            finally:
                if server:
                    logger.info("Shutting down server...")
                    server.close()
                    await server.wait_closed()
                self._server_running = False
    
    def _signal_handler(self):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal")
        self._shutdown_event.set()
    
    async def start_background_tasks(self):
        """Start background monitoring tasks with proper error handling"""
        try:
            # Create tasks with proper exception handling
            tasks = [
                ('market_data_updates', self.continuous_market_data_updates()),
                ('price_broadcasts', self.broadcast_price_updates()),
                ('connection_monitor', self.monitor_connections()),
                ('health_check', self.health_check_loop())
            ]
            
            for task_name, coro in tasks:
                task = asyncio.create_task(coro, name=task_name)
                # Add exception callback for background tasks
                task.add_done_callback(lambda t, name=task_name: self._handle_task_exception(t, name))
                self.background_tasks.append(task)
            
            # Start bot monitoring if enabled
            if self.trading_bot.bot_enabled:
                bot_task = asyncio.create_task(self.continuous_bot_monitoring(), name='bot_monitoring')
                bot_task.add_done_callback(lambda t: self._handle_task_exception(t, 'bot_monitoring'))
                self.background_tasks.append(bot_task)
                
                # Add continuous position monitoring task (every 5 minutes)
                position_monitor_task = asyncio.create_task(self.continuous_position_monitoring(), name='position_monitoring')
                position_monitor_task.add_done_callback(lambda t: self._handle_task_exception(t, 'position_monitoring'))
                self.background_tasks.append(position_monitor_task)
                
                # Add real-time PnL updates (every 30 seconds)
                pnl_update_task = asyncio.create_task(self.real_time_pnl_updates(), name='pnl_updates')
                pnl_update_task.add_done_callback(lambda t: self._handle_task_exception(t, 'pnl_updates'))
                self.background_tasks.append(pnl_update_task)
                
                # Add high-frequency auto-close monitoring (every 30 seconds)
                autoclose_monitor_task = asyncio.create_task(self.high_frequency_autoclose_monitoring(), name='autoclose_monitoring')
                autoclose_monitor_task.add_done_callback(lambda t: self._handle_task_exception(t, 'autoclose_monitoring'))
                self.background_tasks.append(autoclose_monitor_task)
            
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
            # Restart critical tasks
            if task_name in ['market_data_updates', 'price_broadcasts']:
                logger.info(f"Restarting critical task: {task_name}")
                # Restart the task after a delay
                if self._server_running:
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
                # Update connection statistics
                self.connection_stats['active_connections'] = len(self.clients)
                
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
        
        # Check connection limit early
        if len(self.clients) >= 50:
            logger.warning(f"Connection limit reached, rejecting client {client_id} from {client_ip}")
            await websocket.close(1013, "Too many connections")
            self.connection_stats['failed_handshakes'] += 1
            return
            
        try:
            # Add client to set early
            self.clients.add(websocket)
            self.connection_stats['total_connections'] += 1
            self.connection_stats['active_connections'] = len(self.clients)
            
            logger.info(f"Client {client_id} from {client_ip} connected. Total clients: {len(self.clients)}")
            
            # Send initial data with timeout
            try:
                await asyncio.wait_for(self.send_initial_data(websocket), timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"Initial data send timeout for client {client_id}")
                raise
            except Exception as e:
                logger.error(f"Error sending initial data to client {client_id}: {e}")
                raise
            
            # Improved message handling loop
            await self._handle_client_messages(websocket, client_id)
            
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"Client {client_id} disconnected normally")
            self.connection_stats['clean_disconnects'] += 1
        except websockets.exceptions.ConnectionClosedError as e:
            logger.info(f"Client {client_id} connection closed with error: {e}")
            self.connection_stats['unexpected_disconnects'] += 1
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
            logger.info(f"Client {client_id} connection closed")
            self.connection_stats['clean_disconnects'] += 1
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            self.connection_stats['unexpected_disconnects'] += 1
        finally:
            # Comprehensive cleanup
            await self._cleanup_client(websocket, client_id)
    
    async def _handle_client_messages(self, websocket, client_id):
        """Handle messages from a client with proper error handling"""
        try:
            async for message in websocket:
                try:
                    # Add message size limit
                    if len(message) > 1024 * 1024:  # 1MB limit
                        logger.warning(f"Message too large from client {client_id}")
                        continue
                    
                    data = json.loads(message)
                    
                    # Process message directly to avoid task handling issues
                    await self.handle_message(websocket, data)
                    
                    # Yield control to prevent blocking
                    await asyncio.sleep(0)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Client {client_id} sent invalid JSON")
                    try:
                        await self.safe_send(websocket, {
                            'type': 'error',
                            'data': {'message': 'Invalid JSON format'}
                        })
                    except:
                        break
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {str(e)}")
                    logger.exception(f"Full traceback for client {client_id}:")
                    try:
                        await self.safe_send(websocket, {
                            'type': 'error',
                            'data': {'message': f'Error processing message: {str(e)}'}
                        })
                    except:
                        break
                    
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
            # Connection closed normally, let it bubble up
            raise
        except Exception as e:
            logger.error(f"Error in message handling loop for client {client_id}: {e}")
            raise
    
    async def safe_send(self, websocket, message):
        """Safely send a message to a WebSocket connection"""
        try:
            await websocket.send(safe_json_serialize(message))
            return True
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError) as e:
            logger.debug(f"Connection closed while sending message: {e}")
            return False
        except Exception as e:
            logger.debug(f"Failed to send message: {e}")
            return False

    async def handle_message(self, websocket, data):
        """Handle incoming WebSocket messages with improved error handling and yielding"""
        try:
            message_type = data.get('type') or data.get('action')  # Support both type and action
            
            # Process the message - connection errors will be caught by exception handling
            
            # Handle heartbeat messages
            if message_type == 'ping':
                try:
                    await self.safe_send(websocket, {
                            'type': 'pong',
                            'timestamp': data.get('timestamp', time.time())
                        })
                    return
                except Exception as e:
                    logger.debug(f"Failed to send pong: {e}")
                    return  # Connection likely closed
            
            # Add yielding between message handling to prevent blocking
            await asyncio.sleep(0)
            
            if message_type == 'get_positions':
                positions = self.trade_execution.get_positions()
                balance = self.trade_execution.get_balance()
                await self.safe_send(websocket, {
                    'type': 'positions_response',
                    'data': {
                        'balance': balance,
                        'positions': positions
                    }
                })
                
            elif message_type == 'get_trade_history':
                limit = data.get('limit', 50)
                symbol = data.get('symbol')
                
                trades = self.trade_execution.get_recent_trades(limit)
                if symbol:
                    trades = [t for t in trades if t.get('symbol') == symbol]
                
                await self.safe_send(websocket, {
                    'type': 'trade_history_response',
                    'data': {
                        'trades': trades
                    }
                })
                
            elif message_type == 'get_crypto_data':
                symbol = data.get('symbol')
                if symbol:
                    crypto_data = self.market_data.get_all_crypto_data()
                    response_data = {symbol: crypto_data.get(symbol, {})}
                else:
                    response_data = self.market_data.get_all_crypto_data()
                
                await self.safe_send(websocket, {
                    'type': 'crypto_data_response',
                    'data': response_data
                })
                
            elif message_type == 'execute_trade':
                trade_data = data.get('trade_data', {})
                
                # Yield before heavy operation
                await asyncio.sleep(0)
                
                result = await self.trade_execution.execute_paper_trade(trade_data)
                
                if result['success']:
                    logger.info(f"Trade executed successfully")
                    # Send trade executed response
                    await self.safe_send(websocket, {
                        'type': 'trade_executed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions()
                        }
                    })
                    
                    # Also send paper_trade_response for frontend compatibility
                    await self.safe_send(websocket, {
                        'type': 'paper_trade_response',
                        'data': result
                    })
                    
                    # Broadcast update asynchronously
                    asyncio.create_task(self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    }))
                else:
                    logger.error(f"Trade execution failed: {result['message']}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': result['message']}
                    })
                    
            elif message_type == 'start_bot':
                bot_config = data.get('config', {})
                result = await self.trading_bot.start_bot(bot_config)
                await self.safe_send(websocket, {
                    'type': 'bot_start_response',
                    'data': result
                })
                
                # Broadcast updated bot status to all clients
                if result.get('success'):
                    bot_status = {
                        'enabled': getattr(self.trading_bot, 'bot_enabled', False),
                        'config': getattr(self.trading_bot, 'bot_config', {}),
                        'start_time': getattr(self.trading_bot, 'start_time', None),
                        'last_run': getattr(self.trading_bot, 'last_run', None),
                    }
                    await self.broadcast_message('bot_status_update', bot_status)
                    
                    # Start bot monitoring task if not already running
                    if not any(task.get_name() == 'bot_monitoring' for task in self.background_tasks if not task.done()):
                        logger.info("Starting bot monitoring task")
                        bot_task = asyncio.create_task(self.continuous_bot_monitoring(), name='bot_monitoring')
                        bot_task.add_done_callback(lambda t: self._handle_task_exception(t, 'bot_monitoring'))
                        self.background_tasks.append(bot_task)
                        
                        # Add position monitoring tasks
                        position_monitor_task = asyncio.create_task(self.continuous_position_monitoring(), name='position_monitoring')
                        position_monitor_task.add_done_callback(lambda t: self._handle_task_exception(t, 'position_monitoring'))
                        self.background_tasks.append(position_monitor_task)
                        
                        pnl_update_task = asyncio.create_task(self.real_time_pnl_updates(), name='pnl_updates')
                        pnl_update_task.add_done_callback(lambda t: self._handle_task_exception(t, 'pnl_updates'))
                        self.background_tasks.append(pnl_update_task)
                        
                        # Add high-frequency auto-close monitoring
                        autoclose_monitor_task = asyncio.create_task(self.high_frequency_autoclose_monitoring(), name='autoclose_monitoring')
                        autoclose_monitor_task.add_done_callback(lambda t: self._handle_task_exception(t, 'autoclose_monitoring'))
                        self.background_tasks.append(autoclose_monitor_task)
                
            elif message_type == 'stop_bot':
                result = await self.trading_bot.stop_bot()
                await self.safe_send(websocket, {
                    'type': 'bot_stop_response',
                    'data': result
                })
                
                # Cancel bot monitoring tasks immediately
                if result.get('success'):
                    # Cancel all bot monitoring tasks
                    for task in self.background_tasks:
                        if task.get_name() in ['bot_monitoring', 'position_monitoring', 'pnl_updates', 'autoclose_monitoring'] and not task.done():
                            task.cancel()
                            logger.info(f"Cancelled {task.get_name()} task")
                    
                    # Clear bot state immediately
                    self.trading_bot.bot_enabled = False
                    self.trading_bot.bot_active_trades.clear()
                    self.trading_bot.bot_pair_status.clear()
                    
                    # Save state to database
                    await self.save_persistent_state()
                    
                    # Broadcast updated bot status to all clients
                    bot_status = {
                        'enabled': False,
                        'config': getattr(self.trading_bot, 'bot_config', {}),
                        'start_time': None,
                        'last_run': getattr(self.trading_bot, 'last_run', None),
                        'active_trades': 0,
                        'pair_status': {}
                    }
                    await self.broadcast_message('bot_status_update', bot_status)
                    
                    # Send immediate confirmation
                    await self.broadcast_message('bot_stopped', {
                        'success': True,
                        'message': 'Bot stopped successfully',
                        'timestamp': time.time()
                    })
                
            elif message_type == 'update_bot_config':
                new_config = data.get('config', {})
                result = await self.trading_bot.update_bot_config(new_config)
                await self.safe_send(websocket, {
                    'type': 'bot_config_update_response',
                    'data': result
                })
                
            elif message_type == 'close_position':
                symbol = data.get('symbol')
                if symbol:
                    # Get current price for closing
                    current_price = self.market_data.get_cached_price(symbol.replace('USDT', '').lower())
                    
                    result = await self.trade_execution.close_position(symbol, current_price)
                    
                    # Send immediate response
                    await self.safe_send(websocket, {
                        'type': 'position_close_response',
                        'data': result
                    })
                    
                    # Remove from bot active trades if exists
                    if symbol in self.trading_bot.bot_active_trades:
                        del self.trading_bot.bot_active_trades[symbol]
                        self.trading_bot.bot_pair_status[symbol] = 'idle'
                    
                    # Broadcast position update immediately
                    await self.broadcast_message('position_update', {
                        'balance': self.trade_execution.get_balance(),
                        'positions': self.trade_execution.get_positions(),
                        'timestamp': time.time()
                    })
                    
                    # Send position closed confirmation
                    await self.broadcast_message('position_closed', {
                        'symbol': symbol,
                        'success': result.get('success', False),
                        'message': result.get('message', 'Position closed'),
                        'timestamp': time.time()
                    })
                    
                    logger.info(f"Position {symbol} closed via manual request")
                else:
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': 'Symbol is required for closing position'}
                    })
                
            elif message_type == 'get_bot_status':
                # Get complete bot status including config
                bot_status = await self.trading_bot.get_bot_status()
                
                # Add config and active trades to status response
                bot_status['config'] = self.trading_bot.bot_config
                bot_status['active_trades'] = list(self.trading_bot.bot_active_trades.values())
                
                await self.safe_send(websocket, {
                    'type': 'bot_status_response',
                    'data': bot_status
                })
                
            elif message_type == 'get_ai_analysis':
                # Handle AI analysis request for specific symbol
                symbol = data.get('symbol')
                if symbol:
                    try:
                        logger.info(f"Received AI analysis request for {symbol}")
                        
                        # Get market data for the symbol
                        market_data = self.market_data.get_all_crypto_data()
                        symbol_key = symbol.replace('USDT', '').lower()
                        
                        if symbol_key in market_data:
                            # Run AI analysis pipeline
                            analysis_result = await self.ai_analysis.run_ai_analysis_pipeline(symbol, market_data[symbol_key])
                            
                            # Log analysis to MongoDB
                            if analysis_result and hasattr(self, 'db') and self.db:
                                try:
                                    analysis_log = {
                                        'symbol': symbol,
                                        'analysis_type': 'ai_pipeline',
                                        'result': analysis_result,
                                        'source': 'user_request',
                                        'timestamp': time.time()
                                    }
                                    await self.db.log_analysis(analysis_log, user_id=28)
                                except Exception as e:
                                    logger.error(f"Error logging analysis: {e}")
                            
                            # Send response back to the requesting client
                            await self.safe_send(websocket, {
                                'type': 'ai_analysis_response',
                                'data': {
                                    'symbol': symbol,
                                    'analysis': analysis_result,
                                    'timestamp': time.time()
                                }
                            })
                            
                            logger.info(f"AI analysis completed and sent for {symbol}")
                        else:
                            await self.safe_send(websocket, {
                                'type': 'error',
                                'data': {'message': f'No market data available for {symbol}'}
                            })
                    except Exception as e:
                        logger.error(f"Error processing AI analysis request for {symbol}: {e}")
                        await self.safe_send(websocket, {
                            'type': 'error',
                            'data': {'message': f'Error processing AI analysis: {str(e)}'}
                        })
                else:
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': 'Symbol is required for AI analysis'}
                    })
                
            elif message_type == 'get_analysis_logs':
                # Handle analysis logs request
                try:
                    limit = data.get('limit', 50)
                    
                    # Get analysis logs from file or in-memory cache
                    analysis_logs = []
                    
                    # Try to read from log file
                    try:
                        with open('trading_server.log', 'r') as f:
                            lines = f.readlines()
                            for line in lines[-limit:]:
                                if any(keyword in line.lower() for keyword in ['ai analysis', 'analysis', 'gpt', 'claude', 'grok']):
                                    parts = line.strip().split(' ', 3)
                                    if len(parts) >= 4:
                                        analysis_logs.append({
                                            'timestamp': time.time(),
                                            'level': parts[2],
                                            'message': parts[3],
                                            'source': 'backend'
                                        })
                    except:
                        pass
                    
                    await self.safe_send(websocket, {
                        'type': 'analysis_logs_response',
                        'data': {'logs': analysis_logs}
                    })
                except Exception as e:
                    logger.error(f"Error getting analysis logs: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting analysis logs: {str(e)}'}
                    })
                    
            elif message_type == 'get_trade_logs':
                # Handle trade logs request (confidence scores, decisions)
                try:
                    limit = data.get('limit', 50)
                    
                    # Get trade logs from database
                    trade_logs = []
                    if hasattr(self, 'db') and self.db:
                        try:
                            # Get recent filter logs from database
                            logs = await self.db.get_recent_filter_logs(limit, user_id=28)
                            trade_logs = [
                                {
                                    'timestamp': log.get('timestamp', time.time()),
                                    'symbol': log.get('symbol', 'Unknown'),
                                    'final_confidence_score': log.get('final_confidence_score', 0),
                                    'confidence_above_threshold': log.get('confidence_above_threshold', False),
                                    'trade_decision': log.get('trade_decision', 'REJECTED'),
                                    'analysis_source': log.get('analysis_source', 'unknown'),
                                    'bot_enabled': log.get('bot_enabled', False)
                                }
                                for log in logs
                            ]
                        except Exception as e:
                            logger.warning(f"Could not get trade logs from database: {e}")
                    
                    await self.safe_send(websocket, {
                        'type': 'trade_logs_response',
                        'data': {'logs': trade_logs}
                    })
                except Exception as e:
                    logger.error(f"Error getting trade logs: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting trade logs: {str(e)}'}
                    })
                    
            # Trading bot configuration handlers
            elif message_type == 'get_bot_config':
                try:
                    config = self.trading_bot.get_config()
                    await self.safe_send(websocket, {
                        'type': 'bot_config',
                        'data': {
                            'config': config,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting bot config: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting bot config: {str(e)}'}
                    })
            
            elif message_type == 'update_bot_config':
                try:
                    new_config = data.get('config', {})
                    self.trading_bot.update_config(new_config)
                    await self.safe_send(websocket, {
                        'type': 'config_updated',
                        'data': {
                            'success': True,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error updating bot config: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error updating bot config: {str(e)}'}
                    })
            
            # Note: Removed duplicate/legacy start_bot and stop_bot handlers that were causing conflicts
            
            # Analysis request handler
            elif message_type == 'get_analysis':
                try:
                    symbol = data.get('symbol', 'BTCUSDT')
                    
                    # Get market data for the symbol
                    market_data = await self.market_data.get_market_data(symbol)
                    
                    if market_data:
                        # Run AI analysis
                        analysis_result = await self.ai_analysis.run_ai_analysis_pipeline(symbol, market_data)
                        
                        await self.safe_send(websocket, {
                            'type': 'analysis_complete',
                            'data': {
                                'symbol': symbol,
                                'analysis': analysis_result,
                                'timestamp': time.time()
                            }
                        })
                    else:
                        await self.safe_send(websocket, {
                            'type': 'error',
                            'data': {'message': f'No market data available for {symbol}'}
                        })
                except Exception as e:
                    logger.error(f"Error getting analysis: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting analysis: {str(e)}'}
                    })
            
            # Manual trade execution handler
            elif message_type == 'execute_trade':
                try:
                    symbol = data.get('symbol')
                    side = data.get('side')
                    amount = data.get('amount')
                    price = data.get('price')
                    trade_type = data.get('type', 'market')
                    
                    if not all([symbol, side, amount]):
                        await self.safe_send(websocket, {
                            'type': 'error',
                            'data': {'message': 'Symbol, side, and amount are required'}
                        })
                        return
                    
                    # Execute the trade
                    result = await self.trade_execution.execute_trade(symbol, side, amount, price, trade_type)
                    
                    await self.safe_send(websocket, {
                        'type': 'trade_executed',
                        'data': {
                            'trade_id': result.get('trade_id'),
                            'symbol': symbol,
                            'side': side,
                            'amount': amount,
                            'price': price,
                            'success': result.get('success', False),
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error executing trade: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error executing trade: {str(e)}'}
                    })
            
            # Market data handlers
            elif message_type == 'get_market_data':
                try:
                    symbol = data.get('symbol')
                    if symbol:
                        market_data = await self.market_data.get_market_data(symbol)
                    else:
                        market_data = await self.market_data.get_all_market_data()
                    
                    await self.safe_send(websocket, {
                        'type': 'market_data',
                        'data': {
                            'market_data': market_data,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting market data: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting market data: {str(e)}'}
                    })
            
            elif message_type == 'get_positions':
                try:
                    positions = self.trade_execution.get_positions()
                    await self.safe_send(websocket, {
                        'type': 'positions',
                        'data': {
                            'positions': positions,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting positions: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting positions: {str(e)}'}
                    })
            
            elif message_type == 'get_trading_history':
                try:
                    limit = data.get('limit', 50)
                    trades = self.trade_execution.get_recent_trades(limit)
                    await self.safe_send(websocket, {
                        'type': 'trading_history',
                        'data': {
                            'trades': trades,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting trading history: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting trading history: {str(e)}'}
                    })
            
            elif message_type == 'get_ai_analysis':
                try:
                    symbol = data.get('symbol', 'BTCUSDT')
                    
                    # Get cached analysis or run new analysis
                    analysis = self.ai_analysis.get_cached_analysis(symbol)
                    
                    if not analysis:
                        market_data = await self.market_data.get_market_data(symbol)
                        if market_data:
                            analysis = await self.ai_analysis.run_ai_analysis_pipeline(symbol, market_data)
                    
                    await self.safe_send(websocket, {
                        'type': 'ai_analysis',
                        'data': {
                            'symbol': symbol,
                            'analysis': analysis,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting AI analysis: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting AI analysis: {str(e)}'}
                    })
            
            elif message_type == 'get_logs':
                try:
                    limit = data.get('limit', 50)
                    
                    # Get recent logs
                    logs = []
                    try:
                        with open('trading_server.log', 'r') as f:
                            lines = f.readlines()
                            for line in lines[-limit:]:
                                logs.append({
                                    'timestamp': time.time(),
                                    'message': line.strip()
                                })
                    except FileNotFoundError:
                        logs = [{'timestamp': time.time(), 'message': 'No log file found'}]
                    
                    await self.safe_send(websocket, {
                        'type': 'logs',
                        'data': {
                            'logs': logs,
                            'timestamp': time.time()
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting logs: {e}")
                    await self.safe_send(websocket, {
                        'type': 'error',
                        'data': {'message': f'Error getting logs: {str(e)}'}
                    })
            
            # Add more message handlers here...
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await self.safe_send(websocket, {
                    'type': 'error',
                    'data': {'message': f'Unknown message type: {message_type}'}
                })
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            logger.exception("Full traceback for message handling:")
            try:
                await self.safe_send(websocket, {
                    'type': 'error',
                    'data': {'message': str(e)}
                })
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
            
            # Update connection count
            self.connection_stats['active_connections'] = len(self.clients)
            
            logger.info(f"Client {client_id} cleanup complete. Active clients: {len(self.clients)}")
            
        except Exception as e:
            logger.error(f"Error during client cleanup for {client_id}: {e}")
    
    # Background task methods with proper yielding
    async def continuous_market_data_updates(self):
        """Continuously update market data with proper error handling"""
        while self._server_running:
            try:
                await self.market_data.fetch_crypto_data()
                await asyncio.sleep(10)  # Update every 10 seconds for fresher data
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def broadcast_price_updates(self):
        """Broadcast price updates to all connected clients"""
        while True:
            try:
                if self.clients:
                    # Fetch latest market data
                    market_data = self.market_data.get_all_crypto_data()
                    
                    # If no data, fetch fresh data
                    if not market_data:
                        await self.market_data.fetch_crypto_data()
                        market_data = self.market_data.get_all_crypto_data()
                    
                    if market_data:
                        # Only log data fetching every 30 seconds instead of every time
                        current_time = time.time()
                        if not hasattr(self, '_last_data_log') or current_time - self._last_data_log > 30:
                            logger.info(f"Fetched data for {len(market_data)} symbols")
                            self._last_data_log = current_time
                        
                        # Broadcast to all clients
                        message = {
                            'type': 'price_updates_batch',
                            'data': market_data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Only log broadcasts every 60 seconds to reduce noise
                        if not hasattr(self, '_last_broadcast_log') or current_time - self._last_broadcast_log > 60:
                            logger.info(f"[BROADCAST] Sending price_updates_batch to {len(self.clients)} clients")
                            self._last_broadcast_log = current_time
                        
                        await self.broadcast_message('price_updates_batch', message)
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in price broadcast loop: {e}")
                await asyncio.sleep(5)
    
    async def broadcast_message(self, message_type: str, data: Dict):
        """Broadcast message to all connected clients with improved error handling"""
        if not self.clients:
            logger.warning(f"[BROADCAST] No clients connected to send {message_type}")
            return
        
        message = {
            'type': message_type,
            'data': data
        }
        
        logger.info(f"[BROADCAST] Sending {message_type} to {len(self.clients)} clients")
        
        try:
            # Create a list copy to avoid modification during iteration
            clients_copy = list(self.clients)
            if not clients_copy:
                return
            
            # Use safe JSON serialization
            serialized_message = safe_json_serialize(message)
            
            # Send messages concurrently with timeout
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
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
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
            await self.safe_send(websocket, initial_data)
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            raise
    
    def enrich_market_data_for_analysis(self, symbol: str, symbol_data: Dict) -> Dict:
        """Enrich market data with required fields for AI analysis"""
        try:
            current_price = symbol_data.get('current_price', 0)
            change_24h = symbol_data.get('price_change_percentage_24h', 0)
            volume_24h = symbol_data.get('total_volume', 0)
            
            # Generate mock price history for analysis if not available
            prices = symbol_data.get('prices', [])
            if len(prices) < 50:
                # Generate simple price history based on current price and 24h change
                prices = []
                base_price = current_price
                for i in range(50):
                    # Simple random walk with trend
                    trend_factor = change_24h / 100 / 50  # Distribute 24h change over 50 periods
                    random_factor = (hash(f"{symbol}_{i}") % 200 - 100) / 10000  # Simple pseudo-random
                    price = base_price * (1 + trend_factor + random_factor)
                    prices.append(price)
                    base_price = price
                
                logger.info(f"Generated {len(prices)} price points for {symbol} analysis")
            
            # Generate mock candle data if not available
            candles = symbol_data.get('candles', [])
            if len(candles) < 20:
                candles = []
                for i in range(20):
                    price = prices[i * 2] if i * 2 < len(prices) else current_price
                    candles.append({
                        'open': price * 0.995,
                        'high': price * 1.005,
                        'low': price * 0.99,
                        'close': price,
                        'volume': volume_24h / 20 if volume_24h > 0 else 1000
                    })
                
                logger.info(f"Generated {len(candles)} candle data points for {symbol} analysis")
            
            # Create enriched data
            enriched_data = {
                'symbol': symbol,
                'current_price': current_price,
                'change_24h': change_24h,
                'volume_24h': volume_24h,
                'prices': prices,
                'candles': candles,
                **symbol_data  # Include original data
            }
            
            logger.info(f"Enriched market data for {symbol}: {len(prices)} prices, {len(candles)} candles")
            return enriched_data
            
        except Exception as e:
            logger.error(f"Error enriching market data for {symbol}: {e}")
            return symbol_data  # Return original data if enrichment fails
    
    def should_skip_pair_analysis(self, symbol: str) -> bool:
        """Check if pair should be skipped from analysis"""
        # Check if we should analyze all pairs regardless of active trades
        analyze_all = self.trading_bot.bot_config.get('analyze_all_pairs', True)
        
        # Only skip if pair is in cooldown period (for new trades, not analysis)
        if symbol in self.trading_bot.bot_cooldown_end:
            if time.time() < self.trading_bot.bot_cooldown_end[symbol]:
                remaining = self.trading_bot.bot_cooldown_end[symbol] - time.time()
                logger.info(f"[COOLDOWN] {symbol} in cooldown, {remaining:.0f}s remaining")
                return True
        
        # Log if pair has active trade but still performing analysis
        if symbol in self.trading_bot.bot_active_trades and analyze_all:
            logger.info(f"[ANALYSIS] {symbol} has active trade, but performing analysis as scheduled")
        
        return False
    
    async def run_pair_analysis(self, symbol: str, enriched_data: dict):
        """Run AI analysis for a single pair"""
        try:
            logger.info(f"Starting AI analysis for {symbol}")
            
            # Run AI analysis pipeline
            analysis_result = await self.ai_analysis.run_ai_analysis_pipeline(symbol, enriched_data)
            
            if analysis_result:
                return analysis_result
            else:
                logger.warning(f"AI analysis failed for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error in AI analysis for {symbol}: {e}")
            raise e
    
    async def monitor_active_trades(self):
        """Monitor active trades for stop loss, take profit, and rollback conditions"""
        if not self.trading_bot.bot_active_trades:
            return
        
        logger.info(f"[MONITOR] Monitoring {len(self.trading_bot.bot_active_trades)} active trades")
        
        for symbol, trade_data in list(self.trading_bot.bot_active_trades.items()):
            try:
                # Get current price
                current_price = self.market_data.get_cached_price(symbol.replace('USDT', '').lower())
                if not current_price:
                    logger.warning(f"[MONITOR] No current price for {symbol}")
                    continue
                
                entry_price = trade_data.get('entry_price', trade_data.get('price', 0))
                trade_amount = trade_data.get('amount', trade_data.get('value_usdt', 0))
                direction = trade_data.get('action', 'BUY')
                
                # Calculate PnL
                if direction == 'BUY':
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    pnl_usd = (current_price - entry_price) * (trade_amount / entry_price)
                else:  # SELL
                    pnl_percent = ((entry_price - current_price) / entry_price) * 100
                    pnl_usd = (entry_price - current_price) * (trade_amount / entry_price)
                
                logger.info(f"[MONITOR] {symbol}: Entry=${entry_price:.2f}, Current=${current_price:.2f}, PnL={pnl_percent:.2f}% (${pnl_usd:.2f})")
                
                # Check stop loss condition
                stop_loss_percent = self.trading_bot.bot_config.get('stop_loss_percent', 2)
                if pnl_percent <= -stop_loss_percent:
                    logger.warning(f"🛑 [AUTO-CLOSE] {symbol} hit STOP LOSS at {pnl_percent:.2f}% (Target: -{stop_loss_percent}%)")
                    await self.close_trade_due_to_stop_loss(symbol, trade_data, current_price, pnl_usd)
                    continue
                
                # Check take profit and trailing profit conditions
                profit_target_max = self.trading_bot.bot_config.get('profit_target_max', 5)
                profit_target_min = self.trading_bot.bot_config.get('profit_target_min', 1)
                trailing_enabled = self.trading_bot.bot_config.get('trailing_enabled', True)
                
                # Initialize trailing data if not exists
                if not hasattr(self.trading_bot, 'trailing_data'):
                    self.trading_bot.trailing_data = {}
                
                if symbol not in self.trading_bot.trailing_data:
                    self.trading_bot.trailing_data[symbol] = {
                        'highest_profit': pnl_usd,
                        'current_target': profit_target_min,
                        'trailing_active': False
                    }
                
                trailing_data = self.trading_bot.trailing_data[symbol]
                
                # Update highest profit achieved
                if pnl_usd > trailing_data['highest_profit']:
                    trailing_data['highest_profit'] = pnl_usd
                
                # Check if trailing should be activated
                if trailing_enabled and pnl_usd >= profit_target_min and not trailing_data['trailing_active']:
                    logger.info(f"[TRAILING] {symbol} activating trailing profit at ${pnl_usd:.2f}")
                    trailing_data['trailing_active'] = True
                    trailing_data['current_target'] = profit_target_min
                
                # Trailing profit logic
                if trailing_data['trailing_active']:
                    # Check if we should increase target (when profit reaches 99% of max target)
                    if pnl_usd >= (trailing_data['current_target'] * 0.99):
                        confidence = trade_data.get('analysis_confidence', 0)
                        if confidence > 0.8:  # High confidence - increase target
                            new_target = min(trailing_data['current_target'] * 2, profit_target_max)
                            if new_target > trailing_data['current_target']:
                                logger.info(f"[TRAILING] {symbol} increasing target from ${trailing_data['current_target']:.2f} to ${new_target:.2f}")
                                trailing_data['current_target'] = new_target
                    
                    # Check if we should close based on trailing stop
                    trailing_stop_price = trailing_data['highest_profit'] * 0.8  # 20% trailing stop
                    if pnl_usd <= trailing_stop_price:
                        logger.info(f"📉 [AUTO-CLOSE] {symbol} hit TRAILING STOP at ${pnl_usd:.2f} (Peak: ${trailing_data['highest_profit']:.2f})")
                        await self.close_trade_due_to_profit(symbol, trade_data, current_price, pnl_usd)
                        continue
                
                # Regular take profit check (without trailing)
                if not trailing_enabled and pnl_usd >= profit_target_min:
                    logger.info(f"💰 [AUTO-CLOSE] {symbol} hit PROFIT TARGET at ${pnl_usd:.2f} (Target: ${profit_target_min:.2f})")
                    await self.close_trade_due_to_profit(symbol, trade_data, current_price, pnl_usd)
                    continue
                
                # Also check simple profit target for trailing mode if profit is high enough
                if trailing_enabled and not trailing_data['trailing_active'] and pnl_usd >= profit_target_min:
                    logger.info(f"💰 [AUTO-CLOSE] {symbol} hit MINIMUM PROFIT TARGET at ${pnl_usd:.2f} (Target: ${profit_target_min:.2f})")
                    await self.close_trade_due_to_profit(symbol, trade_data, current_price, pnl_usd)
                    continue
                
                # Check rollback condition
                loss_check_interval = self.trading_bot.bot_config.get('loss_check_interval_percent', 1)
                if pnl_percent <= -loss_check_interval and self.trading_bot.bot_config.get('rollback_enabled', True):
                    logger.warning(f"[ROLLBACK_CHECK] {symbol} losing {pnl_percent:.2f}%, checking for rollback")
                    await self.check_rollback_condition(symbol, trade_data, current_price, pnl_percent)
                
            except Exception as e:
                logger.error(f"[MONITOR] Error monitoring {symbol}: {e}")
    
    async def close_trade_due_to_stop_loss(self, symbol: str, trade_data: dict, current_price: float, pnl_usd: float):
        """Close trade due to stop loss"""
        try:
            logger.info(f"[CLOSE_SL] Closing {symbol} due to stop loss")
            
            # Remove from active trades
            if symbol in self.trading_bot.bot_active_trades:
                del self.trading_bot.bot_active_trades[symbol]
            
            # Clean up trailing data
            if hasattr(self.trading_bot, 'trailing_data') and symbol in self.trading_bot.trailing_data:
                del self.trading_bot.trailing_data[symbol]
            
            # Update pair status
            self.trading_bot.bot_pair_status[symbol] = 'idle'
            
            # Close position in paper trading
            close_result = await self.trade_execution.close_position(symbol, current_price)
            
            # Update bot statistics
            self.trading_bot.bot_total_profit += pnl_usd
            if pnl_usd > 0:
                self.trading_bot.bot_winning_trades += 1
            
            # Broadcast trade closure with enhanced notification
            await self.broadcast_message('trade_closed', {
                'symbol': symbol,
                'reason': 'stop_loss',
                'pnl_usd': pnl_usd,
                'close_price': current_price,
                'timestamp': time.time(),
                'auto_close': True,
                'notification': f"🛑 AUTO-CLOSE: {symbol} stopped out at ${pnl_usd:.2f} loss"
            })
            
            # Send dedicated auto-close notification
            await self.broadcast_message('auto_close_notification', {
                'type': 'stop_loss',
                'symbol': symbol,
                'pnl_usd': pnl_usd,
                'close_price': current_price,
                'message': f"🛑 {symbol} automatically closed due to STOP LOSS: ${pnl_usd:.2f}",
                'timestamp': time.time()
            })
            
            # Broadcast updated positions
            await self.broadcast_message('position_update', {
                'balance': self.trade_execution.get_balance(),
                'positions': self.trade_execution.get_positions()
            })
            
            logger.info(f"🛑 [AUTO-CLOSE] Successfully closed {symbol} with STOP LOSS: ${pnl_usd:.2f}")
            
        except Exception as e:
            logger.error(f"[CLOSE_SL] Error closing {symbol}: {e}")
    
    async def close_trade_due_to_profit(self, symbol: str, trade_data: dict, current_price: float, pnl_usd: float):
        """Close trade due to profit target"""
        try:
            logger.info(f"[CLOSE_TP] Closing {symbol} due to profit target")
            
            # Remove from active trades
            if symbol in self.trading_bot.bot_active_trades:
                del self.trading_bot.bot_active_trades[symbol]
            
            # Clean up trailing data
            if hasattr(self.trading_bot, 'trailing_data') and symbol in self.trading_bot.trailing_data:
                del self.trading_bot.trailing_data[symbol]
            
            # Update pair status
            self.trading_bot.bot_pair_status[symbol] = 'idle'
            
            # Close position in paper trading
            close_result = await self.trade_execution.close_position(symbol, current_price)
            
            # Update bot statistics
            self.trading_bot.bot_total_profit += pnl_usd
            if pnl_usd > 0:
                self.trading_bot.bot_winning_trades += 1
            
            # Broadcast trade closure with enhanced notification
            await self.broadcast_message('trade_closed', {
                'symbol': symbol,
                'reason': 'take_profit',
                'pnl_usd': pnl_usd,
                'close_price': current_price,
                'timestamp': time.time(),
                'auto_close': True,
                'notification': f"💰 AUTO-CLOSE: {symbol} profit target reached: ${pnl_usd:.2f}"
            })
            
            # Send dedicated auto-close notification
            await self.broadcast_message('auto_close_notification', {
                'type': 'take_profit',
                'symbol': symbol,
                'pnl_usd': pnl_usd,
                'close_price': current_price,
                'message': f"💰 {symbol} automatically closed due to PROFIT TARGET: ${pnl_usd:.2f}",
                'timestamp': time.time()
            })
            
            # Broadcast updated positions
            await self.broadcast_message('position_update', {
                'balance': self.trade_execution.get_balance(),
                'positions': self.trade_execution.get_positions()
            })
            
            logger.info(f"💰 [AUTO-CLOSE] Successfully closed {symbol} with PROFIT TARGET: ${pnl_usd:.2f}")
            
        except Exception as e:
            logger.error(f"[CLOSE_TP] Error closing {symbol}: {e}")
    
    async def check_rollback_condition(self, symbol: str, trade_data: dict, current_price: float, pnl_percent: float):
        """Check if trade should be rolled back based on reanalysis"""
        try:
            # Check if enough time has passed since last reanalysis
            reanalysis_cooldown = self.trading_bot.bot_config.get('reanalysis_cooldown_seconds', 300)
            last_reanalysis = getattr(self.trading_bot, 'last_reanalysis_time', {}).get(symbol, 0)
            
            if time.time() - last_reanalysis < reanalysis_cooldown:
                logger.info(f"[ROLLBACK] {symbol} reanalysis in cooldown")
                return
            
            logger.info(f"[ROLLBACK] Running reanalysis for {symbol}")
            
            # Get current market data
            symbol_key = symbol.replace('USDT', '').lower()
            market_data = self.market_data.get_all_crypto_data()
            
            if symbol_key not in market_data:
                logger.warning(f"[ROLLBACK] No market data for {symbol}")
                return
            
            # Enrich market data
            enriched_data = self.enrich_market_data_for_analysis(symbol, market_data[symbol_key])
            
            # Run AI analysis
            analysis_result = await self.ai_analysis.run_ai_analysis_pipeline(symbol, enriched_data)
            
            if analysis_result:
                final_rec = analysis_result.get('final_recommendation', {})
                new_action = final_rec.get('action', 'HOLD')
                new_confidence = analysis_result.get('combined_confidence', 0)
                
                # Check if recommendation has changed
                original_direction = trade_data.get('direction', 'LONG')
                original_action = 'BUY' if original_direction == 'LONG' else 'SELL'
                
                if new_action != original_action and new_confidence >= self.trading_bot.bot_config.get('ai_confidence_threshold', 0.5):
                    logger.warning(f"[ROLLBACK] {symbol} recommendation changed from {original_action} to {new_action}")
                    await self.execute_rollback_strategy(symbol, trade_data, current_price, new_action, new_confidence)
                else:
                    logger.info(f"[ROLLBACK] {symbol} recommendation unchanged, continuing trade")
                
                # Update last reanalysis time
                if not hasattr(self.trading_bot, 'last_reanalysis_time'):
                    self.trading_bot.last_reanalysis_time = {}
                self.trading_bot.last_reanalysis_time[symbol] = time.time()
            
        except Exception as e:
            logger.error(f"[ROLLBACK] Error in rollback check for {symbol}: {e}")
    
    async def execute_rollback_strategy(self, symbol: str, trade_data: dict, current_price: float, new_action: str, new_confidence: float):
        """Execute rollback strategy by closing current trade and opening opposite"""
        try:
            logger.info(f"[ROLLBACK] Executing rollback strategy for {symbol}")
            
            # Calculate current PnL
            entry_price = trade_data.get('price', 0)
            direction = trade_data.get('direction', 'LONG')
            
            if direction == 'LONG':
                pnl_usd = (current_price - entry_price) * trade_data.get('amount', 0)
            else:
                pnl_usd = (entry_price - current_price) * trade_data.get('amount', 0)
            
            # Close current trade
            await self.close_trade_due_to_rollback(symbol, trade_data, current_price, pnl_usd)
            
            # Wait a moment before opening new trade
            await asyncio.sleep(1)
            
            # Open opposite trade if conditions are met
            if new_confidence >= self.trading_bot.bot_config.get('ai_confidence_threshold', 0.5):
                logger.info(f"[ROLLBACK] Opening opposite {new_action} trade for {symbol}")
                
                # Create new trade data
                new_trade_data = {
                    'symbol': symbol,
                    'direction': 'LONG' if new_action == 'BUY' else 'SHORT',
                    'trade_type': 'buy' if new_action == 'BUY' else 'sell',
                    'amount': self.trading_bot.bot_config.get('trade_amount_usdt', 50) / current_price,
                    'price': current_price,
                    'value_usdt': self.trading_bot.bot_config.get('trade_amount_usdt', 50),
                    'timestamp': time.time(),
                    'bot_trade': True,
                    'rollback_trade': True,
                    'analysis_confidence': new_confidence,
                    'trade_id': f"rollback_trade_{int(time.time())}_{symbol}"
                }
                
                # Execute new trade
                paper_trade_result = await self.trade_execution.execute_paper_trade(new_trade_data)
                
                if paper_trade_result.get('success'):
                    # Update bot state
                    self.trading_bot.bot_active_trades[symbol] = new_trade_data
                    self.trading_bot.bot_pair_status[symbol] = 'in_trade'
                    
                    # Broadcast rollback trade
                    await self.broadcast_message('rollback_trade_executed', {
                        'symbol': symbol,
                        'action': new_action,
                        'price': current_price,
                        'confidence': new_confidence,
                        'timestamp': time.time()
                    })
                    
                    logger.info(f"[ROLLBACK] Successfully executed rollback trade for {symbol}")
                else:
                    logger.error(f"[ROLLBACK] Failed to execute rollback trade for {symbol}")
            
        except Exception as e:
            logger.error(f"[ROLLBACK] Error executing rollback for {symbol}: {e}")
    
    async def close_trade_due_to_rollback(self, symbol: str, trade_data: dict, current_price: float, pnl_usd: float):
        """Close trade due to rollback strategy"""
        try:
            logger.info(f"[CLOSE_RB] Closing {symbol} due to rollback")
            
            # Remove from active trades
            if symbol in self.trading_bot.bot_active_trades:
                del self.trading_bot.bot_active_trades[symbol]
            
            # Update pair status temporarily
            self.trading_bot.bot_pair_status[symbol] = 'rollback'
            
            # Close position in paper trading
            close_result = await self.trade_execution.close_position(symbol, current_price)
            
            # Broadcast trade closure
            await self.broadcast_message('trade_closed', {
                'symbol': symbol,
                'reason': 'rollback',
                'pnl_usd': pnl_usd,
                'close_price': current_price,
                'timestamp': time.time()
            })
            
            logger.info(f"[CLOSE_RB] Successfully closed {symbol} for rollback with PnL: ${pnl_usd:.2f}")
            
        except Exception as e:
            logger.error(f"[CLOSE_RB] Error closing {symbol}: {e}")
    
    async def continuous_bot_monitoring(self):
        """Monitor trading bot and trigger AI analysis"""
        logger.info("Starting bot monitoring and AI analysis loop")
        
        while self._server_running and self.trading_bot.bot_enabled:
            try:
                # Check if bot is still enabled
                if not self.trading_bot.bot_enabled:
                    logger.info("Bot was disabled, stopping monitoring")
                    break
                
                logger.info(f"Bot is enabled, running AI analysis for configured pairs at {datetime.now().strftime('%H:%M:%S')}")
                
                # Get current market data
                market_data = self.market_data.get_all_crypto_data()
                
                # Debug logging
                logger.info(f"Available market data symbols: {list(market_data.keys())}")
                logger.info(f"Bot allowed pairs: {self.trading_bot.bot_config.get('allowed_pairs', [])}")
                
                # Run AI analysis for all allowed pairs concurrently
                allowed_pairs = self.trading_bot.bot_config.get('allowed_pairs', [])
                analysis_tasks = []
                
                for symbol in allowed_pairs:
                    # Convert symbol to match market data format
                    symbol_key = symbol.replace('USDT', '').lower()  # BTCUSDT -> btc
                    
                    if symbol_key in market_data:
                        # Check if pair should be skipped (only for cooldown, not active trades)
                        if self.should_skip_pair_analysis(symbol):
                            logger.info(f"[SKIP] {symbol} in cooldown, skipping analysis")
                            continue
                        
                        # Get symbol-specific market data
                        symbol_data = market_data[symbol_key]
                        
                        # Enrich market data with required fields for analysis
                        enriched_data = self.enrich_market_data_for_analysis(symbol, symbol_data)
                        
                        # Create analysis task
                        analysis_tasks.append(self.run_pair_analysis(symbol, enriched_data))
                    else:
                        logger.warning(f"[SKIP] {symbol} not available in market data")
                
                # Run all analysis tasks concurrently
                if analysis_tasks:
                    # Get the actual symbols being analyzed (not all allowed pairs)
                    analyzed_symbols = []
                    for symbol in allowed_pairs:
                        symbol_key = symbol.replace('USDT', '').lower()
                        if symbol_key in market_data and not self.should_skip_pair_analysis(symbol):
                            analyzed_symbols.append(symbol)
                    
                    logger.info(f"Starting concurrent AI analysis for {len(analysis_tasks)} pairs: {analyzed_symbols}")
                    analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                    
                    # Process results
                    for i, result in enumerate(analysis_results):
                        if not isinstance(result, Exception) and result:
                            symbol = allowed_pairs[i]
                            logger.info(f"AI analysis completed for {symbol}")
                            
                            # Log analysis to MongoDB
                            if hasattr(self, 'db') and self.db:
                                try:
                                    analysis_log = {
                                        'symbol': symbol,
                                        'analysis_type': 'bot_monitoring',
                                        'result': result,
                                        'source': 'bot_continuous_analysis',
                                        'timestamp': time.time()
                                    }
                                    await self.db.log_analysis(analysis_log, user_id=28)
                                except Exception as e:
                                    logger.error(f"Error logging bot analysis: {e}")
                            
                            # Broadcast analysis result to all clients  
                            await self.broadcast_message('ai_analysis_response', {
                                'symbol': symbol,
                                'analysis': result,
                                'timestamp': time.time()
                            })
                            
                            # Extract recommendation details first
                            final_rec = result.get('final_recommendation', {})
                            action = final_rec.get('action', 'HOLD')
                            confidence = float(final_rec.get('confidence', 0))
                            
                            # Create a properly formatted analysis log entry for frontend
                            analysis_log_entry = {
                                'timestamp': time.time() * 1000,  # Frontend expects milliseconds
                                'symbol': symbol,
                                'level': 'info',
                                'message': f"🧠 AI Analysis: {symbol} -> {action} ({confidence:.2f} confidence)",
                                'source': 'Bot Analysis',
                                'action': action,
                                'confidence': confidence,
                                'analysis_source': result.get('source', 'unknown')
                            }
                            
                            # Send analysis log to all clients
                            await self.broadcast_message('analysis_log', analysis_log_entry)
                            
                            # Check if analysis suggests a trade
                            
                            # Check for HOLD override with high confidence
                            if action == 'HOLD' and confidence >= self.trading_bot.bot_config.get('ai_confidence_threshold', 0.7):
                                logger.info(f"AI suggests HOLD for {symbol} with {confidence:.2f} confidence - checking for override")
                                if self.trading_bot._should_override_hold(action, confidence):
                                    action = self.trading_bot._get_override_action(confidence)
                                    logger.info(f"Overriding HOLD to {action} for {symbol} due to high confidence {confidence:.2f}")
                            
                            if action in ['BUY', 'SELL'] and confidence >= self.trading_bot.bot_config.get('ai_confidence_threshold', 0.7):
                                logger.info(f"AI suggests {action} for {symbol} with {confidence:.2f} confidence")
                                
                                # Broadcast trade opportunity
                                await self.broadcast_message('ai_opportunity_alert', {
                                    'symbol': symbol,
                                    'action': action,
                                    'confidence': confidence,
                                    'analysis': result,
                                    'timestamp': time.time()
                                })
                                
                                # Implement automatic trade execution based on bot config
                                logger.info(f"[EXEC] Checking trade execution for {symbol}: manual_approval_mode={self.trading_bot.bot_config.get('manual_approval_mode', False)}")
                                if not self.trading_bot.bot_config.get('manual_approval_mode', False):
                                    # Check if bot should execute this trade
                                    logger.info(f"[CHECK] Checking trading conditions for {symbol}")
                                    should_execute = await self.trading_bot.check_bot_trading_conditions(symbol, result)
                                    logger.info(f"[RESULT] Trading conditions result for {symbol}: {should_execute}")
                                    
                                    if should_execute:
                                        logger.info(f"Executing automatic trade: {action} {symbol} @ {confidence:.2f} confidence")
                                        
                                        # Get current market data for pricing
                                        current_price = self.market_data.get_cached_price(symbol.replace('USDT', '').lower())
                                        if current_price:
                                            # Get current balance
                                            current_balance = self.trade_execution.get_balance()
                                            
                                            # Execute the trade
                                            trade_result = await self.trading_bot.execute_bot_trade(symbol, result, current_price, current_balance)
                                            
                                            if trade_result.get('success'):
                                                logger.info(f"[SUCCESS] Automated trade executed successfully: {trade_result}")
                                                
                                                # Execute the trade in paper trading system
                                                trade_data = trade_result.get('trade_data', {})
                                                if trade_data:
                                                    paper_trade_result = await self.trade_execution.execute_paper_trade(trade_data)
                                                    logger.info(f"[PAPER] Paper trade result: {paper_trade_result}")
                                                
                                                # Broadcast trade execution result
                                                trade_message = {
                                                    'symbol': symbol,
                                                    'action': action,
                                                    'price': current_price,
                                                    'trade_result': trade_result,
                                                    'timestamp': time.time()
                                                }
                                                logger.info(f"[BROADCAST] Sending automated_trade_executed: {trade_message}")
                                                await self.broadcast_message('automated_trade_executed', trade_message)
                                                
                                                # Update bot status
                                                await self.broadcast_message('bot_status_update', await self.trading_bot.get_bot_status())
                                                
                                                # Broadcast position update
                                                await self.broadcast_message('position_update', {
                                                    'balance': self.trade_execution.get_balance(),
                                                    'positions': self.trade_execution.get_positions()
                                                })
                                                
                                                # Broadcast recent trades update
                                                await self.broadcast_message('recent_trades_update', {
                                                    'recent_trades': self.trade_execution.get_recent_trades(50)
                                                })
                                                
                                            else:
                                                logger.error(f"[FAILED] Automated trade failed: {trade_result}")
                                                
                                                # Broadcast trade failure
                                                await self.broadcast_message('automated_trade_failed', {
                                                    'symbol': symbol,
                                                    'action': action,
                                                    'error': trade_result.get('message', 'Unknown error'),
                                                    'timestamp': time.time()
                                                })
                                        else:
                                            logger.error(f"[ERROR] No current price available for {symbol}")
                                    else:
                                        logger.info(f"[SKIP] Trade conditions not met for {symbol}")
                                else:
                                    logger.info(f"[MANUAL] Manual approval required for {action} {symbol} @ {confidence:.2f} confidence")
                        
                        elif isinstance(result, Exception):
                            logger.error(f"Error in AI analysis for {allowed_pairs[i]}: {result}")
                        else:
                            logger.warning(f"AI analysis failed for {allowed_pairs[i]}")
                
                # Monitor active trades if enabled
                if self.trading_bot.bot_config.get('monitor_open_trades', True):
                    await self.monitor_active_trades()
                    
                # Update bot active trades from positions
                self.sync_bot_active_trades_with_positions()
                
                # Wait before next analysis cycle
                analysis_interval = self.trading_bot.bot_config.get('trade_interval_secs', 600)  # Default 10 minutes
                next_analysis_time = datetime.now().timestamp() + analysis_interval
                next_analysis_str = datetime.fromtimestamp(next_analysis_time).strftime('%H:%M:%S')
                logger.info(f"AI analysis cycle completed, waiting {analysis_interval} seconds until {next_analysis_str}")
                await asyncio.sleep(analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in bot monitoring: {e}")
                await asyncio.sleep(120)  # Wait 2 minutes on error
    
    def sync_bot_active_trades_with_positions(self):
        """Sync bot active trades with actual positions"""
        try:
            current_positions = self.trade_execution.get_positions()
            
            # Remove active trades that no longer have positions
            for symbol in list(self.trading_bot.bot_active_trades.keys()):
                if symbol not in current_positions:
                    del self.trading_bot.bot_active_trades[symbol]
                    self.trading_bot.bot_pair_status[symbol] = 'idle'
            
            # Add positions that aren't tracked as active trades
            for symbol, position in current_positions.items():
                if symbol not in self.trading_bot.bot_active_trades:
                    self.trading_bot.bot_active_trades[symbol] = {
                        'symbol': symbol,
                        'action': 'BUY' if position['direction'] == 'long' else 'SELL',
                        'amount': position.get('trade_value', 0),
                        'entry_price': position.get('entry_price', 0),
                        'timestamp': time.time(),
                        'confidence': 0.7  # Default confidence
                    }
                    self.trading_bot.bot_pair_status[symbol] = 'in_trade'
                    
        except Exception as e:
            logger.error(f"Error syncing bot active trades: {e}")
    
    async def real_time_pnl_updates(self):
        """Update PnL for positions every 10 seconds with WebSocket data"""
        logger.info("Starting real-time PnL updates (every 10 seconds)")
        
        while self._server_running:
            try:
                # Wait 10 seconds for more frequent updates
                await asyncio.sleep(10)
                
                if not self.clients:
                    continue
                    
                # Get current positions
                positions = self.trade_execution.get_positions()
                
                if positions:
                    # Update positions with current market prices
                    updated_positions = {}
                    for symbol, position in positions.items():
                        # Get current price from WebSocket market data
                        current_price = self.market_data.get_cached_price(symbol.replace('USDT', '').lower())
                        if current_price:
                            # Update position with current price
                            updated_position = position.copy()
                            updated_position['current_price'] = current_price
                            
                            # Calculate unrealized PnL
                            entry_price = position.get('entry_price', 0)
                            amount = position.get('amount', 0)
                            
                            if position.get('direction') == 'long':
                                unrealized_pnl = (current_price - entry_price) * amount
                            else:
                                unrealized_pnl = (entry_price - current_price) * abs(amount)
                                
                            updated_position['unrealized_pnl'] = unrealized_pnl
                            updated_position['pnl_percent'] = ((unrealized_pnl / (entry_price * abs(amount))) * 100) if entry_price > 0 else 0
                            updated_positions[symbol] = updated_position
                        else:
                            updated_positions[symbol] = position
                    
                    # Broadcast updated positions with real-time data
                    await self.broadcast_message('position_update', {
                        'balance': self.trade_execution.get_balance(),
                        'positions': updated_positions,
                        'timestamp': time.time()
                    })
                    
            except Exception as e:
                logger.error(f"Error in real-time PnL updates: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def high_frequency_autoclose_monitoring(self):
        """High-frequency monitoring for auto-close conditions (every 15 seconds)"""
        logger.info("🎯 Starting high-frequency auto-close monitoring (every 15 seconds)")
        
        while self._server_running:
            try:
                await asyncio.sleep(15)  # Wait 15 seconds for more responsive monitoring
                
                # Skip if bot is not enabled or no active trades
                if not self.trading_bot.bot_enabled or not self.trading_bot.bot_active_trades:
                    continue
                
                logger.debug(f"[AUTO-CLOSE] Monitoring {len(self.trading_bot.bot_active_trades)} active trades for auto-close conditions")
                
                # Monitor active trades for auto-close conditions
                await self.monitor_active_trades()
                
                # Broadcast updated positions to keep frontend in sync
                await self.broadcast_message('position_update', {
                    'balance': self.trade_execution.get_balance(),
                    'positions': self.trade_execution.get_positions(),
                    'timestamp': time.time()
                })
                
            except Exception as e:
                logger.error(f"[AUTO-CLOSE] Error in high-frequency auto-close monitoring: {e}")
                await asyncio.sleep(30)  # Wait 30 seconds on error
    
    async def continuous_position_monitoring(self):
        """Continuously monitor positions every 5 minutes and update PnL"""
        logger.info("Starting continuous position monitoring (every 5 minutes)")
        
        while self._server_running:
            try:
                # Wait 5 minutes
                await asyncio.sleep(300)  # 5 minutes
                
                if not self.trading_bot.bot_enabled:
                    continue
                
                # Monitor active trades more frequently
                await self.monitor_active_trades()
                
                # Broadcast bot status update
                await self.broadcast_message('bot_status_update', await self.trading_bot.get_bot_status())
                    
            except Exception as e:
                logger.error(f"Error in continuous position monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
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
        
        # Save state before shutdown
        await self.save_persistent_state()
        
        logger.info("Server shutdown complete")
    
    async def load_persisted_state(self):
        """Load persisted bot state and positions from database"""
        try:
            logger.info("Loading persisted state from database...")
            
            # Load bot state
            bot_state = await self.db.load_bot_state()
            if bot_state:
                # Restore bot state but keep it disabled for safety
                self.trading_bot.bot_config.update(bot_state.get('config', {}))
                self.trading_bot.bot_total_profit = bot_state.get('total_profit', 0)
                self.trading_bot.bot_total_trades = bot_state.get('total_trades', 0)
                self.trading_bot.bot_winning_trades = bot_state.get('winning_trades', 0)
                # Don't restore active trades - they should be manually restarted
                logger.info("Bot state loaded but bot remains disabled for safety")
            
            # Load positions
            positions = await self.db.load_positions()
            if positions:
                self.trade_execution.positions = positions
                logger.info(f"Loaded {len(positions)} positions from database")
            else:
                logger.info("No positions found in database")
            
        except Exception as e:
            logger.error(f"Error loading persisted state: {e}")
    
    async def save_persistent_state(self):
        """Save bot state and positions to database"""
        try:
            logger.info("Saving persistent state to database...")
            
            # Save bot state
            bot_state = {
                'config': self.trading_bot.bot_config,
                'total_profit': self.trading_bot.bot_total_profit,
                'total_trades': self.trading_bot.bot_total_trades,
                'winning_trades': self.trading_bot.bot_winning_trades,
                'enabled': False  # Always save as disabled for safety
            }
            await self.db.save_bot_state(bot_state)
            
            # Save positions
            positions = self.trade_execution.get_positions()
            await self.db.save_positions(positions)
            
            logger.info("Persistent state saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving persistent state: {e}")

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
        logger.exception("Full error details:")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
