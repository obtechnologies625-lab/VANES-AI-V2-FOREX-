"""Paper-trading simulation with no broker order routing."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PaperTrade:  # pylint: disable=too-many-instance-attributes
    """Represent a simulated trade."""

    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    size: float
    opened_at: int
    closed_at: int | None = None
    exit_price: float | None = None


class PaperTrader:  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Track simulated trades and enforce a daily loss limit."""

    def __init__(self, starting_balance: float, max_daily_loss: float):
        """Initialize the paper account."""
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.max_daily_loss = max_daily_loss
        self.trades: list[PaperTrade] = []
        self._day = date.today()
        self._daily_pnl = 0.0

    @property
    def daily_pnl(self) -> float:
        """Return realized paper profit or loss for the current day."""
        self._reset_day_if_needed()
        return self._daily_pnl

    def can_open(self) -> bool:
        """Return whether the daily loss limit permits another trade."""
        self._reset_day_if_needed()
        return self._daily_pnl > -abs(self.max_daily_loss)

    def open_trade(
        self,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        size: float,
        opened_at: int,
    ) -> PaperTrade | None:
        """Open a simulated trade when inputs and risk limits are valid."""
        if direction not in {"BUY", "SELL"} or entry <= 0 or size <= 0:
            return None
        if not self.can_open():
            return None
        trade = PaperTrade(
            direction, entry, stop_loss, take_profit, size, opened_at
        )
        self.trades.append(trade)
        return trade

    def close_trade(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, trade: PaperTrade, exit_price: float, closed_at: int
    ) -> float:
        """Close a simulated trade and update balance."""
        if exit_price <= 0 or trade not in self.trades:
            return 0.0
        multiplier = 1.0 if trade.direction == "BUY" else -1.0
        pnl = (exit_price - trade.entry) * trade.size * multiplier
        self.balance += pnl
        self._daily_pnl += pnl
        index = self.trades.index(trade)
        self.trades[index] = PaperTrade(
            trade.direction,
            trade.entry,
            trade.stop_loss,
            trade.take_profit,
            trade.size,
            trade.opened_at,
            closed_at,
            exit_price,
        )
        return pnl

    def _reset_day_if_needed(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self._daily_pnl = 0.0
