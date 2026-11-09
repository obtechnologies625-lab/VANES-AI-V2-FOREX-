"""Localhost HTTP bridge used by the MT5 chart panel."""

from datetime import datetime, timezone
from dataclasses import asdict
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import selftest
from .chat_ui import html_page
from .chatbot import MarketChatbot
from .devportal_ui import devportal_page
from .marketplace import MarketplaceStore
from .portal_ui import portal_page


class _Handler(BaseHTTPRequestHandler):
    """Serve the latest VANES state to MetaTrader 5."""

    server_version = "VANES/0.2"

    def _send_html(self, html: str) -> None:
        """Write an HTML page response."""
        payload = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):  # pylint: disable=invalid-name
        """Return state, health, the chat UI, or the strategy portal."""
        if self.path in {"/", "/chat"}:
            self._send_html(html_page())
            return
        if self.path == "/portal":
            self._send_html(portal_page())
            return
        if self.path == "/dev":
            self._send_html(devportal_page())
            return
        if self.path == "/api/dev/selftest":
            payload = json.dumps(
                [asdict(r) for r in selftest.run_selftest()],
                separators=(",", ":"),
            ).encode()
        elif self.path == "/api/dev/env":
            payload = json.dumps(
                selftest.environment_status(),
                separators=(",", ":"),
            ).encode()
        elif self.path == "/api/strategies":
            payload = json.dumps(
                self.server.marketplace.list_strategies(),
                separators=(",", ":"),
            ).encode()
        elif self.path == "/api/sellers":
            payload = json.dumps(
                self.server.marketplace.list_sellers(),
                separators=(",", ":"),
            ).encode()
        elif self.path in {"/api/mt5", "/mt5"}:
            payload = json.dumps(
                self.server.get_state()["state"],
                separators=(",", ":"),
            ).encode()
        elif self.path == "/health":
            payload = json.dumps(
                self.server.get_state()["health"],
                separators=(",", ":"),
            ).encode()
        elif self.path == "/state":
            payload = json.dumps(
                self.server.get_state()["state"],
                separators=(",", ":"),
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

    def _send_json(self, payload: bytes, status: int = 200) -> None:
        """Write a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict:
        """Read and parse a bounded JSON request body."""
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65_536:
            raise ValueError("invalid request size")
        return json.loads(self.rfile.read(length))

    def _handle_register(self) -> None:
        """Register a strategy seller from a portal form post."""
        try:
            body = self._read_json()
            ok, message, seller = self.server.marketplace.register_seller(
                body.get("handle", ""),
                body.get("name", ""),
                body.get("email", ""),
                body.get("bio", ""),
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json(json.dumps({"error": str(exc)}).encode(), 400)
            return
        if ok:
            self._send_json(
                json.dumps(
                    {"ok": True, "message": message, "seller": {
                        "seller_id": seller.seller_id,
                        "handle": seller.handle,
                    }},
                    separators=(",", ":"),
                ).encode()
            )
        else:
            self._send_json(
                json.dumps({"ok": False, "error": message}).encode(), 400
            )

    def _handle_submit_strategy(self) -> None:
        """List a strategy for a registered seller from a portal form post."""
        try:
            body = self._read_json()
            ok, message, strategy = self.server.marketplace.submit_strategy(
                body.get("seller_id", ""),
                body.get("title", ""),
                body.get("description", ""),
                body.get("price", 0),
                body.get("risk_level", "medium"),
                body.get("timeframe", "M15"),
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send_json(json.dumps({"error": str(exc)}).encode(), 400)
            return
        if ok:
            self._send_json(
                json.dumps(
                    {"ok": True, "message": message,
                     "strategy_id": strategy.strategy_id},
                    separators=(",", ":"),
                ).encode()
            )
        else:
            self._send_json(
                json.dumps({"ok": False, "error": message}).encode(), 400
            )

    def do_POST(self):  # pylint: disable=invalid-name
        """Answer chatbot messages and marketplace register/submit requests."""
        if self.path == "/api/sellers/register":
            self._handle_register()
            return
        if self.path == "/api/strategies":
            self._handle_submit_strategy()
            return
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 16_384:
                raise ValueError("invalid request size")
            body = json.loads(self.rfile.read(length))
            message = body.get("message", "")
            if not isinstance(message, str):
                raise ValueError("message must be text")
            reply = self.server.chatbot.reply(message)
            payload = json.dumps(
                {"text": reply.text, "intent": reply.intent},
                separators=(",", ":"),
            ).encode()
            self.send_response(200)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            payload = json.dumps({"error": str(exc)}).encode()
            self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        """Suppress HTTP request logging in the desktop console."""


class LocalBridge:
    """Expose VANES state on localhost only."""

    def __init__(self, host="127.0.0.1", port=8765, chatbot=None, marketplace=None):
        """Create the local bridge server."""
        self._lock = threading.RLock()
        initial = {
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
            "broker_ready": False,
            "risk_gate": "WAITING",
            "point_size": 0.0,
            "updated_at": "",
            "timeframe": "",
            "confirmation_timeframe": "",
            "candles": [],
            "screen_context": "",
            "mt5_screen_active": False,
            "suggested_next_step": "Open MetaTrader 5 to enable visual guidance.",
            "ml_regime": "",
            "ml_prob": 0.0,
            "sentiment": {"score": 0.0, "label": "NEUTRAL", "samples": 0},
            "tilt": 0,
            "journal_prompt": "",
            "execution_slices": [],
            "est_slippage": 0.0,
            "incubation": {},
        }
        self._state = initial
        self._health = {
            "status": "ok",
            "service": "vanes-bridge",
            "market_ready": False,
            "updated_at": "",
        }
        self.server = ThreadingHTTPServer((host, port), _Handler)
        self.server.get_state = self._get_state
        self.server.marketplace = marketplace or MarketplaceStore()
        self.server.chatbot = chatbot or MarketChatbot(
            lambda: self._get_state()["state"]
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )

    def _get_state(self):
        """Return a consistent bridge snapshot."""
        with self._lock:
            return {
                "state": dict(self._state),
                "health": dict(self._health),
            }

    def start(self):
        """Start serving bridge requests in a background thread."""
        self.thread.start()

    def update(self, **values):
        """Update the state exposed to MetaTrader 5."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._state.update(values)
            self._state["updated_at"] = now
            self._health["updated_at"] = now
            self._health["market_ready"] = (
                self._state["bid"] > 0 and self._state["ask"] > 0
            )

    def stop(self):
        """Stop and close the local bridge server."""
        self.server.shutdown()
        self.server.server_close()
