"""
Main WebSocket server for crypto trading bot
"""
import asyncio
import websockets
import json
import logging
import time
from typing import Dict, Set
from datetime import datetime

from config import Config
from database import DatabaseManager
from market_data import MarketDataManager
from news_analysis import NewsAnalysisManager
from ai_analysis import AIAnalysisManager
from trading_bot import TradingBot
from trade_execution import TradeExecutionManager

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
    """Main trading server that orchestrates all components"""
    
    def __init__(self):
        logger.info("Initializing Trading Server...")
        
        # Initialize all managers
        self.db = DatabaseManager()
        self.market_data = MarketDataManager()
        self.news_analysis = NewsAnalysisManager()
        self.ai_analysis = AIAnalysisManager()
        self.trading_bot = TradingBot()
        self.trade_execution = TradeExecutionManager(self.db)
        
        # WebSocket clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Analysis control
        self.analysis_enabled = False
        self.analysis_start_time = None
        
        # Background tasks
        self.background_tasks = []
        
        logger.info("Trading Server initialization complete!")
        
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            logger.info(f"Starting WebSocket server on {Config.HOST}:{Config.PORT}")
            
            server = await websockets.serve(
                self.handle_client,
                Config.HOST,
                Config.PORT,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info(f"WebSocket server started successfully")
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.info("Server is ready! Waiting for client connections...")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise
    
    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        try:
            # Start market data updates
            self.background_tasks.append(
                asyncio.create_task(self.continuous_market_data_updates())
            )
            
            # Start price broadcasts
            self.background_tasks.append(
                asyncio.create_task(self.broadcast_price_updates())
            )
            
            # Start bot monitoring if enabled
            if self.trading_bot.bot_enabled:
                self.background_tasks.append(
                    asyncio.create_task(self.continuous_bot_monitoring())
                )
            
            logger.info(f"Started {len(self.background_tasks)} background tasks")
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {e}")
    
    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        client_id = id(websocket)
        
        # Check connection limit
        if len(self.clients) >= 10:  # Limit to 10 simultaneous connections
            logger.warning(f"Connection limit reached, rejecting client {client_id}")
            await websocket.close(1013, "Too many connections")
            return
            
        try:
            # Add client to set
            self.clients.add(websocket)
            logger.info(f"Client {client_id} connected. Total clients: {len(self.clients)}")
            
            # Send initial data
            try:
                await self.send_initial_data(websocket)
            except Exception as e:
                logger.error(f"Error sending initial data to client {client_id}: {e}")
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data, client_id)
                except json.JSONDecodeError:
                    logger.error(f"Client {client_id} sent invalid JSON")
                    try:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'data': {'message': 'Invalid JSON format'}
                        }))
                    except:
                        break
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    try:
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'data': {'message': str(e)}
                        }))
                    except:
                        break
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except websockets.exceptions.ConnectionClosedError:
            logger.info(f"Client {client_id} connection closed unexpectedly")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            # Remove client from set
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} removed. Total clients: {len(self.clients)}")
    
    async def send_initial_data(self, websocket):
        """Send initial data to new client (matches frontend expectations)"""
        try:
            # Get current data
            positions = self.trade_execution.get_positions()
            balance = self.trade_execution.get_balance()
            recent_trades = self.trade_execution.get_recent_trades(50)
            crypto_data = self.market_data.get_all_crypto_data()
            price_cache = self.market_data.get_all_prices()
            
            # Send comprehensive initial data that matches frontend expectations
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
            await websocket.send(json.dumps(initial_data))
            
            # Also send individual responses for compatibility
            # Send positions
            await websocket.send(json.dumps({
                'type': 'positions_response',
                'data': {
                    'balance': balance,
                    'positions': positions
                }
            }))
            
            # Send trade history
            await websocket.send(json.dumps({
                'type': 'trade_history_response',
                'data': {
                    'trades': recent_trades
                }
            }))
            
            # Send crypto data
            await websocket.send(json.dumps({
                'type': 'crypto_data_response',
                'data': crypto_data
            }))
            
            # Send bot status
            bot_status = await self.trading_bot.get_bot_status()
            await websocket.send(json.dumps({
                'type': 'bot_status_response',
                'data': bot_status
            }))
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
    
    async def handle_message(self, websocket, data, client_id=None):
        """Handle incoming WebSocket messages (matches frontend expectations)"""
        try:
            message_type = data.get('type')
            
            if message_type == 'get_positions':
                positions = self.trade_execution.get_positions()
                balance = self.trade_execution.get_balance()
                await websocket.send(json.dumps({
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
                
                await websocket.send(json.dumps({
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
                
                await websocket.send(json.dumps({
                    'type': 'crypto_data_response',
                    'data': response_data
                }))
                
            elif message_type == 'execute_trade':
                trade_data = data.get('trade_data', {})
                result = await self.trade_execution.execute_paper_trade(trade_data)
                
                if result['success']:
                    logger.info(f"Trade executed successfully")
                    # Send trade executed response (matches frontend expectations)
                    await websocket.send(json.dumps({
                        'type': 'trade_executed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions()
                        }
                    }))
                    
                    # Also send paper_trade_response for frontend compatibility
                    await websocket.send(json.dumps({
                        'type': 'paper_trade_response',
                        'data': result
                    }))
                    
                    # Broadcast position update to all clients
                    await self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    })
                else:
                    logger.error(f"Trade execution failed: {result['message']}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'paper_trade':
                trade_data = data.get('trade_data', {})
                result = await self.trade_execution.execute_paper_trade(trade_data)
                
                if result['success']:
                    logger.info(f"Paper trade executed successfully")
                    # Send trade executed response (matches frontend expectations)
                    await websocket.send(json.dumps({
                        'type': 'trade_executed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions()
                        }
                    }))
                    
                    # Also send paper_trade_response for frontend compatibility
                    await websocket.send(json.dumps({
                        'type': 'paper_trade_response',
                        'data': result
                    }))
                    
                    # Broadcast position update to all clients
                    await self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    })
                else:
                    logger.error(f"Paper trade execution failed: {result['message']}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'close_position':
                symbol = data.get('symbol')
                result = await self.trade_execution.close_position(symbol)
                
                if result['success']:
                    logger.info(f"Position closed successfully")
                    # Send position closed response (matches frontend expectations)
                    await websocket.send(json.dumps({
                        'type': 'position_closed',
                        'data': {
                            'trade': result['trade_data'],
                            'new_balance': result['new_balance'],
                            'positions': self.trade_execution.get_positions(),
                            'realized_pnl': result.get('profit_loss', 0)
                        }
                    }))
                    
                    # Broadcast position update to all clients
                    await self.broadcast_message('position_update', {
                        'balance': result['new_balance'],
                        'positions': self.trade_execution.get_positions()
                    })
                else:
                    logger.error(f"Position close failed: {result['message']}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'data': {'message': result['message']}
                    }))
                
            elif message_type == 'start_bot':
                config = data.get('config', {})
                result = await self.trading_bot.start_bot(config)
                
                await websocket.send(json.dumps({
                    'type': 'start_bot_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot started successfully")
                    
                    # Automatically start AI analysis when bot starts
                    if not self.analysis_enabled:
                        await self.start_analysis()
                    
                    # Broadcast bot status update
                    bot_status = await self.trading_bot.get_bot_status()
                    await self.broadcast_message('bot_status_update', {
                        'enabled': True,
                        'start_time': self.trading_bot.bot_start_time,
                        'config': self.trading_bot.bot_config,
                        'message': 'Trading bot started successfully'
                    })
                else:
                    logger.error(f"Bot start failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'stop_bot':
                result = await self.trading_bot.stop_bot()
                
                await websocket.send(json.dumps({
                    'type': 'stop_bot_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot stopped successfully")
                    # Broadcast bot status update
                    await self.broadcast_message('bot_status_update', {
                        'enabled': False,
                        'message': 'Trading bot stopped'
                    })
                else:
                    logger.error(f"Bot stop failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'get_bot_status':
                bot_status = await self.trading_bot.get_bot_status()
                
                await websocket.send(json.dumps({
                    'type': 'bot_status_response',
                    'data': bot_status
                }))
                
            elif message_type == 'update_bot_config':
                new_config = data.get('config', {})
                result = await self.trading_bot.update_bot_config(new_config)
                
                await websocket.send(json.dumps({
                    'type': 'update_bot_config_response',
                    'data': result
                }))
                
                if result['success']:
                    logger.info(f"Bot config updated successfully")
                else:
                    logger.error(f"Bot config update failed: {result.get('message', 'Unknown error')}")
                
            elif message_type == 'start_analysis':
                result = await self.start_analysis()
                
                await websocket.send(json.dumps({
                    'type': 'start_analysis_response',
                    'data': result
                }))
                
            elif message_type == 'stop_analysis':
                result = await self.stop_analysis()
                
                await websocket.send(json.dumps({
                    'type': 'stop_analysis_response',
                    'data': result
                }))
                
            elif message_type == 'get_analysis_status':
                status = await self.get_analysis_status()
                
                await websocket.send(json.dumps({
                    'type': 'analysis_status_response',
                    'data': status
                }))
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': f'Unknown message type: {message_type}'}
                }))
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            try:
                await websocket.send(json.dumps({
                    'type': 'error',
                    'data': {'message': str(e)}
                }))
            except:
                pass
    
    async def start_analysis(self):
        """Start AI analysis"""
        try:
            if self.analysis_enabled:
                logger.info(" Analysis already running")
                return
            
            logger.info("  Starting AI analysis...")
            self.analysis_enabled = True
            self.analysis_start_time = datetime.now()
            
            # Start continuous analysis task
            self.background_tasks.append(
                asyncio.create_task(self.continuous_ai_monitoring())
            )
            
            logger.info(" AI analysis started successfully")
            
            # Broadcast status
            await self.broadcast_analysis_status('started', 'Analysis started successfully')
            
        except Exception as e:
            logger.error(f" Error starting analysis: {e}")
    
    async def stop_analysis(self):
        """Stop AI analysis"""
        try:
            logger.info(" Stopping AI analysis...")
            self.analysis_enabled = False
            self.analysis_start_time = None
            
            logger.info(" AI analysis stopped successfully")
            
            # Broadcast status
            await self.broadcast_analysis_status('stopped', 'Analysis stopped')
            
        except Exception as e:
            logger.error(f" Error stopping analysis: {e}")
    
    async def get_analysis_status(self):
        """Get analysis status"""
        return {
            'enabled': self.analysis_enabled,
            'start_time': self.analysis_start_time.isoformat() if self.analysis_start_time else None,
            'target_pairs': Config.TARGET_PAIRS
        }
    
    async def continuous_market_data_updates(self):
        """Continuously update market data"""
        while True:
            try:
                await self.market_data.fetch_crypto_data()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error updating market data: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def continuous_ai_monitoring(self):
        """Continuously monitor for AI trading opportunities"""
        while self.analysis_enabled:
            try:
                # Get current market data
                crypto_data = self.market_data.get_all_crypto_data()
                current_prices = self.market_data.get_all_prices()
                
                for symbol in Config.TARGET_PAIRS:
                    try:
                        if symbol not in crypto_data:
                            continue
                        
                        market_data = crypto_data[symbol]
                        current_price = current_prices.get(symbol, market_data.get('current_price', 0))
                        
                        if not current_price:
                            continue
                        
                        # Run AI analysis
                        analysis = await self.ai_analysis.run_ai_analysis_pipeline(symbol, market_data)
                        
                        if analysis:
                            # Send analysis log
                            analysis_log = {
                                'timestamp': time.time(),
                                'level': 'high' if analysis.get('combined_confidence', 0) > 0.7 else 'medium',
                                'message': f'AI Analysis for {symbol}: {analysis.get("final_recommendation", {}).get("action", "HOLD")} with {analysis.get("combined_confidence", 0):.2f} confidence',
                                'symbol': symbol,
                                'confidence_score': analysis.get('combined_confidence', 0),
                                'action': analysis.get('final_recommendation', {}).get('action', 'HOLD'),
                                'reasoning': analysis.get('final_recommendation', {}).get('reasoning', ''),
                                'entry_price': current_price,
                                'source': 'ai_analysis'
                            }
                            
                            await self.broadcast_message('analysis_log', analysis_log)
                            
                            # Check if bot should execute trade
                            if self.trading_bot.bot_enabled:
                                should_trade = await self.trading_bot.check_bot_trading_conditions(symbol, analysis)
                                
                                if should_trade:
                                    logger.info(f"Bot trading conditions met for {symbol}, executing trade")
                                    
                                    # Get current balance
                                    balance = self.trade_execution.get_balance()
                                    
                                    # Execute bot trade
                                    trade_result = await self.trading_bot.execute_bot_trade(symbol, analysis, current_price, balance)
                                    
                                    if trade_result['success']:
                                        logger.info(f"Bot trade executed successfully for {symbol}")
                                        
                                        # Create trade data for execution system
                                        trade_data = trade_result['trade_data']
                                        execution_trade_data = {
                                            'symbol': symbol,
                                            'direction': trade_data['direction'],
                                            'amount': trade_data['amount'],
                                            'price': trade_data['price'],
                                            'trade_id': f"bot_{int(time.time())}_{symbol}",
                                            'bot_trade': True
                                        }
                                        
                                        # Execute the trade through the trade execution system
                                        execution_result = await self.trade_execution.execute_paper_trade(execution_trade_data)
                                        
                                        if execution_result['success']:
                                            # Broadcast bot trade executed
                                            await self.broadcast_message('bot_trade_executed', {
                                                'symbol': symbol,
                                                'trade_data': {
                                                    'symbol': symbol,
                                                    'direction': trade_data['direction'],
                                                    'price': trade_data['price'],
                                                    'amount': trade_data['amount'],
                                                    'take_profit': trade_data.get('take_profit', current_price * 1.02),
                                                    'stop_loss': trade_data.get('stop_loss', current_price * 0.98),
                                                    'confidence_score': analysis.get('combined_confidence', 0),
                                                    'timestamp': time.time()
                                                }
                                            })
                                            
                                            # Send trade log
                                            await self.broadcast_message('trade_log', {
                                                'timestamp': time.time(),
                                                'level': 'success',
                                                'message': f'Bot trade executed: {symbol} {trade_data["direction"]} {trade_data["amount"]:.6f} @ ${trade_data["price"]:.2f}',
                                                'profit': 0,
                                                'symbol': symbol,
                                                'action': trade_data['direction']
                                            })
                                            
                                            # Broadcast position update
                                            positions = self.trade_execution.get_positions()
                                            balance = self.trade_execution.get_balance()
                                            await self.broadcast_message('position_update', {
                                                'balance': balance,
                                                'positions': positions
                                            })
                                            
                                            # Broadcast trade executed for compatibility
                                            await self.broadcast_message('trade_executed', {
                                                'trade': execution_result['trade_data'],
                                                'new_balance': balance,
                                                'positions': positions
                                            })
                                        else:
                                            logger.error(f"Bot trade execution failed for {symbol}: {execution_result.get('message', 'Unknown error')}")
                                    else:
                                        logger.error(f"Bot trade execution failed for {symbol}: {trade_result.get('message', 'Unknown error')}")
                                else:
                                    logger.info(f"Trading conditions not met for {symbol}, skipping trade")
                            else:
                                logger.info(f"Bot disabled, skipping trade execution for {symbol}")
                        else:
                            # Send analysis log for failed analysis
                            await self.broadcast_message('analysis_log', {
                                'timestamp': time.time(),
                                'level': 'medium',
                                'message': f'AI analysis failed for {symbol}',
                                'symbol': symbol,
                                'confidence_score': 0,
                                'action': 'HOLD',
                                'reasoning': 'Analysis failed',
                                'source': 'ai_analysis'
                            })
                    
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        continue
                    
                    # Wait between symbols
                    await asyncio.sleep(Config.ANALYSIS_INTERVAL)
                
                # Wait before next cycle
                await asyncio.sleep(Config.ANALYSIS_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in AI monitoring: {e}")
                await asyncio.sleep(60)
    
    async def continuous_bot_monitoring(self):
        """Continuously monitor bot trades"""
        while self.trading_bot.bot_enabled:
            try:
                # Get current prices
                current_prices = self.market_data.get_all_prices()
                
                # Check for trade exits
                exit_trades = await self.trading_bot.check_bot_trade_exits(current_prices)
                for exit_trade in exit_trades:
                    logger.info(f"Closing bot trade for {exit_trade['symbol']}")
                    # Close the position
                    symbol = exit_trade['symbol']
                    result = await self.trade_execution.close_position(symbol, exit_trade['exit_price'])
                    
                    if result['success']:
                        logger.info(f"Bot trade closed successfully for {symbol}")
                        # Broadcast bot trade closed
                        await self.broadcast_message('bot_trade_closed', {
                            'symbol': symbol,
                            'trade_record': result['trade_data']
                        })
                        
                        # Send trade log
                        await self.broadcast_message('trade_log', {
                            'timestamp': time.time(),
                            'level': 'success',
                            'message': f'Bot trade closed: {symbol} @ ${exit_trade["exit_price"]}, P&L: ${result.get("profit_loss", 0)}',
                            'profit': result.get('profit_loss', 0)
                        })
                        
                        # Broadcast position update
                        positions = self.trade_execution.get_positions()
                        balance = self.trade_execution.get_balance()
                        await self.broadcast_message('position_update', {
                            'balance': balance,
                            'positions': positions
                        })
                    else:
                        logger.error(f"Bot trade close failed for {symbol}: {result.get('message', 'Unknown error')}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in bot monitoring: {e}")
                await asyncio.sleep(30)
    
    async def broadcast_price_updates(self):
        """Broadcast price updates to all clients"""
        while True:
            try:
                # Get current prices
                prices = self.market_data.get_all_prices()
                
                # Update position current prices
                positions = self.trade_execution.get_positions()
                positions_updated = False
                
                for symbol, price in prices.items():
                    # Update position current price if position exists
                    if symbol in positions:
                        self.trade_execution.update_position_current_price(symbol, price)
                        positions_updated = True
                    
                    crypto_data = self.market_data.get_all_crypto_data()
                    symbol_data = crypto_data.get(symbol, {})
                    
                    price_update = {
                        'symbol': symbol,
                        'price': price,
                        'change_24h': symbol_data.get('change_24h', 0),
                        'volume_24h': symbol_data.get('volume_24h', 0),
                        'market_cap': symbol_data.get('market_cap', 0),
                        'timestamp': time.time()
                    }
                    
                    await self.broadcast_message('price_update', price_update)
                
                # Broadcast updated positions if any were updated
                if positions_updated:
                    balance = self.trade_execution.get_balance()
                    updated_positions = self.trade_execution.get_positions()
                    await self.broadcast_message('position_update', {
                        'balance': balance,
                        'positions': updated_positions
                    })
                
                await asyncio.sleep(10)  # Reduced frequency to every 10 seconds
                
            except Exception as e:
                logger.error(f"Error broadcasting price updates: {e}")
                await asyncio.sleep(30)  # Longer delay on error
    
    async def broadcast_message(self, message_type: str, data: Dict):
        """Broadcast message to all connected clients"""
        if not self.clients:
            return
        
        message = {
            'type': message_type,
            'data': data
        }
        
        try:
            # Create a copy of clients set to avoid modification during iteration
            clients_copy = self.clients.copy()
            disconnected_clients = set()
            
            for client in clients_copy:
                try:
                    await client.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients from the original set
            for client in disconnected_clients:
                self.clients.discard(client)
            
            if disconnected_clients:
                logger.info(f"Removed {len(disconnected_clients)} disconnected clients")
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    
    async def broadcast_analysis_status(self, status: str, message: str):
        """Broadcast analysis status to all clients"""
        try:
            await self.broadcast_message('analysis_status', {
                'status': status,
                'message': message,
                'timestamp': time.time()
            })
        except Exception as e:
            logger.error(f"Error broadcasting analysis status: {e}")
    
    async def shutdown(self):
        """Shutdown the server"""
        logger.info("Shutting down server...")
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close all client connections
        for client in self.clients:
            await client.close()
        
        logger.info("Server shutdown complete")

async def main():
    """Main function"""
    logger.info(" Starting Trading Server...")
    server = TradingServer()
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info(" Received shutdown signal")
    except Exception as e:
        logger.error(f" Server error: {e}")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    try:
        logger.info(" Trading Server v1.0 starting...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Server stopped by user")
    except Exception as e:
        logger.error(f" Server error: {e}") 