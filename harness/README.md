# A 股智能投研 Harness

Harness 是这套系统的工程层。Skill/Plugin 规定智能体“怎么分析”，Harness 规定任务“怎么执行、怎么记录、怎么评测、怎么复盘”。

最终目标保持不变：针对指定 A 股进行动态智能分析，覆盖基本面、热点/产业链、技术面、支撑阻力、资金行为、反方报告和回测，并在满足风控条件时生成候选建仓、加仓、止盈、止损等条件化提醒。

## 分层

```text
Skill / Plugin
  投研方法、角色分工、信号策略、报告模板

Harness
  任务编排、输入输出契约、运行记录、评测、复盘

Data Layer
  AKShare/Tushare/巨潮资讯/交易所公告/行情/财报/行业数据

Runtime Adapter
  Codex / Claude Code / Cursor / local script
```

## 最小运行链路

1. 从 `configs/user_profile.yaml` 读取用户风险约束。
2. 从 `configs/watchlist.yaml` 读取观察池。
3. 从 `tasks/single_stock_research.yaml` 生成一次单股研究任务。
4. 用 `runners/run_research.py` 创建运行目录和智能体提示词。
5. 先用脚本生成 `fundamental_score.json`、`valuation_score.json`、`theme_chain.json`、`technical_snapshot.json`、`backtest_summary.json`、`parameter_scan.json` 等结构化上下文。
6. 由 Codex/Claude Code/Cursor 执行提示词，或用 `signal_orchestrator.py` 直接产出 `report.md`、`signal.json`、`audit.json`。
7. 用 `runners/evaluate_run.py` 检查输出是否符合信号边界和评测规则。
8. 将结果保存在 `runs/{date}/{symbol}/`，用于下一次复盘。

## 运行产物

每次运行建议保留：

```text
runs/2026-06-09/300750.SZ/
  input.json
  prompt.md
  report.md
  signal.json
  audit.json
  evaluation.json
```

## 与 Skill 的关系

Harness 不复制投研规则。默认引用：

- `skills/a-share-investment-research/SKILL.md`
- `skills/a-share-investment-research/references/workflow.md`
- `skills/a-share-investment-research/references/signal-policy.md`
- `skills/a-share-investment-research/templates/stock_report.md`
- `skills/a-share-investment-research/schemas/signal.schema.json`

## 边界

系统只生成研究辅助和条件化提醒，不生成无条件买卖指令。`pilot_build`、`add`、`take_profit_partial`、`stop_loss` 都必须有触发条件、失效条件、仓位限制、证据和反方观点。
