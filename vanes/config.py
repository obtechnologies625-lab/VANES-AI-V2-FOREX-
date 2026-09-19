from dataclasses import dataclass

@dataclass
class AppConfig:
    refresh_ms: int = 1500
    overlay_width: int = 430
    overlay_height: int = 380
    always_on_top: bool = True
    dry_run: bool = True
    platform: str = "MetaTrader 5"
    symbol: str = "EURUSD"
    timeframe: str = "M15"
