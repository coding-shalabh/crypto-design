"""
Automated trading bot logic and execution
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config import Config
from database import DatabaseManager # Import DatabaseManager

logger = logging.getLogger(__name__)

from confidence_score_calculator import ConfidenceScoreCalculator

class TradingBot:
    """Automated trading bot with risk management"""
    
    def __init__(self):
        logger.info("Initializing Trading Bot...")
        
        self.bot_enabled = False
        self.bot_config = Config.get_bot_config()
        
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
        """Start the trading bot"""
        try:
            logger.info("Starting trading bot...")
            
            if self.bot_enabled:
                logger.warning(" Bot is already running")
                return {'success': False, 'message': 'Bot is already running'}
            
            # Update config if provided
            if config:
                logger.info(f" Updating bot config: {config}")
                self.bot_config.update(config)
            
            # Reset daily trade counter if it's a new day
            current_time = time.time()
            if current_time - self.bot_last_trade_reset > 86400:  # 24 hours
                logger.info(" Resetting daily trade counter")
                self.bot_trades_today = 0
                self.bot_last_trade_reset = current_time
            
            self.bot_enabled = True
            self.bot_start_time = current_time
            
            # Initialize pair status
            for pair in self.bot_config['allowed_pairs']:
                self.bot_pair_status[pair] = 'idle'
            
            logger.info(f" Trading bot started successfully!")
            logger.info(f" Allowed pairs: {self.bot_config['allowed_pairs']}")
            logger.info(f" Trade amount: ${self.bot_config['trade_amount_usdt']}")
            logger.info(f" Max trades per day: {self.bot_config['max_trades_per_day']}")
            logger.info(f" AI confidence threshold: {self.bot_config['ai_confidence_threshold']}")
            
            return {
                'success': True, 
                'message': 'Trading bot started successfully',
                'config': self.bot_config
            }
            
        except Exception as e:
            logger.error(f" Error starting bot: {e}")
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
                'start_time': self.bot_start_time,
                'active_trades': len(self.bot_active_trades),
                'trades_today': self.bot_trades_today,
                'total_profit': self.bot_total_profit,
                'total_trades': self.bot_total_trades,
                'winning_trades': self.bot_winning_trades,
                'win_rate': round(win_rate, 2),
                'pair_status': pair_status,
                'running_duration': int(running_time)
            }
            
            logger.info(f" Bot status: Enabled={self.bot_enabled}, Active trades={len(self.bot_active_trades)}, Trades today={self.bot_trades_today}, Win rate={win_rate:.1f}%")
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
            logger.info(f" Bot config updated successfully")
            
            return {'success': True, 'message': 'Bot configuration updated successfully'}
            
        except Exception as e:
            logger.error(f" Error updating bot config: {e}")
            return {'success': False, 'message': f'Error updating config: {e}'}
    
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

    async def execute_trade(self, symbol: str, direction: str, amount_usdt: float, price: float, trade_type: str, confidence_score: float, analysis_data: Dict) -> Dict:
        """Execute a trade using the trade execution manager"""
        try:
            # Calculate quantity based on amount and price
            quantity = amount_usdt / price
            
            # Create trade data
            trade_data = {
                'symbol': symbol,
                'direction': direction.lower(),  # 'buy' or 'sell'
                'amount': quantity,
                'price': price,
                'trade_id': f"bot_trade_{int(time.time())}_{symbol}",
                'trade_type': 'bot',  # Mark as bot trade
                'bot_trade': True,
                'analysis_confidence': confidence_score,
                'analysis_data': analysis_data
            }
            
            # Execute the trade using the trade execution manager
            if hasattr(self, 'trade_execution_manager'):
                result = await self.trade_execution_manager.execute_paper_trade(trade_data)
            else:
                # Fallback: create a mock successful trade
                logger.warning(f"Trade execution manager not available, creating mock trade for {symbol}")
                result = {
                    'success': True,
                    'message': f'Mock trade executed: {symbol} {direction}',
                    'trade_data': trade_data,
                    'new_balance': 1000.0  # Mock balance
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in execute_trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}

    async def execute_bot_trade(self, symbol: str, analysis: Dict, current_price: float, balance: float) -> Dict:
        """Execute a bot trade based on AI analysis"""
        try:
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
                logger.info(f"Overriding HOLD to {action} for {symbol} due to high confidence {ai_confidence:.2f}")

            if action == 'HOLD':
                logger.info(f"Trade execution for {symbol}: HOLD signal received. Not executing trade.")
                return {'success': False, 'message': 'HOLD signal received'}

            # Calculate trade amount
            trade_amount_usdt = self._calculate_trade_amount(balance)
            
            # Execute the trade
            trade_result = await self.execute_trade(
                symbol=symbol,
                direction=action.lower(),
                amount_usdt=trade_amount_usdt,
                price=current_price,
                trade_type='bot',
                confidence_score=ai_confidence,
                analysis_data=analysis
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
                logger.error(f"Bot trade failed for {symbol}: {trade_result.get('message', 'Unknown error')}")
            
            return trade_result
            
        except Exception as e:
            logger.error(f"Error executing bot trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def _should_override_hold(self, action: str, confidence: float) -> bool:
        # Override HOLD if confidence is above the trading threshold
        return action == 'HOLD' and confidence >= self.bot_config['ai_confidence_threshold']

    def _get_override_action(self, confidence: float) -> str:
        # For high confidence HOLD signals, default to BUY as it's more common
        # in bullish markets. This could be enhanced to analyze market conditions.
        logger.info(f" Overriding HOLD signal with BUY due to high confidence: {confidence:.2f}")
        return 'BUY'

    def _calculate_trade_amount(self, balance: float) -> float:
        trade_amount_usdt = min(
            self.bot_config['trade_amount_usdt'],
            balance * 0.95  # Use 95% of balance as safety
        )
        return trade_amount_usdt if trade_amount_usdt >= 10 else 0

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