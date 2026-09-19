"""Windows desktop context observer for the VANES visual-first workflow.

This module observes only local desktop context needed to guide the user:
foreground window title, cursor position, and recent mouse/keyboard activity.
It does not capture credentials, transmit screenshots, or execute clicks/orders.
"""

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import os
from pathlib import Path


# pylint: disable=too-few-public-methods


@dataclass(frozen=True)
class ScreenContext:
    """Describe the visible desktop context available to VANES."""

    supported: bool
    window_title: str
    cursor_x: int
    cursor_y: int
    mouse_active: bool
    keyboard_active: bool
    mt5_active: bool

    @property
    def summary(self):
        """Return a compact, user-facing observation."""
        if not self.supported:
            return "Visual observer unavailable on this platform."
        if not self.window_title:
            return (
                "Desktop visible; active window title unavailable."
            )
        activity = (
            "activity detected"
            if self.mouse_active or self.keyboard_active
            else "no recent input"
        )
        return (
            f"{self.window_title} • {activity}"
        )


class ScreenObserver:
    """Read safe Windows desktop context without controlling the desktop."""

    VK_LBUTTON = 0x01
    VK_RBUTTON = 0x02
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_ALT = 0x12
    VK_RETURN = 0x0D
    VK_SPACE = 0x20

    def __init__(self):
        """Prepare Windows APIs when available."""
        self._user32 = None
        if os.name == "nt":
            try:
                self._user32 = ctypes.windll.user32
            except (AttributeError, OSError):
                self._user32 = None

    def capture_mt5(self, path, region=None):
        """Capture the desktop locally for an explicit visual inspection."""
        if self._user32 is None:
            return False
        try:
            from PIL import ImageGrab  # pylint: disable=import-outside-toplevel
        except ImportError:
            return False

        if region is None:
            image = ImageGrab.grab()
        else:
            image = ImageGrab.grab(bbox=region)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target)
        return True

    def _key_active(self, key):
        """Return whether a virtual key is currently pressed."""
        if self._user32 is None:
            return False
        return bool(self._user32.GetAsyncKeyState(key) & 0x8000)

    def observe(self):
        """Read the current foreground-window and input context."""
        if self._user32 is None:
            return ScreenContext(False, "", 0, 0, False, False, False)

        hwnd = self._user32.GetForegroundWindow()
        title = ""
        if hwnd:
            length = self._user32.GetWindowTextLengthW(hwnd)
            buffer = ctypes.create_unicode_buffer(length + 1)
            self._user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()

        point = wintypes.POINT()
        self._user32.GetCursorPos(ctypes.byref(point))
        mouse_active = self._key_active(self.VK_LBUTTON) or self._key_active(
            self.VK_RBUTTON
        )
        keyboard_active = any(
            self._key_active(key)
            for key in (
                self.VK_SHIFT,
                self.VK_CONTROL,
                self.VK_ALT,
                self.VK_RETURN,
                self.VK_SPACE,
            )
        )
        lowered = title.lower()
        mt5_active = "metatrader 5" in lowered or "metatrader5" in lowered

        return ScreenContext(
            True,
            title,
            int(point.x),
            int(point.y),
            mouse_active,
            keyboard_active,
            mt5_active,
        )


def next_step(context, direction):
    """Suggest the next visible action without performing it."""
    if not context.supported:
        return (
            "Open MetaTrader 5 to enable visual guidance."
        )
    if not context.mt5_active:
        return (
            "Bring MetaTrader 5 to the foreground; "
            "VANES will observe the chart context."
        )
    if direction == "BUY":
        return (
            "Review the MT5 BUY setup, then verify entry, reference "
            "SL/TP, and risk before any manual action."
        )
    if direction == "SELL":
        return (
            "Review the MT5 SELL setup, then verify entry, reference "
            "SL/TP, and risk before any manual action."
        )
    return "Keep the MT5 chart visible; VANES is waiting for a clearer setup."


__all__ = ["ScreenContext", "ScreenObserver", "next_step"]
