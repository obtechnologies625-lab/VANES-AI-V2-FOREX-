"""Simple market-structure and trend analysis."""

from dataclasses import dataclass

from .market import Candle, ema, swing_levels


@dataclass(frozen=True)
class Structure:
    """Describe recent trend and support/resistance."""

    trend: str
    support: float
    resistance: float


def analyze_structure(
    candles: list[Candle], lookback: int = 20
) -> Structure | None:
    """Classify trend from EMA alignment and recent swing levels."""
    levels = swing_levels(candles, lookback)
    if levels is None or len(candles) < 21:
        return None
    closes = [c.close for c in candles]
    fast = ema(closes, 9)[-1]
    slow = ema(closes, 21)[-1]
    trend = "UP" if fast > slow else "DOWN" if fast < slow else "RANGE"
    return Structure(trend, levels[0], levels[1])
