"""Secure HTTPS client with JWT authentication for VANES cloud API."""  # pylint: disable=duplicate-code

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import jwt  # PyJWT


@dataclass(frozen=True)
class CloudResponse:
    """Standardized cloud API response."""

    ok: bool
    status: int
    data: dict[str, Any]
    error: str = ""


class SecureCloudClient:  # pylint: disable=too-few-public-methods
    """Authenticate with JWT and send multimodal packets to the Cloud API Edge Gateway."""

    def __init__(
        self,
        url: str,
        token: str,
        jwt_secret: str,
        subscription_tier: str = "SERVER_B",
        timeout: float = 5.0,
    ):
        self.url = url.rstrip("/") + "/api/v1/analyze"
        self.token = token
        self.jwt_secret = jwt_secret
        self.subscription_tier = subscription_tier
        self.timeout = max(1.0, float(timeout))
        self._last_jwt = ""
        self._last_jwt_exp = 0.0

    def _generate_jwt(self) -> str:
        """Create a short-lived JWT for this request."""
        now = time.time()
        if now < self._last_jwt_exp and self._last_jwt:
            return self._last_jwt
        payload = {
            "sub": self.token,
            "tier": self.subscription_tier,
            "iat": int(now),
            "exp": int(now + 60),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        self._last_jwt = token
        self._last_jwt_exp = now + 45
        return token

    def send_packet(self, packet) -> CloudResponse:
        """Send a TelemetryPacket to the cloud gateway and return the parsed response."""
        body = packet.to_json().encode("utf-8")
        jwt_token = self._generate_jwt()
        request = Request(
            self.url,
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
                    return CloudResponse(
                        ok=False,
                        status=response.status,
                        data={},
                        error=f"HTTP {response.status}",
                    )
                data = json.loads(raw) if raw else {}
                return CloudResponse(
                    ok=True,
                    status=response.status,
                    data=data,
                )
        except (OSError, URLError, ValueError) as exc:
            return CloudResponse(
                ok=False,
                status=0,
                data={},
                error=str(exc),
            )
