"""Shared cyberpunk neon theme for VANES-AI V2 (Tk overlay + web pages)."""

# pylint: disable=line-too-long

# Core neon palette: deep navy void, electric cyan, hot magenta, violet glow.
BG = "#05060c"
BG_ALT = "#0a0f1e"
PANEL = "#0c1424"
PANEL_SOFT = "#0c1424e6"
LINE = "#1b2c4d"
GRID = "#132038"
TEXT = "#d6f7ff"
MUTED = "#6f7fa6"
CYAN = "#00fff0"
MAGENTA = "#ff2bd6"
VIOLET = "#9d00ff"
GOLD = "#f7ff5e"
OK = "#00ffa3"
WARN = "#ffb347"
ERR = "#ff3b6b"

# Tk-friendly font families (monospace / techy).
MONO = "Consolas"
HEAD_FONT = (MONO, 16, "bold")
TITLE_FONT = (MONO, 24, "bold")
BIG_FONT = (MONO, 30, "bold")
SMALL_FONT = (MONO, 8)
BODY_FONT = (MONO, 10)


# Shared CSS variable block + base styling injected into every web page so the
# command center, portal, and any future page look like one neon product.
CSS_BASE = """
:root{
  color-scheme:dark;
  --bg:%(BG)s;--bg2:%(BG_ALT)s;--panel:%(PANEL)s;--panelsoft:%(PANEL_SOFT)s;
  --line:%(LINE)s;--grid:%(GRID)s;--text:%(TEXT)s;--muted:%(MUTED)s;
  --cyan:%(CYAN)s;--magenta:%(MAGENTA)s;--violet:%(VIOLET)s;
  --accent:%(CYAN)s;--gold:%(GOLD)s;--ok:%(OK)s;--warn:%(WARN)s;--err:%(ERR)s;
  --mono:'Share Tech Mono',ui-monospace,'Cascadia Code',Consolas,monospace;
}
*{box-sizing:border-box}
body{
  margin:0;font-family:var(--mono);color:var(--text);
  background:
    radial-gradient(circle at 12%% -10%%,#%(VIOLET)s22 0,transparent 45%%),
    radial-gradient(circle at 88%% 0%%,#%(MAGENTA)s1f 0,transparent 40%%),
    linear-gradient(180deg,#%(BG_ALT)s 0,#%(BG)s 60%%);
  background-attachment:fixed;
}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.35;
  background-image:
    linear-gradient(var(--grid) 1px,transparent 1px),
    linear-gradient(90deg,var(--grid) 1px,transparent 1px);
  background-size:44px 44px;
  mask-image:radial-gradient(circle at 50%% 0%%,#000 0,transparent 85%%);
}
body::after{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:1;opacity:.05;
  background:repeating-linear-gradient(180deg,#%(CYAN)s 0 1px,transparent 1px 3px);
}
main,header,section{position:relative;z-index:2}
::selection{background:#%(MAGENTA)s55;color:#fff}
""" % {
    "BG": BG, "BG_ALT": BG_ALT, "PANEL": PANEL, "PANEL_SOFT": PANEL_SOFT,
    "LINE": LINE, "GRID": GRID, "TEXT": TEXT, "MUTED": MUTED,
    "CYAN": CYAN, "MAGENTA": MAGENTA, "VIOLET": VIOLET,
    "GOLD": GOLD, "OK": OK, "WARN": WARN, "ERR": ERR,
}

# Neon Google font (best-effort; falls back to system monospace offline).
FONT_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">'
)
