# Baseline Backtest

Use `scripts/backtest_signal.py` for a simple, auditable baseline before using vectorbt/Qlib.

Supported rules:

- `breakout`: close breaks prior N-day high, optionally requiring amount expansion. Fixed take-profit / time exit.
- `trend_follow`: `breakout` filtered by an uptrend (close above the trend MA, default MA60), exited by a trailing stop (`--trail-pct`, default 12%) or an MA20 break instead of a fixed take-profit — lets winners run.
- `ma_cross`: short moving average crosses above long moving average.

## Rule Selection (from a 5-stock 2024–2026 backtest)

`trend_follow` vs `breakout`, same basket, vs buy-and-hold:

- **Drawdown improved**: average max drawdown 18% → 12% (e.g. 宁德 22%→9%, 平安 16%→9%).
- **Quality improved on trending quality names**: 宁德 +4%→+24%, 平安 +2%→+18%; beat buy-and-hold 1/5 → 2/5.
- **Trade-offs (honest)**: the MA60 filter suppresses counter-trend rebounds in *falling* names (隆基 +25%→-1%); a 12% trailing stop can be too tight for very high-volatility names (工业富联 +98%→+92%).
- **Neither beats buy-and-hold in a strong bull market** (avg +23% vs +130%): timing underperforms holding in single-direction uptrends — a structural property of timing, not a bug. Real gains there come from position sizing / regime allocation, not a fancier entry rule.

Guidance: prefer `trend_follow` when drawdown control matters or for quality uptrending names; `breakout` can still catch counter-trend rebounds in weak names. Keep both; pick by the stock's regime.

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
