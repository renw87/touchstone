# Touchstone — A 股证据化投研链路

> *Every thesis, put to the test.* 试金石:每个投资假设,都要在证据与回测里被检验真伪。

**Touchstone** 是一套可移植到 Codex、Claude Code、Cursor 等编码智能体的 A 股投研协议和插件包。目标不是让智能体直接替你买卖，而是让它围绕指定股票持续做证据化分析，并在满足预设条件时输出“候选建仓、加仓、止盈、止损、观望”等提醒。

## 当前主线

当前仓库根目录就是插件工程根：

- [.codex-plugin/plugin.json](.codex-plugin/plugin.json)：Codex 插件 manifest。
- [SKILL.md](skills/a-share-investment-research/SKILL.md)：核心 A 股投研 Skill。
- [CLAUDE.md](CLAUDE.md)：Claude Code 兼容入口。
- [CODEX.md](CODEX.md)：Codex 项目地图。
- [a-share-investment-research.mdc](.cursor/rules/a-share-investment-research.mdc)：Cursor 规则入口。
- [commands](commands)：常用工作流命令。
- [skills](skills)：多 Skill 能力包。
- [harness](harness)：任务编排、运行记录、评测和复盘工程层。

`agent-investment-chain/` 保留为早期蓝图文档，根级 `skills/` + `harness/` 是后续迭代主入口。

推荐执行路径：

1. 用 Skill/Plugin 固定投研行为。
2. 用 Harness 生成单股研究、盘前检查、盘后复盘和回测任务。
3. 用 Codex/Claude Code/Cursor 执行任务并产出 `report.md`、`signal.json`、`audit.json`。
4. 用 Harness 评测脚本检查是否越过信号边界。
5. 接入 AKShare/Tushare/巨潮资讯和 vectorbt/Qlib，把数据和回测自动化。

快速创建一次研究任务：

```bash
python run.py 300750.SZ --name 宁德时代
```

带数据上下文的最小流程：

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider auto
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/300750.SZ/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/300750.SZ/financials.json --market-data data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/300750.SZ/announcements.json --theme-input skills/a-share-investment-research/templates/theme_input.example.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/300750.SZ/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/300750.SZ/market_data.json --rule breakout
python skills/a-share-investment-research/scripts/vectorbt_scan.py data/raw/300750.SZ/market_data.json --rule breakout
python run.py 300750.SZ --name 宁德时代
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代
python harness/runners/evaluate_run.py harness/runs/$(date +%F)/300750.SZ
```

在 PowerShell 中，把最后一行日期替换为当前日期目录，例如 `harness/runs/2026-06-10/300750.SZ`。

## 核心链路

1. 输入股票、投资周期、风险偏好、资金约束和已有仓位。
2. 拉取行情、复权价格、财报、公告、行业、热点、资金流、龙虎榜、指数和同业数据。
3. 分别完成基本面、估值、热点/产业链、技术面、支撑阻力、资金行为、风险和反方报告。
   热点/产业链采用“先排产业链层级，再排公司和基金方向”的瓶颈研究路径。
4. 按 22 维研究质量门槛记录覆盖率、核心缺口、交易升级缺口和数据兜底状态。
5. 将观点转成可验证假设，例如“放量突破 20 日高点且行业强于沪深 300”。
6. 回测同类信号，记录胜率、盈亏比、最大回撤、失败样本。
7. 由信号策略层生成条件化提醒，而不是无条件买卖指令。
8. 每日/每周复盘：证据是否改变、触发条件是否失效、仓位是否超限。

## 文件说明

- [MASTER_PROMPT.md](agent-investment-chain/MASTER_PROMPT.md)：给任意智能体的总控提示词。
- [WORKFLOW.md](agent-investment-chain/WORKFLOW.md)：完整动态投研流程。
- [AGENTS.md](agent-investment-chain/AGENTS.md)：多分析角色分工。
- [DATA_SOURCES_A_SHARE.md](agent-investment-chain/DATA_SOURCES_A_SHARE.md)：A 股数据源和字段要求。
- [SIGNAL_POLICY.md](agent-investment-chain/SIGNAL_POLICY.md)：建仓、买入、止盈、止损等提醒规则。
- [USAGE.md](agent-investment-chain/USAGE.md)：在 Codex、Claude Code、Cursor 中的使用方式和落地路线。
- [templates/stock_report.md](agent-investment-chain/templates/stock_report.md)：单股分析报告模板。
- [templates/watchlist.example.yaml](agent-investment-chain/templates/watchlist.example.yaml)：观察池配置示例。
- [templates/alert_rules.example.yaml](agent-investment-chain/templates/alert_rules.example.yaml)：告警规则示例。
- [schemas/analysis_state.schema.json](agent-investment-chain/schemas/analysis_state.schema.json)：分析状态结构。
- [schemas/signal.schema.json](agent-investment-chain/schemas/signal.schema.json)：信号输出结构。

## 推荐技术栈

- A 股数据：AKShare、Tushare、BaoStock、交易所公告、巨潮资讯。
- 存储：DuckDB + Parquet，保留原始数据和清洗后数据。
- 分析：Python、pandas、polars、ta-lib/pandas-ta。
- 回测：内置 baseline 回测用于边界校验，vectorbt 用于参数扫描，Qlib 用于因子和模型研究，Backtrader 用于事件驱动策略。
- 报告：Markdown + JSON，便于智能体读写和复盘。

## 使用边界

所有输出都应视为研究辅助，不构成投资建议。系统只能在你设定的规则下生成条件化提醒，例如“若收盘价站上 20 日均线且成交额放大，则进入试探建仓观察”，不能输出“必买”“稳赚”“满仓”等结论。
