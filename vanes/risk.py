from dataclasses import dataclass

@dataclass(frozen=True)
class RiskPlan:
    entry: float
    stop_loss: float
    take_profit: float
    risk_distance: float
    reward_distance: float
    risk_reward: float

def build_risk_plan(entry: float, direction: str, atr_value: float,
                    stop_atr: float = 1.5, reward_ratio: float = 2.0) -> RiskPlan | None:
    if entry <= 0 or atr_value <= 0:
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
    return RiskPlan(entry, stop, target, risk_distance, reward_distance, reward_ratio)
