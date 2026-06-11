---
name: investor-panel
description: Use when the user wants an investment committee, debate, quality-investing check, growth-vs-value comparison, bear case, or multi-perspective review of an A-share thesis. 输出投委会式分歧和决策边界。
metadata:
  short-description: 多视角投委会和反方审查
---

# Investor Panel

Use this skill after the main research draft and before trade-level signals.

## Panel Seats

- Value quality: moat, cash flow, ROE, capital allocation.
- Growth: market space, growth durability, product cycle.
- China market: policy, regulation, ST, unlocks, pledges, LHB, price limits.
- Technical: trend, support/resistance, volatility.
- Quant: rule clarity, backtest, drawdown, sample risk.
- Bear case: strongest reason the thesis fails.

## Output

- strongest long thesis.
- strongest bear thesis.
- unresolved evidence gaps.
- what evidence would upgrade, downgrade, or exit.
- final committee boundary: `no_trade`, `watch`, or eligible for signal evaluation.

## Boundary

The panel does not set trade prices by itself. It gates whether the main research Skill may evaluate `pilot_build` or `add`.
