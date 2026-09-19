"""Trading-platform adapters for read-only market data."""

from dataclasses import dataclass

from .market import Candle
from .signals import MarketSnapshot


@dataclass
class PlatformStatus:
    """Report platform connection state."""

    connected: bool
    message: str


class PlatformAdapter:
    """Define the platform adapter interface."""

    def connect(self) -> PlatformStatus:
        """Connect to the trading platform."""
        return PlatformStatus(False, "No platform adapter configured")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        """Return the latest quote for a symbol."""
        return MarketSnapshot(symbol=symbol)

    def candles(
        self, symbol: str, timeframe: str, count: int = 150
    ) -> list[Candle]:
        """Return historical candles for a symbol."""
        del symbol, timeframe, count
        return []

    def close(self) -> None:
        """Close the platform connection."""


class MT5Adapter(PlatformAdapter):
    """Read-only MetaTrader 5 adapter."""

    TIMEFRAMES = {
        "M1": "TIMEFRAME_M1",
        "M5": "TIMEFRAME_M5",
        "M15": "TIMEFRAME_M15",
        "M30": "TIMEFRAME_M30",
        "H1": "TIMEFRAME_H1",
        "H4": "TIMEFRAME_H4",
        "D1": "TIMEFRAME_D1",
    }

    def __init__(self):
        """Initialize an unconnected adapter."""
        self._mt5 = None

    def connect(self) -> PlatformStatus:
        """Initialize the MetaTrader 5 Python API."""
        try:
            import MetaTrader5 as mt5  # pylint: disable=import-outside-toplevel,import-error
        except ImportError:
            return PlatformStatus(
                False, "MetaTrader5 package is not installed"
            )
        if not mt5.initialize():
            return PlatformStatus(
                False, "MetaTrader 5 initialize() failed"
            )
        self._mt5 = mt5
        return PlatformStatus(True, "Connected to MetaTrader 5")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        """Read the latest bid/ask quote."""
        if self._mt5 is None or not self._mt5.symbol_select(symbol, True):
            return MarketSnapshot(symbol=symbol)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return MarketSnapshot(symbol=symbol)
        return MarketSnapshot(
            symbol,
            float(tick.bid),
            float(tick.ask),
            float(tick.ask - tick.bid),
        )

    def candles(
        self, symbol: str, timeframe: str = "M15", count: int = 150
    ) -> list[Candle]:
        """Read historical OHLCV candles from MetaTrader 5."""
        if self._mt5 is None or not self._mt5.symbol_select(symbol, True):
            return []
        tf_name = self.TIMEFRAMES.get(
            timeframe.upper(), "TIMEFRAME_M15"
        )
        rates = self._mt5.copy_rates_from_pos(
            symbol, getattr(self._mt5, tf_name), 0, count
        )
        if rates is None:
            return []
        return [
            Candle(
                int(rate["time"]),
                float(rate["open"]),
                float(rate["high"]),
                float(rate["low"]),
                float(rate["close"]),
                float(rate["tick_volume"]),
            )
            for rate in rates
        ]

    def close(self) -> None:
        """Shut down the MetaTrader 5 connection."""
        if self._mt5 is not None:
            self._mt5.shutdown()
            self._mt5 = None
