# LHB Analyzer

Use `$lhb-analyzer` to interpret Dragon-Tiger list and short-term capital-flow clues.

Output:

- date, reason for LHB listing, turnover, amount.
- seat classification: institution, quant, known hot money, unknown.
- net buy/sell interpretation.
- whether flow is confirmation, noise, or risk.

Boundary:

- LHB cannot independently create `pilot_build` or `add`.
- It can only adjust `flow_score` and risk notes in the main research Skill.
