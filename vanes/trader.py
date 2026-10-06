"""Live MetaTrader 5 order dispatch for SERVER_A tier subscribers."""  # pylint: disable=duplicate-code

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OrderResult:  # pylint: disable=too-many-instance-attributes  # pylint: disable=too-many-instance-attributes
    """Outcome of a single order attempt."""

    success: bool
    ticket: int
    symbol: str
    direction: str
    volume: float
    price: float
    sl: float
    tp: float
    message: str


@dataclass
class ActivePosition:  # pylint: disable=too-many-instance-attributes  # pylint: disable=too-many-instance-attributes
    """Track an open SERVER_A position."""

    ticket: int
    symbol: str
    direction: int
    volume: float
    open_price: float
    sl: float
    tp: float
    opened_at: float


class MT5Trader:
    """Place and track live MT5 orders for authenticated SERVER_A clients."""

    def __init__(self, adapter):
        self._adapter = adapter
        self._mt5 = None
        self._positions: dict[int, ActivePosition] = {}
        self._last_error = ""

    def connect(self) -> bool:
        """Initialize the live trading interface."""
        if self._adapter is None:
            self._last_error = "No platform adapter configured"
            return False
        try:
            import MetaTrader5 as mt5  # pylint: disable=import-outside-toplevel
            self._mt5 = mt5
            self._last_error = ""
            return True
        except ImportError:
            self._last_error = "MetaTrader5 package is not installed"
            return False

    @property
    def last_error(self) -> str:
        """Return the most recent error message."""
        return self._last_error

    def place_order(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        symbol: str,
        direction: str,
        volume: float,
        sl: float,
        tp: float,
        comment: str = "VANES-AI SERVER_A",
    ) -> OrderResult:
        """Place a live market order if the adapter and symbol are ready."""
        if self._mt5 is None:
            self._last_error = "MT5 trading interface not initialized"
            return OrderResult(False, 0, symbol, direction, 0.0, 0.0, 0.0, 0.0, self._last_error)
        if not symbol:
            self._last_error = "Empty symbol"
            return OrderResult(False, 0, symbol, direction, 0.0, 0.0, 0.0, 0.0, self._last_error)
        if not self._adapter._select(symbol):  # pylint: disable=protected-access
            self._last_error = f"Symbol {symbol} not selected or unavailable"
            return OrderResult(False, 0, symbol, direction, 0.0, 0.0, 0.0, 0.0, self._last_error)
        tick = self._mt5.symbol_info_tick(symbol)
        if tick is None or tick.bid <= 0 or tick.ask <= 0:
            self._last_error = f"No live tick for {symbol}"
            return OrderResult(False, 0, symbol, direction, 0.0, 0.0, 0.0, 0.0, self._last_error)
        order_type = (
            self._mt5.ORDER_TYPE_BUY
            if direction.upper() == "BUY"
            else self._mt5.ORDER_TYPE_SELL
        )
        price = float(tick.ask if direction.upper() == "BUY" else tick.bid)
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": float(sl),
            "tp": float(tp),
            "deviation": 10,
            "magic": 314159,
            "comment": comment,
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_FOK,
        }
        result = self._mt5.order_send(request)
        if result is None or result.retcode != self._mt5.TRADE_RETCODE_DONE:
            msg = (
                result.comment if result else "order_send returned None"
            )
            self._last_error = f"Order failed: {msg}"
            return OrderResult(False, 0, symbol, direction, 0.0, price, sl, tp, self._last_error)
        ticket = int(result.order)
        self._positions[ticket] = ActivePosition(
            ticket=ticket,
            symbol=symbol,
            direction=order_type,
            volume=float(volume),
            open_price=float(result.price),
            sl=float(sl),
            tp=float(tp),
            opened_at=time.time(),
        )
        self._last_error = ""
        return OrderResult(
            success=True,
            ticket=ticket,
            symbol=symbol,
            direction=direction,
            volume=float(volume),
            price=float(result.price),
            sl=float(sl),
            tp=float(tp),
            message="Order placed",
        )

    def close_position(self, ticket: int) -> OrderResult:
        """Close an open position by ticket."""
        if self._mt5 is None:
            self._last_error = "MT5 trading interface not initialized"
            return OrderResult(False, 0, "", "", 0.0, 0.0, 0.0, 0.0, self._last_error)
        position = self._positions.get(ticket)
        if position is None:
            self._last_error = f"Unknown ticket {ticket}"
            return OrderResult(False, 0, "", "", 0.0, 0.0, 0.0, 0.0, self._last_error)
        tick = self._mt5.symbol_info_tick(position.symbol)
        if tick is None or tick.bid <= 0 or tick.ask <= 0:
            self._last_error = f"No live tick for {position.symbol}"
            return OrderResult(
                False, ticket, position.symbol, "", 0.0, 0.0, 0.0, 0.0, self._last_error
            )
        close_price = float(
            tick.bid if position.direction == self._mt5.ORDER_TYPE_BUY else tick.ask
        )
        request = {
            "action": self._mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": (
                self._mt5.ORDER_TYPE_SELL
                if position.direction == self._mt5.ORDER_TYPE_BUY
                else self._mt5.ORDER_TYPE_BUY
            ),
            "position": ticket,
            "price": close_price,
            "deviation": 10,
            "magic": 314159,
            "comment": "VANES-AI SERVER_A close",
            "type_time": self._mt5.ORDER_TIME_GTC,
            "type_filling": self._mt5.ORDER_FILLING_FOK,
        }
        result = self._mt5.order_send(request)
        if result is None or result.retcode != self._mt5.TRADE_RETCODE_DONE:
            msg = result.comment if result else "order_send returned None"
            self._last_error = f"Close failed: {msg}"
            return OrderResult(
                False, ticket, position.symbol, "", position.volume,
                close_price, 0.0, 0.0, self._last_error
            )
        self._positions.pop(ticket, None)
        self._last_error = ""
        return OrderResult(
            success=True,
            ticket=ticket,
            symbol=position.symbol,
            direction="CLOSE",
            volume=position.volume,
            price=float(result.price),
            sl=0.0,
            tp=0.0,
            message="Position closed",
        )

    def sync_positions(self) -> list[dict[str, Any]]:
        """Sync open positions from MT5 into the local tracker."""
        if self._mt5 is None:
            return []
        positions = self._mt5.positions_get()
        if positions is None:
            return []
        self._positions.clear()
        for pos in positions:
            self._positions[int(pos.ticket)] = ActivePosition(
                ticket=int(pos.ticket),
                symbol=pos.symbol,
                direction=int(pos.type),
                volume=float(pos.volume),
                open_price=float(pos.price_open),
                sl=float(pos.sl),
                tp=float(pos.tp),
                opened_at=float(pos.time),
            )
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "direction": "BUY" if p.direction == self._mt5.ORDER_TYPE_BUY else "SELL",
                "volume": p.volume,
                "open_price": p.open_price,
                "sl": p.sl,
                "tp": p.tp,
                "opened_at": p.opened_at,
            }
            for p in self._positions.values()
        ]
