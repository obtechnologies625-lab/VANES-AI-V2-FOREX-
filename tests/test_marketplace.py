"""Tests for the strategy marketplace store."""

import os
import tempfile
import unittest

from vanes.marketplace import MarketplaceStore


class MarketplaceTests(unittest.TestCase):
    """Validate seller registration and strategy listing rules."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.store = MarketplaceStore(os.path.join(self.directory, "mp.json"))

    def _seller(self):
        ok, _, seller = self.store.register_seller(
            "pipmaster", "Jane Doe", "jane@example.com"
        )
        self.assertTrue(ok)
        return seller

    def test_register_seller(self):
        seller = self._seller()
        self.assertTrue(seller.seller_id.startswith("sel-"))
        self.assertEqual(len(self.store.list_sellers()), 1)

    def test_rejects_bad_handle(self):
        ok, _, seller = self.store.register_seller("x", "Jane", "j@e.com")
        self.assertFalse(ok)
        self.assertIsNone(seller)

    def test_rejects_bad_email(self):
        ok, _, seller = self.store.register_seller("pipmaster", "Jane", "nope")
        self.assertFalse(ok)
        self.assertIsNone(seller)

    def test_rejects_duplicate_handle(self):
        self._seller()
        ok, _, _ = self.store.register_seller("pipmaster", "Other", "o@e.com")
        self.assertFalse(ok)

    def test_submit_requires_known_seller(self):
        ok, _, strategy = self.store.submit_strategy(
            "sel-nope", "Title here", "a sufficiently long description", 10
        )
        self.assertFalse(ok)
        self.assertIsNone(strategy)

    def test_submit_and_list(self):
        seller = self._seller()
        ok, _, strategy = self.store.submit_strategy(
            seller.seller_id,
            "London Breakout",
            "Trades the London open range breakout on M15.",
            99,
        )
        self.assertTrue(ok)
        self.assertEqual(strategy.payment_mode, "contact")
        listings = self.store.list_strategies()
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0]["title"], "London Breakout")
        self.assertEqual(listings[0]["price"], 99.0)

    def test_rejects_negative_price(self):
        seller = self._seller()
        ok, _, _ = self.store.submit_strategy(
            seller.seller_id, "Title", "long enough description", -5
        )
        self.assertFalse(ok)

    def test_rejects_short_description(self):
        seller = self._seller()
        ok, _, _ = self.store.submit_strategy(
            seller.seller_id, "Title", "too short", 5
        )
        self.assertFalse(ok)

    def test_persists_across_reload(self):
        seller = self._seller()
        self.store.submit_strategy(
            seller.seller_id, "Title", "long enough description", 5
        )
        reloaded = MarketplaceStore(str(self.store.path))
        self.assertEqual(len(reloaded.list_sellers()), 1)
        self.assertEqual(len(reloaded.list_strategies()), 1)


if __name__ == "__main__":
    unittest.main()
