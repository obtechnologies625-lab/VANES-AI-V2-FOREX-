import tkinter as tk
from .config import AppConfig
from .market import atr
from .platform import PlatformAdapter
from .risk import build_risk_plan
from .strategy import RuleBasedStrategy

class Overlay:
    """Always-on-top market observer. It provides analysis, not automatic orders."""

    def __init__(self, config: AppConfig, adapter: PlatformAdapter,
                 strategy: RuleBasedStrategy, bridge=None):
        self.config = config
        self.adapter = adapter
        self.strategy = strategy
        self.bridge = bridge

        self.root = tk.Tk()
        self.root.title("VANES-AI V2 • FOREX")
        self.root.geometry(f"{config.overlay_width}x{config.overlay_height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", config.always_on_top)

        tk.Label(self.root, text="VANES-AI V2 • FOREX",
                 font=("Segoe UI", 16, "bold")).pack(pady=(12, 2))
        self.status = tk.Label(self.root, text="Connecting…")
        self.status.pack()
        self.signal = tk.Label(self.root, text="WAIT",
                               font=("Segoe UI", 30, "bold"))
        self.signal.pack(pady=5)
        self.confidence = tk.Label(self.root, text="Confidence: —")
        self.confidence.pack()
        self.reason = tk.Label(self.root, text="Collecting market data",
                               wraplength=390, justify="center")
        self.reason.pack(padx=15, pady=5)
        self.quote = tk.Label(self.root, text="Bid: —   Ask: —   Spread: —")
        self.quote.pack(pady=5)
        self.risk = tk.Label(self.root, text="Risk plan: —",
                             wraplength=390, justify="center")
        self.risk.pack(pady=4)
        tk.Label(self.root, text="OBSERVING • GUIDANCE ONLY • NO AUTO ORDERS",
                 font=("Segoe UI", 8)).pack(side="bottom", pady=8)
        self.root.after(100, self.refresh)

    def refresh(self):
        snapshot = self.adapter.snapshot(self.config.symbol)
        candles = self.adapter.candles(self.config.symbol, self.config.timeframe, 150)
        guidance = self.strategy.evaluate(candles)

        stop_loss = take_profit = 0.0
        atr_value = atr(candles, 14) if len(candles) >= 15 else None
        if atr_value and guidance.direction.value in ("BUY", "SELL") and snapshot.bid:
            entry = snapshot.ask if guidance.direction.value == "BUY" else snapshot.bid
            plan = build_risk_plan(entry, guidance.direction.value, atr_value)
            if plan:
                stop_loss, take_profit = plan.stop_loss, plan.take_profit
                self.risk.config(
                    text=(f"Reference SL: {stop_loss:.5f}  "
                          f"TP: {take_profit:.5f}  R:R {plan.risk_reward:.1f}:1")
                )
        else:
            self.risk.config(text="Risk plan: no active setup")

        self.signal.config(text=guidance.direction.value)
        self.confidence.config(text=f"Confidence: {guidance.confidence:.0%}")
        self.reason.config(text=guidance.reason)

        if snapshot.bid is None:
            self.status.config(text=f"{self.config.platform}: waiting")
            self.quote.config(text="Bid: —   Ask: —   Spread: —")
        else:
            self.status.config(text=f"{self.config.platform}: connected")
            self.quote.config(
                text=(f"Bid: {snapshot.bid:.5f}   Ask: {snapshot.ask:.5f}   "
                      f"Spread: {snapshot.spread:.5f}")
            )

        if self.bridge:
            self.bridge.update(
                symbol=self.config.symbol,
                direction=guidance.direction.value,
                confidence=guidance.confidence,
                bid=snapshot.bid or 0.0,
                ask=snapshot.ask or 0.0,
                spread=snapshot.spread or 0.0,
                reason=guidance.reason,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        self.root.after(self.config.refresh_ms, self.refresh)

    def run(self):
        self.root.mainloop()
