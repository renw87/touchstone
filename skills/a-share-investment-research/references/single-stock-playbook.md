# 单股分析标准流程 Playbook

> 从「给定一只股票」到「产出条件化信号 + 进入复盘闭环」的端到端流程。
> 配套 agent 视角的抽象步骤见 [workflow.md](workflow.md)；信号边界见 [signal-policy.md](signal-policy.md)；回测规则见 [backtest.md](backtest.md)；闭环见 [reflection-loop.md](reflection-loop.md)。
> 命令以 `601138.SH 工业富联` 为例，换成你的标的即可。

## 流程总览

```
0 明确目标 ─ 1 召回经验 ─ 2 采集数据 ─ 3 多维分析 ─ 4 转可验证假设 ─ 5 回测 ─ 6 生成信号(带边界) ─ 7 登记闭环 ─ 8 到期复盘
                ↑                                                                                              │
                └──────────────────────────── 反思闭环：经验反哺下一次分析 ──────────────────────────────────┘
```

## 0 · 明确目标（输入）

先锁定：股票代码、投资周期（short/swing/medium/long）、风险偏好、资金与仓位约束、当前持仓、禁入项（ST/低流动性/亏损/高质押）。
个人偏好配置在 `harness/configs/user_profile.yaml`（从 `*.example.yaml` 复制）。

## 1 · 召回历史经验（闭环·反哺，分析前先做）

```bash
python skills/a-share-investment-research/scripts/recall_lessons.py --symbol 601138.SH
```

看这只票 / 这类信号过去的方向命中率和教训，用来**校准信心**（不替代分析）。首次分析会提示「暂无记录」，属正常。

## 2 · 采集数据

```bash
python skills/a-share-data-collector/scripts/collect_snapshot.py 601138.SH --name 工业富联 --provider akshare
```

产出 `data/raw/601138.SH/`：`market_data` / `financials` / `announcements` / `lhb` / `collection_status`。
**缺数据标 `insufficient_data`，绝不编造**；接口失败可重试或先用 `--provider empty` 跑通流程。

## 3 · 多维分析（每维都要：评分 + 证据 + 反方 + 失效条件）

```bash
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/601138.SH/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/601138.SH/financials.json --market-data data/raw/601138.SH/market_data.json
python skills/a-share-investment-research/scripts/theme_chain.py data/raw/601138.SH/announcements.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/601138.SH/market_data.json
```

覆盖：**基本面、估值、主题/产业链（先排稀缺层级再排公司）、技术面/支撑阻力、资金流（龙虎榜用 `lhb-analyzer`）、反方报告**。
若线索来自小道消息/荐股群，先跑 `trap-detector`。按 [research-quality-gates.md](research-quality-gates.md) 维护 22 维覆盖，缺口显式标注。

## 4 · 把观点转成可验证假设

写成**可证伪、无未来数据**的规则。例：
- 「放量突破 20 日高，且行业指数强于沪深 300」
- 「回踩 20 日线 2 日收盘不破，且盈利预期上修」

## 5 · 回测验证假设

```bash
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/601138.SH/market_data.json --rule trend_follow --financials data/raw/601138.SH/financials.json --quality-gate
```

规则选择（详见 [backtest.md](backtest.md)）：
- `breakout`：放量突破，能抓弱势股反弹。
- `trend_follow`：突破 + MA60 趋势确认 + 移动止损，回撤更低（优质趋势股优先）。
- `--quality-gate`：point-in-time 基本面门槛，**只在盈利且 ROE 达标的票上择时**。

**回测弱（样本少 / 胜率盈亏比差）→ 信号最高只能 `watch`。**

## 6 · 生成信号（带边界）

```bash
python skills/a-share-investment-research/scripts/signal_orchestrator.py 601138.SH --name 工业富联
python harness/runners/evaluate_run.py harness/runs/<date>/601138.SH
```

产出 `harness/runs/<date>/601138.SH/`：`report.md` + `signal.json` + `audit.json`。
信号词汇：`no_trade / watch / pilot_build / add / hold / take_profit_partial / take_profit_full / stop_loss / exit_risk`。
每条信号必须含：触发条件、止损、止盈计划、仓位上限、证据、反方、回测摘要、免责。

> **硬边界**：缺财报 / 行情 / 回测 / 反方任一 → 最高 `watch`，**不升级到 `pilot_build` / `add`**。

## 7 · 登记进闭环（闭环·登记，产信号后立即）

```bash
python skills/a-share-investment-research/scripts/journal_signal.py harness/runs/<date>/601138.SH/signal.json --market-dir data/raw/601138.SH
```

把信号写入 `harness/journal/signals.jsonl`，记录信号日收盘价为收益基准，状态 `open`，并带上 `next_review_time`。

## 8 · 到期复盘（闭环·回看，到 next_review_time）

```bash
python skills/a-share-investment-research/scripts/reflect_signal.py --benchmark-dir data/raw/_csi300
```

拉信号日之后的真实行情，算**收益 / 最大涨跌 / 方向对错 / alpha（vs 基准）**，沉淀成一条 lesson 写入 `lessons.md`，并把台账标 `resolved`。下次分析同类标的时，**步骤 1 的 `recall` 就会把这条经验喂回来** —— 闭环合拢。

## 持仓后的复盘节奏

| 周期 | 看什么 |
|------|--------|
| 盘前 | 公告 / 政策 / 隔夜事件 / 今日触发位 |
| 盘中 | 只看 价 / 量 / 支撑 / 止损 / 止盈 触发，不重做研究 |
| 盘后 | K 线 / 资金 / 行业相对强度 / 信号结果 |
| 周度 | 行业 / 估值 / 回测参数 |
| 财报后 | 基本面 / 估值 / 反方 全面刷新 |

## 三条铁律

1. **证据化**：不编造价格、财报、回测、估值分位；缺则标 `insufficient_data`，优先一手证据（公告/财报/交易所）。
2. **条件化**：只输出「若…则…」的条件信号，不输出「必买/稳赚/满仓」等无条件结论。
3. **风控优先**：每个交易级信号必须有止损、仓位上限、反方、回测；缺一不升级。考虑 A 股 T+1、涨跌停、ST、停牌、复权、未来数据泄露。

## 一条龙命令（标准深度，复制即用）

```bash
S=601138.SH; N=工业富联
python skills/a-share-investment-research/scripts/recall_lessons.py --symbol $S
python skills/a-share-data-collector/scripts/collect_snapshot.py $S --name $N --provider akshare
python skills/a-share-investment-research/scripts/fundamental_score.py data/raw/$S/financials.json
python skills/a-share-investment-research/scripts/valuation_score.py data/raw/$S/financials.json --market-data data/raw/$S/market_data.json
python skills/a-share-investment-research/scripts/compute_technicals.py data/raw/$S/market_data.json
python skills/a-share-investment-research/scripts/backtest_signal.py data/raw/$S/market_data.json --rule trend_follow --financials data/raw/$S/financials.json --quality-gate
python skills/a-share-investment-research/scripts/signal_orchestrator.py $S --name $N
python harness/runners/evaluate_run.py harness/runs/$(date +%F)/$S
python skills/a-share-investment-research/scripts/journal_signal.py harness/runs/$(date +%F)/$S/signal.json --market-dir data/raw/$S
# …到 next_review_time 再跑：
# python skills/a-share-investment-research/scripts/reflect_signal.py --benchmark-dir data/raw/_csi300
```

> 研究辅助，非投资建议。所有信号都是条件化提醒，不构成买卖指令。
