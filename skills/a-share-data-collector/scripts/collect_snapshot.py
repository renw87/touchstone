#!/usr/bin/env python3
"""Collect an A-share research data snapshot.

This script is intentionally conservative. It can use AKShare when installed,
but it also creates explicit empty placeholder contracts so downstream agents
see missing data instead of inventing it.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect A-share snapshot data.")
    parser.add_argument("symbol", help="A-share symbol, for example 300750.SZ")
    parser.add_argument("--name", default="", help="Stock name")
    parser.add_argument("--provider", choices=["auto", "akshare", "empty"], default="auto")
    parser.add_argument("--start", default="20240101", help="Start date in YYYYMMDD")
    parser.add_argument("--end", default=datetime.now().strftime("%Y%m%d"), help="End date in YYYYMMDD")
    parser.add_argument("--adjust", choices=["none", "qfq", "hfq"], default="qfq")
    parser.add_argument("--out-dir", default="data/raw", help="Output root directory")
    return parser.parse_args()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def akshare_symbol(symbol: str) -> str:
    return symbol.split(".")[0]


def number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def row_value(row: Any, *names: str) -> Any:
    for name in names:
        try:
            if name in row:
                return row[name]
        except TypeError:
            pass
    return None


def collect_akshare(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001 - user-facing status
        return [], f"akshare_import_failed: {exc}"

    adjust = "" if args.adjust == "none" else args.adjust
    try:
        frame = ak.stock_zh_a_hist(
            symbol=akshare_symbol(args.symbol),
            period="daily",
            start_date=args.start,
            end_date=args.end,
            adjust=adjust,
        )
    except Exception as exc:  # noqa: BLE001 - provider failures are status data
        return [], f"akshare_fetch_failed: {exc}"

    bars: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        bars.append(
            {
                "date": str(row_value(row, "日期", "date")),
                "open": number(row_value(row, "开盘", "open")) or 0,
                "high": number(row_value(row, "最高", "high")) or 0,
                "low": number(row_value(row, "最低", "low")) or 0,
                "close": number(row_value(row, "收盘", "close")) or 0,
                "volume": number(row_value(row, "成交量", "volume")) or 0,
                "amount": number(row_value(row, "成交额", "amount")) or 0,
                "turnover_rate": number(row_value(row, "换手率", "turnover_rate")),
                "limit_up": None,
                "limit_down": None,
            }
        )
    return bars, None


def import_akshare() -> tuple[Any | None, str | None]:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001 - user-facing status
        return None, f"akshare_import_failed: {exc}"
    return ak, None


def collect_financials_akshare(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str | None]:
    ak, error = import_akshare()
    if error:
        return [], error

    code = akshare_symbol(args.symbol)
    frames: list[Any] = []
    errors: list[str] = []
    for call_name, kwargs in (
        ("stock_financial_abstract", {"symbol": code}),
        ("stock_financial_analysis_indicator", {"symbol": code}),
    ):
        func = getattr(ak, call_name, None)
        if not func:
            errors.append(f"{call_name}_missing")
            continue
        try:
            frames.append(func(**kwargs))
        except Exception as exc:  # noqa: BLE001 - provider failures are status data
            errors.append(f"{call_name}_failed: {exc}")

    reports: list[dict[str, Any]] = []
    for frame in frames:
        try:
            iterator = frame.iterrows()
        except AttributeError:
            continue
        for _, row in iterator:
            report_period = str(row_value(row, "报告期", "报告日期", "date", "report_period") or "")
            publish_date = str(row_value(row, "公告日期", "发布日期", "publish_date") or report_period)
            if not report_period:
                continue
            reports.append(
                {
                    "report_period": report_period,
                    "publish_date": publish_date,
                    "revenue": number(row_value(row, "营业总收入", "营业收入", "revenue")),
                    "net_profit_parent": number(row_value(row, "归母净利润", "净利润", "net_profit_parent")),
                    "net_profit_excl_nonrecurring": number(row_value(row, "扣非净利润", "net_profit_excl_nonrecurring")),
                    "operating_cash_flow": number(row_value(row, "经营现金流量净额", "operating_cash_flow")),
                    "gross_margin": number(row_value(row, "销售毛利率", "毛利率", "gross_margin")),
                    "net_margin": number(row_value(row, "销售净利率", "净利率", "net_margin")),
                    "roe": number(row_value(row, "净资产收益率", "ROE", "roe")),
                    "debt_to_asset": number(row_value(row, "资产负债率", "debt_to_asset")),
                    "accounts_receivable": number(row_value(row, "应收账款", "accounts_receivable")),
                    "inventory": number(row_value(row, "存货", "inventory")),
                    "goodwill": number(row_value(row, "商誉", "goodwill")),
                }
            )

    deduped: dict[str, dict[str, Any]] = {}
    for report in reports:
        deduped[report["report_period"]] = {**deduped.get(report["report_period"], {}), **report}
    if not deduped:
        return [], "; ".join(errors) if errors else "akshare_financials_empty"
    return list(deduped.values()), None


def collect_announcements_akshare(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str | None]:
    ak, error = import_akshare()
    if error:
        return [], error

    attempts = (
        ("stock_notice_report", {"symbol": akshare_symbol(args.symbol)}),
        ("stock_zh_a_disclosure_report_cninfo", {"symbol": akshare_symbol(args.symbol)}),
    )
    errors: list[str] = []
    announcements: list[dict[str, Any]] = []
    for call_name, kwargs in attempts:
        func = getattr(ak, call_name, None)
        if not func:
            errors.append(f"{call_name}_missing")
            continue
        try:
            frame = func(**kwargs)
        except Exception as exc:  # noqa: BLE001 - provider failures are status data
            errors.append(f"{call_name}_failed: {exc}")
            continue
        try:
            iterator = frame.iterrows()
        except AttributeError:
            continue
        for _, row in iterator:
            title = str(row_value(row, "公告标题", "title", "公告名称", "name") or "")
            publish_time = str(row_value(row, "公告日期", "publish_time", "date", "发布日期") or "")
            if not title:
                continue
            announcements.append(
                {
                    "publish_time": publish_time,
                    "event_type": str(row_value(row, "公告类型", "event_type", "类型") or "unknown"),
                    "title": title,
                    "source_url": str(row_value(row, "公告链接", "url", "source_url") or ""),
                    "summary": "",
                    "impact_direction": "unknown",
                    "confidence": "medium" if publish_time else "low",
                }
            )
    if not announcements:
        return [], "; ".join(errors) if errors else "akshare_announcements_empty"
    return announcements, None


def collect_lhb_akshare(args: argparse.Namespace) -> tuple[list[dict[str, Any]], str | None]:
    ak, error = import_akshare()
    if error:
        return [], error

    attempts = (
        ("stock_lhb_detail_em", {"symbol": akshare_symbol(args.symbol), "start_date": args.start, "end_date": args.end}),
        ("stock_lhb_stock_detail_em", {"symbol": akshare_symbol(args.symbol), "date": args.end}),
    )
    errors: list[str] = []
    entries: list[dict[str, Any]] = []
    for call_name, kwargs in attempts:
        func = getattr(ak, call_name, None)
        if not func:
            errors.append(f"{call_name}_missing")
            continue
        try:
            frame = func(**kwargs)
        except Exception as exc:  # noqa: BLE001 - provider failures are status data
            errors.append(f"{call_name}_failed: {exc}")
            continue
        try:
            iterator = frame.iterrows()
        except AttributeError:
            continue
        for _, row in iterator:
            entries.append(
                {
                    "date": str(row_value(row, "上榜日", "日期", "date") or ""),
                    "reason": str(row_value(row, "解读", "上榜原因", "reason") or ""),
                    "seat": str(row_value(row, "营业部名称", "席位名称", "seat") or ""),
                    "buy_amount": number(row_value(row, "买入额", "买入金额", "buy_amount")),
                    "sell_amount": number(row_value(row, "卖出额", "卖出金额", "sell_amount")),
                    "net_amount": number(row_value(row, "净买额", "net_amount")),
                    "source": call_name,
                }
            )
    if not entries:
        return [], "; ".join(errors) if errors else "akshare_lhb_empty"
    return entries, None


def build_snapshot(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    status = {
        "symbol": args.symbol,
        "name": args.name,
        "provider_requested": args.provider,
        "provider_used": "empty",
        "created_at": datetime.now().isoformat(),
        "status": "partial",
        "errors": [],
        "insufficient_data": ["financials", "announcements", "lhb"],
        "files": {},
    }

    bars: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    announcements_list: list[dict[str, Any]] = []
    lhb_entries: list[dict[str, Any]] = []
    if args.provider in {"auto", "akshare"}:
        bars, error = collect_akshare(args)
        if error:
            status["errors"].append(error)
            if args.provider == "akshare":
                status["insufficient_data"].append("market_data")
        else:
            status["provider_used"] = "akshare"

        reports, error = collect_financials_akshare(args)
        if error:
            status["errors"].append(error)
        else:
            status["provider_used"] = "akshare"

        announcements_list, error = collect_announcements_akshare(args)
        if error:
            status["errors"].append(error)
        else:
            status["provider_used"] = "akshare"

        lhb_entries, error = collect_lhb_akshare(args)
        if error:
            status["errors"].append(error)
        else:
            status["provider_used"] = "akshare"

    if not bars:
        status["insufficient_data"].append("market_data")
    if reports:
        status["insufficient_data"] = [item for item in status["insufficient_data"] if item != "financials"]
    if announcements_list:
        status["insufficient_data"] = [item for item in status["insufficient_data"] if item != "announcements"]
    if lhb_entries:
        status["insufficient_data"] = [item for item in status["insufficient_data"] if item != "lhb"]
    status["insufficient_data"] = sorted(set(status["insufficient_data"]))

    market_data = {
        "symbol": args.symbol,
        "name": args.name,
        "adjustment": args.adjust,
        "source": status["provider_used"],
        "created_at": status["created_at"],
        "bars": bars,
    }
    if bars and not status["errors"]:
        status["status"] = "partial" if status["insufficient_data"] else "success"
    financials = {"symbol": args.symbol, "name": args.name, "source": status["provider_used"], "reports": reports}
    announcements = {"symbol": args.symbol, "name": args.name, "source": status["provider_used"], "announcements": announcements_list}
    lhb = {"symbol": args.symbol, "name": args.name, "source": status["provider_used"], "entries": lhb_entries}
    return market_data, financials, announcements, lhb, status


def main() -> int:
    args = parse_args()
    symbol_dir = Path(args.out_dir) / args.symbol
    market_data, financials, announcements, lhb, status = build_snapshot(args)

    files = {
        "market_data": symbol_dir / "market_data.json",
        "financials": symbol_dir / "financials.json",
        "announcements": symbol_dir / "announcements.json",
        "lhb": symbol_dir / "lhb.json",
        "collection_status": symbol_dir / "collection_status.json",
    }
    status["files"] = {key: str(path) for key, path in files.items()}

    write_json(files["market_data"], market_data)
    write_json(files["financials"], financials)
    write_json(files["announcements"], announcements)
    write_json(files["lhb"], lhb)
    write_json(files["collection_status"], status)

    print(str(symbol_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
