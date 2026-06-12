# Touchstone — A 股证据化投研链路

> *Every thesis, put to the test.* 试金石:每个投资假设,都要在证据与回测里被检验真伪。

**Touchstone** 是一套可移植到 Codex、Claude Code、Cursor 等编码智能体的 A 股投研协议和插件包。目标不是让智能体直接替你买卖，而是让它围绕指定股票持续做证据化分析，并在满足预设条件时输出“候选建仓、加仓、止盈、止损、观望”等提醒。

## 安装

Touchstone 仓库根即插件工程根，按使用环境选择安装方式。

### Claude Code

**方式一 · 整包插件（推荐，一键）**

```text
/plugin marketplace add renw87/touchstone
/plugin install touchstone@touchstone
```

安装后自动加载全部 skills、commands 和 investment-committee agent。

**方式二 · 只装核心 Skill**

```powershell
# Windows
Copy-Item -Recurse skills\a-share-investment-research $HOME\.claude\skills\
```

```bash
# macOS / Linux
cp -r skills/a-share-investment-research ~/.claude/skills/
```

> 单独安装 Skill 时，Skill 目录内的 `scripts/`、`references/` 会一并带上，可做对话式投研；但仓库根的 `harness/` 自动化编排层不在 Skill 内，需要完整克隆仓库才能用。

### Codex

仓库本身是合法的 root-level Codex 插件（已通过 `validate_plugin.py` 校验），manifest 为 [.codex-plugin/plugin.json](.codex-plugin/plugin.json)。按你的 Codex 环境插件安装方式加载即可。

### Cursor

[.cursor/rules/a-share-investment-research.mdc](.cursor/rules/a-share-investment-research.mdc) 会被 Cursor 自动加载为规则。

### 直接克隆（用脚本自动化）

```bash
git clone https://github.com/renw87/touchstone.git
cd touchstone
pip install -r requirements.txt   # 可选：接真实数据与回测时才需要
```

## 使用手册

### 环境与依赖

- **Python 3.9+**。
- **核心脚本零第三方依赖**（仅标准库）：用自备数据或 `--provider empty` 即可跑通「采集 → 评分 → 编排 → 评测」全链路。
- **接真实数据 / 回测**需安装：`pip install akshare pandas numpy vectorbt`。
- 可选增强：`tushare`、`baostock`（备用数据源）、`duckdb`（本地存储）。

### 快速开始

**模式一 · 对话式**（在 Claude Code / Codex / Cursor 内直接对智能体说）

```text
用 $a-share-investment-research 分析宁德时代 300750.SZ。
周期 swing，风险 balanced，账户权益 100000，当前无持仓。
输出完整报告和条件化信号。
```

**模式二 · 脚本自动化**（确定性骨架，可被任意智能体或 CI 调用）

```bash
# 1) 采集数据（真实行情走 akshare；离线骨架用 --provider empty）
python skills/a-share-data-collector/scripts/collect_snapshot.py 300750.SZ --name 宁德时代 --provider akshare

# 2) 一键编排：读取数据 → 基本面/估值/技术面/主题/回测 → 生成信号
python skills/a-share-investment-research/scripts/signal_orchestrator.py 300750.SZ --name 宁德时代

# 3) 评测是否越过信号边界
python harness/runners/evaluate_run.py harness/runs/<日期>/300750.SZ
```

产物写入 `harness/runs/<日期>/<symbol>/`：`report.md`、`signal.json`、`audit.json`。`<日期>` 为运行当天，例如 `harness/runs/2026-06-11/300750.SZ`。

### 信号解读

`signal.json` 的 `signal` 字段只取以下 9 个值：

| 信号 | 含义 |
|------|------|
| `no_trade` | 数据不足或触发禁入，不操作 |
| `watch` | 观察，未达交易级条件 |
| `pilot_build` | 满足条件的试探建仓（需触发条件 / 止损 / 回测齐全）|
| `add` | 加仓（需已有盈利 + 新证据）|
| `hold` | 持有 |
| `take_profit_partial` / `take_profit_full` | 部分 / 全部止盈 |
| `stop_loss` | 止损 |
| `exit_risk` | 风险退出 |

每条信号都附带 `trigger_condition`、`stop_condition`、`take_profit_plan`、`position_limit`、`evidence`、`bear_case`、`backtest_summary` 和 `disclaimer`。

> **关键边界**：缺少财报、行情或回测证据时，信号**最高只能到 `watch`**，不会升级到 `pilot_build` / `add`。

### 配置

`harness/configs/` 下的个人配置（`user_profile.yaml`、`watchlist.yaml` 含资金量与自选股，已被 `.gitignore`，请从 `*.example.yaml` 复制后填写）：

| 文件 | 作用 |
|------|------|
| `user_profile.yaml` | 资金量、风险偏好、单票 / 行业上限、单笔风险 |
| `watchlist.yaml` | 自选股池 |
| `alert_rules.yaml` | 各信号的评分阈值与触发时间 |

首次使用：

```bash
cp harness/configs/user_profile.example.yaml harness/configs/user_profile.yaml
cp harness/configs/watchlist.example.yaml   harness/configs/watchlist.yaml
```

### 已知限制与排错

- **akshare 财报 / 龙虎榜接口随版本变动**：部分接口（如 `stock_lhb_detail_em`）签名已变，`financials`、`lhb` 可能采集为空。系统会标记 `insufficient_data` 并把信号 cap 在 `watch` / `no_trade`（不会瞎编）。需要完整基本面时，升级脚本以适配新版 akshare API，或接入 Tushare / 巨潮资讯作为财报源。
- **行情数据正常**：akshare 日线行情可用（实测可拉取约 589 根 K 线），技术面与 baseline 回测可正常运行。
- **Windows 控制台中文乱码**：执行前设 `set PYTHONUTF8=1`（或 `chcp 65001`）；产物文件本身为正确 UTF-8。
- **信号不升级**：缺财报或回测时无法到 `pilot_build` / `add` 属预期设计，非 bug。

### 回测规则

`backtest_signal.py` 支持三种规则：

- `breakout`：放量突破 N 日高，固定止盈 / 时间退出。
- `trend_follow`：突破 + MA60 趋势确认进场，移动止损 / 跌破 MA20 退出（让利润奔跑，回撤更低）。
- `ma_cross`：均线金叉。

可叠加 `--quality-gate --financials <financials.json>`：point-in-time 基本面门槛（盈利 + ROE 达标才进场），只在基本面强的票上择时。规则选择与回测结论见 [backtest.md](skills/a-share-investment-research/references/backtest.md)。

### 反思闭环（让系统越用越准）

信号不是产完就结束，而是被登记、回看、沉淀、反哺，形成学习闭环：

```bash
# 分析前：召回该股 / 该信号类型的历史经验
python skills/a-share-investment-research/scripts/recall_lessons.py --symbol 300750.SZ
# 产信号后：登记进台账（记信号日收盘价为收益基准）
python skills/a-share-investment-research/scripts/journal_signal.py harness/runs/<date>/300750.SZ/signal.json --market-dir data/raw/300750.SZ
# 到回看期：回看真实收益 / 方向 / alpha，沉淀经验
python skills/a-share-investment-research/scripts/reflect_signal.py --benchmark-dir data/raw/_csi300
```

信号台账与经验记录在 `harness/journal/`（个人数据，已 gitignore，仅本地）。详见 [reflection-loop.md](skills/a-share-investment-research/references/reflection-loop.md)。

## 当前主线

当前仓库根目录就是插件工程根：

- [.codex-plugin/plugin.json](.codex-plugin/plugin.json)：Codex 插件 manifest。
- [SKILL.md](skills/a-share-investment-research/SKILL.md)：核心 A 股投研 Skill。
- [single-stock-playbook.md](skills/a-share-investment-research/references/single-stock-playbook.md)：单股分析端到端流程（0→8 步 + 命令 + 闭环）。
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
