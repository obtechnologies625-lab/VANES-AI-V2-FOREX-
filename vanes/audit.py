"""Append-only JSONL audit logging for VANES."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class AuditLogger:  # pylint: disable=too-few-public-methods
    """Write timestamped application events to a local JSONL file."""

    def __init__(self, path: str):
        """Create an audit logger and ensure its parent directory exists."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: str, **values: Any) -> None:
        """Append one structured event."""
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **values,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
