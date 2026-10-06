"""Subscription tier, trial tracking, and paywall enforcement for VANES."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from .config import AppConfig


@dataclass(frozen=True)
class TierInfo:
    """Subscription tier metadata."""

    id: str
    name: str
    price: float
    trial_limit: int
    features: list[str]


TIERS = {
    "SERVER_A": TierInfo(
        id="SERVER_A",
        name="SERVER A",
        price=3000.0,
        trial_limit=5,
        features=[
            "Live MT5 order dispatch",
            "Gemini 2.5 multimodal AI",
            "Audio + screen capture",
            "Priority support",
        ],
    ),
    "SERVER_B": TierInfo(
        id="SERVER_B",
        name="SERVER B",
        price=4000.0,
        trial_limit=5,
        features=[
            "Gemini 2.5 multimodal AI",
            "Audio + screen capture",
            "Paper trading",
            "Standard support",
        ],
    ),
    "SERVER_C": TierInfo(
        id="SERVER_C",
        name="SERVER C",
        price=5000.0,
        trial_limit=5,
        features=[
            "Basic text analysis",
            "Paper trading only",
            "Community support",
        ],
    ),
}


class TrialTracker:
    """Track trial usage per tier in a local JSON file."""

    def __init__(self, path: str = "data/vanes_trials.json"):
        self.path = path
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load trial data from disk."""
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                self._data = json.load(handle)
        except (OSError, ValueError):
            self._data = {}

    def _save(self) -> None:
        """Persist trial data to disk."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
        except (OSError, ValueError) as exc:
            print(f"VANES: failed to save trial data: {exc}")

    def remaining_trials(self, tier: str) -> int:
        """Return remaining free trials for a tier."""
        tier_data = self._data.get(tier, {})
        used = int(tier_data.get("used", 0))
        limit = TIERS.get(tier, TIERS["SERVER_C"]).trial_limit
        return max(0, limit - used)

    def use_trial(self, tier: str) -> bool:
        """Consume one trial slot for the tier. Returns True if successful."""
        if self.remaining_trials(tier) <= 0:
            return False
        tier_data = self._data.setdefault(tier, {})
        tier_data["used"] = int(tier_data.get("used", 0)) + 1
        self._save()
        return True

    def has_paid(self, tier: str) -> bool:
        """Check if the user has paid for the tier."""
        return bool(self._data.get(tier, {}).get("paid", False))

    def mark_paid(self, tier: str) -> None:
        """Mark the tier as paid."""
        tier_data = self._data.setdefault(tier, {})
        tier_data["paid"] = True
        tier_data["used"] = 0
        self._save()


class SubscriptionManager:
    """Manage tier selection, trials, and paywall enforcement."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.tracker = TrialTracker()
        self.selected_tier = config.subscription_tier

    def can_access(self) -> tuple[bool, str]:
        """Check if the selected tier is accessible.

        Returns (allowed, reason).
        """
        tier = self.selected_tier
        info = TIERS.get(tier, TIERS["SERVER_C"])

        if self.tracker.has_paid(tier):
            return True, f"{info.name} - Paid"

        remaining = self.tracker.remaining_trials(tier)
        if remaining > 0:
            return True, f"{info.name} - Trial ({remaining} left)"

        return False, f"{tier} requires payment (${info.price:.0f})"

    def consume_access(self) -> tuple[bool, str]:
        """Consume one access token for the current tier.

        Returns (allowed, message).
        """
        tier = self.selected_tier
        info = TIERS.get(tier, TIERS["SERVER_C"])

        if self.tracker.has_paid(tier):
            return True, f"{info.name} - Paid access"

        if self.tracker.use_trial(tier):
            remaining = self.tracker.remaining_trials(tier)
            return True, f"{info.name} - Trial used ({remaining} left)"

        return False, f"Trial exhausted. Upgrade {info.name} for ${info.price:.0f}"

    def tier_info(self) -> TierInfo:
        """Return metadata for the selected tier."""
        return TIERS.get(self.selected_tier, TIERS["SERVER_C"])
