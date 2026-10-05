"""Local capture modules for audio and MT5 screen context."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import BinaryIO

import numpy as np


@dataclass(frozen=True)
class AudioChunk:
    """A captured audio buffer with metadata."""

    timestamp: float
    sample_rate: int
    channels: int
    data: bytes
    device: str


@dataclass(frozen=True)
class ScreenFrame:
    """A captured screen frame with metadata."""

    timestamp: float
    width: int
    height: int
    format: str
    data: bytes
    region: str


class AudioCapture:
    """Capture microphone audio chunks when enabled."""

    def __init__(self, device: str = "", chunk_seconds: float = 2.0):
        self.device = device
        self.chunk_seconds = max(0.5, float(chunk_seconds))
        self._stream = None
        self._running = False

    def start(self) -> None:
        """Start audio capture if the audio stack is available."""
        if self._running:
            return
        try:
            import soundcard as sc  # pylint: disable=import-outside-toplevel
        except ImportError:
            return
        try:
            sample_rate = 16000
            channels = 1
            if self.device:
                mic = sc.get_microphone(id=self.device, include_loopback=True)
            else:
                mic = sc.get_microphone(include_loopback=True)
            self._stream = mic.recorder(
                samplerate=sample_rate, channels=channels
            )
            self._stream.start()
            self._running = True
            self._sample_rate = sample_rate
            self._channels = channels
        except (OSError, ValueError):
            self._stream = None
            self._running = False

    def capture(self) -> AudioChunk | None:
        """Return one audio chunk, or None if capture is unavailable."""
        if not self._running or self._stream is None:
            return None
        try:
            frames = int(self._sample_rate * self.chunk_seconds)
            audio = self._stream.record(frames)
            if audio is None or audio.size == 0:
                return None
            pcm = (audio * 32767).astype(np.int16).tobytes()
            return AudioChunk(
                timestamp=time.time(),
                sample_rate=self._sample_rate,
                channels=self._channels,
                data=pcm,
                device=self.device or "default",
            )
        except (OSError, ValueError):
            return None

    def stop(self) -> None:
        """Stop audio capture."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except (OSError, ValueError):
                pass
            self._stream = None
        self._running = False


class ScreenCapture:
    """Capture MT5 screen frames when enabled."""

    def __init__(
        self,
        region: str = "",
        fps: int = 1,
        max_bytes: int = 524288,
    ):
        self.region = region
        self.fps = max(1, int(fps))
        self.max_bytes = max(1024, int(max_bytes))
        self._running = False
        self._last_capture = 0.0
        self._interval = 1.0 / self.fps

    def start(self) -> None:
        """Prepare screen capture if the imaging stack is available."""
        if self._running:
            return
        try:
            from PIL import ImageGrab  # pylint: disable=import-outside-toplevel
            self._ImageGrab = ImageGrab
            self._running = True
        except ImportError:
            self._running = False

    def _parse_region(self):
        """Return a PIL-compatible bbox or None for full screen."""
        if not self.region:
            return None
        parts = self.region.split(",")
        if len(parts) != 4:
            return None
        try:
            return tuple(int(p.strip()) for p in parts)
        except ValueError:
            return None

    def capture(self) -> ScreenFrame | None:
        """Return one screen frame if the interval has elapsed, else None."""
        if not self._running:
            return None
        now = time.time()
        if now - self._last_capture < self._interval:
            return None
        self._last_capture = now
        try:
            bbox = self._parse_region()
            image = self._ImageGrab.grab(bbox=bbox)
            img_format = "PNG"
            from io import BytesIO
            buffer = BytesIO()
            image.save(buffer, format=img_format, optimize=True)
            raw = buffer.getvalue()
            if len(raw) > self.max_bytes:
                quality = max(10, 85 - len(raw) // 65536)
                buffer = BytesIO()
                image.save(
                    buffer, format="JPEG", quality=quality, optimize=True
                )
                raw = buffer.getvalue()
                img_format = "JPEG"
            return ScreenFrame(
                timestamp=now,
                width=image.width,
                height=image.height,
                format=img_format,
                data=raw,
                region=self.region or "full",
            )
        except (OSError, ValueError):
            return None

    def stop(self) -> None:
        """Stop screen capture."""
        self._running = False
        self._last_capture = 0.0
