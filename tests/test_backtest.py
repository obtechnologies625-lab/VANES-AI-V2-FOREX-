"""Tests for deterministic historical replay."""

import unittest

from vanes.backtest import BacktestConfig, run_backtest
from vanes.market import Candle
from vanes.signals import Direction, Guidance


class FixedBuyStrategy:
    """Emit a BUY after enough history for a controlled replay test."""

    class Config:
        atr_period = 2

    config = Config()

    def evaluate(self, candles, spread_points=None):
        """Return a fixed BUY signal once history exists."""
        del spread_points
        if len(candles) < 3:
            return Guidance(Direction.WAIT, 0.0, "history")
        return Guidance(Direction.BUY, 0.9, "test")


class BacktestTests(unittest.TestCase):
    """Validate entries, exits, and report metrics."""

    def candles(self):
        values = [
            (1.00, 1.02, 0.99, 1.01),
            (1.01, 1.03, 1.00, 1.02),
            (1.02, 1.06, 1.01, 1.05),
            (1.05, 1.08, 1.04, 1.07),
            (1.07, 1.10, 1.06, 1.09),
            (1.09, 1.11, 1.08, 1.10),
        ]
        return [
            Candle(index, open_, high, low, close, 100)
            for index, (open_, high, low, close) in enumerate(values)
        ]

    def test_target_trade_updates_report(self):
        report = run_backtest(
            self.candles(),
            strategy=FixedBuyStrategy(),
            config=BacktestConfig(
                starting_balance=1000,
                risk_percent=1,
                stop_atr=1,
                reward_ratio=1,
                value_per_price_unit=1,
                max_trades=1,
            ),
        )
        self.assertEqual(report.trade_count, 1)
        self.assertEqual(report.wins, 1)
        self.assertGreater(report.net_pnl, 0)
        self.assertEqual(report.trades[0].reason, "TARGET")

    def test_empty_history_is_safe(self):
        report = run_backtest([], config=BacktestConfig(starting_balance=500))
        self.assertEqual(report.ending_balance, 500)
        self.assertEqual(report.trade_count, 0)


if __name__ == "__main__":
    unittest.main()
