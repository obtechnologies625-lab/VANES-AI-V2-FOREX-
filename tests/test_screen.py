"""Tests for the visual desktop observer."""

import unittest
from unittest.mock import patch

from vanes.screen import ScreenObserver, next_step


class ScreenObserverTests(unittest.TestCase):
    """Validate safe cross-platform visual context behavior."""

    def test_non_windows_observer_is_safe(self):
        with patch("vanes.screen.os.name", "posix"):
            context = ScreenObserver().observe()
        self.assertFalse(context.supported)
        self.assertFalse(context.mt5_active)

    def test_mt5_guidance_is_actionable(self):
        context = type(
            "Context",
            (),
            {"supported": True, "mt5_active": True, "summary": "MetaTrader 5"},
        )()
        self.assertIn("BUY setup", next_step(context, "BUY"))

    def test_non_mt5_guidance_points_to_mt5(self):
        context = type(
            "Context",
            (),
            {"supported": True, "mt5_active": False, "summary": "Browser"},
        )()
        self.assertIn("MetaTrader 5", next_step(context, "WAIT"))


if __name__ == "__main__":
    unittest.main()
