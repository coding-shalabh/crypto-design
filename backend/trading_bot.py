"""
Automated trading bot logic and execution
"""
import asyncio
import logging
import time
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from config import Config
from database import DatabaseManager # Import DatabaseManager

logger = logging.getLogger(__name__)

from confidence_score_calculator import ConfidenceScoreCalculator

class TradingBot:
    """Automated trading bot with risk management"""
    
    def __init__(self):
        logger.info("Initializing Trading Bot...")
        
        self.bot_enabled = False
        self.bot_config = self._load_bot_config()
        
        # Bot state tracking
        self.bot_start_time = None
        self.bot_trades_today = 0
        self.bot_last_trade_reset = time.time()
        self.bot_active_trades = {}  # symbol -> trade details
        self.bot_pair_status = {}  # symbol -> 'idle', 'in_trade', 'cooldown'
        self.bot_cooldown_end = {}  # symbol -> cooldown end timestamp
        self.bot_trailing_stops = {}  # symbol -> trailing stop details
        self.bot_trade_history = []  # List of completed trades
        self.bot_total_profit = 0.0
        self.bot_total_trades = 0
        self.bot_winning_trades = 0
        
        # 🔥 NEW: Mode-specific tracking for live vs mock statistics
        self.mock_total_profit = 0.0
        self.mock_total_trades = 0
        self.mock_winning_trades = 0
        self.mock_trades_today = 0
        
        self.live_total_profit = 0.0
        self.live_total_trades = 0
        self.live_winning_trades = 0
        self.live_trades_today = 0
        
        # Confidence Score Calculator
        self.confidence_calculator = ConfidenceScoreCalculator()
        
        # Database Manager for logging
        self.db_manager = DatabaseManager()
        
        # Trade Execution Manager
        from trade_execution import TradeExecutionManager
        self.trade_execution_manager = TradeExecutionManager(self.db_manager)

        # Opportunity tracking
        self.opportunity_cooldown = {}  # symbol -> cooldown end time
        self.accepted_trade_directions = {}  # symbol -> trade direction details
        
        logger.info(f"Bot config loaded: {self.bot_config}")
        logger.info("Trading Bot initialization complete!")
        
    async def start_bot(self, config: Dict = None) -> Dict:
        """Start the trading bot with enhanced readiness verification"""
        try:
            logger.info("🚀 Starting trading bot...")
            
            if self.bot_enabled:
                logger.warning("⚠️ Bot is already running")
                return {'success': False, 'message': 'Bot is already running'}
            
            # Update config if provided
            if config:
                logger.info(f"⚙️ Updating bot config: {config}")
                self.bot_config.update(config)
            
            # 🔥 NEW: Verify trading readiness immediately
            logger.info("🔍 Verifying trading readiness...")
            readiness = self.trade_execution_manager.trading_manager.verify_trading_readiness()
            
            if not readiness['ready']:
                error_msg = f"Trading system not ready: {readiness.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False, 
                    'message': error_msg,
                    'readiness': readiness
                }
            
            logger.info(f"✅ Trading system ready in {readiness['mode']} mode")
            if readiness.get('usdt_balance'):
                balance = readiness['usdt_balance']
                logger.info(f"💰 Available balance: {balance.get('total', 0):.2f} USDT ({balance.get('wallet_type', 'Unknown')} wallet)")
            
            # Reset daily trade counter if it's a new day
            current_time = time.time()
            if current_time - self.bot_last_trade_reset > 86400:  # 24 hours
                logger.info("🔄 Resetting daily trade counter")
                self.bot_trades_today = 0
                self.mock_trades_today = 0
                self.live_trades_today = 0
                self.bot_last_trade_reset = current_time
            
            self.bot_enabled = True
            self.bot_start_time = current_time
            
            # Initialize pair status
            for pair in self.bot_config['allowed_pairs']:
                self.bot_pair_status[pair] = 'idle'
            
            logger.info(f"🎯 Trading bot started successfully!")
            logger.info(f"📊 Allowed pairs: {self.bot_config['allowed_pairs']}")
            logger.info(f"💵 Trade amount: ${self.bot_config['trade_amount_usdt']}")
            logger.info(f"📈 Max trades per day: {self.bot_config['max_trades_per_day']}")
            logger.info(f"🤖 AI confidence threshold: {self.bot_config['ai_confidence_threshold']}")
            
            return {
                'success': True, 
                'message': 'Trading bot started successfully',
                'config': self.bot_config,
                'readiness': readiness
            }
            
        except Exception as e:
            logger.error(f"💥 Error starting bot: {e}")
            return {'success': False, 'message': f'Error starting bot: {e}'}
    
    async def stop_bot(self) -> Dict:
        """Stop the trading bot"""
        try:
            logger.info(" Stopping trading bot...")
            
            if not self.bot_enabled:
                logger.warning(" Bot is not running")
                return {'success': False, 'message': 'Bot is not running'}
            
            self.bot_enabled = False
            self.bot_start_time = None
            
            logger.info(" Trading bot stopped successfully")
            return {'success': True, 'message': 'Trading bot stopped successfully'}
            
        except Exception as e:
            logger.error(f" Error stopping bot: {e}")
            return {'success': False, 'message': f'Error stopping bot: {e}'}
    
    async def get_bot_status(self) -> Dict:
        """Get current bot status (matches frontend expectations)"""
        try:
            running_time = 0
            if self.bot_start_time:
                running_time = time.time() - self.bot_start_time
            
            # Calculate win rate
            win_rate = (self.bot_winning_trades / self.bot_total_trades * 100) if self.bot_total_trades > 0 else 0
            
            # Get pair status for allowed pairs
            pair_status = {}
            for pair in self.bot_config.get('allowed_pairs', []):
                pair_status[pair] = self.bot_pair_status.get(pair, 'idle')
            
            status = {
                'enabled': self.bot_enabled,
                'start_time': datetime.fromtimestamp(self.bot_start_time).isoformat() if self.bot_start_time else None,
                'active_trades': len(self.bot_active_trades),
                'trades_today': self.bot_trades_today,
                'total_profit': round(self.bot_total_profit, 2),
                'total_trades': self.bot_total_trades,
                'winning_trades': self.bot_winning_trades,
                'win_rate': round(win_rate, 2),
                'pair_status': pair_status,
                'running_duration': int(running_time),
                # 🔥 NEW: Mode-specific statistics
                'mock_total_profit': round(self.mock_total_profit, 2),
                'mock_total_trades': self.mock_total_trades,
                'mock_winning_trades': self.mock_winning_trades,
                'mock_trades_today': self.mock_trades_today,
                'live_total_profit': round(self.live_total_profit, 2),
                'live_total_trades': self.live_total_trades,
                'live_winning_trades': self.live_winning_trades,
                'live_trades_today': self.live_trades_today
            }
            
            # Removed frequent bot status logging to reduce spam
            return status
            
        except Exception as e:
            logger.error(f" Error getting bot status: {e}")
            return {
                'enabled': False,
                'start_time': None,
                'active_trades': 0,
                'trades_today': 0,
                'total_profit': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'win_rate': 0,
                'pair_status': {},
                'running_duration': 0
            }
    
    async def update_bot_config(self, new_config: Dict) -> Dict:
        """Update bot configuration"""
        try:
            logger.info(f" Updating bot configuration: {new_config}")
            
            # Validate config
            required_keys = ['max_trades_per_day', 'trade_amount_usdt', 'ai_confidence_threshold']
            for key in required_keys:
                if key not in new_config:
                    logger.error(f" Missing required config key: {key}")
                    return {'success': False, 'message': f'Missing required config key: {key}'}
            
            self.bot_config.update(new_config)
            
            # Save configuration to file for persistence
            try:
                import json
                config_file = 'bot_config.json'
                with open(config_file, 'w') as f:
                    json.dump(self.bot_config, f, indent=2)
                logger.info(f" Bot config saved to {config_file}")
            except Exception as e:
                logger.warning(f" Failed to save config to file: {e}")
            
            logger.info(f" Bot config updated successfully")
            
            return {'success': True, 'message': 'Bot configuration updated successfully'}
            
        except Exception as e:
            logger.error(f" Error updating bot config: {e}")
            return {'success': False, 'message': f'Error updating config: {e}'}
    
    def get_bot_config(self) -> Dict:
        """Get current bot configuration"""
        return self.bot_config.copy()
    
    async def check_bot_trading_conditions(self, symbol: str, analysis: Dict) -> bool:
        """Check if trading conditions are met for bot trading"""
        try:
            # Basic checks
            if not self.bot_enabled:
                logger.info(f"Bot trading conditions check for {symbol}: Bot disabled")
                return False
                
            if not self._is_symbol_allowed(symbol):
                logger.info(f"Bot trading conditions check for {symbol}: Symbol not allowed")
                return False
                
            if not self._is_within_daily_trade_limit():
                logger.info(f"Bot trading conditions check for {symbol}: Daily trade limit reached")
                return False
                
            if not self._is_within_concurrent_trade_limit():
                logger.info(f"Bot trading conditions check for {symbol}: Concurrent trade limit reached")
                return False
                
            if not self._is_pair_idle(symbol):
                logger.info(f"Bot trading conditions check for {symbol}: Pair has active trade")
                return False
                
            if not self._is_not_in_cooldown(symbol):
                logger.info(f"Bot trading conditions check for {symbol}: Pair in cooldown")
                return False

            # Extract confidence score based on analysis format
            final_confidence_score = 0.0
            
            # Handle new GPT final recommendation format
            if analysis.get('source') == 'gpt_final':
                # New format: GPT final recommendation with 30-minute trade setup
                final_recommendation = analysis.get('final_recommendation', {})
                final_confidence_score = float(final_recommendation.get('confidence', 0))
                timeframe = final_recommendation.get('timeframe', '30 minutes')
                logger.info(f"Using GPT final recommendation confidence for {symbol}: {final_confidence_score:.2f} ({timeframe})")
            else:
                # Legacy format: Old analysis structure
                final_recommendation = analysis.get('final_recommendation', {})
                ai_confidence = float(final_recommendation.get('confidence', 0))
                combined_confidence = float(analysis.get('combined_confidence', ai_confidence))
                final_confidence_score = max(ai_confidence, combined_confidence)
                logger.info(f"Using legacy analysis confidence for {symbol}: {final_confidence_score:.2f}")

            # Log filter details
            filter_data = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'bot_enabled': self.bot_enabled,
                'symbol_allowed': self._is_symbol_allowed(symbol),
                'within_daily_trade_limit': self._is_within_daily_trade_limit(),
                'within_concurrent_trade_limit': self._is_within_concurrent_trade_limit(),
                'pair_idle': self._is_pair_idle(symbol),
                'not_in_cooldown': self._is_not_in_cooldown(symbol),
                'analysis_source': analysis.get('source', 'unknown'),
                'final_confidence_score': final_confidence_score,
                'confidence_above_threshold': self._is_confidence_above_threshold(final_confidence_score),
                'trade_decision': 'REJECTED' # Default to rejected, updated to 'ACCEPTED' if all pass
            }
            
            # Check confidence threshold
            if not self._is_confidence_above_threshold(final_confidence_score):
                logger.info(f"Bot trading conditions check for {symbol}: Confidence {final_confidence_score:.2f} below threshold {self.bot_config['ai_confidence_threshold']}")
                filter_data['trade_decision'] = 'REJECTED'
                logger.info(f"Trade filter details for {symbol}: {filter_data}")
                return False
            
            # All conditions passed
            filter_data['trade_decision'] = 'ACCEPTED'
            logger.info(f"Trade filter details for {symbol}: {filter_data}")
            logger.info(f"Bot trading conditions check for {symbol}: ALL CONDITIONS MET - Trade will execute")
            return True
            
        except Exception as e:
            logger.error(f"Error checking bot trading conditions for {symbol}: {e}")
            return False
    
    def _load_bot_config(self) -> Dict:
        """Load bot configuration from file or use defaults"""
        try:
            import json
            import os
            config_file = 'bot_config.json'
            
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                logger.info(f" Loaded bot config from {config_file}")
                return saved_config
            else:
                logger.info(" No saved config found, using defaults")
                return Config.get_bot_config()
        except Exception as e:
            logger.warning(f" Failed to load config from file: {e}, using defaults")
            return Config.get_bot_config()
    
    def _is_symbol_allowed(self, symbol: str) -> bool:
        return symbol in self.bot_config['allowed_pairs']

    def _is_within_daily_trade_limit(self) -> bool:
        return self.bot_trades_today < self.bot_config['max_trades_per_day']

    def _is_within_concurrent_trade_limit(self) -> bool:
        return len(self.bot_active_trades) < self.bot_config['max_concurrent_trades']

    def _is_pair_idle(self, symbol: str) -> bool:
        return self.bot_pair_status.get(symbol, 'idle') == 'idle'

    def _is_not_in_cooldown(self, symbol: str) -> bool:
        if symbol in self.bot_cooldown_end:
            if time.time() < self.bot_cooldown_end[symbol]:
                return False
        return True

    def _is_confidence_above_threshold(self, confidence: float) -> bool:
        return confidence >= self.bot_config['ai_confidence_threshold']

    async def execute_trade(self, symbol: str, direction: str, amount_usdt: float, price: float, trade_type: str, confidence_score: float, analysis_data: Dict, trading_mode: str = 'mock') -> Dict:
        """Execute a trade using the trading manager (supports both mock and live trading)"""
        try:
            # Calculate quantity based on amount and price
            quantity = amount_usdt / price
            
            # Import trading manager if not already available
            if not hasattr(self, 'trading_manager'):
                from trading_manager import TradingManager
                self.trading_manager = TradingManager()
                # Set the trading mode
                self.trading_manager.set_trading_mode(trading_mode)
            
            # Place the order using trading manager (handles both mock and live)
            try:
                order_result = self.trading_manager.place_order(
                    symbol=symbol,
                    side=direction.upper(),  # 'BUY' or 'SELL'
                    order_type='MARKET',  # Use market orders for bot trading
                    quantity=quantity,
                    price=price
                )
                
                if order_result.get('success'):
                    # Create trade data for logging
                    trade_data = {
                        'symbol': symbol,
                        'direction': direction.lower(),
                        'amount': quantity,
                        'price': price,
                        'trade_id': f"bot_trade_{int(time.time())}_{symbol}",
                        'trade_type': 'bot',
                        'bot_trade': True,
                        'analysis_confidence': confidence_score,
                        'analysis_data': analysis_data,
                        'mode': trading_mode
                    }
                    
                    # Log the trade to database
                    if hasattr(self, 'db_manager'):
                        await self.db_manager.log_trade(trade_data)
                    
                    return {
                        'success': True,
                        'message': f'{trading_mode.capitalize()} trade executed: {symbol} {direction}',
                        'trade_data': trade_data,
                        'order_result': order_result
                    }
                else:
                    return {
                        'success': False,
                        'message': f'Order placement failed: {order_result.get("message", "Unknown error")}'
                    }
                    
            except Exception as order_error:
                logger.error(f"Order placement failed for {symbol}: {order_error}")
                return {
                    'success': False,
                    'message': f'Order placement error: {str(order_error)}'
                }
            
        except Exception as e:
            logger.error(f"Error in execute_trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}

    async def execute_bot_trade(self, symbol: str, analysis: Dict, current_price: float, balance: float, trading_mode: str = 'mock') -> Dict:
        """Execute a bot trade with enhanced balance verification"""
        try:
            logger.info(f"🤖 Executing bot trade for {symbol} at ${current_price:.2f}")
            
            # 🔥 NEW: Verify trading readiness before executing
            readiness = self.trade_execution_manager.trading_manager.verify_trading_readiness()
            if not readiness['ready']:
                error_msg = f"Trading system not ready: {readiness.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'reason': 'trading_not_ready'
                }
            
            # 🔥 NEW: Get fresh balance for the current mode
            balance_data = self.trade_execution_manager.trading_manager.get_trading_balance('USDT', trading_mode)
            if not balance_data.get('success', True):
                error_msg = f"Failed to get balance: {balance_data.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'message': error_msg,
                    'reason': 'balance_fetch_failed'
                }
            
            available_balance = balance_data.get('free', 0)
            wallet_type = balance_data.get('wallet_type', 'UNKNOWN')
            
            logger.info(f"💰 Available balance: ${available_balance:.2f} USDT ({wallet_type} wallet)")
            
            # Handle new GPT final recommendation format
            if analysis.get('source') == 'gpt_final':
                # New format: GPT final recommendation with 30-minute trade setup
                final_recommendation = analysis.get('final_recommendation', {})
                ai_confidence = float(final_recommendation.get('confidence', 0))
                action = final_recommendation.get('action', 'HOLD')
                timeframe = final_recommendation.get('timeframe', '30 minutes')
                
                logger.info(f"Processing GPT final recommendation for {symbol}: {action} with {ai_confidence:.2f} confidence ({timeframe})")
                
                # Check if we should use the trade setup from GPT
                trade_setup = analysis.get('trade_setup', {})
                if trade_setup and action in ['BUY', 'SELL']:
                    logger.info(f"Using GPT trade setup for {symbol}: {trade_setup}")
                
            else:
                # Legacy format: Old analysis structure
                final_recommendation = analysis.get('final_recommendation', {})
                ai_confidence = float(final_recommendation.get('confidence', 0))
                combined_confidence = float(analysis.get('combined_confidence', ai_confidence))
                ai_confidence = max(ai_confidence, combined_confidence)
                action = final_recommendation.get('action', 'HOLD')
                logger.info(f"Processing legacy analysis for {symbol}: {action} with {ai_confidence:.2f} confidence")

            # Override HOLD if confidence is high enough
            if self._should_override_hold(action, ai_confidence):
                action = self._get_override_action(ai_confidence)
                logger.info(f"🔄 Overriding HOLD to {action} for {symbol} due to high confidence {ai_confidence:.2f}")

            if action == 'HOLD':
                logger.info(f"⏸️ Skipping trade for {symbol} - HOLD signal with confidence {ai_confidence:.2f}")
                return {
                    'success': False,
                    'message': 'HOLD signal - no trade executed',
                    'reason': 'hold_signal',
                    'confidence': ai_confidence
                }

            # Calculate trade amount using fresh balance
            trade_amount_usdt = self._calculate_trade_amount(available_balance)
            
            # Check if trade amount is sufficient
            if available_balance < trade_amount_usdt:
                reason = f"Insufficient balance for trade. Required: ${trade_amount_usdt:.2f}, Available: ${available_balance:.2f}"
                logger.warning(f"⚠️ {reason}")
                return {
                    'success': False,
                    'message': reason,
                    'reason': 'insufficient_balance',
                    'required_amount': trade_amount_usdt,
                    'available_balance': available_balance
                }
            
            # Check daily trade limit
            if not self._is_within_daily_trade_limit():
                reason = f"Daily trade limit reached ({self.bot_config['max_trades_per_day']} trades)"
                logger.warning(f"Trade execution failed for {symbol}: {reason}")
                self._log_failed_trade(symbol, reason, ai_confidence, analysis)
                return {'success': False, 'message': reason}
            
            # Check concurrent trade limit
            if not self._is_within_concurrent_trade_limit():
                reason = f"Concurrent trade limit reached ({self.bot_config['max_concurrent_trades']} trades)"
                logger.warning(f"Trade execution failed for {symbol}: {reason}")
                self._log_failed_trade(symbol, reason, ai_confidence, analysis)
                return {'success': False, 'message': reason}
            
            # Execute the trade
            trade_result = await self.execute_trade(
                symbol=symbol,
                direction=action.lower(),
                amount_usdt=trade_amount_usdt,
                price=current_price,
                trade_type='bot',
                confidence_score=ai_confidence,
                analysis_data=analysis,
                trading_mode=trading_mode
            )
            
            if trade_result.get('success'):
                logger.info(f"Bot trade executed successfully for {symbol}: {action} ${trade_amount_usdt:.2f} at ${current_price:.2f}")
                # Set cooldown for this pair
                cooldown_duration = self.bot_config.get('cooldown_secs', 300)
                self.bot_cooldown_end[symbol] = time.time() + cooldown_duration
                
                # Update bot statistics
                self.bot_trades_today += 1
                self.bot_total_trades += 1
                self.bot_pair_status[symbol] = 'in_trade'
                
                # 🔥 NEW: Update mode-specific statistics
                if trading_mode == 'mock':
                    self.mock_total_trades += 1
                    self.mock_trades_today += 1
                elif trading_mode == 'live':
                    self.live_total_trades += 1
                    self.live_trades_today += 1
                
                # Store active trade details
                self.bot_active_trades[symbol] = {
                    'symbol': symbol,
                    'action': action,
                    'amount': trade_amount_usdt,
                    'entry_price': current_price,
                    'timestamp': time.time(),
                    'confidence': ai_confidence
                }
            else:
                reason = trade_result.get('message', 'Trade execution failed')
                logger.error(f"Bot trade failed for {symbol}: {reason}")
                self._log_failed_trade(symbol, reason, ai_confidence, analysis)
            
            return trade_result
            
        except Exception as e:
            reason = f"Exception during trade execution: {str(e)}"
            logger.error(f"Error executing bot trade for {symbol}: {e}")
            self._log_failed_trade(symbol, reason, ai_confidence, analysis)
            return {'success': False, 'message': reason}
    
    def _should_override_hold(self, action: str, confidence: float) -> bool:
        # Override HOLD if confidence is above the trading threshold
        return action == 'HOLD' and confidence >= self.bot_config['ai_confidence_threshold']

    def _get_override_action(self, confidence: float) -> str:
        # For high confidence HOLD signals, default to BUY as it's more common
        # in bullish markets. This could be enhanced to analyze market conditions.
        logger.info(f" Overriding HOLD signal with BUY due to high confidence: {confidence:.2f}")
        return 'BUY'

    def _calculate_trade_amount(self, balance: float) -> float:
        """Calculate trade amount based on configuration limits and actual balance"""
        try:
            # Get configured amounts
            configured_amount = self.bot_config.get('trade_amount_usdt', 50)
            max_amount_per_trade = self.bot_config.get('max_amount_per_trade_usdt', 500)
            risk_percent = self.bot_config.get('risk_per_trade_percent', 5.0)
            
            # Calculate maximum based on risk percentage
            max_risk_amount = balance * (risk_percent / 100)
            
            # Calculate safe balance usage (95% of balance as safety)
            safe_balance_amount = balance * 0.95
            
            # Use configured amount as primary, but respect max limits
            # Don't let risk percentage override configured amount if configured amount is reasonable
            if configured_amount <= max_amount_per_trade and configured_amount <= safe_balance_amount:
                trade_amount_usdt = configured_amount
            else:
                # Choose the minimum of limits only if configured amount is too high
                trade_amount_usdt = min(
                    configured_amount,        # User configured amount
                    max_amount_per_trade,     # Max amount per trade limit
                    safe_balance_amount       # Balance safety limit
                )
            
            # Ensure minimum trade amount (configurable with fallback)
            min_trade_amount = self.bot_config.get('min_trade_amount_usdt', 10)
            if trade_amount_usdt < min_trade_amount:
                logger.warning(f"Calculated trade amount ${trade_amount_usdt:.2f} is below minimum ${min_trade_amount}")
                # If balance is sufficient, use minimum amount instead of failing
                if balance >= min_trade_amount:
                    logger.info(f"Using minimum trade amount ${min_trade_amount} instead")
                    trade_amount_usdt = min_trade_amount
                else:
                    logger.warning(f"Balance ${balance:.2f} is insufficient even for minimum trade amount ${min_trade_amount}")
                    return 0
            
            logger.info(f"Trade amount calculated: ${trade_amount_usdt:.2f} "
                       f"(config: ${configured_amount}, max: ${max_amount_per_trade}, "
                       f"risk: ${max_risk_amount:.2f}, balance: ${balance:.2f})")
            
            return trade_amount_usdt
            
        except Exception as e:
            logger.error(f"Error calculating trade amount: {e}")
            return self.bot_config.get('trade_amount_usdt', 50)  # Fallback to configured amount

    def _create_trade_data(
        self, symbol: str, action: str, quantity: float, current_price: float, trade_amount_usdt: float, confidence: float, recommendation: Dict
    ) -> Dict:
        return {
            'symbol': symbol,
            'direction': 'LONG' if action == 'BUY' else 'SHORT',
            'trade_type': 'buy' if action == 'BUY' else 'sell',
            'amount': quantity,
            'price': current_price,
            'value_usdt': trade_amount_usdt,
            'timestamp': time.time(),
            'bot_trade': True,
            'analysis_confidence': confidence,
            'analysis_recommendation': recommendation,
            'trade_id': f"bot_trade_{int(time.time())}_{symbol}"
        }

    def _update_bot_state_for_new_trade(self, symbol: str, trade_data: Dict):
        self.bot_trades_today += 1
        self.bot_pair_status[symbol] = 'in_trade'
        self.bot_active_trades[symbol] = trade_data
        self.last_trade_data = trade_data
        cooldown_duration = self.bot_config.get('pair_cooldown_seconds', 300)
        self.bot_cooldown_end[symbol] = time.time() + cooldown_duration
        opportunity_cooldown = self.bot_config.get('opportunity_cooldown_seconds', 600)
        self.opportunity_cooldown[symbol] = time.time() + opportunity_cooldown

    async def check_bot_trade_exits(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Check for bot trade exits based on current prices"""
        try:
            exit_trades = []
            
            for symbol, trade_data in self.bot_active_trades.items():
                if symbol not in current_prices:
                    continue
                
                current_price = current_prices[symbol]
                entry_price = trade_data['price']
                direction = trade_data['direction']
                
                logger.info(f" Checking exit conditions for {symbol}: {direction} @ ${entry_price}, current: ${current_price}")
                
                # Calculate P&L
                if direction == 'BUY':
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                else:  # SELL
                    pnl_percent = ((entry_price - current_price) / entry_price) * 100
                
                # Check exit conditions
                should_exit = False
                exit_reason = ""
                
                # Take profit
                take_profit_percent = self.bot_config.get('take_profit_percent', 2.0)
                if pnl_percent >= take_profit_percent:
                    should_exit = True
                    exit_reason = f"Take profit at {pnl_percent:.2f}%"
                
                # Stop loss
                stop_loss_percent = self.bot_config.get('stop_loss_percent', -1.5)
                if pnl_percent <= stop_loss_percent:
                    should_exit = True
                    exit_reason = f"Stop loss at {pnl_percent:.2f}%"
                
                # Trailing stop
                if symbol in self.bot_trailing_stops:
                    trailing_stop = self.bot_trailing_stops[symbol]
                    if direction == 'BUY' and current_price <= trailing_stop['stop_price']:
                        should_exit = True
                        exit_reason = f"Trailing stop at ${trailing_stop['stop_price']}"
                    elif direction == 'SELL' and current_price >= trailing_stop['stop_price']:
                        should_exit = True
                        exit_reason = f"Trailing stop at ${trailing_stop['stop_price']}"
                
                if should_exit:
                    logger.info(f" Exit signal for {symbol}: {exit_reason}")
                    exit_trades.append({
                        'symbol': symbol,
                        'exit_price': current_price,
                        'exit_reason': exit_reason,
                        'pnl_percent': pnl_percent,
                        'trade_data': trade_data
                    })
                    
                    # Update trailing stop if profitable
                    if pnl_percent > 0:
                        trailing_percent = self.bot_config.get('trailing_stop_percent', 0.5)
                        if direction == 'BUY':
                            new_stop = current_price * (1 - trailing_percent / 100)
                            if symbol not in self.bot_trailing_stops or new_stop > self.bot_trailing_stops[symbol]['stop_price']:
                                self.bot_trailing_stops[symbol] = {
                                    'stop_price': new_stop,
                                    'set_at': time.time()
                                }
                                logger.info(f" Updated trailing stop for {symbol}: ${new_stop}")
                        else:  # SELL
                            new_stop = current_price * (1 + trailing_percent / 100)
                            if symbol not in self.bot_trailing_stops or new_stop < self.bot_trailing_stops[symbol]['stop_price']:
                                self.bot_trailing_stops[symbol] = {
                                    'stop_price': new_stop,
                                    'set_at': time.time()
                                }
                                logger.info(f" Updated trailing stop for {symbol}: ${new_stop}")
            
            return exit_trades
            
        except Exception as e:
            logger.error(f" Error checking bot trade exits: {e}")
            return []
    
    async def check_trade_direction_reversal(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Check for trade direction reversals based on new analysis"""
        try:
            reversals = []
            
            for symbol, trade_data in self.bot_active_trades.items():
                if symbol not in current_prices:
                    continue
                
                current_price = current_prices[symbol]
                entry_price = trade_data['price']
                direction = trade_data['direction']
                
                # Check if price moved significantly against the trade
                price_change_percent = ((current_price - entry_price) / entry_price) * 100
                
                if direction == 'BUY' and price_change_percent < -2.0:
                    logger.info(f" Potential reversal for {symbol}: BUY trade down {price_change_percent:.2f}%")
                    reversals.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'reason': f'Price down {price_change_percent:.2f}% from entry'
                    })
                elif direction == 'SELL' and price_change_percent > 2.0:
                    logger.info(f" Potential reversal for {symbol}: SELL trade up {price_change_percent:.2f}%")
                    reversals.append({
                        'symbol': symbol,
                        'current_price': current_price,
                        'reason': f'Price up {price_change_percent:.2f}% from entry'
                    })
            
            return reversals
            
        except Exception as e:
            logger.error(f" Error checking trade direction reversals: {e}")
            return []
    
    def get_bot_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get bot trade history"""
        return self.bot_trade_history[-limit:] if self.bot_trade_history else []
    
    def reset_bot_statistics(self):
        """Reset bot statistics"""
        logger.info(" Resetting bot statistics")
        self.bot_trades_today = 0
        self.bot_total_profit = 0.0
        self.bot_total_trades = 0
        self.bot_winning_trades = 0
        self.bot_trade_history = []
        self.bot_active_trades = {}
        self.bot_pair_status = {}
        self.bot_cooldown_end = {}
        self.bot_trailing_stops = {}
        self.opportunity_cooldown = {}
        logger.info(" Bot statistics reset complete")
    
    def _log_failed_trade(self, symbol: str, reason: str, confidence: float, analysis: Dict):
        """Log a failed trade attempt with reason"""
        try:
            failed_trade = {
                'symbol': symbol,
                'action': analysis.get('final_recommendation', {}).get('action', 'UNKNOWN'),
                'confidence': confidence,
                'reason': reason,
                'timestamp': time.time(),
                'failed': True,
                'bot_trade': True,
                'trade_type': 'bot',
                'analysis_data': analysis,
                'direction': 'LONG',  # Default, will be updated based on action
                'amount': 0,
                'price': 0,
                'pnl': 0
            }
            
            # Add to trade history so it appears in the frontend
            self.bot_trade_history.append(failed_trade)
            
            # Keep only last 100 trades
            if len(self.bot_trade_history) > 100:
                self.bot_trade_history = self.bot_trade_history[-100:]
            
            logger.info(f"Logged failed trade for {symbol}: {reason} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to log failed trade: {e}")
