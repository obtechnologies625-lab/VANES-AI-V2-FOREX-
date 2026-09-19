"""Transparent indicator-based market guidance strategy."""

from dataclasses import dataclass

from .market import Candle, ema, rsi
from .signals import Direction, Guidance


@dataclass(frozen=True)
class StrategyConfig:  # pylint: disable=too-few-public-methods
    """Configure the indicator periods and confidence threshold."""

    fast_ema: int = 9
    slow_ema: int = 21
    rsi_period: int = 14
    atr_period: int = 14
    min_confidence: float = 0.60


class RuleBasedStrategy:
    """Generate transparent, non-executing market guidance."""

    def __init__(self, config: StrategyConfig | None = None):
        """Create a strategy with optional configuration."""
        self.config = config or StrategyConfig()

    def evaluate(self, candles: list[Candle]) -> Guidance:
        """Evaluate EMA and RSI alignment."""
        minimum = max(
            self.config.slow_ema + 2,
            self.config.rsi_period + 2,
            self.config.atr_period + 2,
        )
        if len(candles) < minimum:
            return Guidance(Direction.WAIT, 0.0, "Collecting candle history")

        closes = [candle.close for candle in candles]
        fast = ema(closes, self.config.fast_ema)[-1]
        slow = ema(closes, self.config.slow_ema)[-1]
        current_rsi = rsi(closes, self.config.rsi_period)

        if current_rsi is None:
            return Guidance(Direction.WAIT, 0.0, "Waiting for indicators")

        if fast > slow and 50.0 < current_rsi < 70.0:
            strength = (fast - slow) / max(slow, 1e-9) * 20.0
            confidence = min(0.95, 0.60 + min(strength, 0.25))
            return Guidance(
                Direction.BUY,
                confidence,
                f"Fast EMA above slow EMA; RSI {current_rsi:.1f}",
            )

        if fast < slow and 30.0 < current_rsi < 50.0:
            strength = (slow - fast) / max(slow, 1e-9) * 20.0
            confidence = min(0.95, 0.60 + min(strength, 0.25))
            return Guidance(
                Direction.SELL,
                confidence,
                f"Fast EMA below slow EMA; RSI {current_rsi:.1f}",
            )

        return Guidance(
            Direction.WAIT,
            0.50,
            f"No aligned setup; RSI {current_rsi:.1f}",
        )
