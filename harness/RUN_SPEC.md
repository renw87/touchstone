# Harness Run Spec

## Run ID

默认格式：

```text
{YYYY-MM-DD}/{symbol}
```

例如：

```text
runs/2026-06-09/300750.SZ/
```

如果同一股票一天运行多次，可追加时间：

```text
runs/2026-06-09/300750.SZ-143000/
```

## Required Inputs

`input.json` 必须包含：

- `task_id`
- `task_type`
- `symbol`
- `name`
- `horizon`
- `risk_style`
- `account`
- `current_position`
- `requested_outputs`
- `skill_context`

## Required Outputs

智能体执行后至少产出：

- `report.md`
- `signal.json`
- `audit.json`

## Audit Requirements

`audit.json` 记录：

- 使用的 Skill 和 reference 文件。
- 数据来源和缺失字段。
- 是否触发禁入条件。
- 是否生成反方报告。
- 是否有回测摘要。
- 信号是否符合风控规则。
- 下次复盘时间。

## Signal Boundary

没有证据、没有回测、数据缺失、或风险不可控时，最高信号为 `watch`。

以下输出视为失败：

- 无条件买入/卖出。
- 没有止损。
- 没有仓位上限。
- 没有反方观点。
- 使用未标注来源的数据。
- 把新闻或热点当作唯一买入依据。
