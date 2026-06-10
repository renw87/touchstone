# Backtest Signal

Use the Harness task `harness/tasks/backtest_signal.yaml`.

Baseline script:

```bash
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
```

Parameter scan:

```bash
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
```

Convert an investment thesis into testable rules:

- entry.
- filters.
- exit.
- cost/slippage/tax.
- T+1 and price-limit assumptions.
- sample period and adjustment mode.

Output:

- trade count.
- win rate.
- profit factor.
- max drawdown.
- failed samples.
- whether signal can upgrade beyond `watch`.
