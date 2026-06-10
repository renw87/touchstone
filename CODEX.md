# Touchstone — Codex Project Map

**Touchstone** is an evidence-based A-share investment research Skill/Plugin plus Harness, modeled after UZI-Skill's root-level layout.

## First 60 Seconds

1. The plugin root is the repository root.
2. Primary Skill: `skills/a-share-investment-research/SKILL.md`.
3. Harness runner: `python run.py <symbol> --name <name>`.
4. Harness records live under `harness/runs/{date}/{symbol}/`.

## Directory Map

```text
.codex-plugin/      Codex plugin manifest
.cursor/            Cursor rules
skills/             Agent-loadable skills
commands/           Command prompts for common workflows
agents/             Analyst role panels and orchestration notes
harness/            Task runner, schemas, evals, run records
docs/               Design notes and reference docs
hooks/              Future session/start hooks
run.py              Root runner wrapper
```

## Main Workflows

```bash
python run.py 300750.SZ --name 宁德时代
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/300750.SZ/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-data data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代
python harness/runners/evaluate_run.py harness/examples/complete_run
python skills/a-share-investment-research/scripts/validate_signal.py harness/examples/complete_run/signal.json
```

## Signal Boundary

All outputs are research assistance only. No unconditional buy/sell/full-position language. Any `pilot_build` or `add` signal must include trigger, stop, position limit, take-profit plan, evidence, bear case, and backtest summary.
