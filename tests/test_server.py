"""Tests for the local bridge."""

import json
import threading
import unittest
from urllib.request import urlopen

from vanes.server import LocalBridge


class ServerTests(unittest.TestCase):
    """Validate the local HTTP state bridge."""

    def test_health_and_state(self):
        bridge = LocalBridge(port=0)
        port = bridge.server.server_address[1]
        bridge.update(symbol="EURUSD", direction="WAIT")
        thread = threading.Thread(target=bridge.start)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                self.assertEqual(json.loads(response.read())["status"], "ok")
            with urlopen(f"http://127.0.0.1:{port}/state", timeout=2) as response:
                self.assertEqual(json.loads(response.read())["symbol"], "EURUSD")
        finally:
            bridge.stop()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
