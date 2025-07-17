"""
Automated trading bot logic and execution
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from config import Config

logger = logging.getLogger(__name__)

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
        """Check if bot should execute a trade based on conditions"""
        try:
            logger.info(f" Checking trading conditions for {symbol}")
            
            if not self.bot_enabled:
                logger.info(f"Bot disabled, skipping {symbol}")
                return False
            
            # Check if symbol is allowed
            if symbol not in self.bot_config['allowed_pairs']:
                logger.info(f" {symbol} not in allowed pairs: {self.bot_config['allowed_pairs']}")
                return False
            
            # Check daily trade limit
            if self.bot_trades_today >= self.bot_config['max_trades_per_day']:
                logger.info(f" Daily trade limit reached for {symbol} ({self.bot_trades_today}/{self.bot_config['max_trades_per_day']})")
                return False
            
            # Check concurrent trade limit
            active_trades = len(self.bot_active_trades)
            if active_trades >= self.bot_config['max_concurrent_trades']:
                logger.info(f" Max concurrent trades reached for {symbol} ({active_trades}/{self.bot_config['max_concurrent_trades']})")
                return False
            
            # Check pair status
            pair_status = self.bot_pair_status.get(symbol, 'idle')
            if pair_status != 'idle':
                logger.info(f"{symbol} not idle (status: {pair_status})")
                return False
            
            # Check cooldown
            if symbol in self.bot_cooldown_end:
                if time.time() < self.bot_cooldown_end[symbol]:
                    remaining = self.bot_cooldown_end[symbol] - time.time()
                    logger.info(f"⏰ {symbol} in cooldown, {remaining:.0f}s remaining")
                    return False
            
            # Check AI confidence threshold
            confidence = analysis.get('combined_confidence', 0)
            threshold = self.bot_config['ai_confidence_threshold']
            if confidence < threshold:
                logger.info(f" Confidence {confidence:.2f} below threshold {threshold} for {symbol}")
                return False
            
            # Check opportunity cooldown
            if symbol in self.opportunity_cooldown:
                if time.time() < self.opportunity_cooldown[symbol]:
                    remaining = self.opportunity_cooldown[symbol] - time.time()
                    logger.info(f"⏰ {symbol} in opportunity cooldown, {remaining:.0f}s remaining")
                    return False
            
            logger.info(f" All trading conditions met for {symbol}!")
            return True
            
        except Exception as e:
            logger.error(f" Error checking bot trading conditions for {symbol}: {e}")
            return False
    
    async def execute_bot_trade(self, symbol: str, analysis: Dict, current_price: float, balance: float) -> Dict:
        """Execute a bot trade based on AI analysis"""
        try:
            logger.info(f" Executing bot trade for {symbol} at ${current_price}")
            
            # Get trade recommendation
            recommendation = analysis.get('final_recommendation', {})
            action = recommendation.get('action', 'HOLD')
            confidence = analysis.get('combined_confidence', 0)
            
            logger.info(f" Trade recommendation: {action} with {confidence:.2f} confidence")
            
            if action == 'HOLD':
                logger.info(f"HOLD signal for {symbol}, no trade executed")
                return {'success': False, 'message': 'HOLD signal received'}
            
            # Calculate trade amount
            trade_amount_usdt = min(
                self.bot_config['trade_amount_usdt'],
                balance * 0.95  # Use 95% of balance as safety
            )
            
            if trade_amount_usdt < 10:  # Minimum trade amount
                logger.warning(f" Insufficient balance for {symbol}: ${balance}")
                return {'success': False, 'message': 'Insufficient balance for trade'}
            
            # Calculate quantity
            quantity = trade_amount_usdt / current_price
            
            # Create trade data
            trade_data = {
                'symbol': symbol,
                'direction': 'LONG' if action == 'BUY' else 'SHORT',  # Map BUY/SELL to LONG/SHORT
                'amount': quantity,
                'price': current_price,
                'value_usdt': trade_amount_usdt,
                'timestamp': time.time(),
                'bot_trade': True,
                'analysis_confidence': confidence,
                'analysis_recommendation': recommendation
            }
            
            # Update bot state
            self.bot_trades_today += 1
            self.bot_pair_status[symbol] = 'in_trade'
            self.bot_active_trades[symbol] = trade_data
            
            # Set cooldown
            cooldown_duration = self.bot_config.get('pair_cooldown_seconds', 300)  # 5 minutes
            self.bot_cooldown_end[symbol] = time.time() + cooldown_duration
            
            # Set opportunity cooldown
            opportunity_cooldown = self.bot_config.get('opportunity_cooldown_seconds', 600)  # 10 minutes
            self.opportunity_cooldown[symbol] = time.time() + opportunity_cooldown
            
            logger.info(f" Bot trade executed for {symbol}: {action} {quantity:.6f} @ ${current_price}")
            logger.info(f" Trade value: ${trade_amount_usdt}")
            logger.info(f" Trades today: {self.bot_trades_today}/{self.bot_config['max_trades_per_day']}")
            logger.info(f"⏰ Cooldown set for {symbol}: {cooldown_duration}s")
            
            return {
                'success': True,
                'message': f'Bot trade executed: {action} {symbol}',
                'trade_data': trade_data
            }
            
        except Exception as e:
            logger.error(f" Error executing bot trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error executing trade: {e}'}
    
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