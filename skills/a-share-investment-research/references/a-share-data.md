# A-share Data Requirements

## Priority Sources

| Data | Common sources | Preferred stable sources | Notes |
|---|---|---|---|
| Prices | AKShare, BaoStock | Tushare, JoinQuant, Wind, Choice | State 前复权/后复权/不复权 |
| Financials | AKShare, BaoStock, 巨潮资讯 | Tushare, Wind, Choice | Use consolidated statements |
| Announcements | 巨潮资讯, exchange websites | Wind, Choice | Keep source URL and publish time |
| Industry | 申万, 中信, 证监会 | Wind, Choice | Peer comparison must use same classification |
| News/themes | official policy, 财联社, 证券时报 | paid news DB | Secondary evidence only |
| Dragon-Tiger | exchange, AKShare | Tushare, Wind | Flow clue, not standalone buy evidence |
| Margin financing | exchange, AKShare | Tushare, Wind | Check eligibility |
| Index | 中证指数, AKShare | Wind, Choice | Needed for relative strength |

## Required Fields

Basic:

- `symbol`, `name`, `exchange`, `board`, `industry`, `list_date`
- `is_st`, `is_suspended`, `market_cap`, `float_market_cap`

Market:

- `date`, `open`, `high`, `low`, `close`, `pre_close`
- `volume`, `amount`, `turnover_rate`, `adj_factor`
- `limit_up`, `limit_down`

Financial:

- `report_period`, `publish_date`
- `revenue`, `net_profit_parent`, `net_profit_excl_nonrecurring`
- `operating_cash_flow`
- `gross_margin`, `net_margin`, `roe`, `roic`
- `debt_to_asset`, `interest_bearing_debt`
- `accounts_receivable`, `inventory`, `goodwill`

Events:

- `event_date`, `publish_time`, `event_type`, `title`
- `source_url`, `summary`, `impact_direction`, `confidence`

Theme:

- `theme`, `theme_stage`, `policy_source`
- `industry_chain_segment`, `company_exposure`, `revenue_link`
- `evidence_url`, `evidence_strength`

## Quality Rules

- Do not mix adjustment modes.
- Do not use future financial data in backtests.
- Report period and announcement date are different.
- Keep raw source links for announcements and policy evidence.
- Mark missing core fields as `insufficient_data`.
- If sources conflict, list the conflict and prefer official filings.

## A-share Market Constraints

- Main board usually has 10% price limits; STAR/ChiNext often 20%; BSE often 30%; ST often 5%.
- T+1 means same-day buy cannot be sold the same day.
- Lot size is 100 shares.
- Suspensions and price-limit locks can make backtest fills unrealistic.
- Ex-rights, dividends, bonus shares, and placements require adjusted prices.
- Unlocks, reductions, pledges, performance forecast revisions, and regulatory inquiries must enter risk events.
