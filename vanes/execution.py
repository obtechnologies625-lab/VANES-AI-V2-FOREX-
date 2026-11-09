"""Slippage-aware order routing and splitting for live execution.

A strategy can be right and still lose money to transaction costs. This planner
breaks a target size into broker-valid child slices and estimates the slippage
budget, deferring execution when the live spread would erode the edge.
"""

from dataclasses import dataclass
from math import ceil, floor


@dataclass(frozen=True)
class ExecutionPlan:
    """A routable set of child order slices plus cost estimate."""

    slices: tuple[float, ...]
    estimated_slippage_points: float
    deferred: bool
    reason: str

    @property
    def total_volume(self) -> float:
        """Return the summed child-slice volume."""
        return sum(self.slices)


def plan_order(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    size: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
    spread_points: float,
    slippage_budget_points: float,
    max_slices: int = 4,
    impact_coefficient: float = 0.5,
) -> ExecutionPlan:
    """Split ``size`` into broker-valid slices within the slippage budget."""
    if size <= 0 or volume_min <= 0 or volume_step <= 0 or volume_max <= 0:
        return ExecutionPlan((), 0.0, True, "Invalid size or broker volumes")
    if spread_points > slippage_budget_points:
        return ExecutionPlan(
            (), 0.0, True, "Spread exceeds slippage budget; execution deferred"
        )

    stepped = floor(size / volume_step + 1e-12) * volume_step
    if stepped < volume_min:
        return ExecutionPlan((), 0.0, True, "Size below broker minimum volume")

    count = min(max_slices, max(1, ceil(stepped / volume_max)))
    base = floor(stepped / count / volume_step + 1e-12) * volume_step
    base = max(base, volume_min)
    slices: list[float] = []
    remaining = stepped
    for _ in range(count):
        chunk = min(base, remaining)
        if chunk < volume_min:
            break
        slices.append(round(chunk, 10))
        remaining = round(remaining - chunk, 10)
    if remaining >= volume_min and slices:
        slices[-1] = round(slices[-1] + remaining, 10)
    if not slices:
        return ExecutionPlan((), 0.0, True, "Unable to slice within broker limits")

    half_spread = spread_points / 2.0
    impact = impact_coefficient * (stepped / volume_max)
    return ExecutionPlan(
        tuple(slices),
        round(half_spread + impact, 4),
        False,
        f"{len(slices)} slice(s) within slippage budget",
    )
