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
            with urlopen(
                f"http://127.0.0.1:{port}/health", timeout=2
            ) as response:
                health = json.loads(response.read())
                self.assertEqual(health["status"], "ok")
                self.assertFalse(health["market_ready"])
                self.assertTrue(health["updated_at"])
            bridge.update(bid=1.1, ask=1.1002, point_size=0.00001)
            with urlopen(
                f"http://127.0.0.1:{port}/state", timeout=2
            ) as response:
                state = json.loads(response.read())
                self.assertEqual(state["symbol"], "EURUSD")
                self.assertEqual(state["point_size"], 0.00001)
                self.assertTrue(state["updated_at"])
        finally:
            bridge.stop()
            thread.join(timeout=2)

    def test_realtime_chat_endpoint(self):
        bridge = LocalBridge(port=0)
        port = bridge.server.server_address[1]
        bridge.update(symbol="EURUSD", direction="BUY", confidence=0.8, reason="test")
        thread = threading.Thread(target=bridge.start)
        thread.start()
        try:
            with urlopen(
                f"http://127.0.0.1:{port}/chat", timeout=2
            ) as response:
                self.assertIn(b"VANES-AI V2", response.read())
            import urllib.request
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/chat",
                data=json.dumps({"message": "what is the signal?"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                payload = json.loads(response.read())
                self.assertEqual(payload["intent"], "signal")
                self.assertIn("BUY", payload["text"])
        finally:
            bridge.stop()
            thread.join(timeout=2)

    def test_state_updates_are_serialized(self):
        bridge = LocalBridge(port=0)
        bridge.update(symbol="EURUSD")
        errors = []

        def writer(index):
            try:
                bridge.update(direction=f"WAIT-{index}")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                errors.append(exc)

        threads = [
            threading.Thread(target=writer, args=(i,)) for i in range(20)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertFalse(errors)
        self.assertTrue(bridge._get_state()["state"]["updated_at"])


if __name__ == "__main__":
    unittest.main()
