"""Server selection dialog for VANES-AI V2."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .subscription import TIERS, TrialTracker


class ServerSelectionDialog:
    """Modal dialog for selecting a subscription tier."""

    def __init__(self, parent: tk.Tk | tk.Toplevel, tracker: TrialTracker):
        self.parent = parent
        self.tracker = tracker
        self.selected_tier: str | None = None
        self._on_select: Callable[[str], None] | None = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("VANES-AI V2 - Select Server")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        self.dialog.attributes("-topmost", True)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the server selection UI."""
        tk.Label(
            self.dialog,
            text="VANES-AI V2",
            font=("Segoe UI", 24, "bold"),
        ).pack(pady=(20, 5))

        tk.Label(
            self.dialog,
            text="Select Your Server Tier",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 15))

        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=10)

        for tier_id, info in TIERS.items():
            remaining = self.tracker.remaining_trials(tier_id)
            paid = self.tracker.has_paid(tier_id)
            status = "PAID" if paid else f"{remaining} trials left"

            frame = tk.Frame(button_frame, relief="raised", bd=2)
            frame.pack(side="left", padx=10, pady=10)

            tk.Label(
                frame,
                text=info.name,
                font=("Segoe UI", 16, "bold"),
            ).pack(pady=(10, 5))

            tk.Label(
                frame,
                text=f"${info.price:,.0f}",
                font=("Segoe UI", 14),
            ).pack(pady=5)

            tk.Label(
                frame,
                text=status,
                font=("Segoe UI", 10),
            ).pack(pady=5)

            features_text = "\n".join(f"• {f}" for f in info.features)
            tk.Label(
                frame,
                text=features_text,
                justify="center",
                font=("Segoe UI", 9),
            ).pack(pady=10, padx=10)

            select_btn = ttk.Button(
                frame,
                text="SELECT",
                command=lambda t=tier_id: self._select(tier_id),
            )
            select_btn.pack(pady=(0, 15))

    def _select(self, tier: str) -> None:
        """Handle tier selection."""
        self.selected_tier = tier
        if self._on_select:
            self._on_select(tier)
        self.dialog.destroy()

    def on_select(self, callback: Callable[[str], None]) -> None:
        """Register a callback for tier selection."""
        self._on_select = callback

    def show(self) -> str | None:
        """Show the dialog and return the selected tier, or None if cancelled."""
        self.parent.wait_window(self.dialog)
        return self.selected_tier
