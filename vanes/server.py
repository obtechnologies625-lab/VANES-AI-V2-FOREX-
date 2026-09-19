"""Localhost HTTP bridge used by the MT5 chart panel."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _Handler(BaseHTTPRequestHandler):
    """Serve the latest VANES state to MetaTrader 5."""

    server_version = "VANES/0.2"

    def do_GET(self):  # pylint: disable=invalid-name
        """Return state or health for local bridge requests."""
        if self.path == "/health":
            payload = b'{"status":"ok","service":"vanes-bridge"}'
        elif self.path == "/state":
            payload = json.dumps(
                self.server.state, separators=(",", ":")
            ).encode()
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        """Suppress HTTP request logging in the desktop console."""


class LocalBridge:
    """Expose VANES state on localhost only."""

    def __init__(self, host="127.0.0.1", port=8765):
        """Create the local bridge server."""
        self.server = ThreadingHTTPServer((host, port), _Handler)
        self.server.state = {
            "symbol": "",
            "direction": "WAIT",
            "confidence": 0.0,
            "bid": 0.0,
            "ask": 0.0,
            "spread": 0.0,
            "reason": "Starting VANES",
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "paper_balance": 0.0,
            "paper_daily_pnl": 0.0,
            "paper_open_trades": 0,
        }
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )

    def start(self):
        """Start serving bridge requests in a background thread."""
        self.thread.start()

    def update(self, **values):
        """Update the state exposed to MetaTrader 5."""
        self.server.state.update(values)

    def stop(self):
        """Stop and close the local bridge server."""
        self.server.shutdown()
        self.server.server_close()
