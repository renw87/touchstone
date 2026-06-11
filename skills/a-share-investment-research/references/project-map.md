# Research Pattern Map

Use this map to choose the right local capability during A-share research.

## Deep Stock Research

Use for:

- full A-share analysis.
- trap checks: ST/delisting, financial anomalies, goodwill, receivables, inventory, pledge, regulatory inquiries, earnings forecast reversals.
- Dragon-Tiger list and Chinese market microstructure awareness.
- converting qualitative conclusions into explicit checks.

Local implementation:

- `references/a-share-data.md` for fields.
- `references/research-quality-gates.md` for coverage and self-review gates.
- `references/signal-policy.md` for signal boundaries.

## Multi-Agent Research Team

Use for:

- separate analysts for fundamentals, sentiment/news, technicals, research debate, trading, and risk.
- contradiction review before signal upgrade.

Local implementation:

- `references/agent-roles.md`.
- the final signal is produced only by the orchestrator after bear-case and risk checks.

## Chain Bottleneck Research

Use for:

- starting from hot themes.
- breaking down the industry chain.
- finding bottlenecks and beneficiaries.
- mapping back to stocks and fund directions.

Local implementation:

- `references/chain-bottleneck-research.md`.
- `scripts/theme_chain.py`.
- theme chain path: theme/policy -> segment -> company exposure -> revenue/profit transmission -> evidence -> valuation expectation gap.

## Quality Investing Review

Use for:

- quality-first inspection: good business, moat, cash flow, management, capital allocation, margin of safety.
- cold review before excitement-driven entries.

Local implementation:

- fundamental, valuation, and bear-case sections.
- low valuation cannot override deteriorating fundamentals.

## Quant Workbench

Use for:

- AI research -> strategy rules -> backtest -> parameter scan -> paper tracking -> alerting -> review.

Local implementation:

- `references/workflow.md` phases.
- backtest score is mandatory before `pilot_build` or `add` in automated workflows.

## A-Share Engineering Stack

Use these with the skill when implementing code:

- AKShare or Tushare for Chinese market data.
- DuckDB + Parquet for reproducible local storage.
- vectorbt for fast signal verification.
- Qlib for factor/model research.
- Backtrader for event-driven strategies.
- 巨潮资讯、上交所、深交所、北交所 for primary announcements.
