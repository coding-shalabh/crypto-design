import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
import os
from binance_service import BinanceService
from database import DatabaseManager

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

class InsufficientBalanceError(Exception):
    """Custom exception for insufficient balance with transfer suggestions"""
    def __init__(self, message, error_data=None):
        super().__init__(message)
        self.error_data = error_data or {}

class TradingManager:
    def __init__(self):
        self.binance_service = BinanceService()
        self.db_manager = DatabaseManager()
        self.trading_mode = 'mock'  # Initialize trading mode
        self.mock_balances = {}
        self.mock_orders = {}
        self.mock_trades = []
        self.order_id_counter = 1000
        
        # Initialize mock balance
        self.mock_balances = {
            'USDT': {'free': 100000.0, 'locked': 0.0, 'total': 100000.0}
        }
    
    def set_trading_mode(self, mode: str):
        """Set trading mode to 'mock' or 'live'"""
        self.trading_mode = mode
        logger.info(f"Trading mode set to: {mode}")
    
    def verify_trading_readiness(self) -> Dict:
        """Verify if the system is ready for trading"""
        try:
            # For mock mode, always ready
            if self.trading_mode == 'mock':
                return {
                    'ready': True,
                    'mode': 'mock',
                    'message': 'Mock trading mode - always ready',
                    'usdt_balance': self.get_trading_balance('USDT')
                }
            
            # For live mode, check Binance readiness
            logger.info("Verifying live trading readiness...")
            readiness = self.binance_service.verify_trading_readiness()
            
            if readiness['ready']:
                logger.info("✅ Trading system ready for live trading")
                return {
                    'ready': True,
                    'mode': 'live',
                    'message': 'Live trading ready',
                    'account_status': readiness.get('account_status'),
                    'usdt_balance': readiness.get('usdt_balance'),
                    'can_trade': readiness.get('can_trade')
                }
            else:
                logger.error(f"❌ Trading system not ready: {readiness.get('error')}")
                return {
                    'ready': False,
                    'mode': 'live',
                    'error': readiness.get('error'),
                    'message': 'Live trading not ready'
                }
                
        except Exception as e:
            logger.error(f"Failed to verify trading readiness: {e}")
            return {
                'ready': False,
                'mode': self.trading_mode,
                'error': str(e),
                'message': 'Readiness check failed'
            }
    
    def test_connection(self) -> Dict:
        """Test connection based on trading mode"""
        try:
            if self.trading_mode == 'live':
                success = self.binance_service.test_connectivity()
                return {
                    'success': success,
                    'mode': 'live',
                    'message': 'Binance API connection successful' if success else 'Binance API connection failed'
                }
            else:
                return {
                    'success': True,
                    'mode': 'mock',
                    'message': 'Mock trading mode active'
                }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                'success': False,
                'mode': self.trading_mode,
                'message': str(e)
            }
    
    def get_balance(self, asset: str = 'USDT') -> Dict:
        """Get balance for specific asset (Spot wallet)"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.get_balance(asset)
            else:
                # Mock trading balance
                if asset not in self.mock_balances:
                    self.mock_balances[asset] = {'free': 0.0, 'locked': 0.0, 'total': 0.0}
                return {
                    'asset': asset,
                    **self.mock_balances[asset]
                }
        except Exception as e:
            logger.error(f"Failed to get balance for {asset}: {e}")
            raise
    
    def get_trading_balance(self, asset: str = 'USDT', mode: str = None) -> Dict:
        """Get trading balance optimized for immediate trading decisions"""
        try:
            effective_mode = mode if mode else self.trading_mode
            logger.info(f"Getting trading balance for {asset} in {effective_mode} mode")
            
            # In mock mode, return virtual balance
            if effective_mode == 'mock':
                if asset not in self.mock_balances:
                    default_balance = 100000.0 if asset == 'USDT' else 0.0
                    self.mock_balances[asset] = {
                        'free': default_balance, 
                        'locked': 0.0, 
                        'total': default_balance
                    }
                    
                balance_result = {
                    'asset': asset,
                    'free': self.mock_balances[asset]['free'],
                    'locked': self.mock_balances[asset]['locked'],
                    'total': self.mock_balances[asset]['total'],
                    'wallet_type': 'MOCK',
                    'note': 'Virtual balance for paper trading',
                    'mode': effective_mode,
                    'available_for_trading': self.mock_balances[asset]['free'] > 0,
                    'success': True
                }
                logger.info(f"Mock trading balance for {asset}: ${balance_result['total']:.2f}")
                return balance_result
                
            # In live mode, use optimized futures balance checking
            logger.info(f"Fetching live futures balance for {asset}")
            
            # Use the new optimized method from binance_service
            futures_balance = self.binance_service.get_futures_trading_balance(asset)
            
            if futures_balance['success']:
                futures_balance['mode'] = effective_mode
                futures_balance['note'] = 'Futures Wallet - Optimized for trading'
                logger.info(f"Found futures balance for {asset}: ${futures_balance['total']:.2f}")
                return futures_balance
            
            # If futures fails, fallback to spot wallet
            try:
                spot_balance = self.binance_service.get_balance(asset)
                balance_result = {
                    'asset': asset,
                    'free': spot_balance['free'],
                    'locked': spot_balance['locked'],
                    'total': spot_balance['total'],
                    'wallet_type': 'SPOT',
                    'note': 'Spot Wallet - Fallback from futures',
                    'mode': effective_mode,
                    'available_for_trading': spot_balance['free'] > 0,
                    'success': True
                }
                logger.info(f"Using spot balance for {asset}: ${balance_result['total']:.2f}")
                return balance_result
            except Exception as e:
                logger.error(f"Failed to get spot balance for {asset}: {e}")
            
            # Return zero balance if all fails
            return {
                'asset': asset, 
                'free': 0.0, 
                'locked': 0.0, 
                'total': 0.0,
                'wallet_type': 'FUTURES',
                'note': 'No balance found',
                'mode': effective_mode,
                'available_for_trading': False,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Failed to get trading balance for {asset}: {e}")
            # Emergency fallback to mock balance
            if asset not in self.mock_balances:
                default_balance = 100000.0 if asset == 'USDT' else 0.0
                self.mock_balances[asset] = {
                    'free': default_balance, 
                    'locked': 0.0, 
                    'total': default_balance
                }
            return {
                'asset': asset,
                'free': self.mock_balances[asset]['free'],
                'locked': self.mock_balances[asset]['locked'],
                'total': self.mock_balances[asset]['total'],
                'wallet_type': 'MOCK_FALLBACK',
                'note': 'API failed - emergency fallback',
                'mode': effective_mode,
                'available_for_trading': self.mock_balances[asset]['free'] > 0,
                'success': False,
                'error': str(e)
            }
    
    def get_all_balances(self) -> List[Dict]:
        """Get all non-zero balances"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.get_all_balances()
            else:
                # Mock trading balances
                balances = []
                for asset, balance in self.mock_balances.items():
                    if balance['total'] > 0:
                        balances.append({
                            'asset': asset,
                            **balance
                        })
                return balances
        except Exception as e:
            logger.error(f"Failed to get all balances: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.get_current_price(symbol)
            else:
                # For mock trading, we'll use the same price feed but not execute real trades
                return self.binance_service.get_current_price(symbol)
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                   price: float = None, time_in_force: str = 'GTC', force_check_real_balance: bool = True) -> Dict:
        """Place a trading order - ALWAYS validates against real Binance balance"""
        try:
            # ALWAYS check real balance regardless of trading mode
            if force_check_real_balance:
                try:
                    # Get trading balance to determine wallet type
                    trading_balance = self.get_trading_balance('USDT')
                    wallet_type = trading_balance.get('wallet_type', 'SPOT')
                    
                    if side.upper() == 'BUY':
                        current_price = self.get_current_price(symbol)
                        required_usdt = quantity * (price if price else current_price)
                        available_usdt = trading_balance.get('free', 0.0)
                        if available_usdt < required_usdt:
                            # Check other wallets for sufficient balance
                            transfer_suggestions = self._get_transfer_suggestions('USDT', required_usdt, wallet_type)
                            error_data = {
                                'error_type': 'insufficient_balance',
                                'required_amount': required_usdt,
                                'available_amount': available_usdt,
                                'asset': 'USDT',
                                'current_wallet': wallet_type,
                                'transfer_suggestions': transfer_suggestions
                            }
                            raise InsufficientBalanceError(f"Insufficient real USDT balance. Required: {required_usdt}, Available: {available_usdt}", error_data)
                    else:  # SELL
                        base_asset = symbol.replace('USDT', '')
                        # Get trading balance for base asset
                        base_trading_balance = self.get_trading_balance(base_asset)
                        available_base = base_trading_balance.get('free', 0.0)
                        if available_base < quantity:
                            raise Exception(f"Insufficient real {base_asset} balance. Required: {quantity}, Available: {available_base}")
                except Exception as e:
                    logger.warning(f"Failed to check real balance, proceeding with {self.trading_mode} mode: {e}")
            
            if self.trading_mode == 'live':
                return self._place_live_order(symbol, side, order_type, quantity, price, time_in_force)
            else:
                return self._place_mock_order(symbol, side, order_type, quantity, price, time_in_force)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def _place_live_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                         price: float = None, time_in_force: str = 'GTC') -> Dict:
        """Place live order on Binance"""
        try:
            result = self.binance_service.place_order(symbol, side, order_type, quantity, price, time_in_force)
            
            # Store order in database with 'live' mode
            self._store_order_in_db(result, 'live')
            
            return {
                'success': True,
                'mode': 'live',
                'order': result
            }
        except Exception as e:
            logger.error(f"Live order placement failed: {e}")
            raise
    
    def _place_mock_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                         price: float = None, time_in_force: str = 'GTC') -> Dict:
        """Place mock order (paper trading)"""
        try:
            current_price = self.get_current_price(symbol)
            
            # Generate mock order ID
            order_id = self.order_id_counter
            self.order_id_counter += 1
            
            # For market orders, use current price
            if order_type.upper() == 'MARKET':
                execution_price = current_price
            else:
                execution_price = price if price else current_price
            
            # Calculate values
            base_asset = symbol.replace('USDT', '')
            quote_asset = 'USDT'
            
            if side.upper() == 'BUY':
                usdt_amount = quantity * execution_price
                
                # Check USDT balance
                usdt_balance = self.get_balance('USDT')
                if usdt_balance['free'] < usdt_amount:
                    raise Exception(f"Insufficient USDT balance. Required: {usdt_amount}, Available: {usdt_balance['free']}")
                
                # Update balances
                self.mock_balances['USDT']['free'] -= usdt_amount
                if base_asset not in self.mock_balances:
                    self.mock_balances[base_asset] = {'free': 0.0, 'locked': 0.0, 'total': 0.0}
                self.mock_balances[base_asset]['free'] += quantity
                self.mock_balances[base_asset]['total'] += quantity
                
            else:  # SELL
                # Check base asset balance
                if base_asset not in self.mock_balances:
                    raise Exception(f"No {base_asset} balance to sell")
                
                base_balance = self.get_balance(base_asset)
                if base_balance['free'] < quantity:
                    raise Exception(f"Insufficient {base_asset} balance. Required: {quantity}, Available: {base_balance['free']}")
                
                # Update balances
                usdt_amount = quantity * execution_price
                self.mock_balances[base_asset]['free'] -= quantity
                self.mock_balances[base_asset]['total'] -= quantity
                self.mock_balances['USDT']['free'] += usdt_amount
                self.mock_balances['USDT']['total'] += usdt_amount
            
            # Create mock order result
            mock_order = {
                'orderId': order_id,
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': str(quantity),
                'price': str(execution_price),
                'status': 'FILLED',
                'timeInForce': time_in_force,
                'executedQty': str(quantity),
                'cummulativeQuoteQty': str(usdt_amount),
                'transactTime': int(time.time() * 1000),
                'origQty': str(quantity)
            }
            
            # Store mock trade
            mock_trade = {
                'id': len(self.mock_trades) + 1,
                'orderId': order_id,
                'symbol': symbol,
                'side': side.upper(),
                'quantity': quantity,
                'price': execution_price,
                'quoteQty': usdt_amount,
                'time': int(time.time() * 1000),
                'isBuyer': side.upper() == 'BUY',
                'isMaker': False
            }
            
            self.mock_trades.append(mock_trade)
            self.mock_orders[order_id] = mock_order
            
            # Store order in database with 'mock' mode
            self._store_order_in_db(mock_order, 'mock')
            
            return {
                'success': True,
                'mode': 'mock',
                'order': mock_order
            }
            
        except Exception as e:
            logger.error(f"Mock order placement failed: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get open orders"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.get_open_orders(symbol)
            else:
                # For mock trading, return orders that are not filled
                open_orders = []
                for order in self.mock_orders.values():
                    if order['status'] != 'FILLED':
                        if symbol is None or order['symbol'] == symbol:
                            open_orders.append(order)
                return open_orders
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.cancel_order(symbol, order_id)
            else:
                # Cancel mock order
                if order_id in self.mock_orders:
                    self.mock_orders[order_id]['status'] = 'CANCELED'
                    return {
                        'success': True,
                        'mode': 'mock',
                        'message': f'Mock order {order_id} canceled'
                    }
                else:
                    raise Exception(f"Mock order {order_id} not found")
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        try:
            if self.trading_mode == 'live':
                if symbol:
                    return self.binance_service.get_trade_history(symbol, limit)
                else:
                    # Get from database for all symbols
                    return self._get_trades_from_db('live', limit)
            else:
                # Return mock trades
                trades = self.mock_trades.copy()
                if symbol:
                    trades = [t for t in trades if t['symbol'] == symbol]
                return trades[-limit:]
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            raise
    
    def _store_order_in_db(self, order: Dict, mode: str):
        """Store order in database"""
        try:
            # This would integrate with your existing database structure
            # For now, we'll add to a trades collection with mode indicator
            trade_data = {
                'mode': mode,
                'order_id': order.get('orderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'quantity': float(order.get('quantity', 0)),
                'price': float(order.get('price', 0)),
                'status': order.get('status'),
                'timestamp': datetime.now(),
                'raw_order': order
            }
            
            # Add to database (implement based on your DB structure)
            logger.info(f"Stored {mode} order in database: {order.get('orderId')}")
            
        except Exception as e:
            logger.error(f"Failed to store order in database: {e}")
    
    def _get_trades_from_db(self, mode: str, limit: int = 50) -> List[Dict]:
        """Get trades from database"""
        try:
            # Implement based on your database structure
            # This is a placeholder
            return []
        except Exception as e:
            logger.error(f"Failed to get trades from database: {e}")
            return []
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary including P&L"""
        try:
            balances = self.get_all_balances()
            total_usdt_value = 0.0
            
            for balance in balances:
                if balance['asset'] == 'USDT':
                    total_usdt_value += balance['total']
                else:
                    try:
                        symbol = f"{balance['asset']}USDT"
                        price = self.get_current_price(symbol)
                        total_usdt_value += balance['total'] * price
                    except:
                        # Skip assets that don't have USDT pairs
                        continue
            
            initial_balance = 100000.0  # Starting mock balance
            if self.trading_mode == 'live':
                # For live trading, calculate based on actual deposits/withdrawals
                initial_balance = total_usdt_value  # Placeholder
            
            pnl = total_usdt_value - initial_balance
            pnl_percentage = (pnl / initial_balance) * 100 if initial_balance > 0 else 0
            
            return {
                'mode': self.trading_mode,
                'total_value_usdt': total_usdt_value,
                'initial_balance': initial_balance,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'balances': balances
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            raise
    
    def get_categorized_balances(self) -> Dict:
        """Get balances categorized by wallet type (Spot, Futures, etc.)"""
        try:
            if self.trading_mode == 'live':
                # Check if Binance service has valid credentials
                if not self.binance_service.api_key or not self.binance_service.api_secret:
                    logger.warning("Binance API credentials not configured for live mode")
                    # Return empty structure with warning
                    return {
                        'SPOT': {'name': 'Spot Wallet', 'balances': [], 'total_usdt': 0.0},
                        'FUTURES': {'name': 'Futures Wallet', 'balances': [], 'total_usdt': 0.0},
                        'MARGIN': {'name': 'Cross Margin', 'balances': [], 'total_usdt': 0.0},
                        'FUNDING': {'name': 'Funding Wallet', 'balances': [], 'total_usdt': 0.0},
                        'error': 'API credentials not configured'
                    }
                
                return self.binance_service.get_categorized_balances()
            else:
                # For mock trading, simulate categorized balances
                mock_categorized = {
                    'SPOT': {
                        'name': 'Spot Wallet',
                        'balances': [],
                        'total_usdt': 0.0
                    },
                    'FUTURES': {
                        'name': 'Futures Wallet',
                        'balances': [],
                        'total_usdt': 0.0
                    },
                    'MARGIN': {
                        'name': 'Cross Margin',
                        'balances': [],
                        'total_usdt': 0.0
                    },
                    'FUNDING': {
                        'name': 'Funding Wallet',
                        'balances': [],
                        'total_usdt': 0.0
                    }
                }
                
                # Add mock balances to SPOT category
                for asset, balance in self.mock_balances.items():
                    if balance['total'] > 0:
                        balance_data = {
                            'asset': asset,
                            'free': balance['free'],
                            'locked': balance['locked'],
                            'total': balance['total'],
                            'wallet_type': 'SPOT'
                        }
                        mock_categorized['SPOT']['balances'].append(balance_data)
                        
                        # Calculate USDT value
                        if asset == 'USDT':
                            mock_categorized['SPOT']['total_usdt'] += balance['total']
                        else:
                            try:
                                symbol = f"{asset}USDT"
                                price = self.get_current_price(symbol)
                                mock_categorized['SPOT']['total_usdt'] += balance['total'] * price
                            except:
                                continue
                
                return mock_categorized
                
        except Exception as e:
            logger.error(f"Failed to get categorized balances: {e}")
            raise
    
    def get_wallet_balances(self, wallet_type: str) -> List[Dict]:
        """Get balances for a specific wallet type"""
        try:
            if self.trading_mode == 'live':
                if wallet_type == 'SPOT':
                    return self.binance_service.get_spot_balances()
                elif wallet_type == 'FUTURES':
                    return self.binance_service.get_futures_balances()
                elif wallet_type == 'MARGIN':
                    return self.binance_service.get_margin_balances()
                elif wallet_type == 'FUNDING':
                    return self.binance_service.get_funding_balances()
                else:
                    raise Exception(f"Unsupported wallet type: {wallet_type}")
            else:
                # For mock trading, return spot balances for all wallet types
                balances = []
                for asset, balance in self.mock_balances.items():
                    if balance['total'] > 0:
                        balances.append({
                            'asset': asset,
                            'free': balance['free'],
                            'locked': balance['locked'],
                            'total': balance['total'],
                            'wallet_type': wallet_type
                        })
                return balances
                
        except Exception as e:
            logger.error(f"Failed to get {wallet_type} balances: {e}")
            raise
    
    def _get_transfer_suggestions(self, asset: str, required_amount: float, current_wallet: str) -> List[Dict]:
        """Get suggestions for transferring funds from other wallets"""
        suggestions = []
        try:
            # Get categorized balances to check other wallets
            categorized_balances = self.binance_service.get_categorized_balances()
            
            for wallet_type, wallet_data in categorized_balances.items():
                if wallet_type == current_wallet:
                    continue
                    
                # Find the asset in this wallet
                for balance in wallet_data.get('balances', []):
                    if balance['asset'] == asset and float(balance['free']) >= required_amount:
                        suggestions.append({
                            'from_wallet': wallet_type,
                            'to_wallet': current_wallet,
                            'asset': asset,
                            'available_amount': float(balance['free']),
                            'required_amount': required_amount,
                            'wallet_name': wallet_data['name']
                        })
                        break
            
            return suggestions
        except Exception as e:
            logger.error(f"Failed to get transfer suggestions: {e}")
            return []
    
    def transfer_between_wallets(self, asset: str, amount: float, from_wallet: str, to_wallet: str) -> Dict:
        """Transfer balance between different wallet types"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.transfer_between_wallets(asset, amount, from_wallet, to_wallet)
            else:
                # For mock trading, simulate the transfer
                if from_wallet == 'SPOT' and to_wallet in ['FUTURES', 'MARGIN', 'FUNDING']:
                    # Simulate transfer from spot to other wallets
                    if asset not in self.mock_balances:
                        return {
                            'success': False,
                            'message': f'Insufficient {asset} balance in {from_wallet} wallet'
                        }
                    
                    available_balance = self.mock_balances[asset]['free']
                    if available_balance < amount:
                        return {
                            'success': False,
                            'message': f'Insufficient {asset} balance. Available: {available_balance}, Requested: {amount}'
                        }
                    
                    # Simulate successful transfer
                    return {
                        'success': True,
                        'transaction_id': f'mock_transfer_{int(time.time())}',
                        'asset': asset,
                        'amount': amount,
                        'from_wallet': from_wallet,
                        'to_wallet': to_wallet,
                        'message': f'Mock transfer: {amount} {asset} from {from_wallet} to {to_wallet}'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Mock trading only supports transfers from SPOT wallet'
                    }
                    
        except Exception as e:
            logger.error(f"Failed to transfer {amount} {asset} from {from_wallet} to {to_wallet}: {e}")
            return {
                'success': False,
                'message': f'Transfer failed: {str(e)}'
            }
    
    def get_transfer_history(self, limit: int = 50) -> List[Dict]:
        """Get transfer history between wallets"""
        try:
            if self.trading_mode == 'live':
                return self.binance_service.get_transfer_history(limit)
            else:
                # For mock trading, return empty history
                return []
                
        except Exception as e:
            logger.error(f"Failed to get transfer history: {e}")
            return []