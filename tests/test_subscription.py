"""Tests for subscription tiers and access helpers."""

import unittest

from vanes.subscription import (
    BASE_TIER,
    DEFAULT_TIER,
    LIVE_TRADING_TIER,
    TIERS,
    TIER_ORDER,
    tier_allows_live,
    tier_allows_marketplace_sales,
)


class TierTests(unittest.TestCase):
    """Validate the Beginner/Intermediate/Pro tier model."""

    def test_three_tiers_in_ascending_price_order(self):
        self.assertEqual(TIER_ORDER, ("BEGINNER", "INTERMEDIATE", "PRO"))
        self.assertEqual(list(TIERS), list(TIER_ORDER))
        prices = [TIERS[tier].price for tier in TIER_ORDER]
        self.assertEqual(prices, sorted(prices))
        self.assertLess(prices[0], prices[-1])

    def test_only_pro_allows_live_trading(self):
        self.assertTrue(tier_allows_live("PRO"))
        self.assertFalse(tier_allows_live("INTERMEDIATE"))
        self.assertFalse(tier_allows_live("BEGINNER"))

    def test_only_pro_sells_strategies(self):
        self.assertTrue(tier_allows_marketplace_sales("PRO"))
        self.assertFalse(tier_allows_marketplace_sales("INTERMEDIATE"))
        self.assertFalse(tier_allows_marketplace_sales("BEGINNER"))

    def test_tier_constants(self):
        self.assertEqual(LIVE_TRADING_TIER, "PRO")
        self.assertEqual(BASE_TIER, "BEGINNER")
        self.assertEqual(DEFAULT_TIER, "INTERMEDIATE")

    def test_beginner_is_fallback_for_unknown_tier(self):
        self.assertIs(TIERS[BASE_TIER], TIERS["BEGINNER"])


if __name__ == "__main__":
    unittest.main()
