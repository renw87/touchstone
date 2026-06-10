#!/usr/bin/env python3
"""Score A-share valuation from financials, price, market cap, peers, and history."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score valuation from financials and optional market valuation inputs.")
    parser.add_argument("financials", help="Path to financials.json")
    parser.add_argument("--market-data", default=None, help="Path to market_data.json. Defaults next to financials.json.")
    parser.add_argument("--valuation-input", default=None, help="Optional JSON with market_cap, total_shares, peer_medians, or history.")
    parser.add_argument("--peers", default=None, help="Optional peer valuation JSON.")
    parser.add_argument("--history", default=None, help="Optional historical valuation JSON.")
    parser.add_argument("--price", type=float, default=None, help="Latest price override.")
    parser.add_argument("--market-cap", type=float, default=None, help="Market cap override, same unit as financial statement values.")
    parser.add_argument("--float-market-cap", type=float, default=None)
    parser.add_argument("--total-shares", type=float, default=None, help="Total shares override for market_cap = price * total_shares.")
    parser.add_argument("--out", default=None, help="Output path. Defaults to valuation_score.json next to financials.json.")
    return parser.parse_args()


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def first_number(*values: Any) -> float | None:
    for value in values:
        out = num(value)
        if out is not None:
            return out
    return None


def latest_close(market: dict[str, Any]) -> float | None:
    bars = sorted(market.get("bars", []), key=lambda item: str(item.get("date", "")))
    if not bars:
        return None
    return num(bars[-1].get("close"))


def latest_reports(financials: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    reports = sorted(financials.get("reports", []), key=lambda item: str(item.get("report_period", "")))
    latest = reports[-1] if reports else {}
    previous = reports[-2] if len(reports) >= 2 else {}
    return latest, previous


def growth(latest: float | None, previous: float | None) -> float | None:
    if latest is None or previous is None or previous == 0:
        return None
    return latest / previous - 1


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def percentile(value: float | None, values: list[float]) -> float | None:
    if value is None or not values:
        return None
    below_or_equal = sum(1 for item in values if item <= value)
    return below_or_equal / len(values)


def collect_peer_medians(peers: dict[str, Any], valuation_input: dict[str, Any]) -> dict[str, float]:
    explicit = valuation_input.get("peer_medians") or peers.get("peer_medians") or peers.get("median") or {}
    out = {key: value for key, value in ((key, num(explicit.get(key))) for key in ("pe", "pb", "ps")) if value is not None}
    peer_rows = peers.get("peers", [])
    for key in ("pe", "pb", "ps"):
        if key in out:
            continue
        values = [num(row.get(key)) for row in peer_rows if num(row.get(key)) is not None and num(row.get(key)) > 0]
        if values:
            out[key] = round(float(median(values)), 6)
    return out


def collect_history(history: dict[str, Any], valuation_input: dict[str, Any], metric: str) -> list[float]:
    values: list[float] = []
    for source in (valuation_input, history):
        raw = source.get(f"{metric}_history") or source.get("history") or source.get("valuation_history") or []
        for item in raw:
            value = num(item.get(metric) if isinstance(item, dict) else item)
            if value is not None and value > 0:
                values.append(value)
    return values


def add_component(components: list[dict[str, Any]], name: str, score: float, evidence: str) -> None:
    components.append({"name": name, "score": round(score, 4), "evidence": evidence})


def score_valuation(args: argparse.Namespace) -> dict[str, Any]:
    financial_path = Path(args.financials)
    market_path = Path(args.market_data) if args.market_data else financial_path.parent / "market_data.json"
    valuation_path = Path(args.valuation_input) if args.valuation_input else None
    peer_path = Path(args.peers) if args.peers else None
    history_path = Path(args.history) if args.history else None

    financials = read_json(financial_path)
    market = read_json(market_path)
    valuation_input = read_json(valuation_path)
    peers = read_json(peer_path)
    history = read_json(history_path)

    latest, previous = latest_reports(financials)
    insufficient: list[str] = []
    components: list[dict[str, Any]] = []
    evidence: list[str] = []
    warnings: list[str] = []

    price = first_number(args.price, valuation_input.get("price"), valuation_input.get("latest_price"), latest_close(market))
    total_shares = first_number(args.total_shares, valuation_input.get("total_shares"), latest.get("total_shares"))
    market_cap = first_number(
        args.market_cap,
        valuation_input.get("market_cap"),
        valuation_input.get("total_market_cap"),
        price * total_shares if price is not None and total_shares is not None else None,
    )
    float_market_cap = first_number(args.float_market_cap, valuation_input.get("float_market_cap"))

    revenue = first_number(latest.get("revenue"), latest.get("operating_revenue"))
    previous_revenue = first_number(previous.get("revenue"), previous.get("operating_revenue"))
    profit = first_number(latest.get("net_profit_parent"), latest.get("net_profit"))
    previous_profit = first_number(previous.get("net_profit_parent"), previous.get("net_profit"))
    equity = first_number(
        latest.get("shareholder_equity_parent"),
        latest.get("shareholder_equity"),
        latest.get("net_assets_parent"),
        latest.get("book_value_parent"),
        valuation_input.get("book_value_parent"),
        valuation_input.get("book_equity"),
    )

    if not latest:
        insufficient.append("financials.reports")
    if price is None:
        insufficient.append("latest_price")
    if market_cap is None:
        insufficient.append("market_cap")
    if total_shares is None and market_cap is None:
        insufficient.append("total_shares")

    pe = safe_ratio(market_cap, profit)
    ps = safe_ratio(market_cap, revenue)
    pb = safe_ratio(market_cap, equity)
    revenue_growth = growth(revenue, previous_revenue)
    profit_growth = growth(profit, previous_profit)
    peg = pe / (profit_growth * 100) if pe is not None and profit_growth is not None and profit_growth > 0 else None
    peer_medians = collect_peer_medians(peers, valuation_input)
    pe_percentile = percentile(pe, collect_history(history, valuation_input, "pe"))
    pb_percentile = percentile(pb, collect_history(history, valuation_input, "pb"))

    if pe is None:
        insufficient.append("pe")
    if ps is None:
        insufficient.append("ps")
    if pb is None:
        insufficient.append("pb")
    if peg is None:
        insufficient.append("peg")
    if not peer_medians:
        insufficient.append("peer_valuation")
    if pe_percentile is None and pb_percentile is None:
        insufficient.append("historical_valuation_percentile")

    score = 0.0
    risk_score = 3.0
    if any(value is not None for value in (pe, ps, pb)):
        score += 0.8
        add_component(components, "valuation_visibility", 0.8, "至少一个核心估值指标可用。")

    if pe is not None:
        if pe <= 15:
            score += 1.1
            risk_score += 0.4
            add_component(components, "pe", 1.1, f"PE {pe:.2f}，处于偏低区间。")
        elif pe <= 30:
            score += 0.8
            add_component(components, "pe", 0.8, f"PE {pe:.2f}，处于合理区间。")
        elif pe <= 50:
            score += 0.3
            add_component(components, "pe", 0.3, f"PE {pe:.2f}，估值偏高。")
        else:
            risk_score -= 0.8
            add_component(components, "pe", -0.4, f"PE {pe:.2f}，估值压力较高。")

    if pb is not None:
        if pb <= 2:
            score += 0.8
            risk_score += 0.3
            add_component(components, "pb", 0.8, f"PB {pb:.2f}，资产估值较低。")
        elif pb <= 4:
            score += 0.4
            add_component(components, "pb", 0.4, f"PB {pb:.2f}，资产估值中性。")
        else:
            risk_score -= 0.4
            add_component(components, "pb", -0.2, f"PB {pb:.2f}，资产估值偏高。")

    if ps is not None:
        if ps <= 3:
            score += 0.6
            add_component(components, "ps", 0.6, f"PS {ps:.2f}，收入估值较低。")
        elif ps <= 8:
            score += 0.3
            add_component(components, "ps", 0.3, f"PS {ps:.2f}，收入估值中性。")
        else:
            risk_score -= 0.3
            add_component(components, "ps", -0.1, f"PS {ps:.2f}，收入估值偏高。")

    if peg is not None:
        if peg <= 1:
            score += 0.8
            risk_score += 0.3
            add_component(components, "peg", 0.8, f"PEG {peg:.2f}，增长可部分消化估值。")
        elif peg <= 2:
            score += 0.4
            add_component(components, "peg", 0.4, f"PEG {peg:.2f}，增长与估值大致匹配。")
        else:
            risk_score -= 0.3
            add_component(components, "peg", -0.2, f"PEG {peg:.2f}，增长难以覆盖估值。")

    peer_pe = peer_medians.get("pe")
    if pe is not None and peer_pe:
        if pe <= peer_pe:
            score += 0.7
            add_component(components, "peer_pe", 0.7, f"PE 低于或等于同业中位 {peer_pe:.2f}。")
        elif pe <= peer_pe * 1.3:
            score += 0.3
            add_component(components, "peer_pe", 0.3, f"PE 接近同业中位 {peer_pe:.2f}。")
        elif pe >= peer_pe * 1.8:
            risk_score -= 0.5
            add_component(components, "peer_pe", -0.3, f"PE 明显高于同业中位 {peer_pe:.2f}。")

    for metric_name, pct in (("pe_percentile", pe_percentile), ("pb_percentile", pb_percentile)):
        if pct is None:
            continue
        if pct <= 0.4:
            score += 0.4
            add_component(components, metric_name, 0.4, f"历史分位 {pct:.2%}，估值不高。")
        elif pct <= 0.7:
            score += 0.2
            add_component(components, metric_name, 0.2, f"历史分位 {pct:.2%}，估值中性。")
        elif pct >= 0.85:
            risk_score -= 0.5
            add_component(components, metric_name, -0.3, f"历史分位 {pct:.2%}，估值压缩风险较高。")

    if market_cap is not None and price is not None:
        evidence.append(f"估值输入：价格 {price:.4f}，市值 {market_cap:.4f}。")
    if pe is not None:
        evidence.append(f"PE {pe:.2f}")
    if pb is not None:
        evidence.append(f"PB {pb:.2f}")
    if ps is not None:
        evidence.append(f"PS {ps:.2f}")
    if float_market_cap is not None:
        evidence.append(f"流通市值 {float_market_cap:.4f}")
    if not peer_medians:
        warnings.append("缺少同业估值，不能判断相对贵便宜。")
    if pe_percentile is None and pb_percentile is None:
        warnings.append("缺少历史估值序列，不能判断历史分位。")

    score = max(0.0, min(5.0, score))
    risk_score = max(0.0, min(5.0, risk_score))
    insufficient = sorted(set(insufficient))

    return {
        "symbol": financials.get("symbol") or valuation_input.get("symbol"),
        "name": financials.get("name") or valuation_input.get("name"),
        "created_at": datetime.now().isoformat(),
        "sources": {
            "financials": str(financial_path),
            "market_data": str(market_path) if market_path.exists() else "",
            "valuation_input": str(valuation_path) if valuation_path else "",
            "peers": str(peer_path) if peer_path else "",
            "history": str(history_path) if history_path else "",
        },
        "latest_report_period": str(latest.get("report_period", "")),
        "metrics": {
            "price": price,
            "market_cap": market_cap,
            "float_market_cap": float_market_cap,
            "pe": pe,
            "pb": pb,
            "ps": ps,
            "peg": peg,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "peer_medians": peer_medians,
            "historical_percentiles": {"pe": pe_percentile, "pb": pb_percentile},
        },
        "scores": {"valuation": round(score, 4), "risk": round(risk_score, 4)},
        "components": components,
        "evidence": evidence or ["缺少足够估值输入，不能进行估值评分。"],
        "warnings": warnings,
        "insufficient_data": insufficient,
        "verdict": "insufficient_data" if insufficient else "valuation_score_complete",
    }


def main() -> int:
    args = parse_args()
    financial_path = Path(args.financials)
    out_path = Path(args.out) if args.out else financial_path.parent / "valuation_score.json"
    write_json(out_path, score_valuation(args))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
