#!/usr/bin/env python3
"""Reflection loop · Stage 2+3 (Review & Reflect).

For every open journal entry whose next_review_time is due, pull the real price
action after the signal date, compute return / max gain / max drawdown /
direction / alpha vs a benchmark, write a reflection (reflections.jsonl +
lessons.md), and mark the journal entry resolved.

Loop: journal_signal.py -> reflect_signal.py -> recall_lessons.py
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

SIGNALS = Path("harness/journal/signals.jsonl")
REFLECTIONS = Path("harness/journal/reflections.jsonl")
LESSONS = Path("harness/journal/lessons.md")

# Bullish-leaning signals: a positive forward return means the call was right.
BULLISH = {"watch", "pilot_build", "add", "hold"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
    path.write_text(body + ("\n" if rows else ""), encoding="utf-8")


def load_bars(market_dir: Path) -> list[dict[str, Any]]:
    md = market_dir / "market_data.json"
    if not md.exists():
        return []
    return json.loads(md.read_text(encoding="utf-8")).get("bars", [])


def evaluate(entry: dict[str, Any], bars: list[dict[str, Any]], benchmark_bars: list[dict[str, Any]] | None) -> dict[str, Any]:
    as_of = entry["as_of"]
    ref = entry.get("ref_close")
    after = [b for b in bars if str(b.get("date", "")) > as_of]
    result: dict[str, Any] = {"reviewed_bars": len(after)}
    if not after or not ref:
        result["verdict"] = "insufficient_data"
        return result

    closes = [b["close"] for b in after]
    last_close = closes[-1]
    max_high = max(b["high"] for b in after)
    min_low = min(b["low"] for b in after)
    ret = (last_close - ref) / ref
    result.update({
        "ref_close": ref,
        "last_close": last_close,
        "return_pct": round(ret, 4),
        "max_gain_pct": round((max_high - ref) / ref, 4),
        "max_drawdown_pct": round((min_low - ref) / ref, 4),
        "window": f"{after[0]['date']}~{after[-1]['date']}",
    })

    if entry["signal"] in BULLISH:
        result["direction_correct"] = ret > 0

    # Alpha vs benchmark over the same window length.
    if benchmark_bars:
        b_before = [b for b in benchmark_bars if str(b.get("date", "")) <= as_of]
        b_after = [b for b in benchmark_bars if str(b.get("date", "")) > as_of]
        if b_before and b_after:
            b0 = b_before[-1]["close"]
            idx = min(len(b_after), len(after)) - 1
            b1 = b_after[idx]["close"]
            if b0:
                bret = (b1 - b0) / b0
                result["benchmark_return_pct"] = round(bret, 4)
                result["alpha_pct"] = round(ret - bret, 4)

    if entry["signal"] in BULLISH:
        result["verdict"] = "correct" if ret > 0.02 else ("wrong" if ret < -0.02 else "flat")
    else:
        result["verdict"] = "reviewed"
    return result


def make_lesson(entry: dict[str, Any], ev: dict[str, Any]) -> str:
    sg = entry["signal"]
    name = entry.get("name", "")
    if ev.get("verdict") == "insufficient_data":
        return f"{entry['as_of']} {entry['symbol']}({name}) 信号[{sg}]：回看期数据不足，待后续补看。"
    ret = ev.get("return_pct", 0) * 100
    alpha = ev.get("alpha_pct")
    atxt = f"，超额 alpha {alpha * 100:+.1f}%" if alpha is not None else ""
    judge = {"correct": "方向正确", "wrong": "方向错误", "flat": "基本走平", "reviewed": "已复盘"}.get(ev["verdict"], ev["verdict"])
    return (
        f"{entry['as_of']} {entry['symbol']}({name}) 信号[{sg}]：{judge}，"
        f"{ev['window']} 收益 {ret:+.1f}%{atxt}"
        f"（最大涨 {ev['max_gain_pct'] * 100:+.1f}% / 最大回撤 {ev['max_drawdown_pct'] * 100:+.1f}%）。"
    )


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Review & reflect due signals (reflection-loop stage 2+3).")
    ap.add_argument("--signal-id", help="Only reflect this signal id; default = all due open entries.")
    ap.add_argument("--market-root", default="data/raw", help="Root dir of per-symbol market data.")
    ap.add_argument("--benchmark-dir", help="Dir holding benchmark market_data.json (e.g. CSI300) for alpha.")
    ap.add_argument("--as-of-today", default=date.today().isoformat(), help="Treat this date as 'today' (testing).")
    ap.add_argument("--force", action="store_true", help="Ignore next_review_time due check.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    signals = read_jsonl(SIGNALS)
    reflections = read_jsonl(REFLECTIONS)
    benchmark_bars = load_bars(Path(args.benchmark_dir)) if args.benchmark_dir else None
    today = args.as_of_today

    targets = []
    for e in signals:
        if e.get("status") != "open":
            continue
        if args.signal_id and e["signal_id"] != args.signal_id:
            continue
        nrt = str(e.get("next_review_time", ""))[:10]
        if args.force or not nrt or nrt <= today:
            targets.append(e)

    if not targets:
        print("无到期待复盘信号。")
        return 0

    lesson_lines = []
    for e in targets:
        bars = load_bars(Path(args.market_root) / e["symbol"])
        ev = evaluate(e, bars, benchmark_bars)
        reflections.append({
            "signal_id": e["signal_id"],
            "symbol": e["symbol"],
            "name": e.get("name", ""),
            "as_of": e["as_of"],
            "signal": e["signal"],
            "reviewed_at": today,
            "result": ev,
            "lesson": make_lesson(e, ev),
        })
        lesson_lines.append(reflections[-1]["lesson"])
        if ev.get("verdict") != "insufficient_data":
            e["status"] = "resolved"
            e["resolved_at"] = today
        print(f"reflected: {e['signal_id']} {e['symbol']} -> {ev.get('verdict')}")

    write_jsonl(REFLECTIONS, reflections)
    write_jsonl(SIGNALS, signals)
    LESSONS.parent.mkdir(parents=True, exist_ok=True)
    with LESSONS.open("a", encoding="utf-8") as f:
        for ln in lesson_lines:
            f.write(f"- {ln}\n")
    print(f"done: {len(targets)} 条已复盘，经验写入 {LESSONS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
