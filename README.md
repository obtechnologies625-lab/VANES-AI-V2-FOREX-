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

## Historical backtesting

VANES includes a deterministic candle-replay engine in `vanes/backtest.py`.

The replay engine:

- Uses only candles available before each signal (no look-ahead).
- Evaluates the existing `RuleBasedStrategy`.
- Enters at the next candle open after a signal.
- Builds SL/TP from ATR using the same risk-plan logic as the observer.
- Exits at stop or target; if both are touched in one candle, stop is treated as first for a conservative result.
- Closes any remaining position at the final candle close.
- Reports net P/L, return, trade count, wins/losses, win rate, gross profit/loss, profit factor and maximum drawdown.
- Never submits broker orders.

Example:

    from vanes.backtest import BacktestConfig, run_backtest

    report = run_backtest(
        candles,
        config=BacktestConfig(
            starting_balance=10000,
            risk_percent=1,
            value_per_price_unit=1,
        ),
    )

    print(report.net_pnl, report.max_drawdown, report.win_rate_percent)

`value_per_price_unit` is deliberately explicit because real FX cash-per-price-unit varies by broker, symbol and account currency. It must be calibrated from MT5 symbol metadata before treating a backtest as a broker-accurate P/L estimate.

The current engine is a single-symbol/single-timeframe replay. Multi-timeframe historical alignment and broker-accurate tick economics are separate hardening steps.


### Tick-accurate execution replay

`run_tick_backtest()` replays strategy execution against historical MT5 bid/ask ticks.

- Indicators use only candles strictly before each decision candle.
- BUY entries use ask and BUY exits use bid.
- SELL entries use bid and SELL exits use ask.
- Stops and targets are checked tick-by-tick, removing OHLC ordering ambiguity.
- `MT5Adapter.ticks()` loads historical bid/ask ticks with MT5 `copy_ticks_range()`.
- Broker tick size/value and volume constraints can be supplied through `BacktestConfig`.
- Commission is applied only when explicitly supplied.
- Swaps, historical slippage and changing broker contract settings are not invented.
### Forex accuracy boundary

For broker-accurate backtests, populate `BacktestConfig` with the MT5 symbol's `trade_tick_size`, `trade_tick_value`, `volume_min`, `volume_max`, and `volume_step` from `MT5Adapter.symbol_spec()`. The engine then sizes volume from actual cash risk instead of assuming one generic price-unit value.

Execution costs are explicit: `spread_price` models the quoted spread and `commission_per_lot` models commission. Historical OHLC candles do not contain historical bid/ask spreads, commissions, swaps, or tick-by-tick execution, so an OHLC-only backtest cannot honestly claim tick-level broker accuracy. For that level of accuracy, VANES must replay MT5 tick data and the broker's historical contract/symbol settings.

The backtester sorts MT5 candles chronologically, never uses future candles for a signal, and applies conservative stop-first handling when one OHLC candle touches both stop and target.
