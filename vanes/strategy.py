from dataclasses import dataclass
from .market import Candle, atr, ema, rsi
from .signals import Direction, Guidance

@dataclass(frozen=True)
class StrategyConfig:
    fast_ema: int = 9
    slow_ema: int = 21
    rsi_period: int = 14
    atr_period: int = 14
    min_confidence: float = 0.60

class RuleBasedStrategy:
    """Transparent educational signal model; it does not execute trades."""

    def __init__(self, config: StrategyConfig | None = None):
        self.config = config or StrategyConfig()

    def evaluate(self, candles: list[Candle]) -> Guidance:
        minimum = max(self.config.slow_ema + 2, self.config.rsi_period + 2, self.config.atr_period + 2)
        if len(candles) < minimum:
            return Guidance(Direction.WAIT, 0.0, "Collecting candle history")

        closes = [c.close for c in candles]
        fast = ema(closes, self.config.fast_ema)[-1]
        slow = ema(closes, self.config.slow_ema)[-1]
        current_rsi = rsi(closes, self.config.rsi_period)

        if current_rsi is None:
            return Guidance(Direction.WAIT, 0.0, "Waiting for indicators")

        if fast > slow and 50.0 < current_rsi < 70.0:
            confidence = min(0.95, 0.60 + min((fast - slow) / max(slow, 1e-9) * 20.0, 0.25))
            return Guidance(Direction.BUY, confidence, f"Fast EMA above slow EMA; RSI {current_rsi:.1f}")
        if fast < slow and 30.0 < current_rsi < 50.0:
            confidence = min(0.95, 0.60 + min((slow - fast) / max(slow, 1e-9) * 20.0, 0.25))
            return Guidance(Direction.SELL, confidence, f"Fast EMA below slow EMA; RSI {current_rsi:.1f}")

        return Guidance(Direction.WAIT, 0.50, f"No aligned setup; RSI {current_rsi:.1f}")
