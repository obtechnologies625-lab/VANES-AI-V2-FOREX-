"""Walk-forward out-of-sample validation for the VANES regime model.

Rolls a training window across history, fits the classifier in-sample, and
scores it only on the unseen forward window. This is the anti-overfitting gate:
an edge that only exists in-sample collapses here.
"""

from dataclasses import dataclass

from .market import Candle
from .ml import REGIMES, RegimeClassifier, build_dataset


@dataclass(frozen=True)
class WalkForwardFold:
    """One in-sample train / out-of-sample test split."""

    train_start: int
    train_end: int
    test_start: int
    test_end: int
    train_accuracy: float
    oos_accuracy: float
    oos_samples: int


@dataclass(frozen=True)
class WalkForwardReport:
    """Aggregate out-of-sample verdict across all folds."""

    folds: tuple[WalkForwardFold, ...]
    oos_accuracy: float
    baseline_accuracy: float
    edge_survives: bool

    @property
    def fold_count(self) -> int:
        """Return how many out-of-sample folds were evaluated."""
        return len(self.folds)


def walk_forward_validate(  # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
    candles: list[Candle],
    train_window: int = 120,
    test_window: int = 40,
    step: int = 40,
    horizon: int = 8,
    threshold: float = 0.0015,
) -> WalkForwardReport:
    """Roll the regime model forward and score it out-of-sample."""
    folds: list[WalkForwardFold] = []
    start = 0
    while start + train_window + test_window <= len(candles):
        train_slice = candles[start : start + train_window]
        test_slice = candles[
            start + train_window : start + train_window + test_window
        ]
        train_x, train_y = build_dataset(train_slice, horizon, threshold)
        if train_x:
            model = RegimeClassifier()
            train_acc = model.fit(train_x, train_y)
            test_x, test_y = build_dataset(test_slice, horizon, threshold)
            if test_x:
                correct = sum(
                    1
                    for x, y in zip(test_x, test_y)
                    if model.predict(x) == REGIMES[y]
                )
                folds.append(
                    WalkForwardFold(
                        start,
                        start + train_window,
                        start + train_window,
                        start + train_window + test_window,
                        train_acc,
                        correct / len(test_x),
                        len(test_x),
                    )
                )
        start += step

    if not folds:
        return WalkForwardReport((), 0.0, 0.0, False)

    total_samples = sum(fold.oos_samples for fold in folds)
    oos_accuracy = (
        sum(fold.oos_accuracy * fold.oos_samples for fold in folds)
        / total_samples
        if total_samples
        else 0.0
    )
    baseline = _majority_baseline(candles, horizon, threshold)
    edge_survives = len(folds) >= 2 and oos_accuracy > baseline
    return WalkForwardReport(
        tuple(folds), oos_accuracy, baseline, edge_survives
    )


def _majority_baseline(
    candles: list[Candle], horizon: int, threshold: float
) -> float:
    """Return the accuracy of always predicting the most common regime."""
    _, labels = build_dataset(candles, horizon, threshold)
    if not labels:
        return 0.0
    counts = [labels.count(cls) for cls in range(len(REGIMES))]
    return max(counts) / len(labels)
