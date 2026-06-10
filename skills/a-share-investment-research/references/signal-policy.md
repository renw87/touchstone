# Signal Policy

Signals are conditional research alerts. They are not direct investment advice.

## Allowed Signals

| Signal | Meaning |
|---|---|
| `no_trade` | Risk too high or conditions insufficient |
| `watch` | Enter or stay in watchlist |
| `pilot_build` | Small trial position only |
| `add` | Add only after confirmation and risk check |
| `hold` | Hold and update stop/take-profit plan |
| `take_profit_partial` | Reduce position in batches |
| `take_profit_full` | Exit after target/risk event |
| `stop_loss` | Exit by risk discipline |
| `exit_risk` | Exit due to fundamental/event/liquidity deterioration |

## No-trade Gates

If any gate is active, the maximum signal is `watch` or `no_trade`:

- ST, delisting risk, or credible financial fraud concern.
- Suspension, continuous one-price limit boards, or unrealistic liquidity.
- Daily amount below user requirement.
- Key financial data missing or conflicted.
- Major lawsuit, regulatory inquiry, debt default, high pledge risk without explanation.
- Backtest is negative expectation or drawdown exceeds user limit.

## Scoring

Score each 0-5:

- `fundamental_score`
- `valuation_score`
- `theme_score`
- `technical_score`
- `flow_score`
- `risk_score`: higher means more controllable.
- `backtest_score`

Default thresholds:

- `watch`: total >= 20 and no no-trade gate.
- `pilot_build`: total >= 26, technical trigger active, risk >= 3, backtest >= 3.
- `add`: total >= 30, existing position profitable or risk declined, new evidence confirms thesis.
- `take_profit_partial`: target reached, valuation high percentile, or volume/momentum exhaustion.
- `stop_loss`: invalidation level breached, thesis disproved, or portfolio risk exceeded.

## Position Sizing

Trial position:

```text
shares = floor((account_equity * risk_per_trade) / (entry_price - stop_price) / 100) * 100
```

Also cap by:

- max single-stock weight.
- max industry weight.
- liquidity.
- user risk style.

## Add Rules

Add only when:

- first tranche is profitable or risk has objectively declined.
- new evidence strengthens the thesis.
- breakout/pullback confirmation is present.
- total risk remains under budget.

Do not average down unless the original plan explicitly allowed staged entries and fundamentals did not deteriorate.

## Stop Rules

Priority:

1. Fundamental/event thesis invalidation.
2. Technical invalidation by close below support/ATR/MA stop.
3. Time stop.
4. Portfolio/industry risk stop.

Always specify trigger price and whether close confirmation is required.

## Take-profit Rules

Use staged exits:

- First target: previous high, box top, base valuation range, or 1.5R-2R.
- Second target: optimistic valuation, theme climax, exhaustion, or 3R+.
- Trailing: 10/20-day MA break, ATR trailing stop, heavy upper shadow, volume exhaustion.

## Required Alert Fields

- `signal`
- `confidence`
- `trigger_condition`
- `entry_zone`
- `stop_condition`
- `take_profit_plan`
- `position_limit`
- `evidence`
- `bear_case`
- `backtest_summary`
- `next_review_time`
