# Score Valuation

Use this after financial and market data collection.

```bash
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-data data/raw/300750.SZ/market_data.json
```

With explicit valuation inputs:

```bash
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-cap 1000000000000 --price 200 --total-shares 5000000000 --peers data/raw/300750.SZ/peers.json --history data/raw/300750.SZ/valuation_history.json
```

Output:

```text
data/raw/300750.SZ/valuation_score.json
```

Missing market cap, latest price, peer valuation, or historical percentile must remain in `insufficient_data` and must limit signal upgrades.
