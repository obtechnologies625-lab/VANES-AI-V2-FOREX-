"""Risk-reference calculations for VANES guidance."""

from dataclasses import dataclass
from math import floor


@dataclass(frozen=True)
class RiskPlan:
    """Describe a reference entry, stop, target, and reward ratio."""

    entry: float
    stop_loss: float
    take_profit: float
    risk_distance: float
    reward_distance: float
    risk_reward: float


def build_risk_plan(
    entry: float,
    direction: str,
    atr_value: float,
    stop_atr: float = 1.5,
    reward_ratio: float = 2.0,
) -> RiskPlan | None:
    """Build a reference risk plan without submitting an order."""
    if entry <= 0 or atr_value <= 0 or stop_atr <= 0 or reward_ratio <= 0:
        return None
    risk_distance = atr_value * stop_atr
    reward_distance = risk_distance * reward_ratio
    if direction == "BUY":
        stop = entry - risk_distance
        target = entry + reward_distance
    elif direction == "SELL":
        stop = entry + risk_distance
        target = entry - reward_distance
    else:
        return None
    return RiskPlan(
        entry, stop, target, risk_distance, reward_distance, reward_ratio
    )


def position_size(
    balance: float,
    risk_percent: float,
    risk_distance: float,
    value_per_price_unit: float = 1.0,
) -> float:
    """Calculate a reference position size from account risk."""
    if balance <= 0 or risk_percent <= 0 or risk_distance <= 0:
        return 0.0
    if value_per_price_unit <= 0:
        return 0.0
    risk_cash = balance * risk_percent / 100.0
    return risk_cash / (risk_distance * value_per_price_unit)


def position_size_from_tick(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    balance: float,
    risk_percent: float,
    risk_distance: float,
    tick_size: float,
    tick_value: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
) -> float:
    """Calculate broker-aware volume from MT5 tick economics."""
    values = (
        balance, risk_percent, risk_distance, tick_size, tick_value,
        volume_min, volume_max, volume_step,
    )
    if any(value <= 0 for value in values) or volume_max < volume_min:
        return 0.0
    risk_cash = balance * risk_percent / 100.0
    loss_per_lot = risk_distance / tick_size * tick_value
    if loss_per_lot <= 0:
        return 0.0
    raw = risk_cash / loss_per_lot
    stepped = floor(raw / volume_step + 1e-12) * volume_step
    if stepped < volume_min:
        return 0.0
    return min(stepped, volume_max)


def daily_loss_limit(balance: float, percent: float) -> float:
    """Return the maximum allowed daily loss in account currency."""
    if balance <= 0 or percent <= 0:
        return 0.0
    return balance * percent / 100.0
