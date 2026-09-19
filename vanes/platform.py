"""Trading-platform adapters for read-only market data."""

from dataclasses import dataclass

from .market import Candle
from .signals import MarketSnapshot


@dataclass(frozen=True)
class SymbolSpec:
    """Broker symbol economics needed for accurate risk calculations."""

    point: float
    digits: int
    tick_size: float
    tick_value: float
    volume_min: float
    volume_max: float
    volume_step: float


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

    def symbol_spec(self, symbol: str) -> SymbolSpec | None:
        """Return broker-provided symbol economics."""
        del symbol

    def point_size(self, symbol: str) -> float:
        """Return a conservative fallback point size."""
        del symbol
        return 0.00001

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
            return PlatformStatus(False, "MetaTrader5 package is not installed")
        if not mt5.initialize():
            return PlatformStatus(
                False, f"MetaTrader 5 initialize() failed: {mt5.last_error()}"
            )
        self._mt5 = mt5
        return PlatformStatus(True, "Connected to MetaTrader 5")

    def _select(self, symbol: str) -> bool:
        """Select a symbol and report whether it is usable."""
        return self._mt5 is not None and self._mt5.symbol_select(symbol, True)

    def snapshot(self, symbol: str) -> MarketSnapshot:
        """Read the latest bid/ask quote."""
        if not self._select(symbol):
            return MarketSnapshot(symbol=symbol)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None or tick.bid <= 0 or tick.ask <= 0 or tick.ask < tick.bid:
            return MarketSnapshot(symbol=symbol)
        return MarketSnapshot(
            symbol, float(tick.bid), float(tick.ask), float(tick.ask - tick.bid)
        )

    def point_size(self, symbol: str) -> float:
        """Return the MT5 symbol point size."""
        if not self._select(symbol):
            return 0.00001
        info = self._mt5.symbol_info(symbol)
        if info is None or info.point <= 0:
            return 0.00001
        return float(info.point)

    def symbol_spec(self, symbol: str) -> SymbolSpec | None:  # pylint: disable=too-many-return-statements
        """Read tick economics and volume limits from MT5."""
        if not self._select(symbol):
            return None
        info = self._mt5.symbol_info(symbol)
        if info is None:
            return None
        fields = (
            info.point, info.digits, info.trade_tick_size, info.trade_tick_value,
            info.volume_min, info.volume_max, info.volume_step,
        )
        if any(value is None for value in fields):
            return None
        if info.point <= 0 or info.trade_tick_size <= 0:
            return None
        if info.trade_tick_value <= 0 or info.volume_min <= 0:
            return None
        if info.volume_max < info.volume_min or info.volume_step <= 0:
            return None
        return SymbolSpec(
            float(info.point), int(info.digits), float(info.trade_tick_size),
            float(info.trade_tick_value), float(info.volume_min),
            float(info.volume_max), float(info.volume_step),
        )

    def candles(
        self, symbol: str, timeframe: str = "M15", count: int = 150
    ) -> list[Candle]:
        """Read historical OHLCV candles from MetaTrader 5."""
        if not self._select(symbol) or count <= 0:
            return []
        tf_name = self.TIMEFRAMES.get(timeframe.upper())
        if tf_name is None:
            return []
        rates = self._mt5.copy_rates_from_pos(
            symbol, getattr(self._mt5, tf_name), 0, count
        )
        if rates is None:
            return []
        candles = [
            Candle(
                int(rate["time"]), float(rate["open"]), float(rate["high"]),
                float(rate["low"]), float(rate["close"]), float(rate["tick_volume"]),
            )
            for rate in rates
        ]
        return sorted(candles, key=lambda candle: candle.time)

    def close(self) -> None:
        """Shut down the MetaTrader 5 connection."""
        if self._mt5 is not None:
            self._mt5.shutdown()
            self._mt5 = None
