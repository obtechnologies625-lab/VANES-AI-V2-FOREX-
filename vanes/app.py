from .config import AppConfig
from .platform import MT5Adapter
from .strategy import RuleBasedStrategy
from .ui import Overlay

def main():
    config = AppConfig()
    adapter = MT5Adapter()
    status = adapter.connect()
    print(f"VANES-AI V2: {status.message}")

    try:
        Overlay(
            config=config,
            adapter=adapter,
            strategy=RuleBasedStrategy(),
        ).run()
    finally:
        adapter.close()

if __name__ == "__main__":
    main()
