"""Signal data structures used by the VANES strategy engine."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Direction(str, Enum):
    """Represent the current guidance direction."""

    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


@dataclass
class MarketSnapshot:
    """Represent the latest bid/ask market quote."""

    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None


@dataclass
class Guidance:
    """Represent a strategy decision and its explanation."""

    direction: Direction
    confidence: float
    reason: str


class SignalEngine:  # pylint: disable=too-few-public-methods
    """Provide a safe, read-only quote validation layer."""

    def evaluate(self, snapshot: MarketSnapshot) -> Guidance:
        """Validate a quote before strategy processing."""
        if snapshot.bid is None or snapshot.ask is None:
            return Guidance(Direction.WAIT, 0.0, "Waiting for market data")
        if snapshot.ask <= snapshot.bid:
            return Guidance(Direction.WAIT, 0.0, "Invalid quote; waiting")
        return Guidance(
            Direction.WAIT,
            0.0,
            f"{snapshot.symbol}: market connected; "
            "strategy module not configured",
        )
