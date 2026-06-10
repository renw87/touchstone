# Agent Roles

These roles can be run by one agent sequentially or by multiple agents in parallel.

## Data Steward

- Fetch and validate prices, financials, announcements, industry, themes, flow, and index data.
- Record source, timestamp, adjustment mode, and missing fields.
- Prefer official filings when sources conflict.

Output: data quality report and `insufficient_data`.

## Fundamental Analyst

- Analyze revenue, net profit,扣非净利, operating cash flow, margins, ROE/ROIC, debt, receivables, inventory, goodwill.
- Separate recurring business improvement from one-off gains.

Output: `fundamental_score` and key doubts.

## Valuation Analyst

- Compare historical PE/PB/PS/dividend yield percentiles.
- Compare relevant peers under the same industry classification.
- Build pessimistic, base, and optimistic valuation scenarios.

Output: `valuation_score` and valuation range.

## Theme And Industry Analyst

- Map theme/policy to industry segment, company exposure, and financial transmission.
- Judge theme stage: start, spread, climax, fade.

Output: `theme_score` and evidence chain.

## Technical Analyst

- Analyze 20/60/120/250-day trends, MACD, RSI, KDJ, BOLL, ATR, amount, volume, and relative strength.
- Identify executable positions: breakout, pullback, failure, exhaustion.

Output: `technical_score`, trigger, stop, and invalidation.

## Support Resistance Analyst

- Identify support/resistance from volume-by-price, previous highs/lows, gaps, moving averages, boxes, and ATR.
- Distinguish watch levels from execution levels.

Output: price table with action and invalidation.

## Capital Flow Analyst

- Review amount, turnover, Dragon-Tiger list, margin financing, institutional/trader clues, and industry ETF behavior.
- Distinguish sustained flow from one-day speculation.

Output: `flow_score`.

## Bear Case Analyst

- Write the strongest opposing thesis.
- Identify assumptions that would invalidate the trade.
- List evidence that forces downgrade or exit.

Output: bear-case strength and risk triggers.

## Backtest Researcher

- Convert the thesis into testable rules.
- Avoid future data: report date and announcement date must be handled separately.
- Include costs, slippage, price-limit constraints, and T+1 assumptions.

Output: backtest summary and `backtest_score`.

## Signal Orchestrator

- Apply no-trade gates, score thresholds, risk budget, and position rules.
- Finalize `signal.schema.json`.

Output: conditional signal and next review task.
