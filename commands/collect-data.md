# Collect Data

Use `$a-share-data-collector` to prepare structured data before a Harness research run.

Standard flow:

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
python run.py 300750.SZ --name 宁德时代
```

If AKShare is unavailable, the collector writes explicit empty contracts and `collection_status.json`; downstream signals must stay capped at `watch`.
