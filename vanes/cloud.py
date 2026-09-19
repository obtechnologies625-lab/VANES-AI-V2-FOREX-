"""Optional secure publisher for the VANES cloud dashboard.

The publisher is disabled unless both VANES_CLOUD_URL and VANES_CLOUD_TOKEN
are configured. It sends only the read-only market/paper state needed by the
dashboard; it never sends broker credentials or places orders.
"""

import json
import os
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


class CloudStatePublisher:
    """Publish sanitized VANES state to a Cloudflare Worker."""

    FIELDS = (
        "symbol",
        "direction",
        "confidence",
        "bid",
        "ask",
        "spread",
        "reason",
        "stop_loss",
        "take_profit",
        "risk_gate",
        "broker_ready",
        "paper_balance",
        "paper_daily_pnl",
        "paper_open_trades",
        "point_size",
    )

    def __init__(self, url, token, interval_seconds=3.0, timeout=5.0):
        """Create a publisher with a minimum interval between requests."""
        self.url = url.rstrip("/") + "/api/publish"
        self.token = token
        self.interval_seconds = max(0.5, float(interval_seconds))
        self.timeout = max(1.0, float(timeout))
        self._last_publish = 0.0
        self.last_error = ""

    @classmethod
    def from_environment(cls):
        """Create a publisher from environment variables, or return None."""
        url = os.getenv("VANES_CLOUD_URL", "").strip()
        token = os.getenv("VANES_CLOUD_TOKEN", "").strip()
        if not url or not token:
            return None
        return cls(
            url,
            token,
            os.getenv("VANES_CLOUD_PUBLISH_INTERVAL", "3"),
            os.getenv("VANES_CLOUD_TIMEOUT", "5"),
        )

    def publish(self, state):
        """Publish a sanitized state if the throttle interval has elapsed."""
        now = time.monotonic()
        if now - self._last_publish < self.interval_seconds:
            return True

        payload = {
            key: state[key]
            for key in self.FIELDS
            if key in state
        }
        payload["updated_at"] = None
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = Request(
            self.url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "User-Agent": "VANES-AI-V2/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status < 200 or response.status >= 300:
                    raise URLError(f"cloud returned HTTP {response.status}")
                response.read()
            self._last_publish = now
            self.last_error = ""
            return True
        except (OSError, URLError, ValueError) as exc:
            self.last_error = str(exc)
            return False
