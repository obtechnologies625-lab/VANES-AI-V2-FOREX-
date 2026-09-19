from dataclasses import dataclass

@dataclass
class AppConfig:
    refresh_ms: int = 1000
    overlay_width: int = 380
    overlay_height: int = 310
    always_on_top: bool = True
    dry_run: bool = True
    platform: str = "MetaTrader 5"
    symbol: str = "EURUSD"
