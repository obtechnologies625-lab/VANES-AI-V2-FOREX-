import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class _Handler(BaseHTTPRequestHandler):
    server_version = "VANES/0.1"

    def do_GET(self):
        if self.path != "/state":
            self.send_response(404)
            self.end_headers()
            return
        payload = json.dumps(self.server.state, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        return

class LocalBridge:
    """Localhost-only HTTP bridge for the MT5 chart panel."""

    def __init__(self, host="127.0.0.1", port=8765):
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
        }
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )

    def start(self):
        self.thread.start()

    def update(self, **values):
        self.server.state.update(values)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
