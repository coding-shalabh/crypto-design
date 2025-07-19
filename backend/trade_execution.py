"""
Trade execution and position management for paper trading
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from config import Config

logger = logging.getLogger(__name__)

class TradeExecutionManager:
    """Manages paper trading execution and position tracking"""
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.paper_balance = Config.PAPER_BALANCE
        self.positions = {}  # symbol -> position data
        self.recent_trades = []
        self.processed_trade_ids = set()
        self.pending_trades = {}  # symbol -> pending trade data
        self.accepted_trades = {}  # symbol -> accepted trade data
        self.trade_entries = {}  # symbol -> entry details for logging
        
    async def execute_paper_trade(self, trade_data: Dict) -> Dict:
        """Execute a paper trade with proper direction mapping and position netting"""
        try:
            symbol = trade_data.get('symbol')
            # Try direction first (normalized), then fall back to trade_type for backward compatibility
            direction_raw = trade_data.get('direction', trade_data.get('trade_type', 'buy'))
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            trade_id = trade_data.get('trade_id', f"trade_{int(time.time())}_{symbol}")
            
            #   FIXED: Normalize direction mapping
            if direction_raw.upper() in ['BUY', 'LONG']:
                trade_direction = 'BUY'
                position_direction = 'long'
                trade_amount = abs(amount)  # Ensure positive for long
            elif direction_raw.upper() in ['SELL', 'SHORT']:
                trade_direction = 'SELL'
                position_direction = 'short'
                trade_amount = -abs(amount)  # Ensure negative for short
            else:
                logger.error(f"Unknown direction: {direction_raw}")
                return {'success': False, 'message': f'Unknown direction: {direction_raw}'}
            
            logger.info(f"Processing trade: {symbol} {direction_raw} -> {trade_direction}/{position_direction}")
            
            if not all([symbol, amount, price]):
                return {'success': False, 'message': 'Missing required trade data'}
            
            # Calculate trade value (use absolute amount for margin calculation)
            trade_value = abs(trade_amount) * price
            
            #   FIXED: Proper balance validation for paper trading
            # For paper trading, we need margin for both long and short positions
            # Use absolute value for margin calculation to avoid negative margin
            margin_required = trade_value * 0.1  # 10% margin requirement
            
            if margin_required > self.paper_balance:
                return {'success': False, 'message': f'Insufficient balance: ${self.paper_balance:.2f} available, ${margin_required:.2f} margin needed'}
            
            # Check for existing position
            existing_position = self.positions.get(symbol)
            
            if existing_position:
                # FIXED: Implement position netting instead of closing
                existing_amount = existing_position.get('amount', 0)
                existing_direction = existing_position.get('direction', 'long')
                
                logger.info(f"Existing position: {symbol} {existing_direction} {existing_amount}")
                logger.info(f"New trade: {symbol} {position_direction} {trade_amount}")
                
                # Calculate net position
                if existing_direction == 'long':
                    existing_signed_amount = abs(existing_amount)
                else:
                    existing_signed_amount = -abs(existing_amount)
                
                net_amount = existing_signed_amount + trade_amount
                
                logger.info(f"Net position calculation: {existing_signed_amount} + {trade_amount} = {net_amount}")
                
                if abs(net_amount) < 0.001:  # Position completely closed
                    # Close the position entirely
                    await self.close_position(symbol)
                    logger.info(f"Position {symbol} completely closed due to netting")
                    
                    # Return success with zero position
                    return {
                        'success': True,
                        'message': f'Position {symbol} closed due to netting',
                        'trade_data': {
                            'trade_id': trade_id,
                            'symbol': symbol,
                            'direction': trade_direction,
                            'amount': trade_amount,
                            'price': price,
                            'value': trade_value,
                            'timestamp': time.time(),
                            'trade_type': trade_data.get('trade_type', 'MANUAL'),
                            'status': 'netted',
                            'pnl': 0
                        },
                        'new_balance': self.paper_balance
                    }
                else:
                    # Update existing position with net amount
                    if net_amount > 0:
                        new_direction = 'long'
                        new_amount = abs(net_amount)
                    else:
                        new_direction = 'short'
                        new_amount = -abs(net_amount)
                    
                    # Calculate weighted average price for the new position
                    existing_value = abs(existing_amount) * existing_position.get('entry_price', 0)
                    new_value = abs(trade_amount) * price
                    total_value = existing_value + new_value
                    total_amount = abs(existing_amount) + abs(trade_amount)
                    
                    if total_amount > 0:
                        avg_price = total_value / total_amount
                    else:
                        avg_price = price
                    
                    # Update position
                    existing_position['amount'] = new_amount
                    existing_position['direction'] = new_direction
                    existing_position['avg_price'] = avg_price
                    existing_position['entry_price'] = avg_price
                    existing_position['current_price'] = price
                    existing_position['trade_value'] = abs(new_amount) * price
                    
                    logger.info(f"Position {symbol} updated: {new_direction} {new_amount} @ ${avg_price:.2f}")
                    
                    # Create trade record
                    trade_record = {
                        'trade_id': trade_id,
                        'symbol': symbol,
                        'direction': trade_direction,
                        'amount': trade_amount,
                        'price': price,
                        'value': trade_value,
                        'timestamp': time.time(),
                        'trade_type': trade_data.get('trade_type', 'MANUAL'),
                        'status': 'netted',
                        'pnl': 0
                    }
                    
                    self.recent_trades.insert(0, trade_record)
                    if len(self.recent_trades) > 100:
                        self.recent_trades = self.recent_trades[:100]
                    
                    # Log to database
                    await self.db.log_trade(trade_record)
                    
                    return {
                        'success': True,
                        'message': f'Position {symbol} netted to {new_direction} {new_amount}',
                        'trade_data': trade_record,
                        'new_balance': self.paper_balance
                    }
            
            # No existing position, create new one
            # Execute new trade - deduct margin from balance
            self.paper_balance -= margin_required
            
            # Create position (matches frontend expectations)
            position = {
                'symbol': symbol,
                'amount': abs(trade_amount),
                'avg_price': price,
                'entry_price': price,
                'current_price': price,
                'unrealized_pnl': 0.0,
                'direction': position_direction,
                'margin_used': margin_required,
                'trade_value': trade_value
            }
            
            self.positions[symbol] = position
            
            # Store entry details for logging
            self.trade_entries[symbol] = {
                'entry_price': price,
                'amount': trade_amount,
                'value': trade_value,
                'timestamp': datetime.now().isoformat(),
                'trade_data': trade_data
            }
            
            #   FIXED: Create proper trade record
            trade_record = {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': trade_direction,
                'amount': trade_amount,
                'price': price,
                'value': trade_value,
                'timestamp': time.time(),
                'trade_type': trade_data.get('trade_type', 'MANUAL'),
                'status': 'executed',
                'pnl': 0
            }
            
            self.recent_trades.insert(0, trade_record)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]
            
            self.processed_trade_ids.add(trade_id)
            
            # Log to database
            await self.db.log_trade(trade_record)
            
            logger.info(f"Paper trade executed: {symbol} {trade_direction} {abs(trade_amount)} @ ${price:.2f}")
            
            return {
                'success': True,
                'message': f'Paper trade executed: {symbol} {trade_direction}',
                'trade_data': trade_record,
                'new_balance': self.paper_balance
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing paper trade: {e}")
            return {'success': False, 'message': f'Error executing trade: {e}'}

    async def close_position(self, symbol: str, close_price: Optional[float] = None) -> Dict:
        """Close a position"""
        try:
            position = self.positions.get(symbol)
            if not position:
                return {'success': False, 'message': f'No position found for {symbol}'}
            
            # Get current price if not provided
            if close_price is None:
                # This would typically come from market data
                close_price = position['entry_price']  # Use entry price as fallback
            
            # Calculate profit/loss 
            # For consistency with position PnL calculation, use abs(amount) for short positions
            if position['direction'] == 'long':
                entry_value = position['amount'] * position['entry_price']
                close_value = position['amount'] * close_price
                profit_loss = close_value - entry_value
            else:  # short
                # For short positions, use abs(amount) to get correct PnL
                abs_amount = abs(position['amount'])
                entry_value = abs_amount * position['entry_price']
                close_value = abs_amount * close_price
                profit_loss = entry_value - close_value
            
            # Update balance - return margin plus profit/loss
            margin_used = position.get('margin_used', entry_value * 0.1)
            self.paper_balance += margin_used + profit_loss
            
            # Get entry details for logging
            entry_details = self.trade_entries.get(symbol, {})
            
            # Log closed trade
            await self.db.log_closed_trade(
                symbol=symbol,
                position=position,
                close_price=close_price,
                close_value=close_value,
                profit_loss=profit_loss,
                entry_details=entry_details
            )
            
            # Create trade record (matches frontend expectations)
            trade_id = f"close_{int(time.time())}_{symbol}"
            trade_record = {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': 'SELL' if position['direction'] == 'long' else 'BUY',
                'amount': position['amount'],
                'price': close_price,
                'value': close_value,
                'timestamp': time.time(),
                'trade_type': 'MANUAL',
                'status': 'executed',
                'pnl': profit_loss
            }
            
            self.recent_trades.insert(0, trade_record)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]
            
            # Clean up
            del self.positions[symbol]
            if symbol in self.trade_entries:
                del self.trade_entries[symbol]
            
            logger.info(f" Position closed: {symbol} @ ${close_price:.2f}, P&L: ${profit_loss:.2f}")
            
            return {
                'success': True,
                'message': f'Position closed: {symbol}',
                'trade_data': trade_record,
                'profit_loss': profit_loss,
                'new_balance': self.paper_balance
            }
            
        except Exception as e:
            logger.error(f" Error closing position for {symbol}: {e}")
            return {'success': False, 'message': f'Error closing position: {e}'}
    
    async def accept_trade(self, symbol: str, trade_data: Dict) -> Dict:
        """Accept a pending trade"""
        try:
            if symbol not in self.pending_trades:
                return {'success': False, 'message': f'No pending trade found for {symbol}'}
            
            pending_trade = self.pending_trades[symbol]
            
            # Execute the trade
            result = await self.execute_paper_trade(pending_trade)
            
            if result['success']:
                # Move to accepted trades
                self.accepted_trades[symbol] = pending_trade
                del self.pending_trades[symbol]
                
                logger.info(f" Trade accepted and executed for {symbol}")
                return result
            else:
                return result
                
        except Exception as e:
            logger.error(f" Error accepting trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error accepting trade: {e}'}
    
    async def add_pending_trade(self, symbol: str, trade_data: Dict) -> Dict:
        """Add a pending trade for manual approval"""
        try:
            self.pending_trades[symbol] = trade_data
            logger.info(f"Pending trade added for {symbol}")
            return {'success': True, 'message': f'Pending trade added for {symbol}'}
            
        except Exception as e:
            logger.error(f" Error adding pending trade for {symbol}: {e}")
            return {'success': False, 'message': f'Error adding pending trade: {e}'}
    
    async def check_pending_trades(self) -> List[Dict]:
        """Check for pending trades that need approval"""
        try:
            pending_list = []
            for symbol, trade_data in self.pending_trades.items():
                pending_list.append({
                    'symbol': symbol,
                    'trade_data': trade_data,
                    'timestamp': time.time()
                })
            
            return pending_list
            
        except Exception as e:
            logger.error(f" Error checking pending trades: {e}")
            return []
    
    def get_positions(self) -> Dict:
        """Get current positions (matches frontend expectations)"""
        return self.positions.copy()
    
    def update_position_prices(self, price_updates: Dict[str, float]):
        """Update position prices with current market prices"""
        updated_positions = []
        for symbol, current_price in price_updates.items():
            if symbol in self.positions:
                position = self.positions[symbol]
                old_price = position.get('current_price', 0)
                position['current_price'] = current_price
                
                # Calculate unrealized PnL
                entry_price = position['entry_price']
                amount = position['amount']
                
                # Log price updates for debugging
                if abs(current_price - old_price) > 0.01:  # Only log significant changes
                    logger.info(f"Position {symbol} price updated: ${old_price:.2f} -> ${current_price:.2f}")
                updated_positions.append(symbol)
                
                if position['direction'] == 'long':
                    unrealized_pnl = (current_price - entry_price) * amount
                else:  # short
                    # For short positions, use absolute amount to get correct PnL sign
                    unrealized_pnl = (entry_price - current_price) * abs(amount)
                
                position['unrealized_pnl'] = unrealized_pnl
                
                logger.debug(f"Updated {symbol} position: price ${current_price:.2f}, PnL ${unrealized_pnl:.2f}")
        
        return self.positions
    
    def update_position_current_price(self, symbol: str, current_price: float):
        """Update the current price of a position"""
        if symbol in self.positions:
            self.positions[symbol]['current_price'] = current_price
    
    def get_balance(self) -> float:
        """Get current paper balance"""
        return self.paper_balance
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades (matches frontend expectations)"""
        return self.recent_trades[:limit]
    
    def get_pending_trades(self) -> Dict:
        """Get pending trades"""
        return self.pending_trades.copy()
    
    def get_accepted_trades(self) -> Dict:
        """Get accepted trades"""
        return self.accepted_trades.copy()
    
    def reset_paper_trading(self):
        """Reset paper trading state"""
        self.paper_balance = Config.PAPER_BALANCE
        self.positions.clear()
        self.recent_trades.clear()
        self.processed_trade_ids.clear()
        self.pending_trades.clear()
        self.accepted_trades.clear()
        self.trade_entries.clear()
        logger.info(" Paper trading state reset") 