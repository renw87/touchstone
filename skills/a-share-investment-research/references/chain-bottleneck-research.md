# Chain Bottleneck Research

Use this reference when the task starts from a hot theme, industry direction, supply-chain bottleneck, or "which stocks/funds should be researched first".

## Core Path

1. Define scope: market, theme, time window, stock/fund universe, and whether the output is a broad scan or a single-company challenge.
2. Translate the story into a system change:
   `demand wave -> system pressure -> required technical change -> constrained layer`.
3. Rank industry-chain layers before ranking companies.
4. Find scarce layers using:
   - low supplier count;
   - long qualification or customer certification;
   - hard expansion because of equipment, permits, know-how, purity, yield, or cycle time;
   - customer urgency shown by orders, capacity reservations, prepayments, tenders, or price acceptance;
   - market still treating the company as an old category.
5. Build a candidate universe across leaders, upstream suppliers, equipment, materials, testing, infrastructure, adjacent beneficiaries, and lower-priority popular names.
6. Grade evidence and downgrade weak claims.
7. Output research priorities, not buy/sell commands.

## Evidence Ladder

Strong evidence:

- exchange filings, annual/interim/quarterly reports, official announcements;
- exchange inquiry letters, regulatory/project approvals, environmental/energy approvals;
- official contracts, orders, tenders, capacity reservations, customer certification records;
- patents, standards, technical papers, official investor relations materials.

Medium evidence:

- reputable financial media, trade publications, industry association data;
- company website/product pages;
- specialist or sell-side research with visible assumptions;
- supplier/customer cross-checks from public disclosures.

Weak evidence:

- KOL posts, social media, screenshots, forum claims, unexplained price/volume moves.

Weak evidence may generate leads, but cannot justify `pilot_build` or `add`.

## Bottleneck Score Factors

Use `scripts/theme_chain.py` with `--theme-input` to score layers and candidates. Each factor is 0-5:

- `demand_inflection`: demand wave is visible and accelerating.
- `architecture_coupling`: the layer is tightly coupled to the new system design.
- `bottleneck_severity`: customers cannot scale without this layer.
- `supplier_concentration`: few qualified suppliers.
- `expansion_difficulty`: hard to expand because of equipment, yield, permits, certification, or know-how.
- `evidence_quality`: public evidence strength.
- `valuation_disconnect`: market classification or valuation may not reflect the new role.
- `catalyst_timing`: near-term events can verify or falsify the thesis.

Penalties are also 0-5:

- `dilution_financing`
- `governance`
- `geopolitics`
- `liquidity`
- `hype_risk`
- `accounting_quality`
- `cyclicality`
- `alternative_design_risk`

## Output Shape

For theme scans, report:

- layer ranking first;
- candidate research list second;
- fund/ETF direction only after explaining underlying layer exposure;
- evidence strength for each top candidate;
- popular areas that rank lower and why;
- next checks;
- what would make the view weaker.

For single-company challenges, answer:

- what exactly the company constrains;
- where it sits in the chain;
- whether evidence is strong, medium, weak, or needs checking;
- what the market may be overestimating;
- what data would force downgrade.

## A-Share Source Path

Prefer:

- 年报、半年报、季报、临时公告；
- 交易所问询函、互动易、上证 e 互动；
- 招投标、中标公告、客户认证；
- 环评、能评、地方项目备案、产能建设记录；
- 专利、标准、行业协会资料；
- 应收、存货、合同负债、经营现金流、毛利率；
- 关联交易、资产注入、定增、可转债、股权质押。
