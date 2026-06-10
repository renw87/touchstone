# Vectorbt Scan

Use vectorbt for parameter scanning after market data collection.

```bash
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
```

Common variants:

```bash
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule ma_cross --short-windows 5,10,20 --long-windows 30,60,120
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout --lookbacks 20,60,120 --amount-multipliers 1.0,1.2,1.5
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout --engine skip
```

Output:

- `parameter_scan.json`
- `parameter_scan_report.md`

If vectorbt or pandas is missing, the script writes `engine_status=dependency_missing` and downstream trade-level signals must remain capped.

If vectorbt imports too slowly, use `--engine skip` to write an explicit `engine_status=not_run` scan and keep the main research chain moving.
