from .config import AppConfig
from .platform import MT5Adapter
from .server import LocalBridge
from .strategy import RuleBasedStrategy
from .ui import Overlay

def main():
    config = AppConfig()
    adapter = MT5Adapter()
    bridge = LocalBridge()
    strategy = RuleBasedStrategy()

    status = adapter.connect()
    print(f"VANES-AI V2: {status.message}")
    bridge.start()
    print("VANES bridge: http://127.0.0.1:8765/state")

    try:
        Overlay(
            config=config,
            adapter=adapter,
            strategy=strategy,
            bridge=bridge,
        ).run()
    finally:
        bridge.stop()
        adapter.close()

if __name__ == "__main__":
    main()
