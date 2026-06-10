# Touchstone — Agent Instructions

Use this repository (**Touchstone**) as a root-level Skill/Plugin project. The main product shape follows UZI-Skill:

- `skills/` contains callable skills.
- `commands/` contains reusable command prompts.
- `agents/` contains analyst panel definitions.
- `harness/` turns skills into auditable runs.

## Priority Order

When asked to analyze an A-share stock:

1. Read `skills/a-share-investment-research/SKILL.md`.
2. Read only the needed references in `skills/a-share-investment-research/references/`.
3. For common workflows, use `commands/analyze-stock.md`, `commands/quick-scan.md`, or `commands/scan-trap.md`.
4. If creating a run, use `python run.py <symbol> --name <name>`.
5. If data is needed, use `skills/a-share-data-collector/scripts/collect_snapshot.py`, `skills/a-share-investment-research/scripts/fundamental_score.py`, `skills/a-share-investment-research/scripts/valuation_score.py`, `skills/a-share-investment-research/scripts/theme_chain.py`, `skills/a-share-investment-research/scripts/compute_technicals.py`, `skills/a-share-investment-research/scripts/backtest_signal.py`, and `skills/a-share-investment-research/scripts/vectorbt_scan.py`.
6. For deterministic automation, use `skills/a-share-investment-research/scripts/signal_orchestrator.py` to write `report.md`, `signal.json`, and `audit.json` into the run directory.
7. Validate with `harness/runners/evaluate_run.py`.

## Never Do

- Do not output unconditional trading instructions.
- Do not fabricate prices, financials, announcements, valuation percentiles, or backtest results.
- Do not upgrade beyond `watch` if evidence or backtest is missing.
- Do not treat theme popularity as sufficient for `pilot_build` or `add`.

## Skill Selection

- `a-share-investment-research`: full stock research and conditional signals.
- `a-share-data-collector`: data source planning and collection contracts.
- `trap-detector`: promotion/pump-risk scan.
- `lhb-analyzer`: Dragon-Tiger list and capital-flow interpretation.
- `investor-panel`: debate-style review from value, growth, macro, technical, China-market, and quant perspectives.
