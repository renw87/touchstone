# Compute Technicals

Use this after market data collection.

```bash
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
```

Output:

```text
data/raw/300750.SZ/technical_snapshot.json
```

The snapshot includes moving averages, MACD, RSI, ATR, trend flags, and support/resistance levels. Missing bar history is recorded in `insufficient_data`.
