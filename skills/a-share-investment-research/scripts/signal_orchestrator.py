#!/usr/bin/env python3
"""Create conditional signal, audit, report, and alert log from prepared data."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ACTION_SIGNALS = {"pilot_build", "add", "take_profit_partial", "take_profit_full", "stop_loss", "exit_risk"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Orchestrate A-share conditional signal.")
    parser.add_argument("symbol_arg", nargs="?", help="A-share symbol, for example 300750.SZ")
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--name", default="")
    parser.add_argument("--data-dir", default=None, help="Defaults to data/raw/{symbol}")
    parser.add_argument("--run-dir", default=None, help="Defaults to harness/runs/{today}/{symbol}")
    parser.add_argument("--account-equity", type=float, default=100000)
    parser.add_argument("--max-single-stock-weight", type=float, default=0.15)
    parser.add_argument("--risk-per-trade", type=float, default=0.01)
    parser.add_argument("--shares", type=int, default=0)
    parser.add_argument("--cost-price", type=float, default=None)
    parser.add_argument("--alerts-log", default="harness/alerts/alerts.jsonl")
    args = parser.parse_args()
    args.symbol = args.symbol or args.symbol_arg
    if not args.symbol:
        parser.error("symbol is required, either positional or --symbol")
    return args


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False) + "\n")


def num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_support_below(technical: dict[str, Any], close: float) -> float | None:
    levels = technical.get("support_resistance", []) if technical else []
    supports = [
        num(level.get("price"))
        for level in levels
        if level.get("kind") == "support" and num(level.get("price")) > 0 and num(level.get("price")) <= close
    ]
    return max(supports) if supports else None


def first_resistance_above(technical: dict[str, Any], close: float) -> float | None:
    levels = technical.get("support_resistance", []) if technical else []
    resistances = [
        num(level.get("price"))
        for level in levels
        if level.get("kind") == "resistance" and num(level.get("price")) >= close
    ]
    return min(resistances) if resistances else None


def technical_score(technical: dict[str, Any] | None) -> tuple[float, list[str], list[str]]:
    if not technical:
        return 0.0, [], ["technical_snapshot"]
    insufficient = list(technical.get("insufficient_data", []))
    indicators = technical.get("indicators", {})
    trend = technical.get("trend", {})
    score = 0.0
    evidence: list[str] = []
    close = num(technical.get("latest_close"))
    if close:
        evidence.append(f"最新收盘价 {close:.2f}")
    for key, label in (("above_ma20", "站上 MA20"), ("above_ma60", "站上 MA60"), ("above_ma120", "站上 MA120")):
        if trend.get(key):
            score += 1.0
            evidence.append(label)
    rsi = indicators.get("rsi14")
    if isinstance(rsi, (int, float)) and 35 <= rsi <= 70:
        score += 0.5
        evidence.append(f"RSI14 中性区间 {rsi:.2f}")
    if technical.get("support_resistance"):
        score += 0.5
        evidence.append("存在可用支撑阻力位。")
    return min(score, 5.0), evidence, insufficient


def backtest_score(backtest: dict[str, Any] | None, scan: dict[str, Any] | None) -> tuple[float, list[str], list[str]]:
    score = 0.0
    evidence: list[str] = []
    insufficient: list[str] = []
    if not backtest:
        insufficient.append("backtest_summary")
    else:
        insufficient.extend(backtest.get("insufficient_data", []))
        metrics = backtest.get("metrics", {})
        trade_count = int(metrics.get("trade_count") or 0)
        win_rate = num(metrics.get("win_rate"))
        profit_factor = metrics.get("profit_factor")
        max_drawdown = num(metrics.get("max_drawdown"), 1.0)
        total_return = num(metrics.get("total_return"))
        if trade_count > 0:
            score += 1.0
            evidence.append(f"baseline 回测交易数 {trade_count}")
        if win_rate >= 0.45:
            score += 0.8
            evidence.append(f"baseline 胜率 {win_rate:.2%}")
        if isinstance(profit_factor, (int, float)) and profit_factor >= 1.2:
            score += 1.0
            evidence.append(f"baseline 盈亏比 {profit_factor:.2f}")
        if max_drawdown <= 0.15 and trade_count > 0:
            score += 0.7
            evidence.append(f"baseline 最大回撤 {max_drawdown:.2%}")
        if total_return > 0:
            score += 0.5
            evidence.append(f"baseline 总收益 {total_return:.2%}")
        if trade_count == 0:
            insufficient.append("backtest_trade_count")

    if scan:
        if scan.get("engine_status") == "ok" and not scan.get("insufficient_data") and scan.get("best"):
            score += 1.0
            evidence.append("vectorbt 参数扫描存在可用 best 结果。")
        else:
            insufficient.extend(scan.get("insufficient_data", []))
            if scan.get("engine_status") in {"not_run", "dependency_missing"}:
                insufficient.append(f"parameter_scan_{scan.get('engine_status')}")
    else:
        insufficient.append("parameter_scan")
    return min(score, 5.0), evidence, sorted(set(insufficient))


def flow_score(lhb: dict[str, Any] | None) -> tuple[float, list[str], list[str]]:
    if not lhb:
        return 0.0, [], ["lhb"]
    entries = lhb.get("entries", [])
    if not entries:
        return 0.5, ["龙虎榜无记录或数据为空。"], ["lhb.entries"]
    net = sum(num(item.get("net_amount")) for item in entries)
    if net > 0:
        return 2.0, [f"龙虎榜样本净买额合计 {net:.2f}"], []
    if net < 0:
        return 0.5, [f"龙虎榜样本净卖额合计 {abs(net):.2f}"], []
    return 1.0, ["龙虎榜样本净额中性。"], []


def structured_score(source: dict[str, Any] | None, file_key: str, score_key: str, label: str) -> tuple[float, float, list[str], list[str]]:
    if not source:
        return 0.0, 0.0, [], [file_key]
    scores = source.get("scores", {})
    score = num(scores.get(score_key))
    risk = num(scores.get("risk"))
    evidence = [f"{label}: {item}" for item in source.get("evidence", [])]
    insufficient = list(source.get("insufficient_data", []))
    if source.get("verdict") == "insufficient_data" and file_key not in insufficient:
        insufficient.append(file_key)
    return min(score, 5.0), min(risk, 5.0), evidence, insufficient


def position_lots(account_equity: float, risk_per_trade: float, entry: float, stop: float, max_weight: float) -> int:
    if entry <= 0 or stop <= 0 or entry <= stop:
        return 0
    risk_cash = account_equity * risk_per_trade
    lots_by_risk = int(risk_cash / (entry - stop) // 100)
    lots_by_weight = int((account_equity * max_weight) / entry // 100)
    return max(0, min(lots_by_risk, lots_by_weight))


def build_signal(args: argparse.Namespace, data_dir: Path) -> tuple[dict[str, Any], dict[str, Any], str]:
    now = datetime.now()
    next_review = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    market = read_json(data_dir / "market_data.json")
    collection_status = read_json(data_dir / "collection_status.json")
    fundamental = read_json(data_dir / "fundamental_score.json")
    valuation = read_json(data_dir / "valuation_score.json")
    theme = read_json(data_dir / "theme_chain.json")
    technical = read_json(data_dir / "technical_snapshot.json")
    backtest = read_json(data_dir / "backtest_summary.json")
    scan = read_json(data_dir / "parameter_scan.json")
    lhb = read_json(data_dir / "lhb.json")

    name = args.name or (market or {}).get("name") or args.symbol
    latest_close = num((technical or {}).get("latest_close"))
    support = first_support_below(technical or {}, latest_close) if latest_close else None
    resistance = first_resistance_above(technical or {}, latest_close) if latest_close else None
    atr = num(((technical or {}).get("indicators") or {}).get("atr14"))
    stop_price = support or (latest_close - 2 * atr if latest_close and atr else 0)
    target_1 = resistance or (latest_close * 1.08 if latest_close else 0)
    target_2 = latest_close * 1.16 if latest_close else 0

    fundamental_score_value = num(((fundamental or {}).get("scores") or {}).get("fundamental"))
    risk_score_value = num(((fundamental or {}).get("scores") or {}).get("risk"))
    tech_score, tech_evidence, tech_missing = technical_score(technical)
    bt_score, bt_evidence, bt_missing = backtest_score(backtest, scan)
    flow_score_value, flow_evidence, flow_missing = flow_score(lhb)
    valuation_score_value, valuation_risk_value, valuation_evidence, valuation_missing = structured_score(valuation, "valuation_score", "valuation", "估值")
    theme_score_value, theme_risk_value, theme_evidence, theme_missing = structured_score(theme, "theme_chain", "theme", "主题")
    total_score = fundamental_score_value + risk_score_value + tech_score + bt_score + flow_score_value + valuation_score_value + theme_score_value

    insufficient = []
    if market is None:
        insufficient.append("market_data")
    insufficient.extend((collection_status or {}).get("insufficient_data", []))
    insufficient.extend((fundamental or {}).get("insufficient_data", []) if fundamental else ["financials", "fundamental_score"])
    insufficient.extend(valuation_missing)
    insufficient.extend(theme_missing)
    insufficient.extend(tech_missing)
    insufficient.extend(bt_missing)
    insufficient.extend(flow_missing)
    insufficient = sorted(set(insufficient))

    evidence = []
    evidence.extend((fundamental or {}).get("evidence", []))
    evidence.extend(valuation_evidence)
    evidence.extend(theme_evidence)
    evidence.extend(tech_evidence)
    evidence.extend(bt_evidence)
    evidence.extend(flow_evidence)
    if not evidence:
        evidence.append("缺少足够结构化证据，不能升级为交易级提醒。")

    no_trade_gates: list[str] = []
    if "market_data" in insufficient or "market_data.bars" in insufficient:
        no_trade_gates.append("market_data_missing")
    if "financials" in insufficient or "financials.reports" in insufficient:
        no_trade_gates.append("financial_data_missing")

    technical_trigger = bool(latest_close and tech_score >= 2.5 and (resistance is None or latest_close >= resistance * 0.995))
    backtest_ok = bool(bt_score >= 3 and backtest and not (backtest.get("insufficient_data")))
    fundamental_ok = bool(fundamental_score_value >= 3 and risk_score_value >= 3)
    valuation_ok = bool(valuation and valuation_score_value >= 2 and valuation_risk_value >= 2.5 and "valuation_score" not in insufficient)
    theme_assessed = bool(theme and "theme_chain" not in insufficient)

    signal_name = "watch"
    reason = "数据或证据不足，维持观察。"
    if no_trade_gates:
        signal_name = "no_trade"
        reason = "触发禁入/缺数条件：" + ", ".join(no_trade_gates)
    elif args.shares > 0 and args.cost_price:
        if latest_close and stop_price and latest_close <= stop_price:
            signal_name = "stop_loss"
            reason = "价格跌破预设风险线，触发止损提醒。"
        elif latest_close and latest_close >= args.cost_price * 1.15:
            signal_name = "take_profit_partial"
            reason = "持仓达到阶段性收益阈值，触发分批止盈提醒。"
        else:
            signal_name = "hold"
            reason = "已有持仓但未触发止盈/止损，维持持有并复盘。"
    elif fundamental_ok and valuation_ok and theme_assessed and technical_trigger and backtest_ok and total_score >= 26:
        signal_name = "pilot_build"
        reason = "基本面、估值、主题核验、技术触发和回测证据均满足试探建仓阈值。"
    elif total_score >= 20 and not no_trade_gates:
        signal_name = "watch"
        reason = "综合分达到观察阈值，但交易级条件未全部满足。"

    suggested_lots = position_lots(args.account_equity, args.risk_per_trade, latest_close, stop_price or 0, args.max_single_stock_weight)
    if signal_name not in {"pilot_build", "add"}:
        suggested_lots = 0

    signal = {
        "symbol": args.symbol,
        "name": name,
        "as_of": now.isoformat(),
        "signal": signal_name,
        "confidence": round(max(0.1, min(0.85, 0.2 + total_score / 35 * 0.6)), 4),
        "reason": reason,
        "trigger_condition": "放量突破关键阻力并完成收盘确认；若数据缺失项补齐后仍满足评分阈值，可升级评估。"
        if signal_name in {"watch", "no_trade"}
        else "当前条件已触发，请按仓位和风控规则执行前复核。",
        "entry_zone": {
            "low": round(latest_close * 0.995, 4) if latest_close else 0,
            "high": round(latest_close * 1.005, 4) if latest_close else 0,
            "basis": "latest_close +/- 0.5%; final execution must check liquidity and price limit.",
        },
        "stop_condition": f"收盘跌破 {stop_price:.4f} 或基本面/事件证据恶化。"
        if stop_price
        else "缺少有效止损价，不能升级为交易级提醒。",
        "take_profit_plan": [
            {"condition": f"触及第一目标 {target_1:.4f}" if target_1 else "缺少第一目标价", "action": "take_profit_partial", "price": round(target_1, 4) if target_1 else 0},
            {"condition": f"触及第二目标 {target_2:.4f}" if target_2 else "缺少第二目标价", "action": "take_profit_full", "price": round(target_2, 4) if target_2 else 0},
        ],
        "position_limit": {
            "max_weight": args.max_single_stock_weight,
            "max_loss_pct_of_account": args.risk_per_trade,
            "suggested_lots": suggested_lots,
        },
        "evidence": evidence[:12],
        "bear_case": "最强反方：数据缺口、基本面证据不足、回测样本不足或技术突破失败，都可能使当前提醒失效。",
        "backtest_summary": {
            "period": backtest_period_text(backtest),
            "win_rate": num(((backtest or {}).get("metrics") or {}).get("win_rate")),
            "profit_factor": num(((backtest or {}).get("metrics") or {}).get("profit_factor")),
            "max_drawdown": num(((backtest or {}).get("metrics") or {}).get("max_drawdown")),
            "trade_count": int(num(((backtest or {}).get("metrics") or {}).get("trade_count"))),
            "verdict": str((backtest or {}).get("verdict", "not_run")),
        },
        "next_review_time": next_review,
        "disclaimer": "Research assistance only, not investment advice.",
    }

    audit = {
        "skill_used": "skills/a-share-investment-research/SKILL.md",
        "references_used": [
            "references/workflow.md",
            "references/signal-policy.md",
            "references/backtest.md",
        ],
        "data_sources": [
            str(data_dir / filename)
            for filename in (
                "market_data.json",
                "financials.json",
                "announcements.json",
                "lhb.json",
                "fundamental_score.json",
                "valuation_score.json",
                "theme_chain.json",
                "technical_snapshot.json",
                "backtest_summary.json",
                "parameter_scan.json",
            )
            if (data_dir / filename).exists()
        ],
        "insufficient_data": insufficient,
        "no_trade_gates": no_trade_gates,
        "has_bear_case": True,
        "has_backtest_summary": backtest is not None,
        "signal_boundary_ok": signal_name not in {"pilot_build", "add"} or (suggested_lots > 0 and backtest_ok and fundamental_ok and valuation_ok and theme_assessed),
        "next_review_time": next_review,
        "scores": {
            "fundamental": round(fundamental_score_value, 4),
            "risk": round(risk_score_value, 4),
            "technical": round(tech_score, 4),
            "backtest": round(bt_score, 4),
            "flow": round(flow_score_value, 4),
            "valuation": round(valuation_score_value, 4),
            "valuation_risk": round(valuation_risk_value, 4),
            "theme": round(theme_score_value, 4),
            "theme_risk": round(theme_risk_value, 4),
            "total": round(total_score, 4),
        },
    }

    report = render_report(signal, audit)
    return signal, audit, report


def backtest_period_text(backtest: dict[str, Any] | None) -> str:
    period = (backtest or {}).get("period") or {}
    start = str(period.get("start") or "")
    end = str(period.get("end") or "")
    return f"{start} to {end}" if start or end else "not_available"


def render_report(signal: dict[str, Any], audit: dict[str, Any]) -> str:
    scores = audit.get("scores", {})
    return f"""# 单股动态投研报告

## Conditional Conclusion

- Signal: `{signal["signal"]}`
- Reason: {signal.get("reason")}
- Trigger: {signal.get("trigger_condition")}
- Stop: {signal.get("stop_condition")}
- Next review: {signal.get("next_review_time")}

## Evidence

{chr(10).join(f"- {item}" for item in signal.get("evidence", []))}

## Fundamental / 基本面

- Score: {scores.get("fundamental")}
- Risk score: {scores.get("risk")}
- Missing: {", ".join(audit.get("insufficient_data", []))}

## Valuation / 估值

- Score: {scores.get("valuation")}
- Risk score: {scores.get("valuation_risk")}
- Missing: {", ".join(item for item in audit.get("insufficient_data", []) if "valuation" in item or item in {"market_cap", "latest_price", "pe", "pb", "ps", "peg", "peer_valuation", "historical_valuation_percentile"})}

## Theme And Industry Chain / 热点产业链

- Score: {scores.get("theme")}
- Risk score: {scores.get("theme_risk")}
- Missing: {", ".join(item for item in audit.get("insufficient_data", []) if "theme" in item or "industry_chain" in item)}

## Technical / 技术

- Score: {scores.get("technical")}
- Entry zone: {signal.get("entry_zone")}
- Stop condition: {signal.get("stop_condition")}

## Support And Resistance / 支撑阻力

- Entry basis: {signal.get("entry_zone", {}).get("basis")}
- Take profit plan: {signal.get("take_profit_plan")}

## Capital Flow / 资金

- Flow score: {scores.get("flow")}

## Bear Case / 反方

{signal.get("bear_case")}

## Backtest / 回测

```json
{json.dumps(signal.get("backtest_summary"), ensure_ascii=False, indent=2)}
```

## Alert Plan

- Position limit: {signal.get("position_limit")}
- Signal boundary ok: {audit.get("signal_boundary_ok")}
"""


def main() -> int:
    args = parse_args()
    today = datetime.now().strftime("%Y-%m-%d")
    data_dir = Path(args.data_dir) if args.data_dir else Path("data/raw") / args.symbol
    run_dir = Path(args.run_dir) if args.run_dir else Path("harness/runs") / today / args.symbol
    run_dir.mkdir(parents=True, exist_ok=True)

    signal, audit, report = build_signal(args, data_dir)
    write_json(run_dir / "signal.json", signal)
    write_json(run_dir / "audit.json", audit)
    write_text(run_dir / "report.md", report)

    if signal.get("signal") in ACTION_SIGNALS:
        append_jsonl(Path(args.alerts_log), {"created_at": datetime.now().isoformat(), **signal})

    print(str(run_dir / "signal.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
