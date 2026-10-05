"""Desktop observer UI for VANES-AI V2."""

import os
import tkinter as tk

from PIL import Image, ImageTk

from .alerts import AlertEngine
from .audit import AuditLogger
from .cloud import CloudStatePublisher, CloudPublishResult
from .config import AppConfig
from .market import atr
from .paper import PaperTrader
from .platform import PlatformAdapter
from .risk import build_risk_plan, position_size_from_tick, validate_trade_risk
from .screen import ScreenObserver, next_step
from .strategy import RuleBasedStrategy


class Overlay:  # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
    """Display live VANES analysis, secure pipeline status, and tier-based alerts."""

    def __init__(
        self,
        config: AppConfig,
        adapter: PlatformAdapter,
        strategy: RuleBasedStrategy,
        bridge=None,
        audit: AuditLogger | None = None,
        paper: PaperTrader | None = None,
        cloud_publisher: CloudStatePublisher | None = None,
        secure_client=None,
        audio_capture=None,
        screen_capture=None,
        aggregator=None,
        trader=None,
    ):
        """Create the always-on-top observer window."""
        self.config = config
        self.adapter = adapter
        self.strategy = strategy
        self.bridge = bridge
        self.audit = audit
        self.paper = paper
        self.cloud_publisher = cloud_publisher
        self.secure_client = secure_client
        self.audio_capture = audio_capture
        self.screen_capture = screen_capture
        self.aggregator = aggregator
        self.trader = trader
        self.last_signal = None
        self.alerts = AlertEngine()
        self.screen_observer = ScreenObserver()
        self._alert_queue: list[str] = []
        self._last_cloud_error = ""

        self.root = tk.Tk()
        self.root.title("VANES-AI V2 • FOREX")
        self.root.geometry(f"{config.overlay_width}x{config.overlay_height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", config.always_on_top)
        self._set_window_icon()

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
        self.broker_status = tk.Label(
            self.root, text="Broker spec: waiting",
            wraplength=390, justify="center"
        )
        self.broker_status.pack(pady=2)
        self.screen_status = tk.Label(
            self.root, text="Screen: observing desktop context",
            wraplength=390, justify="center"
        )
        self.screen_status.pack(pady=2)
        self.next_step = tk.Label(
            self.root, text="Next step: preparing visual guidance",
            wraplength=390, justify="center"
        )
        self.next_step.pack(pady=2)
        self.tier_label = tk.Label(
            self.root,
            text=f"TIER: {config.subscription_tier}",
            font=("Segoe UI", 8),
        )
        self.tier_label.pack(pady=2)
        self.error_banner = tk.Label(
            self.root,
            text="",
            bg="#2b1218",
            fg="#ffb3b8",
            wraplength=390,
            justify="center",
        )
        self.error_banner.pack(pady=2)
        self.cloud_status = tk.Label(
            self.root,
            text="Cloud: disabled",
            font=("Segoe UI", 8),
        )
        self.cloud_status.pack(pady=2)
        self.trader_status = tk.Label(
            self.root,
            text="Trader: inactive",
            font=("Segoe UI", 8),
        )
        self.trader_status.pack(pady=2)
        tk.Label(
            self.root,
            text="OBSERVING • PAPER ONLY • NO BROKER ORDERS",
            font=("Segoe UI", 8),
        ).pack(side="bottom", pady=8)
        self.root.after(100, self.refresh)

    def _set_window_icon(self) -> None:
        """Set the window icon from the project logo if available."""
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "..", "icon.svg"
            )
            image = Image.open(icon_path)
            icon = ImageTk.PhotoImage(image)
            self.root.iconphoto(True, icon)
            self._icon_image = icon
        except (OSError, ImportError, Exception):
            pass

    def _show_error_banner(self, message: str) -> None:
        """Display a red error banner in the overlay."""
        self.error_banner.config(text=f"ERROR: {message}" if message else "")
        if message:
            self.root.after(5000, lambda: self.error_banner.config(text=""))

    def _show_alert(self, message: str) -> None:
        """Queue a transparent alert text notification."""
        self._alert_queue.append(message)
        if len(self._alert_queue) > 3:
            self._alert_queue.pop(0)
        self._render_alerts()

    def _render_alerts(self) -> None:
        """Render queued alerts as transparent overlay text."""
        text = " | ".join(self._alert_queue)
        if text:
            self.root.title(f"ALERT: {text}")
        else:
            self.root.title("VANES-AI V2 • FOREX")

    def _update_trader_status(self) -> None:
        """Update the trader status label."""
        if self.trader is None:
            self.trader_status.config(text="Trader: inactive")
        elif self.config.subscription_tier == "SERVER_A":
            self.trader_status.config(text="Trader: SERVER_A LIVE")
        else:
            self.trader_status.config(text="Trader: tier locked")

    def refresh(self):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """Refresh quotes, analysis, risk reference, and bridge state."""
        audio_chunks = []
        screen_frames = []
        if self.audio_capture:
            chunk = self.audio_capture.capture()
            if chunk:
                audio_chunks.append(chunk)
        if self.screen_capture:
            frame = self.screen_capture.capture()
            if frame:
                screen_frames.append(frame)
        screen = self.screen_observer.observe()
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
        risk_gate = "WAITING"
        spec = self.adapter.symbol_spec(self.config.symbol)
        if spec:
            self.broker_status.config(
                text=(
                    f"Broker spec: ready • point {spec.point:g} • "
                    f"tick {spec.tick_size:g}/{spec.tick_value:g} • "
                    f"volume {spec.volume_min:g}-{spec.volume_max:g}"
                )
            )
        else:
            self.broker_status.config(
                text="Broker spec: unavailable • risk sizing blocked"
            )

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
                risk_gate = "PASS" if risk_check.allowed else "BLOCK"
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

        stale = snapshot.bid is None or snapshot.ask is None
        new_alerts = self.alerts.evaluate(
            guidance.direction.value, guidance.confidence, risk_gate, stale
        )
        for alert in new_alerts:
            if self.audit:
                self.audit.write(
                    "alert",
                    symbol=self.config.symbol,
                    kind=alert.kind,
                    message=alert.message,
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
        self.screen_status.config(text=f"Screen: {screen.summary}")
        self.next_step.config(
            text=f"Next step: {next_step(screen, guidance.direction.value)}"
        )

        digits = spec.digits if spec else max(
            0, len(f"{point_size:.10f}".rstrip("0").split(".")[-1])
        )
        if snapshot.bid is None or snapshot.ask is None:
            self.status.config(text=f"{self.config.platform}: waiting")
            self.quote.config(text="Bid: —   Ask: —   Spread: —")
        else:
            self.status.config(
                text=(
                    f"{self.config.platform}: connected • "
                    f"point {point_size:g}"
                )
            )
            spread_text = "unavailable"
            if snapshot.spread is not None:
                spread_text = f"{snapshot.spread:.{digits}f}"
                if spread_points is not None:
                    spread_text += f" ({spread_points:.1f} pt)"
            self.quote.config(
                text=(
                    f"Bid: {snapshot.bid:.{digits}f}   "
                    f"Ask: {snapshot.ask:.{digits}f}   "
                    f"Spread: {spread_text}"
                )
            )

        if self.bridge:
            diagnostics = self.strategy.diagnostics(candles)
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
                paper_open_trades=(
                    sum(1 for trade in self.paper.trades if trade.closed_at is None)
                    if self.paper else 0
                ),
                broker_ready=spec is not None,
                risk_gate=risk_gate,
                point_size=point_size,
                analysis=diagnostics,
                timeframe=self.config.timeframe,
                confirmation_timeframe=self.config.confirmation_timeframe,
                candles=[
                    {
                        "time": candle.time,
                        "open": candle.open,
                        "high": candle.high,
                        "low": candle.low,
                        "close": candle.close,
                        "volume": candle.volume,
                    }
                    for candle in candles[-200:]
                ],
                mt5_connected=snapshot.bid is not None and snapshot.ask is not None,
                screen_context=screen.summary,
                mt5_screen_active=screen.mt5_active,
                suggested_next_step=next_step(screen, guidance.direction.value),
            )
        if self.cloud_publisher:
            state_payload = {
                "symbol": self.config.symbol,
                "direction": guidance.direction.value,
                "confidence": guidance.confidence,
                "bid": snapshot.bid or 0.0,
                "ask": snapshot.ask or 0.0,
                "spread": snapshot.spread or 0.0,
                "reason": guidance.reason,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "paper_balance": self.paper.balance if self.paper else 0.0,
                "paper_daily_pnl": self.paper.daily_pnl if self.paper else 0.0,
                "alerts": [
                    {"kind": alert.kind, "message": alert.message}
                    for alert in new_alerts
                ],
                "paper_open_trades": (
                    sum(1 for trade in self.paper.trades
                        if trade.closed_at is None)
                    if self.paper else 0
                ),
                "paper_trades": [
                    {
                        "direction": trade.direction,
                        "entry": trade.entry,
                        "stop_loss": trade.stop_loss,
                        "take_profit": trade.take_profit,
                        "size": trade.size,
                        "opened_at": trade.opened_at,
                        "closed_at": trade.closed_at,
                        "exit_price": trade.exit_price,
                    }
                    for trade in (self.paper.trades[-20:] if self.paper else [])
                ],
                "broker_ready": spec is not None,
                "risk_gate": risk_gate,
                "point_size": point_size,
                "audio_chunks": audio_chunks,
                "screen_frames": screen_frames,
            }
            result = self.cloud_publisher.publish(state_payload)
            if isinstance(result, CloudPublishResult):
                if result.ok:
                    self.cloud_status.config(
                        text=f"Cloud: connected • tier {self.config.subscription_tier}"
                    )
                    if result.analysis:
                        self._show_alert(f"AI: {result.analysis[:120]}")
                else:
                    self.cloud_status.config(text=f"Cloud: {result.error[:40]}")
                    if result.error and result.error != "throttled":
                        self._show_error_banner(result.error[:80])
            else:
                self.cloud_status.config(text="Cloud: published")

        if self.secure_client and self.aggregator:
            packet_state = {
                "symbol": self.config.symbol,
                "direction": guidance.direction.value,
                "confidence": guidance.confidence,
                "bid": snapshot.bid or 0.0,
                "ask": snapshot.ask or 0.0,
                "spread": snapshot.spread or 0.0,
                "reason": guidance.reason,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_gate": risk_gate,
                "broker_ready": spec is not None,
                "paper_balance": self.paper.balance if self.paper else 0.0,
                "paper_daily_pnl": self.paper.daily_pnl if self.paper else 0.0,
                "paper_open_trades": (
                    sum(1 for trade in self.paper.trades
                        if trade.closed_at is None)
                    if self.paper else 0
                ),
                "point_size": point_size,
                "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "audio_chunks": audio_chunks,
                "screen_frames": screen_frames,
            }
            packet = self.aggregator.build_packet(packet_state)
            if packet:
                response = self.secure_client.send_packet(packet)
                if response.ok:
                    self.cloud_status.config(
                        text=f"Cloud: analyzed • tier {self.config.subscription_tier}"
                    )
                    if response.data.get("analysis"):
                        self._show_alert(f"AI: {response.data['analysis'][:120]}")
                    if response.data.get("order_dispatch") == "READY":
                        self._show_alert("SERVER_A: Order dispatch ready")
                else:
                    self.cloud_status.config(text=f"Cloud: {response.error[:40]}")
                    if response.status == 402:
                        self._show_error_banner("PAYWALL: Subscription required")
                    elif response.error:
                        self._show_error_banner(response.error[:80])

        self._update_trader_status()
        if self.trader and self.config.subscription_tier == "SERVER_A":
            positions = self.trader.sync_positions()
            if positions:
                self._show_alert(f"Positions: {len(positions)} open")

        self.root.after(self.config.refresh_ms, self.refresh)

    def run(self):
        """Start the Tkinter event loop."""
        self.root.mainloop()
