"""Application entry point for VANES-AI V2."""

from .aggregator import PacketAggregator
from .audit import AuditLogger
from .capture import AudioCapture, ScreenCapture
from .cloud import CloudStatePublisher
from .config import AppConfig
from .jwt_client import SecureCloudClient
from .paper import PaperTrader
from .platform import MT5Adapter
from .risk import daily_loss_limit
from .server import LocalBridge
from .strategy import RuleBasedStrategy, StrategyConfig
from .subscription import SubscriptionManager
from .trader import MT5Trader
from .ui import Overlay


def main():  # pylint: disable=too-many-locals
    """Start the VANES desktop observer, local MT5 bridge, and multimodal pipeline."""
    config = AppConfig.from_environment()
    subscription = SubscriptionManager(config)

    allowed, reason = subscription.can_access()
    if not allowed:
        print(f"VANES: {reason}")
        return

    adapter = MT5Adapter()
    bridge = LocalBridge()
    strategy = RuleBasedStrategy(
        StrategyConfig(max_spread_points=config.max_spread_points)
    )
    audit = AuditLogger(config.audit_path)

    aggregator = PacketAggregator(
        subscription_tier=subscription.selected_tier,
        max_packet_bytes=config.capture_max_packet_bytes,
    )
    cloud_publisher = CloudStatePublisher.from_environment(aggregator=aggregator)
    secure_client = None
    if config.cloud_url and config.cloud_token and config.jwt_secret:
        secure_client = SecureCloudClient(
            url=config.cloud_url,
            token=config.cloud_token,
            jwt_secret=config.jwt_secret,
            subscription_tier=subscription.selected_tier,
            timeout=config.cloud_timeout,
        )
        print("VANES secure cloud client: enabled")
    elif cloud_publisher:
        print("VANES cloud publishing: enabled (legacy)")
    else:
        print("VANES cloud publishing: disabled")

    audio_capture = AudioCapture(
        device=config.capture_audio_device,
        chunk_seconds=config.capture_audio_chunk_seconds,
    )
    screen_capture = ScreenCapture(
        region=config.capture_screen_region,
        fps=config.capture_screen_fps,
        max_bytes=config.capture_max_packet_bytes,
    )
    if config.capture_audio_enabled:
        audio_capture.start()
    if config.capture_screen_enabled:
        screen_capture.start()

    trader = None
    if subscription.selected_tier == "SERVER_A":
        trader = MT5Trader(adapter)
        if trader.connect():
            print("VANES live trader: enabled (SERVER_A)")
        else:
            print(f"VANES live trader: disabled ({trader.last_error})")
            trader = None

    paper = PaperTrader(
        config.paper_start_balance,
        daily_loss_limit(
            config.paper_start_balance,
            config.max_daily_loss_percent,
        ),
    )

    status = adapter.connect()
    print(f"VANES-AI V2: {status.message}")
    audit.write(
        "platform_status",
        connected=status.connected,
        message=status.message,
    )
    bridge.start()
    print("VANES bridge: http://127.0.0.1:8765/state")
    print("VANES realtime chat: http://127.0.0.1:8765/chat")

    try:
        Overlay(
            config=config,
            adapter=adapter,
            strategy=strategy,
            bridge=bridge,
            audit=audit,
            paper=paper,
            cloud_publisher=cloud_publisher,
            secure_client=secure_client,
            audio_capture=audio_capture,
            screen_capture=screen_capture,
            aggregator=aggregator,
            trader=trader,
            subscription=subscription,
        ).run()
    finally:
        bridge.stop()
        adapter.close()
        audio_capture.stop()
        screen_capture.stop()


if __name__ == "__main__":
    main()
