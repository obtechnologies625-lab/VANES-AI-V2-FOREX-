from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

@dataclass
class MarketSnapshot:
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None

@dataclass
class Guidance:
    direction: Direction
    confidence: float
    reason: str

class SignalEngine:
    """Read-only guidance engine. It never places or modifies orders."""

    def evaluate(self, snapshot: MarketSnapshot) -> Guidance:
        if snapshot.bid is None or snapshot.ask is None:
            return Guidance(Direction.WAIT, 0.0, "Waiting for market data")
        if snapshot.ask <= snapshot.bid:
            return Guidance(Direction.WAIT, 0.0, "Invalid quote; waiting")
        return Guidance(
            Direction.WAIT,
            0.0,
            f"{snapshot.symbol}: market connected; strategy module not configured",
        )
