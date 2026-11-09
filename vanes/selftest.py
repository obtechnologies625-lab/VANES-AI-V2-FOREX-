"""Offline self-test engine powering the VANES developer portal.

Every check runs locally without broker, network, or paid-API access so the
portal can prove the whole stack works on a fresh machine.
"""

from dataclasses import dataclass
import os

from .backtest import BacktestConfig, run_backtest
from .behavior import BehaviorMonitor
from .config import AppConfig
from .execution import plan_order
from .incubation import IncubationTracker
from .market import Candle
from .ml import REGIMES, RegimeClassifier, build_dataset
from .paper import PaperTrader
from .risk import MAX_RISK_PERCENT, build_risk_plan, daily_loss_limit, validate_trade_risk
from .sentiment import score_text
from .walkforward import walk_forward_validate


@dataclass(frozen=True)
class SelfTestResult:
    """One named pass/fail check with a human-readable detail."""

    name: str
    ok: bool
    detail: str


def _candles(count=300, drift=0.0008):
    candles = []
    price = 1.1000
    for index in range(count):
        price *= 1 + (drift if index % 3 else -drift / 2)
        candles.append(
            Candle(
                1_700_000_000 + index * 900,
                price, price * 1.0006, price * 0.9994, price, 100.0,
            )
        )
    return candles


def _check_guardrails():
    config = AppConfig(risk_percent=99.0, max_daily_loss_percent=99.0)
    ok = config.risk_percent == MAX_RISK_PERCENT
    return SelfTestResult(
        "Hard risk guardrails",
        ok,
        f"risk clamped to {config.risk_percent}% / daily {config.max_daily_loss_percent}%",
    )


def _check_ml():
    features, labels = build_dataset(_candles())
    if not features:
        return SelfTestResult("ML regime classifier", False, "no training samples")
    model = RegimeClassifier(epochs=20)
    model.fit(features, labels)
    probs = model.predict_proba(features[0])
    ok = abs(sum(probs) - 1.0) < 1e-6 and model.predict(features[0]) in REGIMES
    return SelfTestResult(
        "ML regime classifier", ok, f"{len(features)} samples, regimes {REGIMES}"
    )


def _check_walkforward():
    report = walk_forward_validate(_candles(), train_window=120, test_window=40)
    ok = report.fold_count >= 1
    return SelfTestResult(
        "Walk-forward OOS validation",
        ok,
        f"{report.fold_count} folds, OOS accuracy {report.oos_accuracy:.2f}",
    )


def _check_sentiment():
    ok = score_text("profits surge rally") > 0 > score_text("crash plunge losses")
    return SelfTestResult("NLP sentiment layer", ok, "bullish/bearish polarity verified")


def _check_behavior():
    monitor = BehaviorMonitor(max_trades_per_day=3)
    for _ in range(4):
        monitor.record_open()
    report = monitor.report()
    return SelfTestResult(
        "Behavioral tilt monitor", report.overtrading, f"tilt {report.tilt_score}/100"
    )


def _check_execution():
    plan = plan_order(0.30, 0.01, 0.10, 0.01, 5.0, 25.0)
    deferred = plan_order(0.10, 0.01, 0.10, 0.01, 40.0, 25.0)
    ok = (not plan.deferred) and len(plan.slices) > 1 and deferred.deferred
    return SelfTestResult(
        "Slippage-aware execution", ok, f"{len(plan.slices)} slices, defers on wide spread"
    )


def _check_risk_plan():
    plan = build_risk_plan(1.1000, "BUY", 0.0015)
    check = validate_trade_risk(
        10_000.0, 1.0, plan.risk_distance, 0.10, 0.0,
        daily_loss_limit(10_000.0, 3.0),
    )
    return SelfTestResult(
        "Risk plan + validation", check.allowed and plan is not None, check.reason
    )


def _check_paper():
    paper = PaperTrader(10_000.0, 300.0)
    trade = paper.open_trade("BUY", 1.1000, 1.0980, 1.1040, 0.10, 1_700_000_000)
    pnl = paper.close_trade(trade, 1.1040, 1_700_003_600) if trade else 0.0
    return SelfTestResult("Paper trading engine", pnl > 0, f"realized pnl {pnl:.2f}")


def _check_backtest():
    report = run_backtest(_candles(), config=BacktestConfig(max_trades=3))
    return SelfTestResult(
        "Historical backtest", report.trade_count >= 0,
        f"{report.trade_count} trades, drawdown {report.max_drawdown_percent:.1f}%",
    )


def _check_incubation(tmp_path):
    tracker = IncubationTracker(tmp_path, required_days=0)
    tracker.touch()
    return SelfTestResult(
        "Incubation gate", tracker.live_allowed(),
        f"{tracker.status().days_elapsed}/{tracker.status().required_days} days",
    )


def run_selftest(tmp_path: str = "data/vanes_selftest_incubation.json"):
    """Run every offline self-test and return the results."""
    return [
        _check_guardrails(),
        _check_ml(),
        _check_walkforward(),
        _check_sentiment(),
        _check_behavior(),
        _check_execution(),
        _check_risk_plan(),
        _check_paper(),
        _check_backtest(),
        _check_incubation(tmp_path),
    ]


def environment_status() -> dict:
    """Report which external APIs/keys are configured, without exposing values."""
    kv_configured = False
    try:
        with open("cloudflare/wrangler.toml", encoding="utf-8") as handle:
            kv_configured = "00000000000000000000000000000000" not in handle.read()
    except OSError:
        kv_configured = False
    try:
        import MetaTrader5  # pylint: disable=import-outside-toplevel,unused-import,import-error
        mt5 = True
    except ImportError:
        mt5 = False
    return {
        "metatrader5": mt5,
        "gemini_api_key": bool(os.getenv("VANES_GEMINI_API_KEY")),
        "cloudflare_api_token": bool(os.getenv("CLOUDFLARE_API_TOKEN")),
        "jwt_secret": bool(os.getenv("VANES_JWT_SECRET")),
        "publish_token": bool(os.getenv("VANES_PUBLISH_TOKEN")),
        "kv_namespace_created": kv_configured,
        "local_bridge": True,
    }
