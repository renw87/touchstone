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
        result = float(value)
    except (TypeError, ValueError):
        return None
    # pandas returns NaN/inf for missing cells; treat those as missing.
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def row_value(row: Any, *names: str) -> Any:
    for name in names:
        try:
            if name in row:
                return row[name]
        except TypeError:
            pass
    return None


def _to_yyyymmdd(value: Any) -> str:
    """Normalize a date-like value ('2024-03-31' or datetime.date) to YYYYMMDD."""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else ""


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
    try:
        frame = ak.stock_financial_abstract(symbol=code)
    except Exception as exc:  # noqa: BLE001 - provider failures are status data
        return [], f"stock_financial_abstract_failed: {exc}"
    if frame is None or getattr(frame, "empty", True):
        return [], "akshare_financials_empty"

    # stock_financial_abstract is a wide table: each row is one metric, columns
    # are 选项/指标 plus one column per report period (YYYYMMDD). We pivot it to
    # one record per report period.
    metric_map = {
        "营业总收入": "revenue",
        "归母净利润": "net_profit_parent",
        "净利润": "net_profit",
        "扣非净利润": "net_profit_excl_nonrecurring",
        "经营现金流量净额": "operating_cash_flow",
        "毛利率": "gross_margin",
        "销售净利率": "net_margin",
        "净资产收益率(ROE)": "roe",
        "资产负债率": "debt_to_asset",
        "股东权益合计(净资产)": "net_assets",
        "商誉": "goodwill",
    }
    period_cols = [c for c in frame.columns if isinstance(c, str) and len(c) == 8 and c.isdigit()]
    if not period_cols:
        return [], "akshare_financials_no_period_columns"

    periods: dict[str, dict[str, Any]] = {
        period: {"report_period": period, "publish_date": period} for period in period_cols
    }
    filled: set[tuple[str, str]] = set()
    for _, row in frame.iterrows():
        field = metric_map.get(str(row_value(row, "指标") or ""))
        if not field:
            continue
        for period in period_cols:
            key = (period, field)
            if key in filled:
                continue  # metric names repeat across 选项 groups; keep the first
            value = number(row.get(period))
            if value is not None:
                periods[period][field] = value
                filled.add(key)

    contract_fields = (
        "revenue", "net_profit_parent", "net_profit", "net_profit_excl_nonrecurring",
        "operating_cash_flow", "gross_margin", "net_margin", "roe", "debt_to_asset",
        "net_assets", "goodwill", "accounts_receivable", "inventory",
    )
    reports: list[dict[str, Any]] = []
    for period in period_cols:  # columns are already ordered newest -> oldest
        record = periods[period]
        for field in contract_fields:
            record.setdefault(field, None)
        if record.get("revenue") is not None or record.get("net_profit_parent") is not None:
            reports.append(record)

    if not reports:
        return [], "akshare_financials_empty"
    return reports, None


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

    code = akshare_symbol(args.symbol)
    # Step 1: list the dates this stock appeared on the Dragon-Tiger list.
    try:
        dates_frame = ak.stock_lhb_stock_detail_date_em(symbol=code)
    except Exception as exc:  # noqa: BLE001 - provider failures are status data
        return [], f"stock_lhb_stock_detail_date_em_failed: {exc}"
    if dates_frame is None or getattr(dates_frame, "empty", True):
        return [], "akshare_lhb_no_records"

    all_dates: list[str] = []
    for _, row in dates_frame.iterrows():
        day = _to_yyyymmdd(row_value(row, "交易日", "上榜日", "日期", "date"))
        if day:
            all_dates.append(day)
    in_range = sorted({d for d in all_dates if args.start <= d <= args.end}, reverse=True)
    if not in_range:
        latest = max(all_dates) if all_dates else "NA"
        return [], f"akshare_lhb_none_in_range (latest_listed={latest})"

    # Step 2: pull buy/sell seat details for the most recent in-range dates.
    errors: list[str] = []
    entries: list[dict[str, Any]] = []
    for day in in_range[:10]:
        for flag in ("买入", "卖出"):
            try:
                detail = ak.stock_lhb_stock_detail_em(symbol=code, date=day, flag=flag)
            except Exception as exc:  # noqa: BLE001 - provider failures are status data
                errors.append(f"stock_lhb_stock_detail_em_{day}_{flag}_failed: {exc}")
                continue
            if detail is None or getattr(detail, "empty", True):
                continue
            for _, row in detail.iterrows():
                entries.append(
                    {
                        "date": f"{day[:4]}-{day[4:6]}-{day[6:8]}",
                        "reason": str(row_value(row, "类型", "解读", "上榜原因", "reason") or ""),
                        "seat": str(row_value(row, "交易营业部名称", "营业部名称", "席位名称", "seat") or ""),
                        "buy_amount": number(row_value(row, "买入金额", "买入额", "buy_amount")),
                        "sell_amount": number(row_value(row, "卖出金额", "卖出额", "sell_amount")),
                        "net_amount": number(row_value(row, "净额", "净买额", "net_amount")),
                        "flag": flag,
                        "source": "stock_lhb_stock_detail_em",
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
