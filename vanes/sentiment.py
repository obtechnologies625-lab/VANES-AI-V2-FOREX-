"""Lexicon-based NLP sentiment scoring for news and social text.

Provides an alternative-data layer: headline / transcript text is scored into a
[-1, 1] bullish-bearish signal and aggregated into a rolling feed sentiment that
the strategy, bridge state, and cloud packet can consume.
"""

from dataclasses import dataclass, field
import math
import re

_BULLISH = {
    "beat", "beats", "upgrade", "upgrades", "upgraded", "rally", "rallies",
    "surge", "surges", "soar", "soars", "gain", "gains", "profit", "profits",
    "bullish", "optimistic", "growth", "strong", "record", "breakout",
    "buy", "buys", "accumulation", "inflow", "inflows", "recovery",
    "recover", "recovers", "expand", "expands", "expansion", "dividend",
}
_BEARISH = {
    "miss", "misses", "downgrade", "downgrades", "downgraded", "crash",
    "crashes", "plunge", "plunges", "tumble", "tumbles", "loss", "losses",
    "bearish", "pessimistic", "recession", "weak", "warning", "breakdown",
    "sell", "sells", "distribution", "outflow", "outflows", "layoff",
    "layoffs", "default", "defaults", "contract", "contracts", "cut", "cuts",
}
_NEGATORS = {"not", "no", "never", "without", "isn't", "aren't", "won't"}


def score_text(text: str) -> float:
    """Score one piece of text into [-1, 1] (positive = bullish)."""
    tokens = re.findall(r"[a-z']+", (text or "").lower())
    if not tokens:
        return 0.0
    hits = 0
    for index, token in enumerate(tokens):
        if token not in _BULLISH and token not in _BEARISH:
            continue
        polarity = 1.0 if token in _BULLISH else -1.0
        if index and tokens[index - 1] in _NEGATORS:
            polarity *= -1.0
        hits += polarity
    if not hits:
        return 0.0
    return math.tanh(hits / 3.0)


@dataclass
class SentimentFeed:
    """Rolling aggregate of recent text sentiment."""

    max_samples: int = 50
    scores: list[float] = field(default_factory=list)

    def ingest(self, text: str) -> float:
        """Score and record one headline / transcript snippet."""
        value = score_text(text)
        self.scores.append(value)
        if len(self.scores) > self.max_samples:
            self.scores.pop(0)
        return value

    @property
    def score(self) -> float:
        """Return the mean sentiment of the rolling window."""
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    @property
    def label(self) -> str:
        """Return a coarse bullish / bearish / neutral bucket."""
        value = self.score
        if value > 0.15:
            return "BULLISH"
        if value < -0.15:
            return "BEARISH"
        return "NEUTRAL"

    @property
    def samples(self) -> int:
        """Return how many snippets are in the rolling window."""
        return len(self.scores)

    def snapshot(self) -> dict:
        """Return a JSON-friendly sentiment summary."""
        return {
            "score": round(self.score, 4),
            "label": self.label,
            "samples": self.samples,
        }
