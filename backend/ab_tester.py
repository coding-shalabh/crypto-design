import asyncio
import logging
from typing import Dict, List

from backtester import Backtester

logger = logging.getLogger(__name__)

class ABTester:
    """Framework for running A/B tests on different bot configurations."""

    def __init__(self, historical_candles: List[Dict]):
        self.historical_candles = historical_candles
        self.results = {}

    async def run_ab_test(self, symbol: str, configurations: Dict[str, Dict]) -> Dict:
        """Runs A/B tests for given configurations and returns their performance metrics.

        Args:
            symbol (str): The trading symbol (e.g., "BTC/USDT").
            configurations (Dict[str, Dict]): A dictionary where keys are configuration names
                                              and values are bot configuration dictionaries.

        Returns:
            Dict: A dictionary containing the backtest results for each configuration.
        """
        logger.info(f"Starting A/B test for {symbol} with {len(configurations)} configurations.")

        for config_name, bot_config in configurations.items():
            logger.info(f"Running backtest for configuration: {config_name}")
            backtester = Backtester(bot_config)
            metrics = await backtester.run_backtest(symbol, self.historical_candles)
            self.results[config_name] = metrics
            logger.info(f"Finished backtest for {config_name}. Metrics: {metrics}")
        
        logger.info("A/B test complete.")
        return self.results

    def get_best_config(self, metric: str = 'total_profit_loss_usdt') -> str:
        """Returns the name of the configuration with the best performance for a given metric."""
        if not self.results:
            return "No results available."

        best_config = None
        best_value = -float('inf')

        for config_name, metrics in self.results.items():
            if metric in metrics and metrics[metric] > best_value:
                best_value = metrics[metric]
                best_config = config_name
        
        return best_config

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Dummy historical candles (same as in backtester.py example)
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

    # Define different bot configurations for A/B testing
    configurations = {
        'Config_A_Conservative': {
            'ai_confidence_threshold': 0.70,
            'trade_amount_usdt': 100,
            'take_profit_percent': 2.5,
            'stop_loss_percent': -1.0,
            'initial_balance': 10000.0,
            'trailing_stop_percent': 0.3
        },
        'Config_B_Aggressive': {
            'ai_confidence_threshold': 0.60,
            'trade_amount_usdt': 200,
            'take_profit_percent': 1.5,
            'stop_loss_percent': -2.0,
            'initial_balance': 10000.0,
            'trailing_stop_percent': 0.7
        },
        'Config_C_Balanced': {
            'ai_confidence_threshold': 0.65,
            'trade_amount_usdt': 150,
            'take_profit_percent': 2.0,
            'stop_loss_percent': -1.5,
            'initial_balance': 10000.0,
            'trailing_stop_percent': 0.5
        }
    }

    ab_tester = ABTester(dummy_candles)
    results = asyncio.run(ab_tester.run_ab_test("BTC/USDT", configurations))

    print("\n--- A/B Test Results ---")
    for config_name, metrics in results.items():
        print(f"\nConfiguration: {config_name}")
        for key, value in metrics.items():
            print(f"  {key}: {value:.2f}")

    best_config_profit = ab_tester.get_best_config(metric='total_profit_loss_usdt')
    print(f"\nBest configuration by total profit: {best_config_profit}")

    best_config_win_rate = ab_tester.get_best_config(metric='win_rate')
    print(f"Best configuration by win rate: {best_config_win_rate}")
