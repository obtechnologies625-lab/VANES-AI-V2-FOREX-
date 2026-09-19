from dataclasses import dataclass
from .market import Candle
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

    def candles(self, symbol: str, timeframe: str, count: int = 150) -> list[Candle]:
        return []

    def close(self) -> None:
        pass

class MT5Adapter(PlatformAdapter):
    TIMEFRAMES = {
        "M1": "TIMEFRAME_M1", "M5": "TIMEFRAME_M5", "M15": "TIMEFRAME_M15",
        "M30": "TIMEFRAME_M30", "H1": "TIMEFRAME_H1", "H4": "TIMEFRAME_H4",
        "D1": "TIMEFRAME_D1",
    }

    def connect(self) -> PlatformStatus:
        try:
            import MetaTrader5 as mt5
        except ImportError:
            return PlatformStatus(False, "MetaTrader5 package is not installed")
        if not mt5.initialize():
            return PlatformStatus(False, "MetaTrader 5 initialize() failed")
        self._mt5 = mt5
        return PlatformStatus(True, "Connected to MetaTrader 5")

    def snapshot(self, symbol: str) -> MarketSnapshot:
        if not hasattr(self, "_mt5") or not self._mt5.symbol_select(symbol, True):
            return MarketSnapshot(symbol=symbol)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None:
            return MarketSnapshot(symbol=symbol)
        return MarketSnapshot(
            symbol, float(tick.bid), float(tick.ask),
            float(tick.ask - tick.bid)
        )

    def candles(self, symbol: str, timeframe: str = "M15", count: int = 150) -> list[Candle]:
        if not hasattr(self, "_mt5") or not self._mt5.symbol_select(symbol, True):
            return []
        tf_name = self.TIMEFRAMES.get(timeframe.upper(), "TIMEFRAME_M15")
        rates = self._mt5.copy_rates_from_pos(
            symbol, getattr(self._mt5, tf_name), 0, count
        )
        if rates is None:
            return []
        return [
            Candle(
                int(r["time"]), float(r["open"]), float(r["high"]),
                float(r["low"]), float(r["close"]), float(r["tick_volume"])
            )
            for r in rates
        ]

    def close(self) -> None:
        if hasattr(self, "_mt5"):
            self._mt5.shutdown()
