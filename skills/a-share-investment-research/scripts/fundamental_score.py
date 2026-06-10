#!/usr/bin/env python3
"""Score basic A-share fundamentals from financials.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score fundamentals from financials.json.")
    parser.add_argument("financials", help="Path to financials.json")
    parser.add_argument("--out", default=None, help="Output path. Defaults to fundamental_score.json next to input.")
    return parser.parse_args()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def pct_growth(latest: float | None, previous: float | None) -> float | None:
    if latest is None or previous is None or previous == 0:
        return None
    return latest / previous - 1


def add_component(components: list[dict[str, Any]], name: str, score: float, evidence: str) -> None:
    components.append({"name": name, "score": round(score, 4), "evidence": evidence})


def score_financials(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    reports = sorted(data.get("reports", []), key=lambda item: str(item.get("report_period", "")))
    insufficient: list[str] = []
    components: list[dict[str, Any]] = []
    evidence: list[str] = []

    if not reports:
        insufficient.append("financials.reports")
        return {
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "created_at": datetime.now().isoformat(),
            "source_financials": str(path),
            "latest_report_period": "",
            "scores": {"fundamental": 0, "risk": 0},
            "components": components,
            "evidence": ["缺少财报数据，不能进行基本面评分。"],
            "insufficient_data": insufficient,
            "verdict": "insufficient_data",
        }

    latest = reports[-1]
    previous = reports[-2] if len(reports) >= 2 else {}
    latest_period = str(latest.get("report_period", ""))

    revenue = num(latest.get("revenue"))
    prev_revenue = num(previous.get("revenue"))
    profit = num(latest.get("net_profit_parent"))
    prev_profit = num(previous.get("net_profit_parent"))
    ocf = num(latest.get("operating_cash_flow"))
    roe = num(latest.get("roe"))
    gross_margin = num(latest.get("gross_margin"))
    net_margin = num(latest.get("net_margin"))
    debt = num(latest.get("debt_to_asset"))
    receivable = num(latest.get("accounts_receivable"))
    inventory = num(latest.get("inventory"))
    goodwill = num(latest.get("goodwill"))

    fundamental = 0.0
    risk = 2.0

    revenue_growth = pct_growth(revenue, prev_revenue)
    if revenue_growth is None:
        insufficient.append("revenue_growth")
    elif revenue_growth > 0.15:
        fundamental += 0.9
        add_component(components, "revenue_growth", 0.9, f"营收增长 {revenue_growth:.2%}")
    elif revenue_growth > 0:
        fundamental += 0.5
        add_component(components, "revenue_growth", 0.5, f"营收增长 {revenue_growth:.2%}")
    else:
        add_component(components, "revenue_growth", 0, f"营收下滑 {revenue_growth:.2%}")

    profit_growth = pct_growth(profit, prev_profit)
    if profit_growth is None:
        insufficient.append("profit_growth")
    elif profit_growth > 0.15:
        fundamental += 0.9
        add_component(components, "profit_growth", 0.9, f"归母净利增长 {profit_growth:.2%}")
    elif profit_growth > 0:
        fundamental += 0.5
        add_component(components, "profit_growth", 0.5, f"归母净利增长 {profit_growth:.2%}")
    else:
        add_component(components, "profit_growth", 0, f"归母净利下滑 {profit_growth:.2%}")

    if ocf is None:
        insufficient.append("operating_cash_flow")
    elif ocf > 0:
        fundamental += 0.8
        risk += 0.5
        add_component(components, "cash_flow", 0.8, "经营现金流为正。")
        if profit and profit > 0 and ocf / profit >= 0.8:
            fundamental += 0.4
            risk += 0.3
            add_component(components, "cash_profit_match", 0.4, f"经营现金流/净利润约 {ocf / profit:.2f}")
    else:
        risk -= 0.6
        add_component(components, "cash_flow", 0, "经营现金流为负。")

    if roe is None:
        insufficient.append("roe")
    elif roe >= 15:
        fundamental += 0.9
        add_component(components, "roe", 0.9, f"ROE {roe:.2f}")
    elif roe >= 8:
        fundamental += 0.5
        add_component(components, "roe", 0.5, f"ROE {roe:.2f}")
    else:
        add_component(components, "roe", 0.1, f"ROE 偏低：{roe:.2f}")

    if gross_margin is not None and gross_margin >= 30:
        fundamental += 0.4
        add_component(components, "gross_margin", 0.4, f"毛利率 {gross_margin:.2f}")
    elif gross_margin is None:
        insufficient.append("gross_margin")

    if net_margin is not None and net_margin >= 10:
        fundamental += 0.3
        add_component(components, "net_margin", 0.3, f"净利率 {net_margin:.2f}")
    elif net_margin is None:
        insufficient.append("net_margin")

    if debt is None:
        insufficient.append("debt_to_asset")
    elif debt <= 40:
        risk += 0.8
        add_component(components, "debt", 0.8, f"资产负债率较低：{debt:.2f}")
    elif debt <= 60:
        risk += 0.4
        add_component(components, "debt", 0.4, f"资产负债率可控：{debt:.2f}")
    else:
        risk -= 0.6
        add_component(components, "debt", -0.6, f"资产负债率偏高：{debt:.2f}")

    balance_risk_fields = {
        "accounts_receivable": receivable,
        "inventory": inventory,
        "goodwill": goodwill,
    }
    missing_balance_fields = [name for name, value in balance_risk_fields.items() if value is None]
    insufficient.extend(missing_balance_fields)
    if not missing_balance_fields:
        risk += 0.3
        add_component(components, "balance_sheet_visibility", 0.3, "应收、存货、商誉字段可用。")

    fundamental = max(0.0, min(5.0, fundamental))
    risk = max(0.0, min(5.0, risk))
    evidence.append(f"最新报告期：{latest_period}")
    if insufficient:
        evidence.append(f"基本面评分缺少字段：{', '.join(sorted(set(insufficient)))}")

    return {
        "symbol": data.get("symbol"),
        "name": data.get("name"),
        "created_at": datetime.now().isoformat(),
        "source_financials": str(path),
        "latest_report_period": latest_period,
        "scores": {"fundamental": round(fundamental, 4), "risk": round(risk, 4)},
        "components": components,
        "evidence": evidence,
        "insufficient_data": sorted(set(insufficient)),
        "verdict": "insufficient_data" if insufficient else "fundamental_score_complete",
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.financials)
    out_path = Path(args.out) if args.out else input_path.parent / "fundamental_score.json"
    write_json(out_path, score_financials(input_path))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
