"""Behavioral AI companion: tilt and drift detection.

Monitors the trader's own actions (paper/live opens, closes, and rule overrides)
and flags self-sabotage patterns — overtrading, revenge trading after a loss,
and guardrail overrides — producing a tilt score and an emotional journaling
prompt. The strategy can be statistically fine and still lose money to human
override; this module watches for exactly that.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class BehaviorReport:
    """Snapshot of detected behavioral risk."""

    tilt_score: int
    overtrading: bool
    revenge_trading: bool
    rule_breaks: int
    journal_prompt: str
    flags: tuple[str, ...]


class BehaviorMonitor:
    """Track trading behavior and surface tilt / drift warnings."""

    def __init__(
        self,
        max_trades_per_day: int = 5,
        revenge_window_minutes: int = 15,
        tilt_alert: int = 40,
    ):
        """Create a monitor with configurable behavioral thresholds."""
        self.max_trades_per_day = max_trades_per_day
        self.revenge_window = timedelta(minutes=revenge_window_minutes)
        self.tilt_alert = tilt_alert
        self._opens: list[datetime] = []
        self._closes: list[tuple[datetime, float]] = []
        self._rule_breaks: list[tuple[datetime, str]] = []

    def record_open(self, when: datetime | None = None) -> None:
        """Record a trade open for overtrading / revenge detection."""
        self._opens.append(when or datetime.now())

    def record_close(self, pnl: float, when: datetime | None = None) -> None:
        """Record a realized close so a following fast re-entry flags revenge."""
        self._closes.append((when or datetime.now(), pnl))

    def record_rule_break(self, reason: str, when: datetime | None = None) -> None:
        """Record a guardrail override or blocked-by-rule attempt."""
        self._rule_breaks.append((when or datetime.now(), reason))

    def _day_opens(self, now: datetime) -> int:
        return sum(1 for ts in self._opens if ts.date() == now.date())

    def _revenge(self, now: datetime) -> bool:
        losses = [ts for ts, pnl in self._closes if pnl < 0]
        if not losses:
            return False
        last_loss = max(losses)
        return any(
            last_loss < ts <= last_loss + self.revenge_window
            for ts in self._opens
        ) and now - last_loss <= self.revenge_window * 4

    def report(self, now: datetime | None = None) -> BehaviorReport:
        """Compute the current tilt score, flags, and journaling prompt."""
        now = now or datetime.now()
        overtrading = self._day_opens(now) > self.max_trades_per_day
        revenge = self._revenge(now)
        recent_breaks = sum(
            1 for ts, _ in self._rule_breaks if now - ts <= timedelta(hours=24)
        )
        score = 0
        flags: list[str] = []
        if overtrading:
            score += 35
            flags.append("overtrading")
        if revenge:
            score += 40
            flags.append("revenge-trading")
        if recent_breaks:
            score += min(25, recent_breaks * 10)
            flags.append(f"rule-breaks:{recent_breaks}")
        score = min(100, score)
        prompt = ""
        if score >= self.tilt_alert:
            prompt = (
                "Tilt risk detected. Pause and journal: what did you feel "
                "right before overriding the plan, and what does the rule "
                "book say instead?"
            )
        return BehaviorReport(
            tilt_score=score,
            overtrading=overtrading,
            revenge_trading=revenge,
            rule_breaks=recent_breaks,
            journal_prompt=prompt,
            flags=tuple(flags),
        )

    def snapshot(self) -> dict:
        """Return a JSON-friendly behavioral summary."""
        report = self.report()
        return {
            "tilt_score": report.tilt_score,
            "flags": list(report.flags),
            "journal_prompt": report.journal_prompt,
        }
