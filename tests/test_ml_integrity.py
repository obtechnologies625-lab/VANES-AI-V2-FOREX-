"""Tests for the ML-integrity, guardrail, and behavioral safety layers."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from datetime import datetime, timedelta
import os
import tempfile
import unittest

from vanes.behavior import BehaviorMonitor
from vanes.config import AppConfig
from vanes.execution import plan_order
from vanes.incubation import IncubationTracker
from vanes.market import Candle
from vanes.ml import REGIMES, RegimeClassifier, build_dataset
from vanes.risk import MAX_DAILY_LOSS_PERCENT, MAX_RISK_PERCENT, clamp_guardrails
from vanes.sentiment import SentimentFeed, score_text
from vanes.walkforward import walk_forward_validate


def _candles(count=200, drift=0.0008):
    candles = []
    price = 1.1000
    for index in range(count):
        price *= 1 + (drift if index % 3 else -drift / 2)
        high = price * 1.0006
        low = price * 0.9994
        candles.append(
            Candle(1_700_000_000 + index * 900, price, high, low, price, 100.0)
        )
    return candles


class GuardrailTests(unittest.TestCase):
    def test_config_clamps_excessive_risk(self):
        config = AppConfig(risk_percent=50.0, max_daily_loss_percent=99.0)
        self.assertEqual(config.risk_percent, MAX_RISK_PERCENT)
        self.assertEqual(config.max_daily_loss_percent, MAX_DAILY_LOSS_PERCENT)

    def test_env_cannot_exceed_guardrails(self):
        os.environ["VANES_RISK_PERCENT"] = "25"
        try:
            config = AppConfig.from_environment()
        finally:
            del os.environ["VANES_RISK_PERCENT"]
        self.assertLessEqual(config.risk_percent, MAX_RISK_PERCENT)

    def test_clamp_keeps_valid_values(self):
        self.assertEqual(clamp_guardrails(1.0, 3.0), (1.0, 3.0))


class MLTests(unittest.TestCase):
    def test_dataset_and_classifier(self):
        candles = _candles()
        features, labels = build_dataset(candles)
        self.assertGreater(len(features), 20)
        self.assertTrue(all(label in (0, 1, 2) for label in labels))
        model = RegimeClassifier(epochs=20)
        model.fit(features, labels)
        probs = model.predict_proba(features[0])
        self.assertAlmostEqual(sum(probs), 1.0, places=5)
        self.assertIn(model.predict(features[0]), REGIMES)


class WalkForwardTests(unittest.TestCase):
    def test_walk_forward_produces_oos_folds(self):
        report = walk_forward_validate(_candles(300), train_window=120, test_window=40, step=40)
        self.assertGreaterEqual(report.fold_count, 1)
        self.assertTrue(0.0 <= report.oos_accuracy <= 1.0)
        self.assertIsInstance(report.edge_survives, bool)

    def test_insufficient_data_yields_empty_report(self):
        report = walk_forward_validate(_candles(50))
        self.assertEqual(report.fold_count, 0)
        self.assertFalse(report.edge_survives)


class IncubationTests(unittest.TestCase):
    def test_incubation_gates_live_until_elapsed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "inc.json")
            tracker = IncubationTracker(path, required_days=30)
            tracker.touch()
            status = tracker.status()
            self.assertEqual(status.days_elapsed, 0)
            self.assertFalse(tracker.live_allowed())
            self.assertEqual(status.sessions, 1)

            unlocked = IncubationTracker(path, required_days=0)
            self.assertTrue(unlocked.live_allowed())


class SentimentTests(unittest.TestCase):
    def test_polarity_and_negation(self):
        self.assertGreater(score_text("profits surge and rally"), 0)
        self.assertLess(score_text("crash plunge and losses"), 0)
        self.assertLess(score_text("not bullish, no rally"), 0)
        self.assertEqual(score_text(""), 0.0)

    def test_feed_aggregate(self):
        feed = SentimentFeed()
        feed.ingest("strong rally and record profits")
        feed.ingest("surge gains")
        self.assertEqual(feed.label, "BULLISH")
        self.assertEqual(feed.snapshot()["samples"], 2)


class BehaviorTests(unittest.TestCase):
    def test_overtrading_flag(self):
        monitor = BehaviorMonitor(max_trades_per_day=3)
        for _ in range(4):
            monitor.record_open()
        report = monitor.report()
        self.assertTrue(report.overtrading)
        self.assertGreaterEqual(report.tilt_score, 35)

    def test_revenge_trading_and_journal_prompt(self):
        now = datetime.now()
        monitor = BehaviorMonitor()
        monitor.record_close(-150.0, when=now)
        monitor.record_open(when=now + timedelta(minutes=5))
        report = monitor.report(now=now + timedelta(minutes=6))
        self.assertTrue(report.revenge_trading)
        self.assertTrue(report.journal_prompt)


class ExecutionTests(unittest.TestCase):
    def test_splits_large_order_within_broker_limits(self):
        plan = plan_order(
            size=0.30, volume_min=0.01, volume_max=0.10, volume_step=0.01,
            spread_points=5.0, slippage_budget_points=25.0,
        )
        self.assertFalse(plan.deferred)
        self.assertGreater(len(plan.slices), 1)
        self.assertTrue(all(0.01 <= s <= 0.10 for s in plan.slices))
        self.assertAlmostEqual(plan.total_volume, 0.30, places=6)

    def test_defers_when_spread_exceeds_budget(self):
        plan = plan_order(
            size=0.10, volume_min=0.01, volume_max=0.10, volume_step=0.01,
            spread_points=40.0, slippage_budget_points=25.0,
        )
        self.assertTrue(plan.deferred)
        self.assertEqual(plan.slices, ())

    def test_defers_below_minimum_volume(self):
        plan = plan_order(
            size=0.001, volume_min=0.01, volume_max=0.10, volume_step=0.01,
            spread_points=5.0, slippage_budget_points=25.0,
        )
        self.assertTrue(plan.deferred)


if __name__ == "__main__":
    unittest.main()
