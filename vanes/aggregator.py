"""Packet encapsulation and aggregation for multimodal VANES telemetry."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TelemetryPacket:
    """One encapsulated multimodal packet with metadata."""

    packet_id: str
    created_at: float
    subscription_tier: str
    symbol: str
    direction: str
    confidence: float
    bid: float
    ask: float
    spread: float
    reason: str
    stop_loss: float
    take_profit: float
    risk_gate: str
    broker_ready: bool
    paper_balance: float
    paper_daily_pnl: float
    paper_open_trades: int
    point_size: float
    updated_at: str
    audio_chunks: list[dict[str, Any]] = field(default_factory=list)
    screen_frames: list[dict[str, Any]] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize the packet to compact JSON."""
        return json.dumps(self._to_dict(), separators=(",", ":"))

    def _to_dict(self) -> dict[str, Any]:
        base = {
            "packet_id": self.packet_id,
            "created_at": self.created_at,
            "subscription_tier": self.subscription_tier,
            "symbol": self.symbol,
            "direction": self.direction,
            "confidence": self.confidence,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "reason": self.reason[:500] if isinstance(self.reason, str) else self.reason,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_gate": self.risk_gate,
            "broker_ready": self.broker_ready,
            "paper_balance": self.paper_balance,
            "paper_daily_pnl": self.paper_daily_pnl,
            "paper_open_trades": self.paper_open_trades,
            "point_size": self.point_size,
            "updated_at": self.updated_at,
        }
        if self.audio_chunks:
            base["audio_chunks"] = self.audio_chunks
        if self.screen_frames:
            base["screen_frames"] = self.screen_frames
        if self.alerts:
            base["alerts"] = self.alerts[-10:]
        if self.extra:
            base["extra"] = self.extra
        return base


class PacketAggregator:
    """Aggregate market state with optional capture media into packets."""

    def __init__(
        self,
        subscription_tier: str = "SERVER_B",
        max_audio_chunks: int = 4,
        max_screen_frames: int = 4,
        max_packet_bytes: int = 524288,
    ):
        self.subscription_tier = subscription_tier
        self.max_audio_chunks = max(1, int(max_audio_chunks))
        self.max_screen_frames = max(1, int(max_screen_frames))
        self.max_packet_bytes = max(1024, int(max_packet_bytes))
        self._packet_counter = 0

    def build_packet(self, state: dict[str, Any]) -> TelemetryPacket | None:
        """Create a packet from the latest VANES state and attached media."""
        audio = state.get("audio_chunks", [])
        screen = state.get("screen_frames", [])
        if not audio and not screen:
            return None
        self._packet_counter += 1
        packet = TelemetryPacket(
            packet_id=f"vnp-{int(time.time())}-{self._packet_counter}",
            created_at=time.time(),
            subscription_tier=self.subscription_tier,
            symbol=str(state.get("symbol", "")),
            direction=str(state.get("direction", "WAIT")),
            confidence=float(state.get("confidence", 0.0)),
            bid=float(state.get("bid", 0.0)),
            ask=float(state.get("ask", 0.0)),
            spread=float(state.get("spread", 0.0)),
            reason=str(state.get("reason", "")),
            stop_loss=float(state.get("stop_loss", 0.0)),
            take_profit=float(state.get("take_profit", 0.0)),
            risk_gate=str(state.get("risk_gate", "WAITING")),
            broker_ready=bool(state.get("broker_ready", False)),
            paper_balance=float(state.get("paper_balance", 0.0)),
            paper_daily_pnl=float(state.get("paper_daily_pnl", 0.0)),
            paper_open_trades=int(state.get("paper_open_trades", 0)),
            point_size=float(state.get("point_size", 0.0)),
            updated_at=str(state.get("updated_at", "")),
        )
        if audio:
            packet.audio_chunks = [
                {
                    "timestamp": chunk.timestamp,
                    "sample_rate": chunk.sample_rate,
                    "channels": chunk.channels,
                    "data": __import__("base64").b64encode(chunk.data).decode("ascii"),
                    "device": chunk.device,
                }
                for chunk in audio[-self.max_audio_chunks:]
            ]
        if screen:
            packet.screen_frames = [
                {
                    "timestamp": frame.timestamp,
                    "width": frame.width,
                    "height": frame.height,
                    "format": frame.format,
                    "data": __import__("base64").b64encode(frame.data).decode("ascii"),
                    "region": frame.region,
                }
                for frame in screen[-self.max_screen_frames:]
            ]
        raw = packet.to_json()
        if len(raw.encode("utf-8")) > self.max_packet_bytes:
            packet.screen_frames = []
            packet.audio_chunks = packet.audio_chunks[:1]
            raw = packet.to_json()
            if len(raw.encode("utf-8")) > self.max_packet_bytes:
                return None
        return packet
