"""
Technical indicators for crypto trading analysis
"""
import math
from typing import List, Dict

class TechnicalIndicators:
    """Collection of technical analysis indicators"""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50  # Neutral RSI if not enough data
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Calculate signal line (EMA of MACD)
        # For simplicity, we'll use a simplified approach
        signal_line = macd_line * 0.8  # Approximation
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_vwap(candles: List[Dict]) -> float:
        """Calculate Volume Weighted Average Price"""
        if not candles:
            return 0
        
        total_volume = 0
        volume_price_sum = 0
        
        for candle in candles:
            volume = candle.get('volume', 0)
            typical_price = (candle.get('high', 0) + candle.get('low', 0) + candle.get('close', 0)) / 3
            
            total_volume += volume
            volume_price_sum += volume * typical_price
        
        return volume_price_sum / total_volume if total_volume > 0 else 0
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int = 20) -> float:
        """Calculate price volatility (standard deviation)"""
        if len(prices) < period:
            return 0
        
        recent_prices = prices[-period:]
        mean_price = sum(recent_prices) / len(recent_prices)
        
        squared_diff_sum = sum((price - mean_price) ** 2 for price in recent_prices)
        variance = squared_diff_sum / len(recent_prices)
        
        return math.sqrt(variance)
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0}
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / len(recent_prices)
        volatility = TechnicalIndicators.calculate_volatility(recent_prices, period)
        
        return {
            'upper': sma + (std_dev * volatility),
            'middle': sma,
            'lower': sma - (std_dev * volatility)
        }
    
    @staticmethod
    def calculate_stochastic(candles: List[Dict], k_period: int = 14, d_period: int = 3) -> Dict:
        """Calculate Stochastic Oscillator"""
        if len(candles) < k_period:
            return {'k': 50, 'd': 50}
        
        recent_candles = candles[-k_period:]
        
        # Calculate %K
        highest_high = max(candle.get('high', 0) for candle in recent_candles)
        lowest_low = min(candle.get('low', 0) for candle in recent_candles)
        current_close = recent_candles[-1].get('close', 0)
        
        if highest_high == lowest_low:
            k_percent = 50
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Calculate %D (SMA of %K)
        d_percent = k_percent  # Simplified for now
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def calculate_atr(candles: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(candles) < period + 1:
            return 0
        
        true_ranges = []
        
        for i in range(1, len(candles)):
            high = candles[i].get('high', 0)
            low = candles[i].get('low', 0)
            prev_close = candles[i-1].get('close', 0)
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_range = max(tr1, tr2, tr3)
            true_ranges.append(true_range)
        
        if len(true_ranges) < period:
            return 0
        
        return sum(true_ranges[-period:]) / period 