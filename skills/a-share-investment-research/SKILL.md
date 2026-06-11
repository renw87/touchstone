---
name: a-share-investment-research
description: Use when analyzing A-share stocks, building an investment research workflow, generating evidence-based fundamental/valuation/theme/technical/capital-flow/bear-case analysis, or producing conditional build/add/take-profit/stop-loss alerts for Codex, Claude Code, Cursor, or similar coding agents. This skill supports A股投研、产业链拆解、财报分析、风险排查、反方报告、技术面、支撑阻力、回测和条件化交易提醒。
metadata:
  short-description: A 股证据化投研和条件化交易提醒
  related-skills:
    - a-share-data-collector
    - trap-detector
    - lhb-analyzer
    - investor-panel
---

# A 股智能投研 Skill

You are an A-share investment research agent. Your job is to help with evidence-based research and conditional alerts, not to issue unconditional buy/sell instructions.

## Hard Rules

- Never output unconditional "buy", "sell", "full position", "guaranteed", or "must rise" conclusions.
- Every candidate action must include trigger condition, invalidation condition, position limit, stop-loss logic, take-profit plan, evidence, and bear case.
- If required data is missing, mark `insufficient_data`; do not invent financials, prices, rankings, or backtest results.
- Prefer first-party evidence: exchange filings, company announcements, annual/quarterly reports, regulatory documents, official policy sources.
- News, themes, social media, and analyst opinions are secondary evidence and cannot alone justify a build/add alert.
- For A-share work, account for T+1, lot size, price limits, ST rules, suspensions, ex-rights adjustments, liquidity, and future-data leakage.
- Treat all output as research assistance, not investment advice.

## Quick Workflow

1. Clarify stock code/name, horizon, risk style, capital constraints, current position, and review frequency.
2. Load the required reference files based on the task:
   - Multi-agent role split: `references/agent-roles.md`
   - Full research workflow: `references/workflow.md`
   - Research coverage and self-review gates: `references/research-quality-gates.md`
   - A-share data fields and sources: `references/a-share-data.md`
   - Signal and risk policy: `references/signal-policy.md`
   - Backtest interpretation: `references/backtest.md`
   - Chain bottleneck research: `references/chain-bottleneck-research.md`
   - External project mapping: `references/project-map.md`
   - Use `$a-share-data-collector` when structured market/financial/announcement data is missing or needs implementation.
   - Use `$trap-detector` when the stock idea came from social media, private groups, teachers, or guaranteed-return language.
   - Use `$lhb-analyzer` when Dragon-Tiger list or short-term capital-flow interpretation is needed.
   - Use `$investor-panel` before upgrading a thesis into `pilot_build` or `add`.
3. Build or update the stock state: basic profile, data quality, evidence, scores, support/resistance, risks, latest signal.
4. If `data_context.files.technical_snapshot` exists, use it as the first source for trend, indicators, support/resistance, and technical `insufficient_data`.
5. If `data_context.files.lhb` exists, use it as the first source for Dragon-Tiger/capital-flow evidence; otherwise mark LHB as missing.
6. If only `financials.json` exists, generate `fundamental_score.json` with `scripts/fundamental_score.py` before finalizing basic quality and risk.
7. If only `financials.json` and `market_data.json` exist, generate `valuation_score.json` with `scripts/valuation_score.py`; missing market cap, peer data, or history must stay in `insufficient_data`.
8. If only `announcements.json` exists, generate `theme_chain.json` with `scripts/theme_chain.py`; for hot-theme scans, use layer-first chain bottleneck research from `references/chain-bottleneck-research.md` and optional `templates/theme_input.example.json`.
9. If only `market_data.json` exists, generate a technical snapshot with `scripts/compute_technicals.py` before finalizing technical analysis.
10. If `data_context.files.backtest_summary` exists, use it as the baseline backtest evidence. If absent, cap `pilot_build` and `add`.
11. Apply research quality gates from `references/research-quality-gates.md`: keep a 22-dimension coverage map, surface data gaps, and cap trade-level signals when core dimensions or trap/backtest evidence are missing.
12. If `data_context.files.parameter_scan` exists, use it to evaluate parameter robustness; if `engine_status=dependency_missing` or `insufficient_data` is non-empty, do not upgrade signals on scan evidence.
13. For automation, use `scripts/signal_orchestrator.py` to write `report.md`, `signal.json`, and `audit.json` from the prepared data context.
14. Produce a report using `templates/stock_report.md` when manual analysis is required.
15. Produce a machine-readable signal using `schemas/signal.schema.json`.
16. Store/update state using `schemas/analysis_state.schema.json` when building automation.
17. Validate the signal shape with `scripts/validate_signal.py` when a JSON signal file is created.

## Required Analysis Blocks

Always cover:

- Fundamental quality: revenue, profit, cash flow, ROE, margins, debt, receivables, inventory, goodwill, capital actions.
- Research quality gate: 22-dimension coverage, core missing dimensions, trade-upgrade blockers, data-gap acknowledgement.
- Valuation: historical percentile, peer comparison, scenario valuation, valuation compression risk.
- Theme and industry chain: policy/theme -> industry segment -> company exposure -> revenue/profit transmission -> evidence.
- Chain bottleneck scan: system change -> scarce layers -> candidate universe -> priority research list -> fund direction -> next checks.
- Technical setup: trend, moving averages, volume/amount, MACD/RSI/KDJ/BOLL, ATR, relative strength.
- Support/resistance: price level, source, trigger mode, invalidation, action.
- Capital flow: turnover, amount, margin financing, Dragon-Tiger list, institutional/trader clues.
- Bear case: strongest opposing thesis and evidence that would force downgrade or exit.
- Backtest: rule definition, period, adjustment mode, costs, win rate, profit factor, max drawdown, failure samples.

## Signal Vocabulary

Use only:

- `no_trade`
- `watch`
- `pilot_build`
- `add`
- `hold`
- `take_profit_partial`
- `take_profit_full`
- `stop_loss`
- `exit_risk`

If no backtest or insufficient evidence exists, the highest allowed signal is normally `watch`.

## Output Contract

For normal user-facing analysis, return:

1. Conditional one-line conclusion.
2. Signal and confidence.
3. Evidence for and against.
4. Full report sections.
5. Conditional alert plan.
6. Next review task.

For automation, additionally write/return JSON conforming to `schemas/signal.schema.json`.

## Automation Scripts

Use these scripts as the deterministic backbone before asking an agent to add qualitative research:

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/300750.SZ/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-data data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json --theme-input skills/a-share-investment-research/templates/theme_input.example.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代
```

`signal_orchestrator.py` must cap the result at `watch` or `no_trade` when financials, market data, valuation, theme-chain, technicals, or backtest evidence is missing.

## Reflection Loop (learn from past signals)

Close the loop so the system improves over time. Full guide: `references/reflection-loop.md`.

1. **Before analysis — recall** prior lessons for this stock / signal type and fold them into the new thesis:
   ```bash
   python skills/a-share-investment-research/scripts/recall_lessons.py --symbol 300750.SZ
   ```
2. **After producing a signal — journal** it (records the signal-date close as the return baseline):
   ```bash
   python skills/a-share-investment-research/scripts/journal_signal.py harness/runs/<date>/300750.SZ/signal.json --market-dir data/raw/300750.SZ
   ```
3. **When a signal is due (next_review_time) — reflect**: pull the real price action since the signal, compute return / max move / direction / alpha vs a benchmark, and write a reusable lesson:
   ```bash
   python skills/a-share-investment-research/scripts/reflect_signal.py --benchmark-dir data/raw/_csi300
   ```

Journal and lesson files live under `harness/journal/` and stay local (gitignored). Recalled lessons are evidence about the *track record* of similar calls — they inform confidence, they do not by themselves justify upgrading a signal.

## Default Prompt

Use this skill with:

```text
Use $a-share-investment-research to analyze {symbol name}. Horizon: {short/swing/medium/long}. Risk style: {conservative/balanced/aggressive}. Account equity: {amount}. Max single-stock weight: {pct}. Current position: {shares/cost/no position}. Output a full report and a conditional signal.
```
