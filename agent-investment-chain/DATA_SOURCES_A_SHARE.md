# A 股数据源和字段要求

## 优先数据源

| 数据类型 | 免费/常用来源 | 更稳定来源 | 关键注意事项 |
|---|---|---|---|
| 日线/分钟线 | AKShare, BaoStock | Tushare, JoinQuant, Wind, Choice | 必须明确前复权/后复权/不复权 |
| 财报 | AKShare, BaoStock, 巨潮资讯 | Tushare, Wind, Choice | 优先合并报表，区分扣非和非经常性损益 |
| 公告 | 巨潮资讯, 交易所官网 | Wind, Choice | 保留公告链接和发布日期 |
| 行业分类 | 申万, 中信, 证监会行业 | Wind, Choice | 同业比较必须行业口径一致 |
| 热点/新闻 | 财联社, 证券时报, 交易所, 政策官网 | 商业新闻库 | 新闻不能替代一手公告 |
| 龙虎榜 | 交易所, AKShare | Tushare, Wind | 只作为资金线索，不等于确定买入 |
| 融资融券 | 交易所, AKShare | Tushare, Wind | 注意股票是否为两融标的 |
| 指数 | 中证指数, AKShare | Wind, Choice | 用于市场环境和相对强弱 |

## 必备字段

### 基础信息

- `symbol`
- `name`
- `exchange`
- `board`
- `industry`
- `list_date`
- `is_st`
- `is_suspended`
- `market_cap`
- `float_market_cap`

### 行情

- `date`
- `open`
- `high`
- `low`
- `close`
- `pre_close`
- `volume`
- `amount`
- `turnover_rate`
- `adj_factor`
- `limit_up`
- `limit_down`

### 财务

- `report_period`
- `revenue`
- `net_profit_parent`
- `net_profit_excl_nonrecurring`
- `operating_cash_flow`
- `gross_margin`
- `net_margin`
- `roe`
- `roic`
- `debt_to_asset`
- `interest_bearing_debt`
- `accounts_receivable`
- `inventory`
- `goodwill`

### 公告和事件

- `event_date`
- `publish_time`
- `event_type`
- `title`
- `source_url`
- `summary`
- `impact_direction`
- `confidence`

### 热点和产业链

- `theme`
- `theme_stage`
- `policy_source`
- `industry_chain_segment`
- `company_exposure`
- `revenue_link`
- `evidence_url`
- `evidence_strength`

## 数据质量规则

- 行情数据必须校验复权方式，不同复权方式不能混用。
- 财报必须区分公告期和报告期，回测中不能使用未来财报数据。
- 公告、新闻、研报必须保留发布时间，避免未来函数。
- 缺失关键字段时必须标记 `insufficient_data`。
- 不同来源数据冲突时，报告冲突并优先使用交易所、巨潮、公司公告。

## A 股特殊处理

- 主板通常 10% 涨跌幅，科创板/创业板通常 20%，北交所通常 30%，ST 通常 5%。
- T+1 下，当日买入不能当日卖出。
- 涨跌停、停牌、流动性不足会导致回测信号不可成交。
- 除权除息、送转、配股必须通过复权价格处理。
- 重大解禁、减持、质押、业绩预告、监管问询需要进入风险事件表。
