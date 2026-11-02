"""Local marketplace where forex pros register and list strategies for sale.

Payments are a placeholder ("contact for pricing") until a processor such as
Stripe is wired in; the store only records intent and listing metadata.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{3,24}$")
RISK_LEVELS = ("low", "medium", "high")


def _now() -> str:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Seller:
    """A registered strategy author."""

    seller_id: str
    handle: str
    name: str
    email: str
    bio: str = ""
    registered_at: str = ""
    status: str = "active"


@dataclass
class Strategy:  # pylint: disable=too-many-instance-attributes
    """A strategy listed for sale by a registered seller."""

    strategy_id: str
    seller_id: str
    title: str
    description: str
    price: float
    risk_level: str = "medium"
    timeframe: str = "M15"
    payment_mode: str = "contact"
    status: str = "listed"
    created_at: str = ""


class MarketplaceStore:
    """Persist sellers and strategies to a local JSON file."""

    def __init__(self, path: str = "data/vanes_marketplace.json"):
        """Create the store and load any existing data."""
        self.path = Path(path)
        self._data: dict[str, Any] = {"sellers": [], "strategies": []}
        self._load()

    def _load(self) -> None:
        """Load marketplace data from disk, tolerating a missing file."""
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self._data = {
                    "sellers": list(loaded.get("sellers", [])),
                    "strategies": list(loaded.get("strategies", [])),
                }
        except (OSError, ValueError):
            self._data = {"sellers": [], "strategies": []}

    def _save(self) -> bool:
        """Persist marketplace data; return False on failure."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as handle:
                json.dump(self._data, handle, indent=2)
            return True
        except OSError:
            return False

    def register_seller(  # pylint: disable=too-many-return-statements
        self, handle: str, name: str, email: str, bio: str = ""
    ) -> tuple[bool, str, Seller | None]:
        """Register a strategy author after validating the submission."""
        handle = (handle or "").strip()
        name = (name or "").strip()
        email = (email or "").strip().lower()
        if not HANDLE_RE.match(handle):
            return False, "Handle must be 3-24 letters, digits, or underscores", None
        if not 1 <= len(name) <= 60:
            return False, "Name must be 1-60 characters", None
        if not EMAIL_RE.match(email):
            return False, "A valid email is required", None
        for seller in self._data["sellers"]:
            if seller.get("handle", "").lower() == handle.lower():
                return False, "That handle is already registered", None
            if seller.get("email") == email:
                return False, "That email is already registered", None
        seller = Seller(
            seller_id=f"sel-{uuid.uuid4().hex[:12]}",
            handle=handle,
            name=name,
            email=email,
            bio=(bio or "").strip()[:500],
            registered_at=_now(),
        )
        self._data["sellers"].append(asdict(seller))
        if not self._save():
            return False, "Could not save registration", None
        return True, f"Welcome, {handle}. You can now list strategies.", seller

    def submit_strategy(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-return-statements
        self,
        seller_id: str,
        title: str,
        description: str,
        price: float,
        risk_level: str = "medium",
        timeframe: str = "M15",
    ) -> tuple[bool, str, Strategy | None]:
        """List a strategy for a registered seller after validation."""
        if not self.get_seller(seller_id):
            return False, "Unknown seller; register first", None
        title = (title or "").strip()
        description = (description or "").strip()
        if not 3 <= len(title) <= 80:
            return False, "Title must be 3-80 characters", None
        if not 10 <= len(description) <= 2000:
            return False, "Description must be 10-2000 characters", None
        try:
            price_value = float(price)
        except (TypeError, ValueError):
            return False, "Price must be a number", None
        if price_value < 0:
            return False, "Price cannot be negative", None
        if risk_level not in RISK_LEVELS:
            return False, f"Risk level must be one of {RISK_LEVELS}", None
        strategy = Strategy(
            strategy_id=f"str-{uuid.uuid4().hex[:12]}",
            seller_id=seller_id,
            title=title,
            description=description,
            price=price_value,
            risk_level=risk_level,
            timeframe=(timeframe or "M15").strip()[:10],
            created_at=_now(),
        )
        self._data["strategies"].append(asdict(strategy))
        if not self._save():
            return False, "Could not save strategy", None
        return True, "Strategy listed. Buyers will contact you to purchase.", strategy

    def get_seller(self, seller_id: str) -> dict[str, Any] | None:
        """Return a seller record by id, or None."""
        for seller in self._data["sellers"]:
            if seller.get("seller_id") == seller_id:
                return seller
        return None

    def list_sellers(self) -> list[dict[str, Any]]:
        """Return all registered sellers."""
        return [dict(s) for s in self._data["sellers"]]

    def list_strategies(self) -> list[dict[str, Any]]:
        """Return all listed strategies, newest first."""
        return [dict(s) for s in reversed(self._data["strategies"])]
