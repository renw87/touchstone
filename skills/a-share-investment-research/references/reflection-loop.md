# Reflection Loop — 信号复盘学习闭环

让 touchstone 从"一次性分析"升级为"越用越准"的系统：每个信号被登记、到期回看真实结果、沉淀成可复用经验、反哺下一次分析。借鉴自 TradingAgents 的 reflection + memory 机制，但保持 touchstone 的轻量、脚本化与 A 股本土口径。

## 四环

| 环 | 脚本 | 作用 |
|----|------|------|
| 1 登记 | `scripts/journal_signal.py` | 把 `signal.json` 追加到 `harness/journal/signals.jsonl`，记录信号日收盘价 `ref_close`（收益基准），状态 `open` |
| 2+3 回看+反思 | `scripts/reflect_signal.py` | 对到 `next_review_time` 的 `open` 信号，拉信号日之后真实行情，算 收益 / 最大涨跌 / 方向对错 / alpha，写 `reflections.jsonl` + `lessons.md`，台账标 `resolved` |
| 4 反哺 | `scripts/recall_lessons.py` | 分析前按 symbol / 信号类型检索历史经验 + 方向胜率，注入分析上下文 |

## 用法

**环1 · 登记**（产出信号后立即）：

```bash
python skills/a-share-investment-research/scripts/journal_signal.py \
  harness/runs/<date>/<symbol>/signal.json --market-dir data/raw/<symbol>
```

**环2+3 · 回看反思**（到回看期自动挑选；`--force` 强制；`--benchmark-dir` 提供基准算 alpha；`--as-of-today` 用于补看历史）：

```bash
python skills/a-share-investment-research/scripts/reflect_signal.py --benchmark-dir data/raw/_csi300
python skills/a-share-investment-research/scripts/reflect_signal.py --signal-id <id> --force --as-of-today 2026-06-11
```

**环4 · 反哺**（分析前）：

```bash
python skills/a-share-investment-research/scripts/recall_lessons.py --symbol <symbol>
python skills/a-share-investment-research/scripts/recall_lessons.py --signal pilot_build
```

## 数据与 schema

- 数据文件 `harness/journal/{signals,reflections}.jsonl` 与 `lessons.md` 含个人信号记录，**已 gitignore，仅存本地**；脚本与 schema 入库。
- Schema：`harness/schemas/signal_journal.schema.json`、`harness/schemas/reflection.schema.json`。

## 判定口径

- 看涨类信号（`watch` / `pilot_build` / `add` / `hold`）：信号后区间收益 `> +2%` 记 `correct`、`< -2%` 记 `wrong`、之间 `flat`；后续行情不足记 `insufficient_data`，下次补看。
- `alpha` = 个股区间收益 − 基准同窗口收益（建议基准：沪深300 / 中证500 / 行业指数），用于区分 beta 与真实选股能力。
- `ref_close` 取信号日（含）或之前最后一根日线收盘，作为收益基准。

## 边界

- 召回的经验是关于"同类判断历史命中率"的证据，用于**校准信心**；它本身**不构成升级信号的理由** —— 升级到 `pilot_build` / `add` 仍须满足 `signal-policy.md` 的硬门槛（触发条件、止损、回测、证据齐全）。
- 复盘只描述事实与可复用教训，不追溯性地编造当时未掌握的信息。
