"""Tests for the optional Cloudflare state publisher."""

import json
import unittest
from unittest.mock import patch

from vanes.cloud import CloudStatePublisher


class CloudPublisherTests(unittest.TestCase):
    """Validate cloud publishing without making network requests."""

    def test_disabled_without_environment(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(CloudStatePublisher.from_environment())

    @patch("vanes.cloud.urlopen")
    def test_publishes_whitelisted_state(self, mock_urlopen):
        response = mock_urlopen.return_value.__enter__.return_value
        response.status = 200
        publisher = CloudStatePublisher(
            "https://example.workers.dev",
            "secret",
            interval_seconds=0.5,
        )
        state = {
            "symbol": "EURUSD",
            "direction": "BUY",
            "confidence": 0.8,
            "bid": 1.1,
            "ask": 1.1002,
            "spread": 0.0002,
            "reason": "test",
            "stop_loss": 1.099,
            "take_profit": 1.102,
            "risk_gate": "PASS",
            "broker_ready": True,
            "paper_balance": 10000,
            "paper_daily_pnl": 0,
            "paper_open_trades": 0,
            "point_size": 0.00001,
            "paper_trades": [
                {
                    "direction": "BUY",
                    "entry": 1.1,
                    "stop_loss": 1.099,
                    "take_profit": 1.102,
                    "size": 0.1,
                    "opened_at": 1,
                    "closed_at": None,
                    "exit_price": None,
                }
            ],
            "broker_password": "must-not-send",
        }
        self.assertTrue(publisher.publish(state))
        request = mock_urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertNotIn("broker_password", body)
        self.assertEqual(body["symbol"], "EURUSD")
        self.assertEqual(body["paper_trades"][0]["direction"], "BUY")
        self.assertEqual(
            request.headers["Authorization"], "Bearer secret"
        )

    @patch("vanes.cloud.urlopen", side_effect=OSError("offline"))
    def test_network_failure_is_non_fatal(self, _mock_urlopen):
        publisher = CloudStatePublisher(
            "https://example.workers.dev",
            "secret",
            interval_seconds=0.5,
        )
        self.assertFalse(publisher.publish({"symbol": "EURUSD"}))
        self.assertIn("offline", publisher.last_error)


if __name__ == "__main__":
    unittest.main()
