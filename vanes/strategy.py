"""Transparent indicator-based market guidance strategy."""

from dataclasses import dataclass

from .market import Candle, ema, rsi
from .signals import Direction, Guidance
from .structure import analyze_structure


@dataclass(frozen=True)
class StrategyConfig:  # pylint: disable=too-few-public-methods
    """Configure indicator, spread, and structure filters."""

    fast_ema: int = 9
    slow_ema: int = 21
    rsi_period: int = 14
    atr_period: int = 14
    min_confidence: float = 0.60
    max_spread_points: float = 25.0


class RuleBasedStrategy:  # pylint: disable=too-few-public-methods
    """Generate transparent, non-executing market guidance."""

    def __init__(self, config: StrategyConfig | None = None):
        """Create a strategy with optional configuration."""
        self.config = config or StrategyConfig()

    def evaluate(
        self,
        candles: list[Candle],
        spread_points: float | None = None,
        confirmation: list[Candle] | None = None,
    ) -> Guidance:
        """Evaluate EMA, RSI, structure, spread, and confirmation alignment."""
        minimum = max(
            self.config.slow_ema + 2,
            self.config.rsi_period + 2,
            self.config.atr_period + 2,
        )
        if len(candles) < minimum:
            return Guidance(Direction.WAIT, 0.0, "Collecting candle history")

        if (
            spread_points is not None
            and spread_points > self.config.max_spread_points
        ):
            return Guidance(Direction.WAIT, 0.0, "Spread filter blocked setup")

        closes = [c.close for c in candles]
        fast = ema(closes, self.config.fast_ema)[-1]
        slow = ema(closes, self.config.slow_ema)[-1]
        current_rsi = rsi(closes, self.config.rsi_period)
        structure = analyze_structure(candles)

        if current_rsi is None or structure is None:
            return Guidance(Direction.WAIT, 0.0, "Waiting for indicators")

        higher_trend = None
        if confirmation and len(confirmation) >= minimum:
            higher = analyze_structure(confirmation)
            higher_trend = higher.trend if higher else None

        if fast > slow and 50.0 < current_rsi < 70.0:
            if structure.trend != "UP" or (
                higher_trend is not None and higher_trend != "UP"
            ):
                return Guidance(
                    Direction.WAIT, 0.0, "Trend confirmation blocked BUY"
                )
            strength = (fast - slow) / max(slow, 1e-9) * 20.0
            confidence = min(0.95, 0.60 + min(strength, 0.25))
            if confidence < self.config.min_confidence:
                return Guidance(Direction.WAIT, confidence, "Low confidence")
            return Guidance(
                Direction.BUY,
                confidence,
                f"EMA trend UP; RSI {current_rsi:.1f}; structure confirmed",
            )

        if fast < slow and 30.0 < current_rsi < 50.0:
            if structure.trend != "DOWN" or (
                higher_trend is not None and higher_trend != "DOWN"
            ):
                return Guidance(
                    Direction.WAIT, 0.0, "Trend confirmation blocked SELL"
                )
            strength = (slow - fast) / max(slow, 1e-9) * 20.0
            confidence = min(0.95, 0.60 + min(strength, 0.25))
            if confidence < self.config.min_confidence:
                return Guidance(Direction.WAIT, confidence, "Low confidence")
            return Guidance(
                Direction.SELL,
                confidence,
                f"EMA trend DOWN; RSI {current_rsi:.1f}; structure confirmed",
            )

        return Guidance(
            Direction.WAIT,
            0.50,
            f"No aligned setup; RSI {current_rsi:.1f}",
        )
