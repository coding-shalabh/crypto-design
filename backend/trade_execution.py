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
        """Execute a paper trade with proper direction mapping"""
        try:
            symbol = trade_data.get('symbol')
            direction_raw = trade_data.get('direction', 'buy')  # Get raw direction from frontend
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            trade_id = trade_data.get('trade_id', f"trade_{int(time.time())}_{symbol}")
            
            #   FIXED: Normalize direction mapping
            if direction_raw.lower() in ['buy', 'long']:
                trade_direction = 'BUY'
                position_direction = 'long'
            elif direction_raw.lower() in ['sell', 'short']:
                trade_direction = 'SELL'
                position_direction = 'short'
            else:
                logger.error(f"Unknown direction: {direction_raw}")
                return {'success': False, 'message': f'Unknown direction: {direction_raw}'}
            
            logger.info(f"Processing trade: {symbol} {direction_raw} -> {trade_direction}/{position_direction}")
            
            if not all([symbol, amount, price]):
                return {'success': False, 'message': 'Missing required trade data'}
            
            # Calculate trade value
            trade_value = amount * price
            
            #   FIXED: Proper balance validation
            if trade_direction == 'BUY':
                if trade_value > self.paper_balance:
                    return {'success': False, 'message': f'Insufficient balance: ${self.paper_balance:.2f} available, ${trade_value:.2f} needed'}
            elif trade_direction == 'SELL':
                current_position = self.positions.get(symbol)
                if not current_position or current_position['amount'] < amount:
                    available = current_position['amount'] if current_position else 0
                    return {'success': False, 'message': f'Insufficient {symbol} position: {available:.6f} available, {amount:.6f} needed'}
            
            # Check for existing position
            existing_position = self.positions.get(symbol)
            
            if existing_position:
                # Close existing position first
                await self.close_position(symbol)
            
            # Execute new trade
            if trade_direction == 'BUY':
                self.paper_balance -= trade_value
            else:
                self.paper_balance += trade_value
            
            # Create position (matches frontend expectations)
            position = {
                'symbol': symbol,
                'amount': amount,
                'avg_price': price,
                'entry_price': price,
                'current_price': price,
                'unrealized_pnl': 0.0,
                'direction': position_direction  #   FIXED: Use normalized direction
            }
            
            self.positions[symbol] = position
            
            # Store entry details for logging
            self.trade_entries[symbol] = {
                'entry_price': price,
                'amount': amount,
                'value': trade_value,
                'timestamp': datetime.now().isoformat(),
                'trade_data': trade_data
            }
            
            #   FIXED: Create proper trade record
            trade_record = {
                'trade_id': trade_id,
                'symbol': symbol,
                'direction': trade_direction,
                'amount': amount,
                'price': price,
                'value': trade_value,
                'timestamp': time.time(),
                'trade_type': 'MANUAL',
                'status': 'executed',
                'pnl': 0
            }
            
            self.recent_trades.insert(0, trade_record)
            if len(self.recent_trades) > 100:
                self.recent_trades = self.recent_trades[:100]
            
            self.processed_trade_ids.add(trade_id)
            
            # Log to database
            await self.db.log_trade(trade_record)
            
            logger.info(f"Paper trade executed: {symbol} {trade_direction} {amount} @ ${price:.2f}")
            
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
            entry_value = position['amount'] * position['entry_price']
            close_value = position['amount'] * close_price
            
            if position['direction'] == 'long':
                profit_loss = close_value - entry_value
            else:  # short
                profit_loss = entry_value - close_value
            
            # Update balance
            self.paper_balance += close_value
            
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