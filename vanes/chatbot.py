"""Realtime, local market chatbot for VANES-AI V2."""

# pylint: disable=line-too-long,too-many-return-statements
from dataclasses import dataclass
from datetime import datetime, timezone
import re


@dataclass(frozen=True)
class ChatReply:
    """Represent one chatbot response."""
    text: str
    intent: str


class MarketChatbot:
    """Answer market questions from the latest VANES state without order execution."""

    def __init__(self, state_provider):
        """Create a chatbot backed by a callable returning VANES state."""
        self._state_provider = state_provider

    def reply(self, message: str) -> ChatReply:
        """Interpret a short user message and answer from current state."""
        text = (message or "").strip()
        if not text:
            return ChatReply("Ask me about the live quote, signal, risk, or status.", "empty")
        state = self._state_provider()
        lowered = text.lower()
        if re.search(r"\b(hello|hi|hey)\b", lowered):
            return ChatReply("VANES is online. Ask: 'status', 'quote', 'signal', 'risk', or 'why'.", "greeting")
        if "help" in lowered or "what can you do" in lowered:
            return ChatReply("I can report the live quote, spread, current guidance, confidence, reference SL/TP, risk gate, broker readiness, paper status, and explain why VANES is waiting. I do not place broker orders.", "help")
        if any(word in lowered for word in ("status", "overview", "summary")):
            return ChatReply(self._status(state), "status")
        if any(word in lowered for word in ("quote", "price", "bid", "ask", "spread")):
            return ChatReply(self._quote(state), "quote")
        if any(word in lowered for word in ("indicator", "ema", "rsi", "atr", "structure", "support", "resistance")):
            return ChatReply(self._analysis(state), "analysis")
        if any(word in lowered for word in ("signal", "trade", "direction", "setup")):
            return ChatReply(self._signal(state), "signal")
        if any(word in lowered for word in ("risk", "stop", "target", "sl", "tp")):
            return ChatReply(self._risk(state), "risk")
        if any(word in lowered for word in ("why", "reason", "explain", "wait")):
            return ChatReply(f"Current guidance is {state.get('direction', 'WAIT')}: {state.get('reason', 'No explanation available')}.", "explain")
        if any(word in lowered for word in ("paper", "balance", "pnl")):
            return ChatReply(self._paper(state), "paper")
        return ChatReply("I can answer live quote, signal, risk, status, paper-trading, and reason questions. Try: 'What is EURUSD doing?' or 'Why wait?'", "unknown")

    @staticmethod
    def _number(value, digits=5):
        """Format a numeric state value safely."""
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return "—"

    def _quote(self, state):
        """Format the current quote."""
        return f"{state.get('symbol') or 'symbol'}: bid {self._number(state.get('bid'))}, ask {self._number(state.get('ask'))}, spread {self._number(state.get('spread'))} (point {self._number(state.get('point_size'), 8)})."

    def _signal(self, state):
        """Format the current guidance."""
        return f"Guidance: {state.get('direction', 'WAIT')} ({float(state.get('confidence', 0)):.1%} confidence). {state.get('reason', 'No reason available')}"

    def _analysis(self, state):
        """Format strategy diagnostics when available."""
        analysis = state.get("analysis") or {}
        if not analysis.get("ready"):
            return str(analysis.get("reason", "Indicators are not ready."))
        return (f"Trend {analysis.get('trend', 'UNKNOWN')}; "
                f"EMA {self._number(analysis.get('fast_ema'))}/{self._number(analysis.get('slow_ema'))}; "
                f"RSI {self._number(analysis.get('rsi'), 1)}; "
                f"ATR {self._number(analysis.get('atr'))}; "
                f"support {self._number(analysis.get('support'))}; "
                f"resistance {self._number(analysis.get('resistance'))}.")

    def _risk(self, state):
        """Format the reference risk state."""
        return f"Risk gate: {state.get('risk_gate', 'WAITING')}. Reference SL {self._number(state.get('stop_loss'))}, TP {self._number(state.get('take_profit'))}. Broker spec ready: {bool(state.get('broker_ready'))}."

    @staticmethod
    def _paper(state):
        """Format paper account status."""
        return f"Paper balance: {float(state.get('paper_balance', 0.0)):.2f}; daily P/L: {float(state.get('paper_daily_pnl', 0.0)):.2f}; open trades: {int(state.get('paper_open_trades', 0))}."

    def _status(self, state):
        """Format a compact live dashboard summary."""
        return f"{state.get('symbol') or 'VANES'} is {state.get('direction', 'WAIT')} at {float(state.get('confidence', 0.0)):.0%} confidence. Bid {self._number(state.get('bid'))}, ask {self._number(state.get('ask'))}; risk {state.get('risk_gate', 'WAITING')}; broker ready {bool(state.get('broker_ready'))}; updated {state.get('updated_at') or 'not yet updated'}."

    @staticmethod
    def system_message():
        """Return the safety boundary shown to chat clients."""
        return "VANES realtime chat is read-only: it can analyze current market state and paper-trading state, but it cannot place broker orders."

    @staticmethod
    def timestamp():
        """Return a UTC timestamp for chat responses."""
        return datetime.now(timezone.utc).isoformat()
