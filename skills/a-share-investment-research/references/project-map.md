# External Project Mapping

This skill borrows ideas from the five projects in the Xiaohongshu note, but does not vendor their code or copy private rules. Use them as design references.

## UZI-Skill

Absorb:

- A-share oriented deep analysis.
- Trap checks: ST/退市、财务异常、商誉、应收、存货、质押、监管问询、业绩预告变脸。
- Dragon-Tiger list and Chinese market microstructure awareness.
- Quant rule mindset: conclusions should become explicit checks.

Implement here:

- `references/a-share-data.md` for fields.
- `references/signal-policy.md` for gatekeeping and risk rules.

## TradingAgents

Absorb:

- Multi-agent research team pattern.
- Separate analysts for fundamentals, sentiment/news, technicals, research debate, trading, and risk.

Implement here:

- `references/agent-roles.md`.
- The final signal is produced only by the orchestrator after the bear case and risk checks.

## Serenity Skill

Absorb:

- Start from hot theme, break down the industry chain, find bottlenecks and beneficiaries, then map back to listed stocks.
- Require business exposure and financial evidence, not only topic popularity.

Implement here:

- Theme chain: theme/policy -> segment -> company exposure -> revenue/profit transmission -> evidence -> valuation expectation gap.

## Buffett Skills

Absorb:

- Quality-first inspection: good business, moat, cash flow, management, capital allocation, margin of safety.
- Force a cold review before excitement-driven entries.

Implement here:

- Fundamental, valuation, and bear-case sections.
- Low valuation cannot override deteriorating fundamentals.

## QuantDinger

Absorb:

- Full workbench path: AI research -> strategy rules -> backtest -> paper trading -> alerting -> review.

Implement here:

- `references/workflow.md` phases.
- Backtest score is mandatory before `pilot_build` or `add` in automated workflows.

## Better Additions For A Shares

Use these with the skill when implementing code:

- AKShare or Tushare for Chinese market data.
- DuckDB + Parquet for reproducible local storage.
- vectorbt for fast signal verification.
- Qlib for factor/model research.
- Backtrader for event-driven strategies.
- 巨潮资讯、上交所、深交所、北交所 for primary announcements.
