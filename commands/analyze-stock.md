# Analyze Stock

Use `$a-share-investment-research` to run a full A-share stock analysis.

Required user inputs:

- symbol and name.
- horizon: short, swing, medium, long.
- risk style: conservative, balanced, aggressive.
- account equity, max single-stock weight, risk per trade.
- current position.

Output:

- full report using `skills/a-share-investment-research/templates/stock_report.md`.
- conditional signal using `skills/a-share-investment-research/schemas/signal.schema.json`.
- audit notes covering data gaps, evidence, no-trade gates, bear case, backtest, and next review.

Deterministic script chain:

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/300750.SZ/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-data data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
python run.py 300750.SZ --name 宁德时代
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代
```

Boundary:

- Without credible backtest and sufficient evidence, cap signal at `watch`.
