"""Tests for strategy safeguards."""

import unittest

from vanes.market import Candle
from vanes.signals import Direction
from vanes.strategy import RuleBasedStrategy, StrategyConfig


class StrategyTests(unittest.TestCase):
    """Validate strategy safety filters."""

    def candles(self, count=50):
        return [
            Candle(i, 1.0 + i * 0.001, 1.001 + i * 0.001,
                   0.999 + i * 0.001, 1.0 + i * 0.001, 100)
            for i in range(count)
        ]

    def test_insufficient_history_waits(self):
        result = RuleBasedStrategy().evaluate(self.candles(10))
        self.assertEqual(result.direction, Direction.WAIT)

    def test_spread_filter_blocks(self):
        strategy = RuleBasedStrategy(
            StrategyConfig(max_spread_points=10)
        )
        result = strategy.evaluate(self.candles(), spread_points=11)
        self.assertEqual(result.direction, Direction.WAIT)
        self.assertIn("Spread", result.reason)


if __name__ == "__main__":
    unittest.main()
