# Orchestrate Signal

Use this after data collection, fundamental scoring, valuation scoring, theme-chain mapping, technical snapshot, baseline backtest, and vectorbt parameter scan.

```bash
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代
```

With explicit account and run directory:

```bash
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代 --account-equity 100000 --max-single-stock-weight 0.15 --risk-per-trade 0.01 --run-dir harness/runs/2026-06-10/300750.SZ
```

Output:

```text
harness/runs/{date}/{symbol}/report.md
harness/runs/{date}/{symbol}/signal.json
harness/runs/{date}/{symbol}/audit.json
```

Action signals are appended to `harness/alerts/alerts.jsonl`. Missing financials, market data, valuation, theme-chain, technicals, trap-risk evidence, core dimensions, or backtest evidence must cap the result at `watch` or `no_trade`.

`audit.json` includes `quality_gates`, a 22-dimension coverage map and max-signal gate.
