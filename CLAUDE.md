# Touchstone — A 股智能投研插件说明

当用户要求分析 A 股、构建投资研究链路、生成建仓/加仓/止盈/止损提醒时，优先读取：

- `skills/a-share-investment-research/SKILL.md`
- `skills/a-share-investment-research/references/workflow.md`
- `skills/a-share-investment-research/references/signal-policy.md`
- `skills/a-share-investment-research/references/research-quality-gates.md`
- `skills/a-share-investment-research/templates/stock_report.md`
- `commands/analyze-stock.md`

所有输出必须是证据化、条件化、可复盘的研究辅助，不输出无条件买卖建议。
缺少研究质量核心维度、trap-risk 证据或回测证据时，不得升级到 `pilot_build` 或 `add`。

自动化优先使用：

- `skills/a-share-data-collector/scripts/collect_snapshot.py`
- `skills/a-share-investment-research/scripts/fundamental_score.py`
- `skills/a-share-investment-research/scripts/valuation_score.py`
- `skills/a-share-investment-research/scripts/theme_chain.py`
- `skills/a-share-investment-research/references/chain-bottleneck-research.md`
- `skills/a-share-investment-research/scripts/compute_technicals.py`
- `skills/a-share-investment-research/scripts/backtest_signal.py`
- `skills/a-share-investment-research/scripts/vectorbt_scan.py`
- `skills/a-share-investment-research/scripts/signal_orchestrator.py`
