#!/usr/bin/env python3
"""Reflection loop · Stage 1 (Journal).

Register a produced signal.json into the append-only signal journal
(harness/journal/signals.jsonl), recording the close on the signal date as the
baseline (ref_close) for later return/alpha review.

Loop: journal_signal.py -> reflect_signal.py -> recall_lessons.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_JOURNAL = "harness/journal/signals.jsonl"


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def signal_id(symbol: str, as_of: str, signal: str) -> str:
    raw = f"{symbol}|{as_of}|{signal}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def ref_close_on(market_dir: str, as_of_date: str) -> float | None:
    """Close on or before the signal date, from market_data.json."""
    md_path = Path(market_dir) / "market_data.json"
    if not md_path.exists():
        return None
    bars = json.loads(md_path.read_text(encoding="utf-8")).get("bars", [])
    on_or_before = [b for b in bars if str(b.get("date", "")) <= as_of_date]
    if on_or_before:
        return on_or_before[-1].get("close")
    return None


def already_logged(journal_path: Path, sid: str) -> bool:
    if not journal_path.exists():
        return False
    for line in journal_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            if json.loads(line).get("signal_id") == sid:
                return True
        except json.JSONDecodeError:
            continue
    return False


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Register a signal into the journal (reflection-loop stage 1).")
    ap.add_argument("signal_json", help="Path to signal.json")
    ap.add_argument("--market-dir", help="Symbol data dir holding market_data.json (for ref_close).")
    ap.add_argument("--journal", default=DEFAULT_JOURNAL)
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    sig = load_json(args.signal_json)

    symbol = sig["symbol"]
    as_of = str(sig.get("as_of", ""))[:10]
    sg = sig.get("signal", "")
    sid = signal_id(symbol, as_of, sg)

    ref = ref_close_on(args.market_dir, as_of) if args.market_dir else None

    entry = {
        "signal_id": sid,
        "symbol": symbol,
        "name": sig.get("name", ""),
        "as_of": as_of,
        "signal": sg,
        "confidence": sig.get("confidence"),
        "ref_close": ref,
        "entry_zone": sig.get("entry_zone"),
        "trigger_condition": sig.get("trigger_condition", ""),
        "stop_condition": sig.get("stop_condition", ""),
        "take_profit_plan": sig.get("take_profit_plan", []),
        "next_review_time": sig.get("next_review_time", ""),
        "status": "open",
        "logged_at": datetime.now().isoformat(),
        "source_signal": str(args.signal_json),
    }

    journal_path = Path(args.journal)
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    if already_logged(journal_path, sid):
        print(f"already_logged: {sid} {symbol} {as_of} {sg}")
        return 0
    with journal_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"logged: {sid} {symbol} {as_of} {sg} ref_close={ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
