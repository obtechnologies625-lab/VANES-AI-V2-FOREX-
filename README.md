# VANES-AI V2 FOREX

VANES-AI V2 is a read-only market-analysis and paper-trading observer for MetaTrader 5. It displays transparent technical guidance and never submits broker orders.

## V0.2 capabilities

- Read-only MetaTrader 5 quotes and OHLCV candles.
- EMA, RSI and ATR indicators.
- Trend, market structure, support and resistance analysis.
- Multi-timeframe confirmation.
- Spread filtering.
- Reference stop-loss, take-profit and position sizing.
- Daily loss-limit calculations.
- Append-only JSONL audit trail.
- Paper-trading account simulation with daily loss protection.
- Localhost JSON bridge for the MT5 chart panel.
- Always-on-top desktop observer.
- Automated unit tests and GitHub Actions CI.

## Installation

Python 3.10+ is required.

Core/CI dependencies:

    python -m pip install -r requirements.txt

For live MetaTrader 5 data on Windows with MT5 installed:

    python -m pip install -r requirements-mt5.txt

Start the observer:

    python -m vanes.app

MetaTrader 5 must be running for live quotes and candles.

## Configuration

Defaults can be overridden with environment variables:

    VANES_SYMBOL=EURUSD
    VANES_TIMEFRAME=M15
    VANES_CONFIRMATION_TIMEFRAME=H1
    VANES_ACCOUNT_BALANCE=10000
    VANES_RISK_PERCENT=1
    VANES_MAX_DAILY_LOSS_PERCENT=3
    VANES_MAX_SPREAD_POINTS=25
    VANES_AUDIT_PATH=data/vanes_audit.jsonl
    VANES_DRY_RUN=1

VANES_DRY_RUN is retained as a safety setting. This release contains no broker-order implementation.

## MT5 chart panel

Open MetaEditor and compile:

    mt5/VANES_Bridge.mq5

Attach it to a chart. In MetaTrader 5, add this allowed WebRequest URL:

    http://127.0.0.1:8765

The panel reads the local Python state endpoint. It does not place, modify, or close trades.

## Paper trading

Paper trading is an internal simulation only. It never calls an MT5 trade API. The simulator tracks balance, realized P/L, open/closed simulated trades and a daily loss limit.

The desktop observer does not automatically enter paper positions. This is intentional: the first paper release is non-invasive. The PaperTrader class can be driven by a future backtest/replay workflow.

## Testing

Run:

    python -m unittest discover -s tests -v
    python -m compileall -q vanes tests
    pylint vanes

GitHub Actions runs syntax checks, unit tests and Pylint on Python 3.10, 3.11 and 3.12.

## Architecture

    MetaTrader 5
         |
         +-- MQL5 chart observer
         |
         +-- Python read-only adapter
                    |
                    v
             VANES analysis core
              +-- indicators
              +-- structure
              +-- strategy
              +-- risk
              +-- paper simulation
              +-- audit
                    |
                    v
              desktop UI / JSON bridge

## Safety boundary

VANES-AI V2 currently has no automatic broker order execution. It is designed to inform the user and record paper-analysis results. Any future live-order module should be separately designed, tested, permissioned and disabled by default.
