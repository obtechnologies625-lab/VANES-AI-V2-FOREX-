# VANES-AI V2 FOREX

Python-core forex observer with a MetaTrader 5 on-chart bridge.

## Current build

- Python application core.
- Read-only MetaTrader 5 market-data adapter.
- Always-on-top desktop observer panel.
- MT5 MQL5 chart panel showing live symbol, bid, ask and spread.
- Guidance engine is safe by default and does not place or modify orders.

## Python setup

Python 3.10+:

    pip install -r requirements.txt
    pip install MetaTrader5

Run:

    python -m vanes.app

MetaTrader 5 must be running for live quotes.

## MT5 on-chart panel

Open MetaEditor in MetaTrader 5 and use:

    mt5/VANES_Bridge.mq5

Compile it and attach the EA to a chart. The panel is an in-terminal observer surface.

## Architecture

    MetaTrader 5
         │
         ├── MQL5 VANES panel
         │
         └── Python MetaTrader5 adapter
                  │
                  ▼
            VANES Python core
                  │
                  ▼
            Guidance / UI

The initial release intentionally observes and directs the user without automatic order execution.

## Next engineering targets

1. Connect the MQL5 panel to the Python signal service.
2. Add configurable symbols and timeframes.
3. Add market-structure and indicator modules.
4. Add risk calculations and paper-trading simulation.
5. Add tests and audit logging.
6. Keep live order routing disabled until explicitly designed and tested.
