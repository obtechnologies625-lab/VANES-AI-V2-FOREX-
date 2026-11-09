"""Dependency-free machine-learning regime classification for VANES.

This is a genuine trained statistical model (multinomial logistic regression
optimised by gradient descent), not a repackaged indicator rule. It learns to
classify the market regime (UP / DOWN / FLAT) from candle features and is
evaluated out-of-sample by :mod:`vanes.walkforward`.
"""

from dataclasses import dataclass, field
import math

from .market import Candle, atr, ema, rsi

REGIMES = ("UP", "DOWN", "FLAT")
_FEATURE_COUNT = 5


def extract_features(  # pylint: disable=too-many-locals
    candles: list[Candle], index: int
) -> list[float] | None:
    """Return a normalized feature vector for the candle at ``index``.

    Features are scale-free ratios so the model generalizes across symbols:
    EMA spread, RSI offset, momentum, ATR volatility ratio, and range position.
    """
    if index < 21 or index >= len(candles):
        return None
    window = candles[: index + 1]
    closes = [c.close for c in window]
    fast = ema(closes, 9)[-1]
    slow = ema(closes, 21)[-1]
    if not slow:
        return None
    current_rsi = rsi(closes, 14)
    atr_value = atr(window, 14)
    close = closes[-1]
    if current_rsi is None or atr_value is None or close <= 0:
        return None
    lookback = candles[index - 5 : index + 1]
    prior = lookback[0].close
    momentum = (close - prior) / prior if prior else 0.0
    recent = candles[index - 14 : index + 1]
    high = max(c.high for c in recent)
    low = min(c.low for c in recent)
    span = high - low
    range_pos = (close - low) / span - 0.5 if span > 0 else 0.0
    return [
        (fast - slow) / slow,
        (current_rsi - 50.0) / 50.0,
        momentum,
        atr_value / close,
        range_pos,
    ]


def label_regime(
    candles: list[Candle], index: int, horizon: int, threshold: float
) -> int | None:
    """Return the regime class index realized ``horizon`` candles after ``index``."""
    future = index + horizon
    if future >= len(candles):
        return None
    start = candles[index].close
    end = candles[future].close
    if start <= 0:
        return None
    change = (end - start) / start
    if change > threshold:
        return 0
    if change < -threshold:
        return 1
    return 2


def build_dataset(
    candles: list[Candle], horizon: int = 8, threshold: float = 0.0015
) -> tuple[list[list[float]], list[int]]:
    """Build (features, labels) pairs for every trainable candle index."""
    features: list[list[float]] = []
    labels: list[int] = []
    for index in range(21, len(candles)):
        vector = extract_features(candles, index)
        label = label_regime(candles, index, horizon, threshold)
        if vector is None or label is None:
            continue
        features.append(vector)
        labels.append(label)
    return features, labels


@dataclass
class RegimeClassifier:
    """Multinomial logistic regression over the three market regimes."""

    learning_rate: float = 0.5
    epochs: int = 60
    l2: float = 0.01
    weights: list[list[float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.weights:
            self.weights = [
                [0.0] * (_FEATURE_COUNT + 1) for _ in REGIMES
            ]

    def _logits(self, x: list[float]) -> list[float]:
        return [
            sum(w * v for w, v in zip(row[1:], x)) + row[0]
            for row in self.weights
        ]

    def predict_proba(self, x: list[float]) -> list[float]:
        """Return softmax probabilities for (UP, DOWN, FLAT)."""
        logits = self._logits(x)
        peak = max(logits)
        exps = [math.exp(value - peak) for value in logits]
        total = sum(exps) or 1.0
        return [value / total for value in exps]

    def predict(self, x: list[float]) -> str:
        """Return the most probable regime label."""
        return REGIMES[max(range(len(REGIMES)), key=lambda i: self.predict_proba(x)[i])]

    def fit(self, features: list[list[float]], labels: list[int]) -> float:
        """Train by gradient descent; return in-sample accuracy."""
        if not features:
            return 0.0
        for _ in range(self.epochs):
            grads = [
                [0.0] * (_FEATURE_COUNT + 1) for _ in REGIMES
            ]
            for x, y in zip(features, labels):
                probs = self.predict_proba(x)
                for cls in range(len(REGIMES)):
                    error = probs[cls] - (1.0 if cls == y else 0.0)
                    grads[cls][0] += error
                    for j, value in enumerate(x):
                        grads[cls][j + 1] += error * value
            count = len(features)
            for cls in range(len(REGIMES)):
                self.weights[cls][0] -= self.learning_rate * grads[cls][0] / count
                for j in range(_FEATURE_COUNT):
                    self.weights[cls][j + 1] -= self.learning_rate * (
                        grads[cls][j + 1] / count
                        + self.l2 * self.weights[cls][j + 1]
                    )
        correct = sum(
            1 for x, y in zip(features, labels) if self.predict(x) == REGIMES[y]
        )
        return correct / len(features)
