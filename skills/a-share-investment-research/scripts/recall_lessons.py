#!/usr/bin/env python3
"""Reflection loop · Stage 4 (Recall / Feedback).

Before analyzing a stock, retrieve past signal reflections (optionally filtered
by symbol or signal type) plus a hit-rate summary, so the agent can fold prior
lessons into the new analysis.

Loop: journal_signal.py -> reflect_signal.py -> recall_lessons.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REFLECTIONS = Path("harness/journal/reflections.jsonl")


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


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Recall past signal reflections (reflection-loop stage 4).")
    ap.add_argument("--symbol", help="Only this symbol's lessons.")
    ap.add_argument("--signal", help="Only this signal type's lessons.")
    ap.add_argument("--limit", type=int, default=10, help="Most recent N lessons.")
    ap.add_argument("--reflections", default=str(REFLECTIONS))
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_jsonl(Path(args.reflections))
    if args.symbol:
        rows = [r for r in rows if r.get("symbol") == args.symbol]
    if args.signal:
        rows = [r for r in rows if r.get("signal") == args.signal]

    scope = []
    if args.symbol:
        scope.append(args.symbol)
    if args.signal:
        scope.append(f"signal={args.signal}")
    scope_txt = "（" + " / ".join(scope) + "）" if scope else "（全部）"

    if not rows:
        print(f"# 历史信号反思{scope_txt}：暂无记录，首次分析该标的/信号类型。")
        return 0

    rows = rows[-args.limit:]
    judged = [r for r in rows if r.get("result", {}).get("verdict") in ("correct", "wrong", "flat")]
    correct = sum(1 for r in judged if r["result"]["verdict"] == "correct")
    header = f"# 历史信号反思{scope_txt}：{len(rows)} 条"
    if judged:
        header += f"，方向胜率 {correct}/{len(judged)}"
    print(header)
    for r in rows:
        print(f"- {r.get('lesson', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
