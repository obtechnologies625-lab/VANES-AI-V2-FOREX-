"""Runtime configuration for the VANES desktop application."""

from dataclasses import dataclass
import os


@dataclass
class AppConfig:  # pylint: disable=too-many-instance-attributes
    """Configure VANES market analysis, risk, capture, and cloud behavior."""

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
    chat_enabled: bool = True
    chat_host: str = "127.0.0.1"
    chat_port: int = 8765
    paper_max_open_trades: int = 1
    paper_start_balance: float = 10000.0
    audit_path: str = "data/vanes_audit.jsonl"

    cloud_url: str = ""
    cloud_token: str = ""
    cloud_publish_interval: float = 3.0
    cloud_timeout: float = 5.0
    subscription_tier: str = "SERVER_B"
    jwt_secret: str = ""
    gemini_api_key: str = ""

    capture_audio_enabled: bool = False
    capture_screen_enabled: bool = False
    capture_audio_device: str = ""
    capture_screen_region: str = ""
    capture_audio_chunk_seconds: float = 2.0
    capture_screen_fps: int = 1
    capture_max_packet_bytes: int = 524288

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
            chat_enabled=os.getenv("VANES_CHAT_ENABLED", "1") != "0",
            chat_host=os.getenv("VANES_CHAT_HOST", "127.0.0.1"),
            chat_port=number("VANES_CHAT_PORT", 8765, int),
            paper_max_open_trades=number("VANES_PAPER_MAX_OPEN_TRADES", 1, int),
            paper_start_balance=number(
                "VANES_PAPER_START_BALANCE", 10000.0, float
            ),
            audit_path=os.getenv(
                "VANES_AUDIT_PATH", "data/vanes_audit.jsonl"
            ),
            cloud_url=os.getenv("VANES_CLOUD_URL", ""),
            cloud_token=os.getenv("VANES_CLOUD_TOKEN", ""),
            cloud_publish_interval=number(
                "VANES_CLOUD_PUBLISH_INTERVAL", 3.0, float
            ),
            cloud_timeout=number("VANES_CLOUD_TIMEOUT", 5.0, float),
            subscription_tier=os.getenv("VANES_SUBSCRIPTION_TIER", "SERVER_B"),
            jwt_secret=os.getenv("VANES_JWT_SECRET", ""),
            gemini_api_key=os.getenv("VANES_GEMINI_API_KEY", ""),
            capture_audio_enabled=os.getenv(
                "VANES_CAPTURE_AUDIO", "0"
            ) == "1",
            capture_screen_enabled=os.getenv(
                "VANES_CAPTURE_SCREEN", "0"
            ) == "1",
            capture_audio_device=os.getenv("VANES_CAPTURE_AUDIO_DEVICE", ""),
            capture_screen_region=os.getenv(
                "VANES_CAPTURE_SCREEN_REGION", ""
            ),
            capture_audio_chunk_seconds=number(
                "VANES_CAPTURE_AUDIO_CHUNK_SECONDS", 2.0, float
            ),
            capture_screen_fps=number("VANES_CAPTURE_SCREEN_FPS", 1, int),
            capture_max_packet_bytes=number(
                "VANES_CAPTURE_MAX_PACKET_BYTES", 524288, int
            ),
        )
