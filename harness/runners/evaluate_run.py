#!/usr/bin/env python3
"""Evaluate a Harness run for basic signal boundary compliance."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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

TRADE_SIGNALS = {"pilot_build", "add"}

REQUIRED_SIGNAL_FIELDS = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an A-share Harness run.")
    parser.add_argument("run_dir", help="Path to harness run directory")
    return parser.parse_args()


def load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 - CLI output
        return None, str(exc)


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def evaluate_signal(signal_path: Path) -> list[str]:
    failures: list[str] = []
    signal, error = load_json(signal_path)
    if error:
        return [f"cannot read signal.json: {error}"]
    assert signal is not None

    missing = sorted(REQUIRED_SIGNAL_FIELDS - set(signal))
    if missing:
        failures.append(f"signal.json missing fields: {', '.join(missing)}")

    signal_name = signal.get("signal")
    if signal_name not in ALLOWED_SIGNALS:
        failures.append(f"invalid signal: {signal_name}")

    confidence = signal.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        failures.append("confidence must be a number between 0 and 1")

    for field in ("trigger_condition", "stop_condition", "bear_case", "next_review_time"):
        if field in signal and not nonempty_string(signal[field]):
            failures.append(f"{field} must be a non-empty string")

    evidence = signal.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        failures.append("evidence must be a non-empty list")

    position_limit = signal.get("position_limit")
    if not isinstance(position_limit, dict):
        failures.append("position_limit must be an object")
    else:
        for field in ("max_weight", "max_loss_pct_of_account"):
            value = position_limit.get(field)
            if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                failures.append(f"position_limit.{field} must be between 0 and 1")

    if signal_name in TRADE_SIGNALS:
        take_profit_plan = signal.get("take_profit_plan")
        if not isinstance(take_profit_plan, list) or not take_profit_plan:
            failures.append("trade signals require a non-empty take_profit_plan")

        backtest = signal.get("backtest_summary")
        if not isinstance(backtest, dict):
            failures.append("trade signals require backtest_summary")
        else:
            verdict = str(backtest.get("verdict", "")).lower()
            trade_count = backtest.get("trade_count")
            if "not_run" in verdict or "未回测" in verdict or "不能升级" in verdict:
                failures.append("trade signals cannot use a not-run backtest verdict")
            if not isinstance(trade_count, int) or trade_count <= 0:
                failures.append("trade signals require positive backtest trade_count")

    return failures


def evaluate_report(report_path: Path) -> list[str]:
    if not report_path.exists():
        return ["report.md missing"]
    text = report_path.read_text(encoding="utf-8", errors="ignore")
    required_terms = ["Fundamental", "Valuation", "Technical", "Bear", "Backtest"]
    cn_terms = ["基本面", "估值", "技术", "反方", "回测"]
    missing = []
    for en, cn in zip(required_terms, cn_terms, strict=True):
        if en not in text and cn not in text:
            missing.append(f"{en}/{cn}")
    return [f"report.md missing sections: {', '.join(missing)}"] if missing else []


def evaluate_audit(audit_path: Path) -> list[str]:
    if not audit_path.exists():
        return ["audit.json missing"]
    audit, error = load_json(audit_path)
    if error:
        return [f"cannot read audit.json: {error}"]
    assert audit is not None
    failures = []
    if audit.get("has_bear_case") is False:
        failures.append("audit says bear case is missing")
    if audit.get("signal_boundary_ok") is False:
        failures.append("audit says signal boundary failed")
    return failures


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    failures: list[str] = []

    if not run_dir.exists():
        print(f"ERROR: run directory does not exist: {run_dir}", file=sys.stderr)
        return 2

    failures.extend(evaluate_signal(run_dir / "signal.json"))
    failures.extend(evaluate_report(run_dir / "report.md"))
    failures.extend(evaluate_audit(run_dir / "audit.json"))

    result = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "passed": not failures,
        "failures": failures,
    }
    (run_dir / "evaluation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("evaluation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
