"""Historical replay engine for VANES strategy validation."""

from dataclasses import dataclass
from math import isfinite

from .market import Candle, atr
from .risk import build_risk_plan, position_size
from .signals import Direction
from .strategy import RuleBasedStrategy


@dataclass(frozen=True)
class BacktestConfig:  # pylint: disable=too-many-instance-attributes
    """Configure deterministic, single-symbol historical replay."""

    starting_balance: float = 10_000.0
    risk_percent: float = 1.0
    stop_atr: float = 1.5
    reward_ratio: float = 2.0
    value_per_price_unit: float = 1.0
    spread_points: float | None = None
    max_trades: int | None = None


@dataclass(frozen=True)
class BacktestTrade:  # pylint: disable=too-many-instance-attributes
    """Record one completed historical trade."""

    direction: str
    opened_at: int
    closed_at: int
    entry: float
    exit_price: float
    stop_loss: float
    take_profit: float
    size: float
    pnl: float
    reason: str


@dataclass(frozen=True)
class BacktestReport:  # pylint: disable=too-many-instance-attributes
    """Summarize deterministic historical strategy performance."""

    starting_balance: float
    ending_balance: float
    net_pnl: float
    return_percent: float
    trade_count: int
    wins: int
    losses: int
    win_rate_percent: float
    gross_profit: float
    gross_loss: float
    profit_factor: float | None
    max_drawdown: float
    max_drawdown_percent: float
    trades: tuple[BacktestTrade, ...]


def _pnl(direction: Direction, entry: float, exit_price: float, size: float) -> float:
    """Calculate normalized trade P/L."""
    multiplier = 1.0 if direction == Direction.BUY else -1.0
    return (exit_price - entry) * size * multiplier


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
def run_backtest(
    candles: list[Candle],
    strategy: RuleBasedStrategy | None = None,
    config: BacktestConfig | None = None,
) -> BacktestReport:
    """Replay candles without look-ahead and without broker order submission."""
    cfg = config or BacktestConfig()
    engine = strategy or RuleBasedStrategy()

    if cfg.starting_balance <= 0:
        raise ValueError("starting_balance must be positive")
    if cfg.risk_percent <= 0 or cfg.value_per_price_unit <= 0:
        raise ValueError("risk settings must be positive")
    if len(candles) < 2:
        return _empty_report(cfg.starting_balance)

    balance = cfg.starting_balance
    peak = balance
    max_drawdown = 0.0
    max_drawdown_percent = 0.0
    trades: list[BacktestTrade] = []
    open_trade = None

    for index in range(1, len(candles)):
        candle = candles[index]

        if open_trade is not None:
            exit_price = None
            reason = None
            if open_trade["direction"] == Direction.BUY:
                if candle.low <= open_trade["stop_loss"]:
                    exit_price, reason = open_trade["stop_loss"], "STOP"
                elif candle.high >= open_trade["take_profit"]:
                    exit_price, reason = open_trade["take_profit"], "TARGET"
            else:
                if candle.high >= open_trade["stop_loss"]:
                    exit_price, reason = open_trade["stop_loss"], "STOP"
                elif candle.low <= open_trade["take_profit"]:
                    exit_price, reason = open_trade["take_profit"], "TARGET"

            if exit_price is not None:
                pnl = _pnl(
                    open_trade["direction"],
                    open_trade["entry"],
                    exit_price,
                    open_trade["size"],
                )
                balance += pnl
                trades.append(
                    BacktestTrade(
                        open_trade["direction"].value,
                        open_trade["opened_at"],
                        candle.time,
                        open_trade["entry"],
                        exit_price,
                        open_trade["stop_loss"],
                        open_trade["take_profit"],
                        open_trade["size"],
                        pnl,
                        reason,
                    )
                )
                open_trade = None
                peak = max(peak, balance)
                drawdown = peak - balance
                max_drawdown = max(max_drawdown, drawdown)
                max_drawdown_percent = max(
                    max_drawdown_percent,
                    drawdown / peak * 100.0 if peak > 0 else 0.0,
                )

        if open_trade is not None:
            continue
        if cfg.max_trades is not None and len(trades) >= cfg.max_trades:
            break

        history = candles[:index]
        guidance = engine.evaluate(history, spread_points=cfg.spread_points)
        if guidance.direction == Direction.WAIT:
            continue

        atr_value = atr(history, engine.config.atr_period)
        if atr_value is None:
            continue

        entry = candle.open
        plan = build_risk_plan(
            entry,
            guidance.direction.value,
            atr_value,
            stop_atr=cfg.stop_atr,
            reward_ratio=cfg.reward_ratio,
        )
        if plan is None:
            continue

        size = position_size(
            balance,
            cfg.risk_percent,
            plan.risk_distance,
            cfg.value_per_price_unit,
        )
        if not isfinite(size) or size <= 0:
            continue

        open_trade = {
            "direction": guidance.direction,
            "entry": entry,
            "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit,
            "size": size,
            "opened_at": candle.time,
        }

    if open_trade is not None:
        final = candles[-1]
        pnl = _pnl(
            open_trade["direction"],
            open_trade["entry"],
            final.close,
            open_trade["size"],
        )
        balance += pnl
        trades.append(
            BacktestTrade(
                open_trade["direction"].value,
                open_trade["opened_at"],
                final.time,
                open_trade["entry"],
                final.close,
                open_trade["stop_loss"],
                open_trade["take_profit"],
                open_trade["size"],
                pnl,
                "END",
            )
        )
        peak = max(peak, balance)
        drawdown = peak - balance
        max_drawdown = max(max_drawdown, drawdown)
        max_drawdown_percent = max(
            max_drawdown_percent,
            drawdown / peak * 100.0 if peak > 0 else 0.0,
        )

    return _build_report(
        cfg.starting_balance,
        balance,
        trades,
        max_drawdown,
        max_drawdown_percent,
    )


def _empty_report(starting_balance: float) -> BacktestReport:
    """Build a valid empty report."""
    return _build_report(starting_balance, starting_balance, [], 0.0, 0.0)


def _build_report(
    starting_balance: float,
    ending_balance: float,
    trades: list[BacktestTrade],
    max_drawdown: float,
    max_drawdown_percent: float,
) -> BacktestReport:
    """Calculate aggregate backtest metrics."""
    wins = sum(1 for trade in trades if trade.pnl > 0)
    losses = sum(1 for trade in trades if trade.pnl < 0)
    gross_profit = sum(max(trade.pnl, 0.0) for trade in trades)
    gross_loss = sum(min(trade.pnl, 0.0) for trade in trades)
    profit_factor = (
        gross_profit / abs(gross_loss) if gross_loss < 0 else None
    )
    count = len(trades)
    win_rate = wins / count * 100.0 if count else 0.0
    net_pnl = ending_balance - starting_balance
    return BacktestReport(
        starting_balance,
        ending_balance,
        net_pnl,
        net_pnl / starting_balance * 100.0,
        count,
        wins,
        losses,
        win_rate,
        gross_profit,
        gross_loss,
        profit_factor,
        max_drawdown,
        max_drawdown_percent,
        tuple(trades),
    )
