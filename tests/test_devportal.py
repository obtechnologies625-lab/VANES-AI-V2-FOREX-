"""Tests for the developer portal, self-test engine, and trademark surfaces."""

import json
import threading
import unittest
from urllib.request import urlopen

from vanes import selftest
from vanes.chat_ui import html_page
from vanes.devportal_ui import devportal_page
from vanes.portal_ui import portal_page
from vanes.server import LocalBridge
from vanes.theme import DEVELOPER_EMAIL, TRADEMARK_LINE


class SelfTestTests(unittest.TestCase):
    """Validate the offline self-test engine and environment reporter."""

    def test_all_selftests_pass(self):
        results = selftest.run_selftest("data/vanes_selftest_incubation_test.json")
        self.assertTrue(results)
        for result in results:
            self.assertTrue(result.ok, f"{result.name} failed: {result.detail}")

    def test_environment_status_keys(self):
        status = selftest.environment_status()
        for key in (
            "metatrader5",
            "gemini_api_key",
            "cloudflare_api_token",
            "jwt_secret",
            "publish_token",
            "kv_namespace_created",
            "local_bridge",
        ):
            self.assertIn(key, status)
            self.assertIsInstance(status[key], bool)
        self.assertTrue(status["local_bridge"])


class TrademarkTests(unittest.TestCase):
    """Every product surface must carry the OB Technologies trademark."""

    def test_devportal_shows_trademark_and_email(self):
        page = devportal_page()
        self.assertIn(TRADEMARK_LINE, page)
        self.assertIn(DEVELOPER_EMAIL, page)

    def test_portal_shows_trademark(self):
        self.assertIn(TRADEMARK_LINE, portal_page())

    def test_command_center_shows_trademark(self):
        self.assertIn(TRADEMARK_LINE, html_page())


class DevPortalRouteTests(unittest.TestCase):
    """The bridge must serve the developer portal and its JSON APIs."""

    def test_dev_routes(self):
        bridge = LocalBridge(port=0)
        port = bridge.server.server_address[1]
        thread = threading.Thread(target=bridge.start)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{port}/dev", timeout=10) as response:
                page = response.read().decode()
                self.assertEqual(response.status, 200)
                self.assertIn(DEVELOPER_EMAIL, page)
            with urlopen(
                f"http://127.0.0.1:{port}/api/dev/selftest", timeout=30
            ) as response:
                results = json.loads(response.read())
                self.assertTrue(all(item["ok"] for item in results))
            with urlopen(
                f"http://127.0.0.1:{port}/api/dev/env", timeout=10
            ) as response:
                status = json.loads(response.read())
                self.assertIn("kv_namespace_created", status)
        finally:
            bridge.stop()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
