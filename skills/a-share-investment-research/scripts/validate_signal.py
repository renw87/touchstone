#!/usr/bin/env python3
"""Validate the basic shape of an A-share conditional signal JSON file.

This intentionally uses only the Python standard library so it can run in
restricted agent environments.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ALLOWED_SIGNALS = {
    "no_trade",
    "watch",
    "pilot_build",
    "add",
    "hold",
    "take_profit_partial",
    "take_profit_full",
    "stop_loss",
    "exit_risk",
}

REQUIRED = {
    "symbol",
    "as_of",
    "signal",
    "confidence",
    "trigger_condition",
    "stop_condition",
    "position_limit",
    "evidence",
    "bear_case",
    "next_review_time",
}


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def validate(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - user-facing CLI
        return fail(f"cannot read JSON: {exc}")

    missing = sorted(REQUIRED - set(data))
    if missing:
        return fail(f"missing required fields: {', '.join(missing)}")

    if data["signal"] not in ALLOWED_SIGNALS:
        return fail(f"invalid signal: {data['signal']}")

    confidence = data["confidence"]
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return fail("confidence must be a number between 0 and 1")

    if not isinstance(data["evidence"], list) or not all(isinstance(x, str) for x in data["evidence"]):
        return fail("evidence must be a list of strings")

    position_limit = data["position_limit"]
    if not isinstance(position_limit, dict):
        return fail("position_limit must be an object")

    for field in ("max_weight", "max_loss_pct_of_account"):
        value = position_limit.get(field)
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            return fail(f"position_limit.{field} must be a number between 0 and 1")

    print("signal ok")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_signal.py <signal.json>", file=sys.stderr)
        return 2
    return validate(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
