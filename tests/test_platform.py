"""Tests for the read-only MetaTrader adapter behavior."""

import unittest
from unittest.mock import Mock

from vanes.platform import MT5Adapter


class PlatformTests(unittest.TestCase):
    """Validate MT5 adapter behavior without requiring a live terminal."""

    def test_invalid_timeframe_returns_no_candles(self):
        adapter = MT5Adapter()
        adapter._mt5 = Mock()
        adapter._mt5.symbol_select.return_value = True
        self.assertEqual(adapter.candles("EURUSD", "BAD", 10), [])

    def test_point_size_comes_from_symbol_info(self):
        adapter = MT5Adapter()
        adapter._mt5 = Mock()
        adapter._mt5.symbol_select.return_value = True
        adapter._mt5.symbol_info.return_value = Mock(point=0.001)
        self.assertEqual(adapter.point_size("USDJPY"), 0.001)

    def test_snapshot_rejects_invalid_quote(self):
        adapter = MT5Adapter()
        adapter._mt5 = Mock()
        adapter._mt5.symbol_select.return_value = True
        adapter._mt5.symbol_info_tick.return_value = Mock(bid=0, ask=0)
        self.assertIsNone(adapter.snapshot("EURUSD").bid)

    def test_symbol_spec_comes_from_mt5(self):
        adapter = MT5Adapter()
        adapter._mt5 = Mock()
        adapter._mt5.symbol_select.return_value = True
        adapter._mt5.symbol_info.return_value = Mock(
            point=0.00001, digits=5, trade_tick_size=0.00001,
            trade_tick_value=1.0, volume_min=0.01, volume_max=100.0,
            volume_step=0.01,
        )
        spec = adapter.symbol_spec("EURUSD")
        self.assertEqual(spec.tick_size, 0.00001)
        self.assertEqual(spec.volume_step, 0.01)

    def test_ticks_read_bid_ask_in_time_order(self):
        adapter = MT5Adapter()
        adapter._mt5 = Mock()
        adapter._mt5.symbol_select.return_value = True
        adapter._mt5.COPY_TICKS_ALL = 2
        adapter._mt5.copy_ticks_range.return_value = [
            {"time_msc": 2000, "bid": 1.1010, "ask": 1.1012, "last": 1.1011, "volume": 2},
            {"time_msc": 1000, "bid": 1.1000, "ask": 1.1002, "last": 1.1001, "volume": 1},
        ]
        ticks = adapter.ticks("EURUSD", 0, 10)
        self.assertEqual([tick.time_msc for tick in ticks], [1000, 2000])
        self.assertEqual(ticks[0].bid, 1.1000)
        self.assertEqual(ticks[0].ask, 1.1002)

    def test_missing_mt5_uses_safe_point_fallback(self):
        adapter = MT5Adapter()
        self.assertEqual(adapter.point_size("EURUSD"), 0.00001)


if __name__ == "__main__":
    unittest.main()
