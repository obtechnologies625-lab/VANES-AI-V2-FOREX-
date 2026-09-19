"""Application entry point for VANES-AI V2."""

from .audit import AuditLogger
from .config import AppConfig
from .paper import PaperTrader
from .platform import MT5Adapter
from .risk import daily_loss_limit
from .server import LocalBridge
from .strategy import RuleBasedStrategy, StrategyConfig
from .ui import Overlay


def main():
    """Start the VANES desktop observer and local MT5 bridge."""
    config = AppConfig.from_environment()
    adapter = MT5Adapter()
    bridge = LocalBridge()
    strategy = RuleBasedStrategy(
        StrategyConfig(max_spread_points=config.max_spread_points)
    )
    audit = AuditLogger(config.audit_path)
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

    try:
        Overlay(
            config=config,
            adapter=adapter,
            strategy=strategy,
            bridge=bridge,
            audit=audit,
            paper=paper,
        ).run()
    finally:
        bridge.stop()
        adapter.close()


if __name__ == "__main__":
    main()
