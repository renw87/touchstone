# Single-stock Research Report

## 1. Conditional Conclusion

- Signal: `watch`
- One-line conclusion: 示例运行没有接入真实行情、财报和回测数据，只能进入观察，不能升级为建仓。
- Trigger: 补齐真实数据并完成回测后，若技术触发、风险预算和反方审查均通过，再评估 `pilot_build`。
- Invalidation: 出现 ST、停牌、重大监管风险、财务证据恶化或流动性不足时降级为 `no_trade`。

## 2. Evidence

### Supporting Evidence

| Evidence | Source | Time | Strength | Note |
|---|---|---|---|---|
| 示例输入完整 | Harness fixture | 2026-06-09 | low | 仅用于脚本验证 |

### Opposing Evidence

| Evidence | Source | Time | Strength | Note |
|---|---|---|---|---|
| 未接入真实数据和回测 | Harness fixture | 2026-06-09 | high | 不能生成建仓信号 |

## 3. Fundamentals

基本面未分析，缺少真实财报数据。

## 4. Valuation

估值未分析，缺少真实估值和同业数据。

## 5. Theme And Industry Chain

热点和产业链未分析，缺少真实证据。

## 6. Technicals

技术面未分析，缺少真实行情数据。

## 7. Support And Resistance

缺少行情数据，不能计算支撑阻力。

## 8. Capital Flow

缺少资金数据。

## 9. Bear Case

最强反方观点：当前只有示例输入，没有一手证据、行情、财报和回测，任何建仓提醒都不可靠。

## 10. Backtest

未运行回测。最高信号只能为 `watch`。

## 11. Alert Plan

- Signal: `watch`
- Entry/add zone: 无
- Stop: 无持仓，不设置交易止损；若未来建仓，必须重新计算。
- Position cap: 0
- Review cadence: 接入数据后重新分析。
