"""Desktop observer UI for VANES-AI V2."""

import tkinter as tk

from .audit import AuditLogger
from .config import AppConfig
from .market import atr
from .paper import PaperTrader
from .platform import PlatformAdapter
from .risk import build_risk_plan, position_size_from_tick, validate_trade_risk
from .strategy import RuleBasedStrategy


class Overlay:  # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
    """Display live VANES analysis without executing broker orders."""

    def __init__(
        self,
        config: AppConfig,
        adapter: PlatformAdapter,
        strategy: RuleBasedStrategy,
        bridge=None,
        audit: AuditLogger | None = None,
        paper: PaperTrader | None = None,
    ):
        """Create the always-on-top observer window."""
        self.config = config
        self.adapter = adapter
        self.strategy = strategy
        self.bridge = bridge
        self.audit = audit
        self.paper = paper
        self.last_signal = None

        self.root = tk.Tk()
        self.root.title("VANES-AI V2 • FOREX")
        self.root.geometry(f"{config.overlay_width}x{config.overlay_height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", config.always_on_top)

        tk.Label(
            self.root, text="VANES-AI V2 • FOREX",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(12, 2))
        self.status = tk.Label(self.root, text="Connecting…")
        self.status.pack()
        self.signal = tk.Label(
            self.root, text="WAIT", font=("Segoe UI", 30, "bold")
        )
        self.signal.pack(pady=5)
        self.confidence = tk.Label(self.root, text="Confidence: —")
        self.confidence.pack()
        self.reason = tk.Label(
            self.root, text="Collecting market data",
            wraplength=390, justify="center",
        )
        self.reason.pack(padx=15, pady=5)
        self.quote = tk.Label(
            self.root, text="Bid: —   Ask: —   Spread: —"
        )
        self.quote.pack(pady=5)
        self.risk = tk.Label(
            self.root, text="Risk plan: —",
            wraplength=390, justify="center",
        )
        self.risk.pack(pady=4)
        self.paper_status = tk.Label(
            self.root, text="Paper: —", wraplength=390, justify="center"
        )
        self.paper_status.pack(pady=2)
        tk.Label(
            self.root,
            text="OBSERVING • PAPER ONLY • NO BROKER ORDERS",
            font=("Segoe UI", 8),
        ).pack(side="bottom", pady=8)
        self.root.after(100, self.refresh)

    def refresh(self):
        """Refresh quotes, analysis, risk reference, and bridge state."""
        snapshot = self.adapter.snapshot(self.config.symbol)
        candles = self.adapter.candles(
            self.config.symbol, self.config.timeframe, self.config.candle_count
        )
        confirmation = self.adapter.candles(
            self.config.symbol,
            self.config.confirmation_timeframe,
            self.config.candle_count,
        )
        point_size = self.adapter.point_size(self.config.symbol)
        spread_points = None
        if snapshot.spread is not None and point_size > 0:
            spread_points = snapshot.spread / point_size
        guidance = self.strategy.evaluate(
            candles, spread_points=spread_points, confirmation=confirmation
        )

        stop_loss = take_profit = size = 0.0
        atr_value = atr(candles, self.strategy.config.atr_period)
        if (
            atr_value
            and guidance.direction.value in ("BUY", "SELL")
            and snapshot.bid
        ):
            entry = (
                snapshot.ask if guidance.direction.value == "BUY"
                else snapshot.bid
            )
            plan = build_risk_plan(entry, guidance.direction.value, atr_value)
            if plan:
                stop_loss, take_profit = plan.stop_loss, plan.take_profit
                spec = self.adapter.symbol_spec(self.config.symbol)
                if spec:
                    size = position_size_from_tick(
                        self.config.account_balance,
                        self.config.risk_percent,
                        plan.risk_distance,
                        spec.tick_size,
                        spec.tick_value,
                        spec.volume_min,
                        spec.volume_max,
                        spec.volume_step,
                    )
                    risk_check = validate_trade_risk(
                        self.config.account_balance,
                        self.config.risk_percent,
                        plan.risk_distance,
                        size,
                        self.paper.daily_pnl if self.paper else 0.0,
                        self.config.account_balance
                        * self.config.max_daily_loss_percent / 100.0,
                        spread_points,
                        self.config.max_spread_points,
                        spec.tick_size,
                        spec.tick_value,
                    )
                else:
                    size = 0.0
                    risk_check = validate_trade_risk(
                        self.config.account_balance,
                        self.config.risk_percent,
                        plan.risk_distance,
                        0.0,
                        max_daily_loss=self.config.account_balance
                        * self.config.max_daily_loss_percent / 100.0,
                    )
                digits = spec.digits if spec else max(
                    0, len(f"{point_size:.10f}".rstrip("0").split(".")[-1])
                )
                self.risk.config(
                    text=(
                        f"Reference SL: {stop_loss:.{digits}f}  "
                        f"TP: {take_profit:.{digits}f}\n"
                        f"Risk size reference: {size:.4f}  "
                        f"R:R {plan.risk_reward:.1f}:1\n"
                        f"Risk gate: {risk_check.reason}"
                    )
                )
        else:
            self.risk.config(text="Risk plan: no active setup")

        if guidance.direction.value != self.last_signal:
            self.last_signal = guidance.direction.value
            if self.audit:
                self.audit.write(
                    "guidance",
                    symbol=self.config.symbol,
                    direction=guidance.direction.value,
                    confidence=guidance.confidence,
                    reason=guidance.reason,
                )

        if self.paper:
            self.paper_status.config(
                text=(
                    f"Paper balance: {self.paper.balance:.2f}  "
                    f"Daily P/L: {self.paper.daily_pnl:.2f}"
                )
            )

        self.signal.config(text=guidance.direction.value)
        self.confidence.config(text=f"Confidence: {guidance.confidence:.0%}")
        self.reason.config(text=guidance.reason)

        if snapshot.bid is None:
            self.status.config(text=f"{self.config.platform}: waiting")
            self.quote.config(text="Bid: —   Ask: —   Spread: —")
        else:
            self.status.config(text=f"{self.config.platform}: connected")
            self.quote.config(
                text=(
                    f"Bid: {snapshot.bid:.5f}   "
                    f"Ask: {snapshot.ask:.5f}   "
                    f"Spread: {snapshot.spread:.5f}"
                )
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
                paper_balance=self.paper.balance if self.paper else 0.0,
                paper_daily_pnl=self.paper.daily_pnl if self.paper else 0.0,
                paper_open_trades=len(self.paper.trades) if self.paper else 0,
            )

        self.root.after(self.config.refresh_ms, self.refresh)

    def run(self):
        """Start the Tkinter event loop."""
        self.root.mainloop()
