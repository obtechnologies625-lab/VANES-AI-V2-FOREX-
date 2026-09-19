"""Runtime configuration for the VANES desktop application."""

from dataclasses import dataclass
import os


@dataclass
class AppConfig:  # pylint: disable=too-many-instance-attributes
    """Configure VANES market analysis, risk, and observer behavior."""

    refresh_ms: int = 1500
    overlay_width: int = 430
    overlay_height: int = 430
    always_on_top: bool = True
    dry_run: bool = True
    platform: str = "MetaTrader 5"
    symbol: str = "EURUSD"
    timeframe: str = "M15"
    confirmation_timeframe: str = "H1"
    candle_count: int = 200
    account_balance: float = 10000.0
    risk_percent: float = 1.0
    max_daily_loss_percent: float = 3.0
    max_spread_points: float = 25.0
    paper_start_balance: float = 10000.0
    audit_path: str = "data/vanes_audit.jsonl"

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Build configuration from VANES_* environment variables."""

        def number(name, default, cast):
            value = os.getenv(name)
            return default if value in (None, "") else cast(value)

        return cls(
            refresh_ms=number("VANES_REFRESH_MS", 1500, int),
            always_on_top=os.getenv("VANES_TOPMOST", "1") != "0",
            dry_run=os.getenv("VANES_DRY_RUN", "1") != "0",
            symbol=os.getenv("VANES_SYMBOL", "EURUSD"),
            timeframe=os.getenv("VANES_TIMEFRAME", "M15"),
            confirmation_timeframe=os.getenv(
                "VANES_CONFIRMATION_TIMEFRAME", "H1"
            ),
            account_balance=number("VANES_ACCOUNT_BALANCE", 10000.0, float),
            risk_percent=number("VANES_RISK_PERCENT", 1.0, float),
            max_daily_loss_percent=number(
                "VANES_MAX_DAILY_LOSS_PERCENT", 3.0, float
            ),
            max_spread_points=number("VANES_MAX_SPREAD_POINTS", 25.0, float),
            paper_start_balance=number(
                "VANES_PAPER_START_BALANCE", 10000.0, float
            ),
            audit_path=os.getenv(
                "VANES_AUDIT_PATH", "data/vanes_audit.jsonl"
            ),
        )
