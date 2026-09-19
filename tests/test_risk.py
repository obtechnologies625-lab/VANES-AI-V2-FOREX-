"""Tests for VANES risk calculations."""

import unittest

from vanes.risk import (
    build_risk_plan,
    daily_loss_limit,
    position_size,
)


class RiskTests(unittest.TestCase):
    """Validate reference risk calculations."""

    def test_buy_plan(self):
        plan = build_risk_plan(1.1000, "BUY", 0.0010)
        self.assertIsNotNone(plan)
        self.assertAlmostEqual(plan.stop_loss, 1.0985)
        self.assertAlmostEqual(plan.take_profit, 1.1030)

    def test_position_size(self):
        self.assertAlmostEqual(position_size(10000, 1, 0.01), 10000)

    def test_daily_limit(self):
        self.assertEqual(daily_loss_limit(10000, 3), 300)


if __name__ == "__main__":
    unittest.main()
