"""Tests for market indicators."""

import unittest

from vanes.market import Candle, atr, ema, rsi, swing_levels


class MarketTests(unittest.TestCase):
    """Validate deterministic indicator calculations."""

    def candles(self, closes):
        return [
            Candle(i, price - 0.1, price + 0.2, price - 0.2, price, 100)
            for i, price in enumerate(closes)
        ]

    def test_ema_returns_same_length(self):
        values = ema([1, 2, 3, 4], 2)
        self.assertEqual(len(values), 4)
        self.assertAlmostEqual(values[-1], 3.5185185, places=5)

    def test_rsi_uptrend(self):
        self.assertEqual(rsi(list(range(1, 16)), 14), 100.0)

    def test_atr_and_levels(self):
        candles = self.candles([1, 2, 3, 4, 5])
        self.assertIsNotNone(atr(candles, 3))
        self.assertEqual(swing_levels(candles, 3), (2.8, 5.2))


if __name__ == "__main__":
    unittest.main()
