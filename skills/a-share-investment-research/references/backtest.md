# Baseline Backtest

Use `scripts/backtest_signal.py` for a simple, auditable baseline before using vectorbt/Qlib.

Supported rules:

- `breakout`: close breaks prior N-day high, optionally requiring amount expansion.
- `ma_cross`: short moving average crosses above long moving average.

Execution assumptions:

- signal is observed at close.
- entry happens at next bar open.
- exit happens at close after T+1 approximation.
- round-trip cost uses `cost_bps`.
- price-limit locked fills are not fully modeled yet.

Required output:

- `backtest_summary.json`
- `backtest_report.md`

## Vectorbt Parameter Scan

Use `scripts/vectorbt_scan.py` to scan parameter grids after the baseline works:

```bash
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
```

Use `--engine skip` when the local vectorbt import is too slow or unavailable but the run still needs an explicit scan artifact:

```bash
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout --engine skip
```

Supported scan rules:

- `breakout`: scan lookback windows and amount multipliers.
- `ma_cross`: scan short/long moving average pairs.

Required output:

- `parameter_scan.json`
- `parameter_scan_report.md`

If `engine_status=dependency_missing` or `engine_status=not_run`, treat the scan as not run. If `insufficient_data` is non-empty or `best` is empty, cap trade-level signals at `watch`.

Do not overfit:

- prefer robust parameter regions over one best parameter.
- penalize tiny trade count.
- include max drawdown and failed samples in the final report.
- never use a vectorbt scan alone to justify `pilot_build` or `add`.

Interpretation:

- If `insufficient_data` is non-empty, cap trade-level signals at `watch`.
- If `trade_count` is 0, treat result as not enough evidence.
- Baseline backtest can support a research hypothesis, but it is not enough alone for `pilot_build` or `add`.

Next implementation stage:

- use point-in-time financial and announcement data to avoid future leakage.
- add vectorbt walk-forward validation and market-regime splits.
