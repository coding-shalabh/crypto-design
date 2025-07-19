import logging
from typing import List, Dict
from datetime import datetime, timedelta

from confidence_score_calculator import ConfidenceScoreCalculator
from technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

class Backtester:
    """Simulates trading bot performance on historical data."""

    def __init__(self, bot_config: Dict):
        self.bot_config = bot_config
        self.confidence_calculator = ConfidenceScoreCalculator()
        self.technical_indicators = TechnicalIndicators()
        self.trade_history = []
        self.initial_balance = bot_config.get('initial_balance', 10000.0)
        self.current_balance = self.initial_balance
        self.active_positions = {}

    def _should_override_hold(self, action: str, confidence: float) -> bool:
        return action == 'HOLD' and confidence > 0.85

    def _get_override_action(self, confidence: float) -> str:
        # This is a simple example. A more sophisticated implementation would
        # analyze the components of the confidence score to determine the
        # direction of the trade.
        return 'BUY' if confidence > 0.5 else 'SELL'

    async def run_backtest(self, symbol: str, historical_candles: List[Dict]) -> Dict:
        """Runs the backtest simulation."""
        logger.info(f"Starting backtest for {symbol} with {len(historical_candles)} candles.")

        for i in range(len(historical_candles)):
            current_candle = historical_candles[i]
            # Ensure we have enough data for indicator calculations
            if i < max(14, 26, 50, 200): # Max period for EMAs, RSI, MACD, etc.
                continue

            # Extract prices for confidence score calculation
            prices = [c['close'] for c in historical_candles[:i+1]]
            candles_slice = historical_candles[:i+1]

            # Calculate confidence score
            confidence_score = self.confidence_calculator.calculate_confidence(symbol, prices, candles_slice)

            # Simulate trade decision based on confidence score
            action = 'HOLD'
            if confidence_score >= self.bot_config['ai_confidence_threshold']:
                # For simplicity, let's assume if confidence is high, we look for a BUY signal
                # and if confidence is very high, we can override a HOLD to BUY.
                # In a real scenario, you'd determine BUY/SELL based on other factors
                # like trend, momentum, etc., which would be part of the confidence_score_calculator
                # or a separate analysis step.
                if confidence_score > 0.75: # Arbitrary threshold for a strong BUY signal
                    action = 'BUY'
                elif confidence_score < 0.25: # Arbitrary threshold for a strong SELL signal
                    action = 'SELL'

            # Apply override logic from TradingBot
            if self._should_override_hold(action, confidence_score):
                action = self._get_override_action(confidence_score)

            # Trade execution logic
            if action == 'BUY':
                if symbol not in self.active_positions:
                    trade_amount_usdt = self.bot_config['trade_amount_usdt']
                    if self.current_balance >= trade_amount_usdt:
                        quantity = trade_amount_usdt / current_candle['close']
                        self.active_positions[symbol] = {
                            'entry_price': current_candle['close'],
                            'quantity': quantity,
                            'direction': 'BUY',
                            'timestamp': current_candle['timestamp'],
                            'trailing_stop_price': 0.0 # Initialize trailing stop
                        }
                        self.current_balance -= trade_amount_usdt
                        self.trade_history.append({
                            'type': 'entry',
                            'symbol': symbol,
                            'price': current_candle['close'],
                            'quantity': quantity,
                            'confidence': confidence_score,
                            'direction': 'BUY',
                            'timestamp': current_candle['timestamp']
                        })
                        logger.info(f"Backtest: Entered BUY position for {symbol} at {current_candle['close']}. Confidence: {confidence_score:.2f}")
                    else:
                        logger.warning(f"Backtest: Insufficient balance to open BUY position for {symbol}.")
            elif action == 'SELL':
                if symbol not in self.active_positions:
                    trade_amount_usdt = self.bot_config['trade_amount_usdt']
                    if self.current_balance >= trade_amount_usdt: # Assuming shorting also requires collateral
                        quantity = trade_amount_usdt / current_candle['close']
                        self.active_positions[symbol] = {
                            'entry_price': current_candle['close'],
                            'quantity': quantity,
                            'direction': 'SELL',
                            'timestamp': current_candle['timestamp'],
                            'trailing_stop_price': 0.0 # Initialize trailing stop
                        }
                        self.current_balance -= trade_amount_usdt # Reduce balance for short collateral
                        self.trade_history.append({
                            'type': 'entry',
                            'symbol': symbol,
                            'price': current_candle['close'],
                            'quantity': quantity,
                            'confidence': confidence_score,
                            'direction': 'SELL',
                            'timestamp': current_candle['timestamp']
                        })
                        logger.info(f"Backtest: Entered SELL position for {symbol} at {current_candle['close']}. Confidence: {confidence_score:.2f}")
                    else:
                        logger.warning(f"Backtest: Insufficient balance to open SELL position for {symbol}.")

            # Simulate exit conditions
            if symbol in self.active_positions:
                position = self.active_positions[symbol]
                entry_price = position['entry_price']
                direction = position['direction']
                
                pnl_percent = 0.0
                if direction == 'BUY':
                    pnl_percent = ((current_candle['close'] - entry_price) / entry_price) * 100
                else: # SELL
                    pnl_percent = ((entry_price - current_candle['close']) / entry_price) * 100

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
                trailing_stop_percent = self.bot_config.get('trailing_stop_percent', 0.5)
                if direction == 'BUY':
                    # Update trailing stop if price moves favorably
                    current_trailing_stop = current_candle['close'] * (1 - trailing_stop_percent / 100)
                    if current_trailing_stop > position['trailing_stop_price']:
                        position['trailing_stop_price'] = current_trailing_stop
                    
                    if current_candle['close'] <= position['trailing_stop_price'] and position['trailing_stop_price'] != 0.0:
                        should_exit = True
                        exit_reason = f"Trailing stop hit at {position['trailing_stop_price']:.2f}"
                else: # SELL
                    current_trailing_stop = current_candle['close'] * (1 + trailing_stop_percent / 100)
                    if current_trailing_stop < position['trailing_stop_price'] or position['trailing_stop_price'] == 0.0:
                        position['trailing_stop_price'] = current_trailing_stop

                    if current_candle['close'] >= position['trailing_stop_price'] and position['trailing_stop_price'] != 0.0:
                        should_exit = True
                        exit_reason = f"Trailing stop hit at {position['trailing_stop_price']:.2f}"

                if should_exit:
                    profit_loss_usdt = 0.0
                    if direction == 'BUY':
                        profit_loss_usdt = (current_candle['close'] - entry_price) * position['quantity']
                        self.current_balance += (position['quantity'] * current_candle['close'])
                    else: # SELL
                        profit_loss_usdt = (entry_price - current_candle['close']) * position['quantity']
                        self.current_balance += (position['quantity'] * current_candle['close'])

                    self.trade_history.append({
                        'type': 'exit',
                        'symbol': symbol,
                        'price': current_candle['close'],
                        'quantity': position['quantity'],
                        'profit_loss_usdt': profit_loss_usdt,
                        'pnl_percent': pnl_percent,
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_reason': exit_reason,
                        'timestamp': current_candle['timestamp']
                    })
                    del self.active_positions[symbol]
                    logger.info(f"Backtest: Exited {direction} position for {symbol} at {current_candle['close']}. P&L: {pnl_percent:.2f}%. Reason: {exit_reason}")

        # Calculate final metrics
        metrics = self._calculate_metrics()
        logger.info("Backtest complete.")
        return metrics

    def _calculate_metrics(self) -> Dict:
        """Calculates performance metrics from the trade history."""
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        total_profit_loss = 0.0
        total_winning_profit = 0.0
        total_losing_loss = 0.0
        
        equity_curve = [self.initial_balance]
        
        for trade in self.trade_history:
            if trade['type'] == 'exit':
                total_trades += 1
                profit_loss = trade['profit_loss_usdt']
                total_profit_loss += profit_loss
                
                if profit_loss > 0:
                    winning_trades += 1
                    total_winning_profit += profit_loss
                else:
                    losing_trades += 1
                    total_losing_loss += abs(profit_loss)
                
                # Update equity curve
                equity_curve.append(equity_curve[-1] + profit_loss)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate Max Drawdown
        peak_equity = equity_curve[0]
        max_drawdown = 0.0
        for equity in equity_curve:
            if equity > peak_equity:
                peak_equity = equity
            drawdown = (peak_equity - equity) / peak_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        # Calculate Average Risk/Reward Ratio
        avg_win = (total_winning_profit / winning_trades) if winning_trades > 0 else 0
        avg_loss = (total_losing_loss / losing_trades) if losing_trades > 0 else 0
        avg_risk_reward_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0

        # Calculate Profit Factor
        profit_factor = (total_winning_profit / total_losing_loss) if total_losing_loss > 0 else 0

        # Placeholder for Sharpe Ratio (requires daily returns and risk-free rate)
        # For a simplified backtest, we can approximate daily returns from trade history
        # This is a very basic approximation and needs proper daily returns for accuracy.
        returns = [trade['profit_loss_usdt'] / self.initial_balance for trade in self.trade_history if trade['type'] == 'exit']
        sharpe_ratio = 0.0
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            std_dev_return = (sum([(r - avg_return)**2 for r in returns]) / (len(returns) - 1))**0.5
            # Assuming risk-free rate is 0 for simplicity
            if std_dev_return > 0:
                sharpe_ratio = avg_return / std_dev_return

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss_usdt': total_profit_loss,
            'final_balance': self.current_balance + sum(pos['quantity'] * historical_candles[-1]['close'] for pos in self.active_positions.values()), # Include value of open positions
            'max_drawdown': max_drawdown,
            'average_risk_reward_ratio': avg_risk_reward_ratio,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio
        }

if __name__ == '__main__':
    # Example Usage
    logging.basicConfig(level=logging.INFO)

    # Dummy bot config
    bot_config = {
        'ai_confidence_threshold': 0.65,
        'trade_amount_usdt': 100,
        'take_profit_percent': 2.0,
        'stop_loss_percent': -1.5,
        'initial_balance': 10000.0
    }

    # Generate dummy historical candles (e.g., 1000 candles)
    dummy_candles = []
    base_price = 100.0
    for i in range(1000):
        price = base_price + (i * 0.1) + (math.sin(i * 0.1) * 5) # Simple trend with sine wave
        dummy_candles.append({
            'timestamp': datetime.now().timestamp() - (1000 - i) * 60 * 30, # 30-min intervals
            'open': price - 0.5,
            'high': price + 1,
            'low': price - 1,
            'close': price,
            'volume': 1000 + (i * 10)
        })

    backtester = Backtester(bot_config)
    metrics = asyncio.run(backtester.run_backtest("BTC/USDT", dummy_candles))
    print("\nBacktest Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.2f}")