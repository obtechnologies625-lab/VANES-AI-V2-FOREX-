"""Optional secure publisher for the VANES cloud dashboard.

The publisher is disabled unless both VANES_CLOUD_URL and VANES_CLOUD_TOKEN
are configured. It sends sanitized market/paper state plus optional multimodal
media (audio chunks and screen frames) to the Cloud API Edge Gateway.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .aggregator import PacketAggregator


@dataclass
class CloudPublishResult:  # pylint: disable=too-many-instance-attributes
    """Result of a cloud publish attempt."""

    ok: bool
    status: int
    error: str = ""
    packet_id: str = ""
    analysis: str = ""
    direction: str = ""
    confidence: float = 0.0
    sources: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.sources is None:
            self.sources = []


class CloudStatePublisher:  # pylint: disable=too-many-instance-attributes
    """Publish sanitized VANES state and multimodal media to a Cloudflare Worker."""

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
        "paper_trades",
        "alerts",
        "point_size",
    )

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        url: str,
        token: str,
        jwt_secret: str,
        subscription_tier: str = "SERVER_B",
        interval_seconds: float = 3.0,
        timeout: float = 5.0,
        aggregator: PacketAggregator | None = None,
    ):
        """Create a publisher with optional multimodal aggregation."""
        self.url = url.rstrip("/")
        self.token = token
        self.jwt_secret = jwt_secret
        self.subscription_tier = subscription_tier
        self.interval_seconds = max(0.5, float(interval_seconds))
        self.timeout = max(1.0, float(timeout))
        self.aggregator = aggregator
        self._last_publish = 0.0
        self.last_error = ""

    @classmethod
    def from_environment(
        cls, aggregator: PacketAggregator | None = None
    ) -> "CloudStatePublisher | None":
        """Create a publisher from environment variables, or return None."""
        url = os.getenv("VANES_CLOUD_URL", "").strip()
        token = os.getenv("VANES_CLOUD_TOKEN", "").strip()
        jwt_secret = os.getenv("VANES_JWT_SECRET", "").strip()
        if not url or not token or not jwt_secret:
            return None
        return cls(
            url,
            token,
            jwt_secret,
            os.getenv("VANES_SUBSCRIPTION_TIER", "SERVER_B"),
            os.getenv("VANES_CLOUD_PUBLISH_INTERVAL", "3"),
            os.getenv("VANES_CLOUD_TIMEOUT", "5"),
            aggregator,
        )

    def publish(self, state: dict[str, object]) -> CloudPublishResult:
        """Publish state and optional multimodal media if the throttle interval has elapsed."""
        now = time.monotonic()
        if now - self._last_publish < self.interval_seconds:
            return CloudPublishResult(ok=False, status=0, error="throttled")

        packet = None
        if self.aggregator is not None:
            packet = self.aggregator.build_packet(state)
        if packet is None:
            payload = {
                key: state[key] for key in self.FIELDS if key in state
            }
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            path = "/api/publish"
        else:
            body = packet.to_json().encode("utf-8")
            path = "/api/v1/analyze"

        jwt_token = self._make_jwt()
        request = Request(
            self.url + path,
            data=body,
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "X-Subscription-Tier": self.subscription_tier,
                "User-Agent": "VANES-AI-V2/2.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                if response.status < 200 or response.status >= 300:
                    self.last_error = f"cloud returned HTTP {response.status}"
                    return CloudPublishResult(
                        ok=False,
                        status=response.status,
                        error=self.last_error,
                    )
                data = json.loads(raw) if raw else {}
                self._last_publish = now
                self.last_error = ""
                return CloudPublishResult(
                    ok=True,
                    status=response.status,
                    packet_id=data.get("packet_id", packet.packet_id if packet else ""),
                    analysis=data.get("analysis", ""),
                    direction=data.get("direction", ""),
                    confidence=data.get("confidence", 0.0),
                    sources=data.get("sources", []),
                )
        except (OSError, URLError, ValueError) as exc:
            self.last_error = str(exc)
            return CloudPublishResult(ok=False, status=0, error=self.last_error)

    def _make_jwt(self) -> str:
        """Create a short-lived JWT for cloud authentication."""
        try:
            import jwt  # pylint: disable=import-outside-toplevel
        except ImportError:
            return self.token
        now = time.time()
        payload = {
            "sub": self.token,
            "tier": self.subscription_tier,
            "iat": int(now),
            "exp": int(now + 60),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
