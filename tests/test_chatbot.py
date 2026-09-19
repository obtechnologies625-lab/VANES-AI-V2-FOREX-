"""Tests for the realtime VANES chatbot."""

import unittest

from vanes.chatbot import MarketChatbot


class ChatbotTests(unittest.TestCase):
    """Validate chatbot intent routing against live state."""

    def setUp(self):
        self.state = {
            "symbol": "EURUSD",
            "direction": "BUY",
            "confidence": 0.72,
            "bid": 1.10001,
            "ask": 1.10021,
            "spread": 0.00020,
            "point_size": 0.00001,
            "reason": "EMA trend UP; RSI 58.2; structure confirmed",
            "stop_loss": 1.09700,
            "take_profit": 1.10663,
            "paper_balance": 10000.0,
            "paper_daily_pnl": 12.0,
            "paper_open_trades": 1,
            "broker_ready": True,
            "risk_gate": "PASS",
            "updated_at": "2026-09-19T00:00:00+00:00",
        }
        self.bot = MarketChatbot(lambda: dict(self.state))

    def test_quote_intent(self):
        reply = self.bot.reply("what is the quote?")
        self.assertEqual(reply.intent, "quote")
        self.assertIn("EURUSD", reply.text)
        self.assertIn("1.10001", reply.text)

    def test_signal_intent(self):
        reply = self.bot.reply("what is the signal?")
        self.assertEqual(reply.intent, "signal")
        self.assertIn("BUY", reply.text)
        self.assertIn("72.0%", reply.text)

    def test_reason_intent(self):
        reply = self.bot.reply("why?")
        self.assertEqual(reply.intent, "explain")
        self.assertIn("EMA trend UP", reply.text)

    def test_unknown_is_safe(self):
        reply = self.bot.reply("tell me something unrelated")
        self.assertEqual(reply.intent, "unknown")
        self.assertIn("live quote", reply.text)


if __name__ == "__main__":
    unittest.main()
