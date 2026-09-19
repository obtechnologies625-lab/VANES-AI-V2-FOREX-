import tkinter as tk

from .config import AppConfig
from .platform import PlatformAdapter
from .signals import SignalEngine

class Overlay:
    """Always-on-top desktop observer panel; no automatic order execution."""

    def __init__(self, config: AppConfig, adapter: PlatformAdapter):
        self.config = config
        self.adapter = adapter
        self.engine = SignalEngine()

        self.root = tk.Tk()
        self.root.title("VANES-AI V2 • FOREX")
        self.root.geometry(f"{config.overlay_width}x{config.overlay_height}")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", config.always_on_top)

        tk.Label(
            self.root, text="VANES-AI V2 • FOREX",
            font=("Segoe UI", 15, "bold")
        ).pack(pady=(12, 3))

        self.status = tk.Label(self.root, text="Connecting…")
        self.status.pack()

        self.signal = tk.Label(
            self.root, text="WAIT",
            font=("Segoe UI", 28, "bold")
        )
        self.signal.pack(pady=7)

        self.reason = tk.Label(
            self.root, text="Waiting for market data",
            wraplength=340
        )
        self.reason.pack(padx=12)

        self.quote = tk.Label(
            self.root, text="Bid: —   Ask: —   Spread: —"
        )
        self.quote.pack(pady=9)

        tk.Label(
            self.root,
            text="OBSERVING • GUIDANCE ONLY • NO AUTO ORDERS",
            font=("Segoe UI", 8)
        ).pack(side="bottom", pady=8)

        self.root.after(100, self.refresh)

    def refresh(self):
        snapshot = self.adapter.snapshot(self.config.symbol)
        guidance = self.engine.evaluate(snapshot)

        self.signal.config(text=guidance.direction.value)
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

        self.root.after(self.config.refresh_ms, self.refresh)

    def run(self):
        self.root.mainloop()
