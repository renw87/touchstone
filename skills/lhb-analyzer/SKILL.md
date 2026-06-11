---
name: lhb-analyzer
description: Use when analyzing A-share 龙虎榜, hot-money seats, institutional seats, short-term capital flow, unusual turnover, or whether LHB flow supports or contradicts a stock thesis. 输出资金行为解释和风险，不单独生成买入信号。
metadata:
  short-description: A 股龙虎榜和短线资金行为分析
---

# LHB Analyzer

Use this skill to interpret Dragon-Tiger list data and short-term capital behavior.

## Inputs

- stock code and name.
- LHB date and reason.
- buy/sell top seats.
- amount, turnover, price change.
- recent K-line context.

## Analysis

- classify seats: institution, quant, known hot money, branch, unknown.
- identify one-day speculation vs sustained flow.
- compare LHB amount with daily amount and float market cap.
- compare same-sector LHB activity to judge whether this stock is the recognizable leader or only a follower.
- flag high-risk patterns: post-limit-board distribution, excessive turnover, repeated unknown seats.

## Output

- LHB summary.
- seat interpretation.
- flow score adjustment.
- risk notes.
- whether this confirms, contradicts, or does not affect the main thesis.

## Boundary

LHB can modify `flow_score` and risk. It cannot independently upgrade to `pilot_build` or `add`.
If LHB is the main bullish evidence while fundamentals, valuation, trap scan, or backtest are missing, cap the main signal at `watch`.
