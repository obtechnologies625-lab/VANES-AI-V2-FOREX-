"""Incubation gate: prove the edge on live, un-traded data before real capital.

The tracker persists the first-observation timestamp and session count so the
required incubation period survives restarts. Live order dispatch stays locked
until the configured number of days of live observation has elapsed.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass(frozen=True)
class IncubationStatus:
    """Snapshot of incubation progress."""

    first_observed: str
    days_elapsed: int
    required_days: int
    sessions: int
    complete: bool


class IncubationTracker:
    """Persist and evaluate the live-trading incubation period."""

    def __init__(self, path: str, required_days: int = 30):
        """Create the tracker, loading any persisted incubation record."""
        self.path = Path(path)
        self.required_days = max(0, required_days)
        self._record = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._record, separators=(",", ":")), encoding="utf-8"
        )

    def touch(self) -> None:
        """Record an observation session, starting the clock on first use."""
        now = datetime.now(timezone.utc).isoformat()
        if not self._record.get("first_observed"):
            self._record["first_observed"] = now
            self._record["sessions"] = 0
        self._record["sessions"] = int(self._record.get("sessions", 0)) + 1
        self._record["last_seen"] = now
        self._save()

    def days_elapsed(self) -> int:
        """Return whole days since first live observation."""
        first = self._record.get("first_observed")
        if not first:
            return 0
        try:
            started = datetime.fromisoformat(first)
        except ValueError:
            return 0
        delta = datetime.now(timezone.utc) - started
        return max(0, delta.days)

    def live_allowed(self) -> bool:
        """Return whether the incubation period has been satisfied."""
        return self.days_elapsed() >= self.required_days

    def status(self) -> IncubationStatus:
        """Return the current incubation snapshot."""
        return IncubationStatus(
            first_observed=self._record.get("first_observed", ""),
            days_elapsed=self.days_elapsed(),
            required_days=self.required_days,
            sessions=int(self._record.get("sessions", 0)),
            complete=self.live_allowed(),
        )
