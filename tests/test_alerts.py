"""Tests for read-only VANES alerts."""

import unittest

from vanes.alerts import AlertEngine


class AlertEngineTests(unittest.TestCase):
    """Validate transition-based alerts."""

    def test_first_state_is_silent(self):
        engine = AlertEngine()
        self.assertEqual(engine.evaluate("WAIT", 0.0, "WAITING", True), [])

    def test_direction_change_alerts(self):
        engine = AlertEngine()
        engine.evaluate("WAIT", 0.0, "WAITING", True)
        alerts = engine.evaluate("BUY", 0.8, "PASS", False)
        self.assertEqual(
            [alert.kind for alert in alerts],
            ["signal", "risk", "data"],
        )
        self.assertIn("BUY", alerts[0].message)

    def test_unchanged_state_is_silent(self):
        engine = AlertEngine()
        engine.evaluate("WAIT", 0.0, "WAITING", True)
        self.assertEqual(engine.evaluate("WAIT", 0.0, "WAITING", True), [])


if __name__ == "__main__":
    unittest.main()
