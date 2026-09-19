"""Tests for VANES risk calculations."""

import unittest

from vanes.risk import (
    build_risk_plan,
    daily_loss_limit,
    position_size,
    position_size_from_tick,
    validate_trade_risk,
)


class RiskTests(unittest.TestCase):
    """Validate reference risk calculations."""

    def test_buy_plan(self):
        plan = build_risk_plan(1.1, "BUY", 0.01)
        self.assertAlmostEqual(plan.stop_loss, 1.085)
        self.assertAlmostEqual(plan.take_profit, 1.13)

    def test_daily_limit(self):
        self.assertEqual(daily_loss_limit(10000, 3), 300)

    def test_position_size(self):
        self.assertEqual(position_size(10000, 1, 0.02), 5000)

    def test_tick_based_position_size(self):
        size = position_size_from_tick(
            balance=10000,
            risk_percent=1,
            risk_distance=0.0020,
            tick_size=0.00001,
            tick_value=1.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
        )
        self.assertAlmostEqual(size, 0.5)

    def test_tick_based_size_respects_minimum(self):
        self.assertEqual(
            position_size_from_tick(100, 1, 1, 0.00001, 1, 0.01, 100, 0.01),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
