"""Tests for the paper-trading simulator."""

import unittest

from vanes.paper import PaperTrader


class PaperTests(unittest.TestCase):
    """Validate paper balance and loss-limit behavior."""

    def test_trade_updates_balance(self):
        trader = PaperTrader(10000, 300)
        trade = trader.open_trade("BUY", 1.0, 0.99, 1.02, 100, 1)
        self.assertIsNotNone(trade)
        self.assertEqual(trader.close_trade(trade, 1.01, 2), 1.0)
        self.assertEqual(trader.balance, 10001.0)

    def test_loss_limit_blocks_new_trade(self):
        trader = PaperTrader(10000, 100)
        first = trader.open_trade("BUY", 1.0, 0.9, 1.1, 1000, 1)
        self.assertIsNotNone(first)
        trader.close_trade(first, 0.8, 2)
        self.assertFalse(trader.can_open())


if __name__ == "__main__":
    unittest.main()
