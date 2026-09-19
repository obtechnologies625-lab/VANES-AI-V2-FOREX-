"""Read-only alert generation for VANES market state."""

from dataclasses import dataclass

# The alert is a data record; it intentionally exposes no behavior.
# pylint: disable=too-few-public-methods


@dataclass(frozen=True)
class Alert:
    """Represent a user-facing market alert."""

    kind: str
    message: str


class AlertEngine:
    """Generate alerts only when a meaningful state transition occurs."""

    def __init__(self):
        """Initialize the transition tracker."""
        self._last_direction = None
        self._last_risk_gate = None
        self._last_stale = None

    def evaluate(self, direction, confidence, risk_gate, stale):
        """Return new alerts for direction, risk, and data-state changes."""
        alerts = []
        if self._last_direction is not None and direction != self._last_direction:
            alerts.append(Alert(
                "signal",
                f"Guidance changed to {direction} ({confidence:.0%} confidence).",
            ))
        if self._last_risk_gate is not None and risk_gate != self._last_risk_gate:
            alerts.append(Alert("risk", f"Risk gate changed to {risk_gate}."))
        if self._last_stale is not None and stale != self._last_stale:
            alerts.append(
                Alert(
                    "data",
                    "Market data is stale." if stale else "Market data is live again.",
                )
            )
        self._last_direction = direction
        self._last_risk_gate = risk_gate
        self._last_stale = stale
        return alerts
