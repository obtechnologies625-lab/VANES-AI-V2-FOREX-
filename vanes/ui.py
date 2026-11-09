"""Desktop observer UI for VANES-AI V2."""

import ctypes
import os
import sys
import tkinter as tk

from PIL import ImageTk

from . import theme
from .alerts import AlertEngine
from .audit import AuditLogger
from .behavior import BehaviorMonitor
from .branding import asset_path, render_icon
from .cloud import CloudStatePublisher, CloudPublishResult
from .config import AppConfig
from .execution import plan_order
from .market import atr
from .paper import PaperTrader
from .platform import PlatformAdapter
from .risk import build_risk_plan, position_size_from_tick, validate_trade_risk
from .screen import ScreenObserver, next_step
from .sentiment import SentimentFeed
from .server_selector import ServerSelectionDialog
from .strategy import RuleBasedStrategy
from .subscription import SubscriptionManager, tier_allows_live


class Overlay:  # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments,too-many-statements
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
        subscription: SubscriptionManager | None = None,
        incubation=None,
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
        self.subscription = subscription
        self.incubation = incubation
        self.sentiment = SentimentFeed()
        self.behavior = BehaviorMonitor()
        self._last_open_trades = 0
        self._last_gate = ""
        self.last_signal = None
        self.alerts = AlertEngine()
        self.screen_observer = ScreenObserver()
        self._alert_queue: list[str] = []
        self._last_cloud_error = ""
        self._last_position_count = -1

        self.root = tk.Tk()
        self.root.title("VANES-AI V2 • FOREX")
        self.root.geometry(f"{config.overlay_width}x{config.overlay_height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", config.always_on_top)
        self.root.configure(bg=theme.BG)
        self._set_window_icon()

        tk.Label(
            self.root, text="⚡ VANES-AI V2 • FOREX",
            font=theme.HEAD_FONT, bg=theme.BG, fg=theme.CYAN,
        ).pack(pady=(12, 2))
        self.status = self._label("Connecting…", fg=theme.MUTED)
        self.status.pack()
        self.signal = tk.Label(
            self.root, text="WAIT", font=theme.BIG_FONT,
            bg=theme.BG, fg=theme.MAGENTA,
        )
        self.signal.pack(pady=5)
        self.confidence = self._label("Confidence: —", fg=theme.OK)
        self.confidence.pack()
        self.reason = self._label(
            "Collecting market data", fg=theme.TEXT, wrap=True
        )
        self.reason.pack(padx=15, pady=5)
        self.quote = self._label(
            "Bid: —   Ask: —   Spread: —", fg=theme.CYAN
        )
        self.quote.pack(pady=5)
        self.risk = self._label("Risk plan: —", fg=theme.TEXT, wrap=True)
        self.risk.pack(pady=4)
        self.paper_status = self._label("Paper: —", fg=theme.TEXT, wrap=True)
        self.paper_status.pack(pady=2)
        self.broker_status = self._label(
            "Broker spec: waiting", fg=theme.MUTED, wrap=True
        )
        self.broker_status.pack(pady=2)
        self.screen_status = self._label(
            "Screen: observing desktop context", fg=theme.MUTED, wrap=True
        )
        self.screen_status.pack(pady=2)
        self.next_step = self._label(
            "Next step: preparing visual guidance", fg=theme.VIOLET, wrap=True
        )
        self.next_step.pack(pady=2)
        self.tier_label = tk.Label(
            self.root,
            text=f"TIER: {config.subscription_tier}",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.GOLD,
        )
        self.tier_label.pack(pady=2)
        self.error_banner = tk.Label(
            self.root,
            text="",
            bg="#2b0713",
            fg=theme.ERR,
            font=theme.SMALL_FONT,
            wraplength=390,
            justify="center",
        )
        self.error_banner.pack(pady=2)
        self.cloud_status = tk.Label(
            self.root,
            text="Cloud: disabled",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MUTED,
        )
        self.cloud_status.pack(pady=2)
        self.trader_status = tk.Label(
            self.root,
            text="Trader: inactive",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MUTED,
        )
        self.trader_status.pack(pady=2)
        self.ml_status = tk.Label(
            self.root,
            text="ML regime: —",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.CYAN,
        )
        self.ml_status.pack(pady=2)
        self.sentiment_status = tk.Label(
            self.root,
            text="Sentiment: NEUTRAL (0 samples)",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MUTED,
        )
        self.sentiment_status.pack(pady=2)
        self.behavior_status = tk.Label(
            self.root,
            text="Behavior: calm (tilt 0)",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MUTED,
            wraplength=390, justify="center",
        )
        self.behavior_status.pack(pady=2)
        self.incubation_status = tk.Label(
            self.root,
            text="Incubation: —",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.GOLD,
        )
        self.incubation_status.pack(pady=2)
        tk.Label(
            self.root,
            text="OBSERVING • PAPER ONLY • NO BROKER ORDERS",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MAGENTA,
        ).pack(side="bottom", pady=(0, 8))
        tk.Label(
            self.root,
            text=f"{theme.TRADEMARK_LINE}  •  {theme.DEVELOPER_EMAIL}",
            font=theme.SMALL_FONT, bg=theme.BG, fg=theme.MUTED,
            wraplength=390, justify="center",
        ).pack(side="bottom", pady=(2, 0))
        self.root.after(100, self.refresh)

    def _label(self, text: str, fg: str, wrap: bool = False) -> tk.Label:
        """Create a neon-themed overlay label."""
        kwargs = {"font": theme.BODY_FONT, "bg": theme.BG, "fg": fg}
        if wrap:
            kwargs.update(wraplength=390, justify="center")
        return tk.Label(self.root, text=text, **kwargs)

    def _set_window_icon(self) -> None:
        """Set the small VANES app icon for the titlebar and Windows taskbar."""
        if sys.platform == "win32":
            self._set_windows_app_id()
            ico = asset_path("vanes_icon.ico")
            if os.path.exists(ico):
                try:
                    self.root.iconbitmap(ico)
                    return
                except tk.TclError:
                    pass
        try:
            icon = ImageTk.PhotoImage(render_icon(64))
            self.root.iconphoto(True, icon)
            self._icon_image = icon
        except (tk.TclError, ImportError, OSError):
            pass

    @staticmethod
    def _set_windows_app_id() -> None:
        """Give Windows a dedicated AppUserModelID so the taskbar shows our icon."""
        try:
            windll = getattr(ctypes, "windll")
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "OBTechnologies.VANES.AI"
            )
        except (AttributeError, OSError):
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
        elif tier_allows_live(self.config.subscription_tier):
            self.trader_status.config(text="Trader: PRO LIVE")
        else:
            self.trader_status.config(text="Trader: tier locked")

    def refresh(self):
        """Refresh the overlay, keeping the update loop alive across errors."""
        try:
            self._refresh_once()
        except tk.TclError:
            return
        except Exception as exc:  # pylint: disable=broad-except
            try:
                self._show_error_banner(f"Refresh failed: {exc}"[:80])
            except tk.TclError:
                return
        self.root.after(self.config.refresh_ms, self.refresh)

    def _refresh_once(self):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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

        open_trades = (
            sum(1 for t in self.paper.trades if t.closed_at is None)
            if self.paper else 0
        )
        if open_trades > self._last_open_trades:
            self.behavior.record_open()
        elif open_trades < self._last_open_trades and self.paper:
            closed = [t for t in self.paper.trades if t.closed_at is not None]
            last_pnl = 0.0
            if closed:
                last = closed[-1]
                multiplier = 1.0 if last.direction == "BUY" else -1.0
                last_pnl = (
                    (last.exit_price or last.entry) - last.entry
                ) * last.size * multiplier
            self.behavior.record_close(last_pnl)
        self._last_open_trades = open_trades

        gate_key = f"{guidance.direction.value}:{risk_gate}"
        if (
            guidance.direction.value in ("BUY", "SELL")
            and risk_gate == "BLOCK"
            and self._last_gate != gate_key
        ):
            self.behavior.record_rule_break("risk gate blocked setup")
        self._last_gate = gate_key

        regime = self.strategy.regime(candles)
        behavior_report = self.behavior.report()
        plan = None
        if spec and size > 0:
            plan = plan_order(
                size,
                spec.volume_min,
                spec.volume_max,
                spec.volume_step,
                spread_points or 0.0,
                self.config.max_spread_points,
            )
        if regime:
            self.ml_status.config(
                text=f"ML regime: {regime[0]} ({regime[1]:.0%})"
            )
        else:
            self.ml_status.config(text="ML regime: collecting data")
        self.sentiment_status.config(
            text=(
                f"Sentiment: {self.sentiment.label} "
                f"({self.sentiment.samples} samples)"
            )
        )
        self.behavior_status.config(
            text=(
                f"Behavior: {', '.join(behavior_report.flags) or 'calm'} "
                f"(tilt {behavior_report.tilt_score})"
                + (
                    f" — {behavior_report.journal_prompt}"
                    if behavior_report.journal_prompt else ""
                )
            )
        )
        if self.incubation:
            incubation_state = self.incubation.status()
            self.incubation_status.config(
                text=(
                    f"Incubation: {incubation_state.days_elapsed}/"
                    f"{incubation_state.required_days} days"
                    f"{' • live unlocked' if incubation_state.complete else ' • live locked'}"
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
                ml_regime=regime[0] if regime else "",
                ml_prob=regime[1] if regime else 0.0,
                sentiment=self.sentiment.snapshot(),
                tilt=behavior_report.tilt_score,
                journal_prompt=behavior_report.journal_prompt,
                execution_slices=list(plan.slices) if plan else [],
                est_slippage=plan.estimated_slippage_points if plan else 0.0,
                incubation=(
                    self.incubation.status().__dict__ if self.incubation else {}
                ),
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
                "updated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
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
                        self._show_alert("PRO: Order dispatch ready")
                else:
                    self.cloud_status.config(text=f"Cloud: {response.error[:40]}")
                    if response.status == 402:
                        self._show_error_banner("PAYWALL: Subscription required")
                    elif response.error:
                        self._show_error_banner(response.error[:80])

        self._update_trader_status()
        if self.trader and tier_allows_live(self.config.subscription_tier):
            positions = self.trader.sync_positions()
            count = len(positions)
            if count != self._last_position_count:
                self._last_position_count = count
                if count:
                    self._show_alert(f"Positions: {count} open")

    def run(self):
        """Start the Tkinter event loop."""
        if self.subscription:
            dialog = ServerSelectionDialog(self.root, self.subscription.tracker)

            def on_select(tier: str) -> None:
                self.subscription.selected_tier = tier
                self.config.subscription_tier = tier
                allowed, reason = self.subscription.can_access()
                if allowed:
                    self.tier_label.config(
                        text=f"TIER: {self.subscription.tier_info().name}"
                    )
                    self._show_alert(f"Server: {reason}")
                else:
                    self._show_error_banner(reason)

            dialog.on_select(on_select)
            selected = dialog.show()
            if not selected:
                self.root.destroy()
                return

            allowed, reason = self.subscription.can_access()
            if not allowed:
                self._show_error_banner(reason)
                self.root.destroy()
                return

            consumed, msg = self.subscription.consume_access()
            if not consumed:
                self._show_error_banner(msg)
                self.root.destroy()
                return

            self.tier_label.config(
                text=f"TIER: {self.subscription.tier_info().name}"
            )
            self._show_alert(f"Connected: {msg}")

        self.root.mainloop()
