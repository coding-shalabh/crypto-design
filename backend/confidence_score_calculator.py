import math
from typing import List, Dict
from datetime import datetime

from technical_indicators import TechnicalIndicators
# from backend.news_analysis import NewsAnalysis # Placeholder for sentiment
# from backend.market_data import MarketData # Placeholder for market structure

class ConfidenceScoreCalculator:
    def __init__(self):
        self.technical_indicators = TechnicalIndicators()
        # self.news_analysis = NewsAnalysis() # Initialize if sentiment analysis is implemented
        # self.market_data = MarketData() # Initialize if market data analysis is implemented

    def calculate_technical_score(self, prices: List[float], candles: List[Dict]) -> float:
        """Calculates the technical analysis sub-score based on various indicators."""
        if not prices or not candles:
            return 0.0

        # Trend Following Indicators (35% weight)
        ema9 = self.technical_indicators.calculate_ema(prices, 9)
        ema21 = self.technical_indicators.calculate_ema(prices, 21)
        ema50 = self.technical_indicators.calculate_ema(prices, 50)
        
        # Calculate SMA 200 if we have enough data
        sma200 = 0.0
        if len(prices) >= 200:
            sma200 = sum(prices[-200:]) / 200

        macd_data = self.technical_indicators.calculate_macd(prices)
        macd_line = macd_data['macd']
        signal_line = macd_data['signal']
        histogram = macd_data['histogram']

        # Momentum Oscillators (35% weight)
        rsi = self.technical_indicators.calculate_rsi(prices)
        stochastic_data = self.technical_indicators.calculate_stochastic(candles)
        stoch_k = stochastic_data['k']
        stoch_d = stochastic_data['d']

        # Volatility Indicators (15% weight)
        bollinger_bands = self.technical_indicators.calculate_bollinger_bands(prices)
        atr = self.technical_indicators.calculate_atr(candles)

        # Volume Analysis (15% weight)
        vwap = self.technical_indicators.calculate_vwap(candles)

        # --- Enhanced scoring based on trading_confidence_research.md ---

        # 1. Trend Score (35% of technical score)
        trend_score = self._calculate_trend_score(prices, ema9, ema21, ema50, sma200, macd_line, signal_line, histogram)

        # 2. Momentum Score (35% of technical score)
        momentum_score = self._calculate_momentum_score(rsi, stoch_k, stoch_d, macd_line, signal_line)

        # 3. Volatility Score (15% of technical score)
        volatility_score = self._calculate_volatility_score(prices, bollinger_bands, atr)

        # 4. Volume Score (15% of technical score)
        volume_score = self._calculate_volume_score(prices, vwap, candles)

        # Combine with weights from research document
        technical_score = (
            trend_score * 0.35 +
            momentum_score * 0.35 +
            volatility_score * 0.15 +
            volume_score * 0.15
        )
        
        return min(max(technical_score, 0.0), 1.0)  # Ensure score is between 0 and 1

    def _calculate_trend_score(self, prices: List[float], ema9: float, ema21: float, ema50: float, 
                              sma200: float, macd_line: float, signal_line: float, histogram: float) -> float:
        """Calculate trend score based on multiple trend indicators"""
        score = 0.5  # Neutral starting point
        
        # EMA alignment (40% of trend score)
        ema_score = 0.0
        if prices[-1] > ema9 > ema21 > ema50:
            ema_score = 0.9  # Strong uptrend
        elif prices[-1] > ema9 and ema9 > ema21:
            ema_score = 0.7  # Moderate uptrend
        elif prices[-1] < ema9 < ema21 < ema50:
            ema_score = 0.1  # Strong downtrend
        elif prices[-1] < ema9 and ema9 < ema21:
            ema_score = 0.3  # Moderate downtrend
        else:
            ema_score = 0.5  # Mixed signals
        
        # MACD analysis (30% of trend score)
        macd_score = 0.5
        if macd_line > signal_line and histogram > 0:
            macd_score = 0.8  # Bullish MACD
        elif macd_line < signal_line and histogram < 0:
            macd_score = 0.2  # Bearish MACD
        elif macd_line > signal_line:
            macd_score = 0.6  # Weak bullish
        elif macd_line < signal_line:
            macd_score = 0.4  # Weak bearish
        
        # SMA 200 analysis (20% of trend score)
        sma_score = 0.5
        if sma200 > 0:
            if prices[-1] > sma200:
                sma_score = 0.7  # Above long-term average
            else:
                sma_score = 0.3  # Below long-term average
        
        # Price momentum (10% of trend score)
        momentum_score = 0.5
        if len(prices) >= 5:
            recent_change = (prices[-1] - prices[-5]) / prices[-5]
            if recent_change > 0.02:  # 2% gain
                momentum_score = 0.8
            elif recent_change < -0.02:  # 2% loss
                momentum_score = 0.2
            else:
                momentum_score = 0.5
        
        # Combine trend components
        trend_score = (
            ema_score * 0.40 +
            macd_score * 0.30 +
            sma_score * 0.20 +
            momentum_score * 0.10
        )
        
        return trend_score

    def _calculate_momentum_score(self, rsi: float, stoch_k: float, stoch_d: float, 
                                 macd_line: float, signal_line: float) -> float:
        """Calculate momentum score based on oscillators"""
        score = 0.5  # Neutral starting point
        
        # RSI analysis (40% of momentum score)
        rsi_score = 0.5
        if rsi < 30:
            rsi_score = 0.8  # Oversold, potential buy
        elif rsi < 40:
            rsi_score = 0.7  # Approaching oversold
        elif rsi > 70:
            rsi_score = 0.2  # Overbought, potential sell
        elif rsi > 60:
            rsi_score = 0.3  # Approaching overbought
        else:
            rsi_score = 0.5  # Neutral
        
        # Stochastic analysis (30% of momentum score)
        stoch_score = 0.5
        if stoch_k < 20 and stoch_d < 20:
            stoch_score = 0.8  # Oversold
        elif stoch_k > 80 and stoch_d > 80:
            stoch_score = 0.2  # Overbought
        elif stoch_k > stoch_d:
            stoch_score = 0.6  # Bullish crossover
        elif stoch_k < stoch_d:
            stoch_score = 0.4  # Bearish crossover
        
        # MACD momentum (30% of momentum score)
        macd_momentum = 0.5
        if macd_line > signal_line and macd_line > 0:
            macd_momentum = 0.8  # Strong bullish momentum
        elif macd_line < signal_line and macd_line < 0:
            macd_momentum = 0.2  # Strong bearish momentum
        elif macd_line > signal_line:
            macd_momentum = 0.6  # Weak bullish momentum
        elif macd_line < signal_line:
            macd_momentum = 0.4  # Weak bearish momentum
        
        # Combine momentum components
        momentum_score = (
            rsi_score * 0.40 +
            stoch_score * 0.30 +
            macd_momentum * 0.30
        )
        
        return momentum_score

    def _calculate_volatility_score(self, prices: List[float], bollinger_bands: Dict, atr: float) -> float:
        """Calculate volatility score based on volatility indicators"""
        score = 0.5  # Neutral starting point
        
        # Bollinger Bands analysis (50% of volatility score)
        bb_score = 0.5
        if 'upper' in bollinger_bands and 'lower' in bollinger_bands:
            current_price = prices[-1]
            upper_band = bollinger_bands['upper']
            lower_band = bollinger_bands['lower']
            
            # Calculate position within bands
            band_width = upper_band - lower_band
            if band_width > 0:
                position = (current_price - lower_band) / band_width
                
                if position > 0.8:
                    bb_score = 0.2  # Near upper band, potential reversal
                elif position < 0.2:
                    bb_score = 0.8  # Near lower band, potential reversal
                else:
                    bb_score = 0.5  # Middle of bands
        
        # ATR analysis (50% of volatility score)
        atr_score = 0.5
        if len(prices) > 0:
            avg_price = sum(prices[-20:]) / min(20, len(prices))
            atr_percent = atr / avg_price if avg_price > 0 else 0
            
            if atr_percent > 0.03:  # High volatility
                atr_score = 0.7  # Favorable for breakout strategies
            elif atr_percent < 0.01:  # Low volatility
                atr_score = 0.3  # Favorable for range-bound strategies
            else:
                atr_score = 0.5  # Normal volatility
        
        # Combine volatility components
        volatility_score = (
            bb_score * 0.50 +
            atr_score * 0.50
        )
        
        return volatility_score

    def _calculate_volume_score(self, prices: List[float], vwap: float, candles: List[Dict]) -> float:
        """Calculate volume score based on volume indicators"""
        score = 0.5  # Neutral starting point
        
        # VWAP analysis (60% of volume score)
        vwap_score = 0.5
        if vwap > 0:
            current_price = prices[-1]
            if current_price > vwap:
                vwap_score = 0.7  # Price above VWAP, bullish
            else:
                vwap_score = 0.3  # Price below VWAP, bearish
        
        # Volume trend analysis (40% of volume score)
        volume_score = 0.5
        if len(candles) >= 5:
            recent_volumes = [candle.get('volume', 0) for candle in candles[-5:]]
            avg_volume = sum(recent_volumes) / len(recent_volumes)
            current_volume = recent_volumes[-1]
            
            if current_volume > avg_volume * 1.5:
                volume_score = 0.8  # High volume, strong signal
            elif current_volume > avg_volume:
                volume_score = 0.6  # Above average volume
            elif current_volume < avg_volume * 0.5:
                volume_score = 0.3  # Low volume, weak signal
            else:
                volume_score = 0.5  # Normal volume
        
        # Combine volume components
        volume_score = (
            vwap_score * 0.60 +
            volume_score * 0.40
        )
        
        return volume_score

    def calculate_sentiment_score(self, symbol: str) -> float:
        """Calculates the market sentiment sub-score. (Placeholder)"""
        # This would involve calling a NewsAnalysis module or similar.
        # For now, return a neutral score.
        # news_sentiment = self.news_analysis.get_sentiment(symbol)
        # social_sentiment = ...
        # institutional_sentiment = ...
        return 0.5 # Placeholder

    def calculate_market_structure_score(self, symbol: str) -> float:
        """Calculates the market microstructure sub-score. (Placeholder)"""
        # This would involve analyzing order book, market depth, price action patterns.
        # For now, return a neutral score.
        # orderbook_score = self.market_data.get_order_book_imbalance(symbol)
        # price_action_score = ...
        return 0.5 # Placeholder

    def _detect_market_regime(self, candles: List[Dict]) -> Dict:
        """Detects current market regime based on volatility and time of day.
        News-heavy detection is a placeholder.
        """
        regime = {
            'volatility': 'normal', # 'high', 'low', 'normal'
            'news_heavy': False, # Placeholder
            'time_of_day': 'normal' # 'market_open', 'mid_day', 'market_close'
        }

        if not candles:
            return regime

        # Volatility Regime (using ATR)
        atr = self.technical_indicators.calculate_atr(candles)
        if atr > 0.01 * candles[-1]['close']: # Arbitrary threshold for high volatility
            regime['volatility'] = 'high'
        elif atr < 0.005 * candles[-1]['close']: # Arbitrary threshold for low volatility
            regime['volatility'] = 'low'

        # Time of Day Regime (assuming UTC timestamps in candles)
        last_candle_time = datetime.fromtimestamp(candles[-1]['timestamp'])
        hour = last_candle_time.hour

        if 0 <= hour < 2: # 00:00-02:00 UTC (Market Open example)
            regime['time_of_day'] = 'market_open'
        elif 12 <= hour < 16: # Mid-day example
            regime['time_of_day'] = 'mid_day'
        elif 20 <= hour < 24: # Market Close example
            regime['time_of_day'] = 'market_close'

        # News-Heavy Day (Placeholder - requires external data)
        # For a real implementation, this would involve checking a news sentiment API
        # or a calendar of economic events.
        # For now, we can simulate it or pass it as an argument if needed for backtesting.
        regime['news_heavy'] = False # Example: set to True for testing news impact

        return regime

    def combine_scores(self, scores: Dict[str, float], symbol: str, candles: List[Dict]) -> float:
        """Combines sub-scores with dynamic weighting based on market conditions."""
        technical_score = scores.get('technical', 0.0)
        sentiment_score = scores.get('sentiment', 0.0)
        structure_score = scores.get('structure', 0.0)

        market_regime = self._detect_market_regime(candles)

        # Base weights from trading_confidence_research.md
        technical_weight = 0.60
        sentiment_weight = 0.25
        structure_weight = 0.15

        # Dynamic weighting adjustments
        if market_regime['volatility'] == 'high':
            technical_weight -= 0.10 # Decrease trend indicator weights
            sentiment_weight += 0.15 # Increase sentiment weights
            # Volume indicator weights would be increased here, but they are part of technical_score
            # This highlights the need for more granular control within technical_score calculation
        elif market_regime['volatility'] == 'low':
            technical_weight += 0.15 # Increase trend indicator weights
            # Decrease momentum weights (part of technical_score)

        if market_regime['news_heavy']:
            sentiment_weight += 0.30
            technical_weight -= 0.15

        if market_regime['time_of_day'] == 'market_open':
            # Increase volume weights (part of technical_score)
            sentiment_weight += 0.15

        # Ensure weights sum to 1 (or handle normalization)
        total_weight = technical_weight + sentiment_weight + structure_weight
        if total_weight != 1.0:
            technical_weight /= total_weight
            sentiment_weight /= total_weight
            structure_weight /= total_weight

        confidence_score = (
            technical_score * technical_weight +
            sentiment_score * sentiment_weight +
            structure_score * structure_weight
        )
        return confidence_score

    def calculate_confidence(self, symbol: str, prices: List[float], candles: List[Dict]) -> float:
        """
        Main method to calculate the comprehensive trading bot confidence score.
        """
        technical_score = self.calculate_technical_score(prices, candles)
        sentiment_score = self.calculate_sentiment_score(symbol)
        market_structure_score = self.calculate_market_structure_score(symbol)

        scores = {
            'technical': technical_score,
            'sentiment': sentiment_score,
            'structure': market_structure_score
        }

        final_confidence_score = self.combine_scores(scores, symbol, candles)
        return final_confidence_score

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    calculator = ConfidenceScoreCalculator()

    # Dummy data for testing
    sample_prices = [i * 10 for i in range(1, 101)] # Prices from 10 to 1000
    sample_candles = [{'high': p + 5, 'low': p - 5, 'close': p, 'volume': 100} for p in sample_prices]

    # Calculate confidence score
    confidence = calculator.calculate_confidence("BTC/USDT", sample_prices, sample_candles)
    print(f"Calculated Confidence Score: {confidence:.2f}")

    # Test with insufficient data
    confidence_insufficient = calculator.calculate_confidence("BTC/USDT", [100, 101, 102], [{'high': 105, 'low': 95, 'close': 100, 'volume': 100}])
    print(f"Calculated Confidence Score (insufficient data): {confidence_insufficient:.2f}")
