#!/usr/bin/env python3
"""Run a simple, auditable baseline backtest from market_data.json.

This is not a replacement for vectorbt/Qlib. It exists so Harness runs can
distinguish "not tested" from "tested with a conservative baseline".
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest a simple signal rule.")
    parser.add_argument("market_data", help="Path to market_data.json")
    parser.add_argument("--rule", choices=["ma_cross", "breakout", "trend_follow"], default="breakout")
    parser.add_argument("--short-window", type=int, default=20)
    parser.add_argument("--long-window", type=int, default=60)
    parser.add_argument("--lookback", type=int, default=60)
    parser.add_argument("--amount-multiplier", type=float, default=1.2)
    parser.add_argument("--max-hold-days", type=int, default=20)
    parser.add_argument("--stop-loss-pct", type=float, default=0.08)
    parser.add_argument("--take-profit-pct", type=float, default=0.16)
    parser.add_argument("--trail-pct", type=float, default=0.12, help="trend_follow trailing stop: exit when close falls this far below the in-trade peak")
    parser.add_argument("--trend-window", type=int, default=60, help="trend_follow entry filter: only enter when close is above this MA")
    parser.add_argument("--cost-bps", type=float, default=15.0, help="Round-trip cost in bps")
    parser.add_argument("--financials", default=None, help="Path to financials.json for the point-in-time quality gate")
    parser.add_argument("--quality-gate", action="store_true", help="Only enter when point-in-time fundamentals pass (profitable + ROE >= --min-roe)")
    parser.add_argument("--min-roe", type=float, default=3.0, help="Minimum ROE (quality gate)")
    parser.add_argument("--fund-lag-days", type=int, default=90, help="Days after report_period before a report counts as published (avoids look-ahead)")
    parser.add_argument("--out-dir", default=None, help="Output directory. Defaults next to market_data.json")
    return parser.parse_args()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def sma(values: list[float], window: int, end: int) -> float | None:
    if end + 1 < window:
        return None
    subset = values[end + 1 - window : end + 1]
    return sum(subset) / window


def signal_ma_cross(closes: list[float], i: int, short_window: int, long_window: int) -> bool:
    if i <= 0:
        return False
    prev_short = sma(closes, short_window, i - 1)
    prev_long = sma(closes, long_window, i - 1)
    now_short = sma(closes, short_window, i)
    now_long = sma(closes, long_window, i)
    if None in (prev_short, prev_long, now_short, now_long):
        return False
    return bool(prev_short <= prev_long and now_short > now_long)


def exit_ma_cross(closes: list[float], i: int, short_window: int, long_window: int) -> bool:
    now_short = sma(closes, short_window, i)
    now_long = sma(closes, long_window, i)
    return bool(now_short is not None and now_long is not None and now_short < now_long)


def signal_breakout(bars: list[dict[str, Any]], closes: list[float], amounts: list[float], i: int, lookback: int, amount_multiplier: float) -> bool:
    if i < lookback:
        return False
    prior_high = max(num(bar.get("high")) for bar in bars[i - lookback : i])
    amount_ma20 = sma(amounts, 20, i)
    amount_ok = amount_ma20 is None or amounts[i] >= amount_multiplier * amount_ma20
    return closes[i] > prior_high and amount_ok


def exit_breakout(closes: list[float], i: int) -> bool:
    ma20 = sma(closes, 20, i)
    return bool(ma20 is not None and closes[i] < ma20)


def signal_trend_follow(bars: list[dict[str, Any]], closes: list[float], amounts: list[float], i: int, lookback: int, amount_multiplier: float, trend_window: int) -> bool:
    """Breakout that only fires when price is above the long-term trend MA.

    Filters out false breakouts in down/weak names. Paired with a trailing-stop
    exit so winners in a genuine uptrend are allowed to run instead of being
    capped at a fixed take-profit (the main reason fixed-target breakout
    underperforms buy-and-hold in strong bull markets).
    """
    if not signal_breakout(bars, closes, amounts, i, lookback, amount_multiplier):
        return False
    ma_trend = sma(closes, trend_window, i)
    return ma_trend is not None and closes[i] > ma_trend


def max_drawdown(equity: list[float]) -> float:
    peak = equity[0] if equity else 1.0
    worst = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            worst = min(worst, value / peak - 1)
    return abs(worst)


def available_fundamentals(reports: list[dict[str, Any]], as_of_str: Any, lag_days: int) -> dict[str, Any] | None:
    """Latest report published on/before as_of (report_period + lag_days).

    Point-in-time: never uses a report that would not yet have been public on
    the signal date, so the quality gate carries no look-ahead bias.
    """
    from datetime import timedelta
    try:
        as_of = datetime.strptime(str(as_of_str)[:10].replace("/", "-"), "%Y-%m-%d").date()
    except ValueError:
        return None
    avail: list[tuple[str, dict[str, Any]]] = []
    for r in reports:
        p = str(r.get("report_period", ""))
        if len(p) != 8 or not p.isdigit():
            continue
        try:
            published = datetime.strptime(p, "%Y%m%d").date() + timedelta(days=lag_days)
        except ValueError:
            continue
        if published <= as_of:
            avail.append((p, r))
    if not avail:
        return None
    avail.sort(key=lambda x: x[0], reverse=True)
    return avail[0][1]


def quality_ok(m: dict[str, Any] | None, min_roe: float) -> bool:
    if not m:
        return False
    npp = m.get("net_profit_parent")
    if npp is None or npp <= 0:  # must be profitable
        return False
    roe = m.get("roe")
    if roe is not None and roe < min_roe:
        return False
    return True


def run_backtest(args: argparse.Namespace) -> dict[str, Any]:
    market = json.loads(Path(args.market_data).read_text(encoding="utf-8"))
    bars = sorted(market.get("bars", []), key=lambda item: str(item.get("date", "")))
    closes = [num(bar.get("close")) for bar in bars]
    amounts = [num(bar.get("amount")) for bar in bars]

    fund_reports: list[dict[str, Any]] = []
    if args.quality_gate and args.financials:
        try:
            fund_reports = json.loads(Path(args.financials).read_text(encoding="utf-8")).get("reports", [])
        except Exception:  # noqa: BLE001 - missing financials just disables the gate
            fund_reports = []

    insufficient: list[str] = []
    min_bars = max(args.long_window, args.lookback) + 2
    if len(bars) < min_bars:
        insufficient.append(f"at_least_{min_bars}_bars")

    trades: list[dict[str, Any]] = []
    equity = [1.0]
    position: dict[str, Any] | None = None
    pending_entry = False
    cost = args.cost_bps / 10000

    for i in range(len(bars)):
        if pending_entry and position is None and i < len(bars):
            entry_price = num(bars[i].get("open")) or closes[i]
            position = {"entry_index": i, "entry_date": bars[i].get("date"), "entry_price": entry_price, "peak": entry_price}
            pending_entry = False

        if position is not None and i > position["entry_index"]:
            entry_price = position["entry_price"]
            close = closes[i]
            high = num(bars[i].get("high")) or close
            held_days = i - position["entry_index"]
            position["peak"] = max(position.get("peak", entry_price), high)
            stop_hit = close <= entry_price * (1 - args.stop_loss_pct)
            if args.rule == "trend_follow":
                # Let winners run: exit only on hard stop, trailing stop, or trend break (MA20).
                trail_hit = close <= position["peak"] * (1 - args.trail_pct)
                ma_break = exit_breakout(closes, i)
                should_exit = stop_hit or trail_hit or ma_break
                reason = "stop_loss" if stop_hit else "trailing_stop" if trail_hit else "ma_break"
            else:
                take_profit_hit = close >= entry_price * (1 + args.take_profit_pct)
                time_exit = held_days >= args.max_hold_days
                rule_exit = exit_ma_cross(closes, i, args.short_window, args.long_window) if args.rule == "ma_cross" else exit_breakout(closes, i)
                should_exit = stop_hit or take_profit_hit or time_exit or rule_exit
                reason = "stop_loss" if stop_hit else "take_profit" if take_profit_hit else "time_exit" if time_exit else "rule_exit"
            if should_exit:
                gross_return = close / entry_price - 1
                net_return = gross_return - cost
                trades.append(
                    {
                        "entry_date": position["entry_date"],
                        "exit_date": bars[i].get("date"),
                        "entry_price": round(entry_price, 4),
                        "exit_price": round(close, 4),
                        "held_days": held_days,
                        "return_pct": round(net_return, 6),
                        "exit_reason": reason,
                    }
                )
                equity.append(equity[-1] * (1 + net_return))
                position = None

        if position is None and not pending_entry and i < len(bars) - 1:
            if args.rule == "ma_cross":
                pending_entry = signal_ma_cross(closes, i, args.short_window, args.long_window)
            elif args.rule == "trend_follow":
                pending_entry = signal_trend_follow(bars, closes, amounts, i, args.lookback, args.amount_multiplier, args.trend_window)
            else:
                pending_entry = signal_breakout(bars, closes, amounts, i, args.lookback, args.amount_multiplier)
            # Point-in-time quality gate: only act on the signal if fundamentals
            # known as of this bar pass (profitable + ROE). Filters weak/loss names.
            if pending_entry and args.quality_gate:
                m = available_fundamentals(fund_reports, bars[i].get("date"), args.fund_lag_days)
                if not quality_ok(m, args.min_roe):
                    pending_entry = False

    wins = [trade for trade in trades if trade["return_pct"] > 0]
    losses = [trade for trade in trades if trade["return_pct"] <= 0]
    gross_profit = sum(trade["return_pct"] for trade in wins)
    gross_loss = abs(sum(trade["return_pct"] for trade in losses))
    profit_factor = gross_profit / gross_loss if gross_loss else (None if not wins else 999.0)
    failed_samples = sorted(losses, key=lambda trade: trade["return_pct"])[:5]

    return {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "created_at": datetime.now().isoformat(),
        "source_market_data": str(Path(args.market_data)),
        "rule": {
            "name": args.rule,
            "short_window": args.short_window,
            "long_window": args.long_window,
            "lookback": args.lookback,
            "amount_multiplier": args.amount_multiplier,
            "max_hold_days": args.max_hold_days,
            "stop_loss_pct": args.stop_loss_pct,
            "take_profit_pct": args.take_profit_pct,
            "trail_pct": args.trail_pct,
            "trend_window": args.trend_window,
            "quality_gate": args.quality_gate,
            "min_roe": args.min_roe if args.quality_gate else None,
            "cost_bps": args.cost_bps,
            "execution": "signal_on_close_enter_next_open_exit_close_t_plus_1_approx",
        },
        "period": {
            "start": str(bars[0].get("date")) if bars else "",
            "end": str(bars[-1].get("date")) if bars else "",
            "bar_count": len(bars),
        },
        "metrics": {
            "trade_count": len(trades),
            "win_rate": round(len(wins) / len(trades), 6) if trades else 0,
            "profit_factor": None if profit_factor is None else round(profit_factor, 6),
            "max_drawdown": round(max_drawdown(equity), 6),
            "total_return": round(equity[-1] - 1, 6),
        },
        "trades": trades,
        "failed_samples": failed_samples,
        "insufficient_data": insufficient,
        "verdict": "insufficient_data" if insufficient else "no_trades" if not trades else "baseline_backtest_complete",
    }


def render_report(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    return f"""# Backtest Report

- Symbol: {summary.get("symbol")}
- Rule: {summary["rule"]["name"]}
- Period: {summary["period"]["start"]} to {summary["period"]["end"]}
- Bar count: {summary["period"]["bar_count"]}
- Trade count: {metrics["trade_count"]}
- Win rate: {metrics["win_rate"]}
- Profit factor: {metrics["profit_factor"]}
- Max drawdown: {metrics["max_drawdown"]}
- Total return: {metrics["total_return"]}
- Verdict: {summary["verdict"]}

## Failed Samples

```json
{json.dumps(summary["failed_samples"], ensure_ascii=False, indent=2)}
```
"""


def main() -> int:
    args = parse_args()
    market_path = Path(args.market_data)
    out_dir = Path(args.out_dir) if args.out_dir else market_path.parent
    summary = run_backtest(args)
    write_json(out_dir / "backtest_summary.json", summary)
    write_text(out_dir / "backtest_report.md", render_report(summary))
    print(str(out_dir / "backtest_summary.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
