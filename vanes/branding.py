"""Procedural VANES brand icon: six-turbine wheel with a lightning-bolt hub.

PIL cannot decode SVG, so the desktop window icon is drawn at runtime. This
guarantees the icon displays on every platform instead of silently failing.
"""

from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# Multi-resolution sizes baked into the Windows .ico (titlebar + taskbar + alt-tab).
ICON_SIZES = [
    (16, 16),
    (24, 24),
    (32, 32),
    (48, 48),
    (64, 64),
    (128, 128),
    (256, 256),
]

CYAN = (39, 233, 255, 255)
VIOLET = (118, 84, 255, 255)
MAGENTA = (255, 43, 214, 255)
BG_TOP = (16, 26, 58)
BG_BOTTOM = (2, 4, 12)
HUB_FILL = (7, 13, 32, 255)
HUB_INNER = (16, 25, 54, 255)
WHITE = (234, 255, 255, 255)
BOLT_FILL = (255, 216, 77, 255)

# Turbine blade, normalized to the outer-ring radius (y up), matching icon.svg.
_BLADE = (
    (-0.068, -0.282),
    (0.126, -0.903),
    (0.320, -0.767),
    (0.117, -0.243),
)

# Lightning bolt in a 100x100 box (y down, apex at top).
_BOLT = (
    (58, 4),
    (24, 54),
    (45, 54),
    (36, 96),
    (76, 42),
    (53, 42),
    (68, 4),
)


def _background(size: int) -> Image.Image:
    """Return a vertical navy gradient backdrop."""
    img = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(img)
    last = max(1, size - 1)
    for y in range(size):
        t = y / last
        color = tuple(
            int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3)
        )
        draw.line([(0, y), (size, y)], fill=(*color, 255))
    return img


def _rotate(point, angle):
    """Rotate a normalized (x, y-up) point by angle radians."""
    cos, sin = math.cos(angle), math.sin(angle)
    x, y = point
    return (x * cos - y * sin, x * sin + y * cos)


def render_icon(size: int = 256) -> Image.Image:  # pylint: disable=too-many-locals
    """Render the VANES wheel-and-bolt icon as a square RGBA image."""
    img = _background(size)
    draw = ImageDraw.Draw(img)
    cx = cy = size / 2.0
    radius = size * 0.40
    ring_width = max(2, int(size * 0.035))

    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=CYAN,
        width=ring_width,
    )

    for index in range(6):
        angle = math.radians(60 * index)
        points = []
        for bx, by in _BLADE:
            rx, ry = _rotate((bx * radius, by * radius), angle)
            points.append((cx + rx, cy - ry))
        color = (CYAN, VIOLET, MAGENTA)[index % 3]
        draw.polygon(points, fill=color, outline=WHITE)

    hub = radius * 0.36
    draw.ellipse(
        [cx - hub, cy - hub, cx + hub, cy + hub],
        fill=HUB_FILL,
        outline=VIOLET,
        width=max(2, int(size * 0.03)),
    )
    inner = radius * 0.21
    draw.ellipse(
        [cx - inner, cy - inner, cx + inner, cy + inner],
        fill=HUB_INNER,
        outline=CYAN,
        width=max(1, int(size * 0.015)),
    )

    bolt_size = radius * 0.66
    bolt = [
        (cx + (bx - 50) / 100.0 * bolt_size, cy + (by - 50) / 100.0 * bolt_size)
        for bx, by in _BOLT
    ]
    draw.polygon(bolt, fill=BOLT_FILL, outline=WHITE)
    return img


def asset_path(name: str) -> str:
    """Return the absolute path of a bundled brand asset."""
    return os.path.join(ASSETS_DIR, name)


def write_ico(path: str | None = None) -> str:
    """Render a multi-resolution Windows .ico app icon and return its path."""
    target = path or asset_path("vanes_icon.ico")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    render_icon(256).save(target, format="ICO", sizes=ICON_SIZES)
    return target


def write_png(path: str | None = None, size: int = 256) -> str:
    """Render a square PNG app icon and return its path."""
    target = path or asset_path("vanes_icon.png")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    render_icon(size).save(target, format="PNG")
    return target
