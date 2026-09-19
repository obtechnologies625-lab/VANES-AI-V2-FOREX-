from dataclasses import dataclass
from .signals import MarketSnapshot

@dataclass
class PlatformStatus:
    connected: bool
    message: str

class PlatformAdapter:
    def connect(self) -> PlatformStatus:
        return PlatformStatus(False, "No platform adapter configured")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        return MarketSnapshot(symbol=symbol)

    def close(self) -> None:
        pass

class MT5Adapter(PlatformAdapter):
    """Read-only MetaTrader 5 market-data adapter."""

    def connect(self) -> PlatformStatus:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            return PlatformStatus(False, "Install MetaTrader5 to connect to MT5")
        if not mt5.initialize():
            return PlatformStatus(False, "MetaTrader 5 initialize() failed")
        self._mt5 = mt5
        return PlatformStatus(True, "Connected to MetaTrader 5")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        if not hasattr(self, "_mt5"):
            return MarketSnapshot(symbol=symbol)
        if not self._mt5.symbol_select(symbol, True):
            return MarketSnapshot(symbol=symbol)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return MarketSnapshot(symbol=symbol)
        return MarketSnapshot(
            symbol=symbol,
            bid=float(tick.bid),
            ask=float(tick.ask),
            spread=float(tick.ask - tick.bid),
        )

    def close(self) -> None:
        if hasattr(self, "_mt5"):
            self._mt5.shutdown()
