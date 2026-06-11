# Research Quality Gates

Use this reference to keep stock research auditable before any trade-level signal is generated.

## Core Principles

- Treat stock research as a staged pipeline: collect data, compute deterministic scores, then require agent judgment before a trade-level signal.
- Keep a 22-dimension coverage map, even when some dimensions are marked `missing` or `not_applicable`.
- Separate quick scans from standard and deep research so runtime and evidence requirements are explicit.
- Use self-review gates before report finalization: data gaps, empty dimensions, unsupported claims, weak backtests, and missing bear case must be visible.
- Use trap detection and Dragon-Tiger analysis as risk modifiers, not as standalone buy evidence.

## Depth Profiles

| Depth | Use | Minimum Work |
|---|---|---|
| `quick` | First pass, watchlist pruning | basic profile, financial snapshot if available, technical snapshot, valuation availability, trap trigger check, no-trade gates. Output only `no_trade` or `watch`. |
| `standard` | Normal single-stock analysis | core financials, valuation, theme/chain, technicals, support/resistance, flow/LHB, bear case, backtest, parameter scan if available, conditional signal. |
| `deep` | Build/add candidate or committee-style review | standard profile plus 22-dimension coverage, qualitative deep dive on weak dimensions, investor-panel debate, scenario valuation, thesis invalidation plan, self-review gate. |

## Preflight Profile

`0_basic` is a preflight gate, not counted inside the 22 research dimensions:

- stock code, name, exchange, board, industry, market cap, float cap, ST/suspension state, liquidity.
- evidence: `market_data.json`, `collection_status.json`, or explicit source notes.

## 22-Dimension Coverage Map

| ID | Dimension | Touchstone Evidence |
|---|---|---|
| `1_financials` | Financial quality | `financials.json`, `fundamental_score.json` |
| `2_kline` | K-line and trend | `market_data.json`, `technical_snapshot.json` |
| `3_macro` | Macro exposure | macro context, rates, FX, commodities, market regime notes |
| `4_peers` | Competitors | peer list, industry classification, peer valuation |
| `5_chain` | Upstream/downstream | `theme_chain.json` industry-chain layers and company exposure |
| `6_research` | Analyst/research view | consensus forecast, report count, target-price dispersion, or explicit missing note |
| `7_industry` | Industry cycle | industry growth, penetration, capacity, policy cycle, theme-chain layer ranking |
| `8_materials` | Materials/cost | cost drivers, commodity inputs, supplier concentration |
| `9_futures` | Futures/commodity links | related futures, inventory, price trend, or not-applicable rationale |
| `10_valuation` | Valuation | `valuation_score.json`; must state PE/PB/PEG/history or mark missing |
| `11_governance` | Governance | pledge, reduction, related-party deals, violations, incentives |
| `12_flow` | Capital flow | turnover, amount, margin financing, northbound/southbound when available |
| `13_policy` | Policy/regulation | official policy source, regulatory change, subsidy/constraint |
| `14_moat` | Moat/IP | patents, switching cost, network effects, cost advantage, brand, license |
| `15_events` | Event/catalyst | `announcements.json`, official filings, approval/order/M&A/event calendar |
| `16_lhb` | Dragon-Tiger list | `lhb.json`, seat interpretation, institution vs hot-money behavior |
| `17_sentiment` | Sentiment | social/news/forum heat with source quality and promotion-risk separation |
| `18_trap` | Pump/scam risk | `$trap-detector` result, 8-signal table, user-source keyword boost |
| `19_contests` | Fund/portfolio holders | fund holders, public portfolios, strategy overlap; optional if unavailable |
| `20_valuation_models` | Scenario valuation models | DCF/comps/asset/liquidation/LBO-style cross-check when supported |
| `21_research_workflow` | Institutional workflow | initiation, earnings preview, catalyst calendar, thesis tracker |
| `22_deep_methods` | Deep decision methods | IC memo, DD checklist, Porter, unit economics, segmental model, bear debate |

## Gate Rules

- `quick` mode may finish with missing dimensions, but cannot output above `watch`.
- `standard` mode must show every missing core dimension in `audit.insufficient_data`.
- `deep` mode should cover at least 15 of 22 dimensions or explicitly acknowledge why the missing dimensions cannot be collected.
- `pilot_build` and `add` require no missing core gates: preflight `0_basic`, `1_financials`, `2_kline`, `10_valuation`, `15_events`, `18_trap`, and `backtest_summary`.
- If `18_trap` is missing and the idea came from social media, private groups, "teacher", "inside information", or guaranteed-return language, cap at `watch` or `no_trade`.
- If `16_lhb` is the main bullish evidence, cap at `watch`; LHB can confirm flow only after fundamentals, valuation, and backtest are adequate.
- If a dimension uses fallback or weak evidence, keep it visible and do not let it independently upgrade the signal.

## Agent Review Duties

Before upgrading beyond `watch`, write or verify:

- data freshness and source quality.
- dimension commentary for the weakest or most thesis-critical dimensions.
- strongest bear case with concrete invalidation evidence.
- contradiction log: where valuation, technicals, flows, and theme evidence disagree.
- `data_gap_acknowledged`: dimensions attempted but still unavailable.

## Quant Rule Families

Use rule families instead of named-person or named-project opinions:

- quality/value/growth/profitability.
- technical trend and support/resistance.
- valuation percentile and peer gap.
- capital-flow and LHB behavior.
- event/catalyst validation.
- risk/fraud/accounting/liquidity gates.
- chain bottleneck and supply-chain scarcity.

These rule families can feed future scanners, but they do not override the signal policy.
