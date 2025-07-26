import os
import time
import hashlib
import hmac
import requests
import json
from typing import Dict, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BinanceService:
    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.base_url = 'https://api.binance.com'
        self.futures_base_url = 'https://fapi.binance.com'
        
        # Wallet type mappings
        self.wallet_types = {
            'SPOT': 'Spot Wallet',
            'FUTURES': 'Futures Wallet', 
            'MARGIN': 'Cross Margin',
            'ISOLATED_MARGIN': 'Isolated Margin',
            'FUNDING': 'Funding Wallet',
            'OPTION': 'Options Wallet'
        }
        
        if not self.api_key or not self.api_secret:
            logger.warning("Binance API credentials not found in environment variables")
            
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for Binance API"""
        return hmac.new(
            self.api_secret.encode('utf-8'), 
            query_string.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint: str, params: Dict = None, method: str = 'GET', signed: bool = False) -> Dict:
        """Make authenticated request to Binance API"""
        if not self.api_key or not self.api_secret:
            raise Exception("Binance API credentials not configured")
            
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
            
        if signed:
            # Subtract 1000ms to account for potential server time difference
            params['timestamp'] = int(time.time() * 1000) - 1000
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                if error_data.get('code') == -1021:  # Timestamp error
                    logger.warning(f"Binance timestamp error, retrying with adjusted timestamp: {error_data}")
                    # Retry with more time adjustment
                    if signed:
                        params['timestamp'] = int(time.time() * 1000) - 2000
                        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                        params['signature'] = self._generate_signature(query_string)
                    
                    # Retry the request once
                    if method == 'GET':
                        response = requests.get(url, headers=headers, params=params, timeout=10)
                    elif method == 'POST':
                        response = requests.post(url, headers=headers, params=params, timeout=10)
                    elif method == 'DELETE':
                        response = requests.delete(url, headers=headers, params=params, timeout=10)
                    
                    response.raise_for_status()
                    return response.json()
                else:
                    logger.error(f"Binance API error: {error_data}")
                    raise Exception(f"Binance API request failed: {e}")
            else:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"HTTP request failed: {e}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_account_info(self) -> Dict:
        """Get account information including balances"""
        try:
            return self._make_request('/api/v3/account', signed=True)
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def get_balance(self, asset: str = 'USDT') -> Dict:
        """Get balance for specific asset"""
        try:
            account_info = self.get_account_info()
            balances = account_info.get('balances', [])
            
            for balance in balances:
                if balance['asset'] == asset:
                    return {
                        'asset': asset,
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    }
            
            return {'asset': asset, 'free': 0.0, 'locked': 0.0, 'total': 0.0}
        except Exception as e:
            logger.error(f"Failed to get balance for {asset}: {e}")
            raise
    
    def get_all_balances(self) -> List[Dict]:
        """Get all non-zero balances"""
        try:
            account_info = self.get_account_info()
            balances = []
            
            for balance in account_info.get('balances', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': total
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get all balances: {e}")
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get trading rules and info for a symbol"""
        try:
            exchange_info = self._make_request('/api/v3/exchangeInfo')
            symbols = exchange_info.get('symbols', [])
            
            for sym in symbols:
                if sym['symbol'] == symbol:
                    return sym
            
            raise Exception(f"Symbol {symbol} not found")
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            response = self._make_request('/api/v3/ticker/price', {'symbol': symbol})
            return float(response['price'])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                   price: float = None, time_in_force: str = 'GTC') -> Dict:
        """Place a trading order"""
        try:
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': order_type.upper(),
                'quantity': str(quantity)
            }
            
            if order_type.upper() in ['LIMIT', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT']:
                if price is None:
                    raise ValueError(f"Price is required for {order_type} orders")
                params['price'] = str(price)
                params['timeInForce'] = time_in_force
            
            return self._make_request('/api/v3/order', params, method='POST', signed=True)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an existing order"""
        try:
            params = {
                'symbol': symbol,
                'orderId': order_id
            }
            return self._make_request('/api/v3/order', params, method='DELETE', signed=True)
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders or for specific symbol"""
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            return self._make_request('/api/v3/openOrders', params, signed=True)
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    def get_order_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get order history for a symbol"""
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            return self._make_request('/api/v3/allOrders', params, signed=True)
        except Exception as e:
            logger.error(f"Failed to get order history for {symbol}: {e}")
            raise
    
    def get_trade_history(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get trade history for a symbol"""
        try:
            params = {
                'symbol': symbol,
                'limit': limit
            }
            return self._make_request('/api/v3/myTrades', params, signed=True)
        except Exception as e:
            logger.error(f"Failed to get trade history for {symbol}: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """Test API connectivity and credentials"""
        try:
            # Test general connectivity
            self._make_request('/api/v3/ping')
            
            # Test authenticated endpoint
            self.get_account_info()
            
            logger.info("Binance API connectivity test successful")
            return True
        except Exception as e:
            logger.error(f"Binance API connectivity test failed: {e}")
            return False
    
    def calculate_quantity(self, symbol: str, usdt_amount: float, price: float = None) -> float:
        """Calculate proper quantity based on USDT amount and symbol rules"""
        try:
            if price is None:
                price = self.get_current_price(symbol)
            
            symbol_info = self.get_symbol_info(symbol)
            
            # Get lot size filter
            lot_size_filter = None
            for filter_info in symbol_info.get('filters', []):
                if filter_info['filterType'] == 'LOT_SIZE':
                    lot_size_filter = filter_info
                    break
            
            if not lot_size_filter:
                raise Exception(f"LOT_SIZE filter not found for {symbol}")
            
            # Calculate base quantity
            quantity = usdt_amount / price
            
            # Apply step size rounding
            step_size = float(lot_size_filter['stepSize'])
            min_quantity = float(lot_size_filter['minQty'])
            max_quantity = float(lot_size_filter['maxQty'])
            
            # Round to step size
            quantity = round(quantity / step_size) * step_size
            
            # Ensure within bounds
            if quantity < min_quantity:
                raise Exception(f"Calculated quantity {quantity} is below minimum {min_quantity}")
            if quantity > max_quantity:
                raise Exception(f"Calculated quantity {quantity} is above maximum {max_quantity}")
            
            return quantity
        except Exception as e:
            logger.error(f"Failed to calculate quantity for {symbol}: {e}")
            raise
    
    def get_categorized_balances(self) -> Dict:
        """Get balances categorized by wallet type (Spot, Futures, etc.)"""
        try:
            categorized_balances = {}
            
            # Get Spot wallet balances
            spot_balances = self.get_spot_balances()
            categorized_balances['SPOT'] = {
                'name': self.wallet_types['SPOT'],
                'balances': spot_balances,
                'total_usdt': self._calculate_total_usdt_value(spot_balances)
            }
            
            # Get Futures wallet balances
            futures_balances = self.get_futures_balances()
            categorized_balances['FUTURES'] = {
                'name': self.wallet_types['FUTURES'],
                'balances': futures_balances,
                'total_usdt': self._calculate_total_usdt_value(futures_balances)
            }
            
            # Get Cross Margin balances
            margin_balances = self.get_margin_balances()
            categorized_balances['MARGIN'] = {
                'name': self.wallet_types['MARGIN'],
                'balances': margin_balances,
                'total_usdt': self._calculate_total_usdt_value(margin_balances)
            }
            
            # Get Funding wallet balances
            funding_balances = self.get_funding_balances()
            categorized_balances['FUNDING'] = {
                'name': self.wallet_types['FUNDING'],
                'balances': funding_balances,
                'total_usdt': self._calculate_total_usdt_value(funding_balances)
            }
            
            return categorized_balances
            
        except Exception as e:
            logger.error(f"Failed to get categorized balances: {e}")
            raise
    
    def get_spot_balances(self) -> List[Dict]:
        """Get Spot wallet balances"""
        try:
            account_info = self.get_account_info()
            balances = []
            
            for balance in account_info.get('balances', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': total,
                        'wallet_type': 'SPOT'
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get spot balances: {e}")
            raise
    
    def _make_futures_request(self, endpoint: str, params: Dict = None, method: str = 'GET', signed: bool = False) -> Dict:
        """Make authenticated request to Binance Futures API"""
        if not self.api_key or not self.api_secret:
            raise Exception("Binance API credentials not configured")
            
        url = f"{self.futures_base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
            
        if signed:
            # Subtract 1000ms to account for potential server time difference
            params['timestamp'] = int(time.time() * 1000) - 1000
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, params=params, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                if error_data.get('code') == -1021:  # Timestamp error
                    logger.warning(f"Binance Futures timestamp error, retrying with adjusted timestamp: {error_data}")
                    # Retry with more time adjustment
                    if signed:
                        params['timestamp'] = int(time.time() * 1000) - 2000
                        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                        params['signature'] = self._generate_signature(query_string)
                    
                    # Retry the request once
                    if method == 'GET':
                        response = requests.get(url, headers=headers, params=params, timeout=10)
                    elif method == 'POST':
                        response = requests.post(url, headers=headers, params=params, timeout=10)
                    elif method == 'DELETE':
                        response = requests.delete(url, headers=headers, params=params, timeout=10)
                    
                    response.raise_for_status()
                    return response.json()
                else:
                    logger.error(f"Binance Futures API error: {error_data}")
                    raise Exception(f"Binance Futures API request failed: {e}")
            else:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"HTTP request failed: {e}")
        except Exception as e:
            logger.error(f"Futures request failed: {e}")
            raise

    def get_futures_balances(self) -> List[Dict]:
        """Get Futures wallet balances"""
        try:
            futures_data = self._make_futures_request('/fapi/v2/balance', signed=True)
            balances = []
            
            for balance in futures_data:
                available = float(balance['availableBalance'])
                total_balance = float(balance['balance'])
                
                if total_balance > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': available,
                        'locked': total_balance - available,
                        'total': total_balance,
                        'wallet_type': 'FUTURES'
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get futures balances: {e}")
            raise
    
    def get_margin_balances(self) -> List[Dict]:
        """Get Cross Margin balances"""
        try:
            response = self._make_request('/sapi/v1/margin/account', signed=True)
            balances = []
            
            for balance in response.get('userAssets', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': total,
                        'wallet_type': 'MARGIN'
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get margin balances: {e}")
            return []  # Return empty list if margin not enabled
    
    def get_funding_balances(self) -> List[Dict]:
        """Get Funding wallet balances"""
        try:
            # Use POST method for funding wallet as per Binance API docs
            response = self._make_request('/sapi/v1/asset/get-funding-asset', {}, method='POST', signed=True)
            balances = []
            
            for balance in response:
                free = float(balance['free'])
                locked = float(balance['locked'])
                freeze = float(balance.get('freeze', 0))
                withdrawing = float(balance.get('withdrawing', 0))
                total = free + locked + freeze + withdrawing
                
                if total > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked + freeze + withdrawing,  # Combine locked amounts
                        'total': total,
                        'wallet_type': 'FUNDING'
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get funding balances: {e}")
            return []  # Return empty list if funding wallet not available
    
    def transfer_between_wallets(self, asset: str, amount: float, from_wallet: str, to_wallet: str) -> Dict:
        """Transfer balance between different wallet types"""
        try:
            # Map wallet types to Binance transfer types
            transfer_types = {
                ('SPOT', 'FUTURES'): 1,      # Main to USDM Futures
                ('FUTURES', 'SPOT'): 2,      # USDM Futures to Main
                ('SPOT', 'MARGIN'): 3,       # Main to Cross Margin
                ('MARGIN', 'SPOT'): 4,       # Cross Margin to Main
                ('SPOT', 'FUNDING'): 7,      # Main to Funding
                ('FUNDING', 'SPOT'): 8,      # Funding to Main
                ('FUTURES', 'MARGIN'): 5,    # USDM Futures to Cross Margin
                ('MARGIN', 'FUTURES'): 6,    # Cross Margin to USDM Futures
            }
            
            transfer_key = (from_wallet, to_wallet)
            if transfer_key not in transfer_types:
                raise Exception(f"Transfer from {from_wallet} to {to_wallet} is not supported")
            
            transfer_type = transfer_types[transfer_key]
            
            params = {
                'asset': asset,
                'amount': str(amount),
                'type': transfer_type
            }
            
            response = self._make_request('/sapi/v1/asset/transfer', params, method='POST', signed=True)
            
            if response.get('tranId'):
                return {
                    'success': True,
                    'transaction_id': response['tranId'],
                    'asset': asset,
                    'amount': amount,
                    'from_wallet': from_wallet,
                    'to_wallet': to_wallet,
                    'message': f'Successfully transferred {amount} {asset} from {self.wallet_types[from_wallet]} to {self.wallet_types[to_wallet]}'
                }
            else:
                return {
                    'success': False,
                    'message': 'Transfer failed - no transaction ID received'
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
            params = {
                'type': 'UNIVERSALTRANSFER',
                'size': limit
            }
            
            response = self._make_request('/sapi/v1/asset/transfer', params, signed=True)
            transfers = []
            
            for transfer in response.get('rows', []):
                transfers.append({
                    'transaction_id': transfer['tranId'],
                    'asset': transfer['asset'],
                    'amount': float(transfer['amount']),
                    'from_wallet': self._get_wallet_name_from_type(transfer['fromSymbol']),
                    'to_wallet': self._get_wallet_name_from_type(transfer['toSymbol']),
                    'timestamp': transfer['timestamp'],
                    'status': transfer['status']
                })
            
            return transfers
        except Exception as e:
            logger.error(f"Failed to get transfer history: {e}")
            return []
    
    def _calculate_total_usdt_value(self, balances: List[Dict]) -> float:
        """Calculate total USDT value of balances"""
        total_usdt = 0.0
        
        for balance in balances:
            asset = balance['asset']
            total_amount = balance['total']
            
            if asset == 'USDT':
                total_usdt += total_amount
            else:
                try:
                    # Get current price in USDT
                    symbol = f"{asset}USDT"
                    price = self.get_current_price(symbol)
                    total_usdt += total_amount * price
                except:
                    # If can't get price, skip this asset
                    continue
        
        return total_usdt
    
    def _get_wallet_name_from_type(self, wallet_symbol: str) -> str:
        """Convert Binance wallet symbol to our wallet type"""
        wallet_mapping = {
            'SPOT': 'SPOT',
            'FAPI': 'FUTURES',
            'MARGIN': 'MARGIN',
            'FUNDING': 'FUNDING'
        }
        return wallet_mapping.get(wallet_symbol, wallet_symbol)