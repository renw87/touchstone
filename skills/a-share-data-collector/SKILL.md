---
name: a-share-data-collector
description: Use when planning or implementing A-share data collection for行情、财报、公告、龙虎榜、融资融券、行业、热点、指数、回测输入 using AKShare, Tushare, BaoStock, 巨潮资讯, exchange websites, or local DuckDB/Parquet contracts.
metadata:
  short-description: A 股数据采集契约和源规划
---

# A-share Data Collector

Use this skill to prepare structured data for the research Harness.

## Data Domains

- market bars: daily/weekly/minute prices, volume, amount, turnover, adjustment factor.
- financials: income statement, balance sheet, cash flow, key indicators.
- announcements: publish time, title, source URL, event type, summary.
- capital flow: LHB, margin financing, turnover, amount.
- industry/theme: classification, index, policy, chain segment, exposure.
- market regime: broad indexes, sector indexes, rates, FX if relevant.

## Output

For each data source:

- provider.
- endpoint/table.
- fields.
- refresh cadence.
- quality checks.
- future-data leakage risk.

## Bundled Script

Use the standard-library collector when the user wants a runnable snapshot:

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
```

Behavior:

- `provider=auto` tries AKShare when installed.
- If AKShare is unavailable or fails, it writes explicit empty contracts and records the issue in `collection_status.json`.
- It writes `market_data.json`, `financials.json`, `announcements.json`, `lhb.json`, and `collection_status.json` under `data/raw/{symbol}/`.
- Empty contracts are intentional; downstream research must mark `insufficient_data` and cap trade-level signals.

## Contracts

Use Harness contracts:

- `harness/data_contracts/market_data.schema.json`
- `harness/data_contracts/financials.schema.json`
- `harness/data_contracts/announcements.schema.json`
- `harness/data_contracts/lhb.schema.json`

## Boundary

This skill prepares data. It does not generate trade signals.
