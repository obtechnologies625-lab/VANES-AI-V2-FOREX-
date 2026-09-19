"""End-to-end smoke test for the local realtime VANES experience."""

import json
import threading
import unittest
from urllib.request import Request, urlopen

from vanes.server import LocalBridge


class RealtimeChatE2ETests(unittest.TestCase):
    """Exercise the HTTP health, state, UI, and chat surfaces together."""

    def test_realtime_chat_contract(self):
        bridge = LocalBridge(port=0)
        port = bridge.server.server_address[1]
        bridge.update(
            symbol="EURUSD",
            direction="WAIT",
            confidence=0.0,
            reason="Collecting candle history",
            bid=1.1,
            ask=1.1002,
        )
        thread = threading.Thread(target=bridge.start)
        thread.start()
        try:
            base = f"http://127.0.0.1:{port}"
            with urlopen(f"{base}/health", timeout=2) as response:
                health = json.loads(response.read())
            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["market_ready"])

            with urlopen(f"{base}/state", timeout=2) as response:
                state = json.loads(response.read())
            self.assertEqual(state["symbol"], "EURUSD")
            self.assertEqual(state["direction"], "WAIT")

            with urlopen(f"{base}/chat", timeout=2) as response:
                page = response.read().decode()
            self.assertIn("VANES-AI V2", page)
            self.assertIn("/state", page)
            self.assertIn("/chat", page)

            request = Request(
                f"{base}/chat",
                data=json.dumps({"message": "status"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                reply = json.loads(response.read())
            self.assertEqual(reply["intent"], "status")
            self.assertIn("EURUSD", reply["text"])
        finally:
            bridge.stop()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
