#!/usr/bin/env python3
"""Run vectorbt parameter scans from market_data.json.

The script writes explicit dependency/status output when vectorbt or pandas is
not installed. Downstream agents must treat that as insufficient evidence.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_csv_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def parse_csv_floats(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run vectorbt parameter scan.")
    parser.add_argument("market_data", help="Path to market_data.json")
    parser.add_argument("--rule", choices=["ma_cross", "breakout"], default="breakout")
    parser.add_argument("--short-windows", default="5,10,20")
    parser.add_argument("--long-windows", default="30,60,120")
    parser.add_argument("--lookbacks", default="20,60,120")
    parser.add_argument("--amount-multipliers", default="1.0,1.2,1.5")
    parser.add_argument("--exit-ma", type=int, default=20)
    parser.add_argument("--cost-bps", type=float, default=15.0, help="Round-trip cost in bps")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--rank-by", choices=["total_return", "sharpe", "profit_factor", "max_drawdown"], default="total_return")
    parser.add_argument("--engine", choices=["auto", "vectorbt", "skip"], default="auto", help="Use skip to write a not_run scan without importing vectorbt.")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages.")
    parser.add_argument("--out-dir", default=None, help="Output directory. Defaults next to market_data.json")
    return parser.parse_args()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def status(args: argparse.Namespace, message: str) -> None:
    if not args.quiet:
        print(f"[vectorbt_scan] {message}", flush=True)


def num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clean_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return round(out, 8)


def dependency_error_summary(market_path: Path, error: str) -> dict[str, Any]:
    market = json.loads(market_path.read_text(encoding="utf-8"))
    bars = sorted(market.get("bars", []), key=lambda item: str(item.get("date", "")))
    return {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "created_at": datetime.now().isoformat(),
        "engine": "vectorbt",
        "engine_status": "dependency_missing",
        "source_market_data": str(market_path),
        "rule": None,
        "parameter_grid": {},
        "period": {
            "start": str(bars[0].get("date")) if bars else "",
            "end": str(bars[-1].get("date")) if bars else "",
            "bar_count": len(bars),
        },
        "ranking": {},
        "results": [],
        "best": [],
        "insufficient_data": ["vectorbt_or_pandas_dependency"],
        "errors": [error],
        "verdict": "dependency_missing",
    }


def portfolio_metric(portfolio: Any, name: str) -> float | None:
    try:
        value = getattr(portfolio, name)()
    except Exception:  # noqa: BLE001 - vectorbt method availability differs by version
        return None
    return clean_float(value)


def trade_metric(portfolio: Any, name: str) -> float | None:
    try:
        value = getattr(portfolio.trades, name)()
    except Exception:  # noqa: BLE001 - vectorbt method availability differs by version
        return None
    return clean_float(value)


def load_market(market_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    market = json.loads(market_path.read_text(encoding="utf-8"))
    bars = sorted(market.get("bars", []), key=lambda item: str(item.get("date", "")))
    insufficient: list[str] = []
    if len(bars) < 80:
        insufficient.append("at_least_80_bars_for_parameter_scan")
    if not bars:
        insufficient.append("market_data.bars")
    return market, bars, sorted(set(insufficient))


def not_run_summary(market_path: Path, args: argparse.Namespace, insufficient: list[str]) -> dict[str, Any]:
    market, bars, _ = load_market(market_path)
    return {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "created_at": datetime.now().isoformat(),
        "engine": "vectorbt",
        "engine_status": "not_run",
        "source_market_data": str(market_path),
        "rule": args.rule,
        "parameter_grid": {
            "short_windows": parse_csv_ints(args.short_windows),
            "long_windows": parse_csv_ints(args.long_windows),
            "lookbacks": parse_csv_ints(args.lookbacks),
            "amount_multipliers": parse_csv_floats(args.amount_multipliers),
            "exit_ma": args.exit_ma,
            "cost_bps": args.cost_bps,
        },
        "period": {
            "start": str(bars[0].get("date")) if bars else "",
            "end": str(bars[-1].get("date")) if bars else "",
            "bar_count": len(bars),
        },
        "ranking": {"rank_by": args.rank_by, "top_n": args.top_n},
        "results": [],
        "best": [],
        "insufficient_data": sorted(set(insufficient)),
        "errors": [],
        "verdict": "insufficient_data",
    }


def load_frame(bars: list[dict[str, Any]]) -> Any:
    import pandas as pd  # type: ignore

    frame = pd.DataFrame(
        [
            {
                "date": str(bar.get("date", "")),
                "open": num(bar.get("open")),
                "high": num(bar.get("high")),
                "low": num(bar.get("low")),
                "close": num(bar.get("close")),
                "amount": num(bar.get("amount")),
            }
            for bar in bars
        ]
    )
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
        frame = frame.dropna(subset=["date"]).set_index("date")
    return frame


def build_signals(frame: Any, rule: str, params: dict[str, Any]) -> tuple[Any, Any]:
    close = frame["close"]
    amount = frame["amount"]

    if rule == "ma_cross":
        short_ma = close.rolling(params["short_window"]).mean()
        long_ma = close.rolling(params["long_window"]).mean()
        raw_entries = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        raw_exits = short_ma < long_ma
    else:
        prior_high = frame["high"].rolling(params["lookback"]).max().shift(1)
        amount_ma20 = amount.rolling(20).mean().shift(1)
        raw_entries = (close > prior_high) & (amount >= params["amount_multiplier"] * amount_ma20.fillna(0))
        exit_ma = close.rolling(params["exit_ma"]).mean()
        raw_exits = close < exit_ma

    entries = raw_entries.shift(1).fillna(False)
    exits = raw_exits.shift(1).fillna(False)
    return entries, exits


def scan(args: argparse.Namespace) -> dict[str, Any]:
    market_path = Path(args.market_data)
    market, bars, insufficient = load_market(market_path)
    status(args, f"loaded {len(bars)} bars from {market_path}")
    if insufficient:
        status(args, f"not running engine because data is insufficient: {', '.join(insufficient)}")
        return not_run_summary(market_path, args, insufficient)
    if args.engine == "skip":
        status(args, "engine skipped by request; writing not_run parameter_scan.json")
        return not_run_summary(market_path, args, ["vectorbt_engine_skipped"])

    status(args, "importing vectorbt and pandas; first import can be slow on Windows")
    try:
        import vectorbt as vbt  # type: ignore
        import pandas as pd  # noqa: F401  # type: ignore
    except Exception as exc:  # noqa: BLE001 - write status instead of crashing
        status(args, f"dependency import failed: {exc}")
        return dependency_error_summary(market_path, str(exc))
    status(args, "vectorbt import complete")

    frame = load_frame(bars)
    if frame.empty:
        status(args, "not running engine because market frame is empty")
        return not_run_summary(market_path, args, ["market_data.bars"])
    close = frame["close"] if not frame.empty else None
    per_side_fee = args.cost_bps / 20000

    if args.rule == "ma_cross":
        grid = [
            {"short_window": short, "long_window": long}
            for short, long in itertools.product(parse_csv_ints(args.short_windows), parse_csv_ints(args.long_windows))
            if short < long
        ]
    else:
        grid = [
            {"lookback": lookback, "amount_multiplier": multiplier, "exit_ma": args.exit_ma}
            for lookback, multiplier in itertools.product(parse_csv_ints(args.lookbacks), parse_csv_floats(args.amount_multipliers))
        ]

    status(args, f"scanning {len(grid)} parameter sets with rule={args.rule}")
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    if not frame.empty:
        for params in grid:
            try:
                entries, exits = build_signals(frame, args.rule, params)
                portfolio = vbt.Portfolio.from_signals(close, entries, exits, fees=per_side_fee, freq="1D")
                trade_count = trade_metric(portfolio, "count")
                result = {
                    "params": params,
                    "metrics": {
                        "total_return": portfolio_metric(portfolio, "total_return"),
                        "max_drawdown": portfolio_metric(portfolio, "max_drawdown"),
                        "sharpe": portfolio_metric(portfolio, "sharpe_ratio"),
                        "trade_count": int(trade_count or 0),
                        "win_rate": trade_metric(portfolio, "win_rate"),
                        "profit_factor": trade_metric(portfolio, "profit_factor"),
                    },
                }
                results.append(result)
            except Exception as exc:  # noqa: BLE001 - keep other params usable
                errors.append(f"{params}: {exc}")

    def ranking_value(item: dict[str, Any]) -> float:
        value = item["metrics"].get(args.rank_by)
        if value is None:
            return float("inf") if args.rank_by == "max_drawdown" else float("-inf")
        return float(value)

    reverse = args.rank_by != "max_drawdown"
    best = sorted(results, key=ranking_value, reverse=reverse)[: args.top_n]
    no_trade_results = not any(item["metrics"].get("trade_count", 0) for item in results)
    if no_trade_results:
        insufficient.append("parameter_scan_no_trades")
    status(args, f"scan complete: results={len(results)}, errors={len(errors)}, insufficient={len(insufficient)}")

    return {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "created_at": datetime.now().isoformat(),
        "engine": "vectorbt",
        "engine_status": "ok",
        "source_market_data": str(market_path),
        "rule": args.rule,
        "parameter_grid": {
            "short_windows": parse_csv_ints(args.short_windows),
            "long_windows": parse_csv_ints(args.long_windows),
            "lookbacks": parse_csv_ints(args.lookbacks),
            "amount_multipliers": parse_csv_floats(args.amount_multipliers),
            "exit_ma": args.exit_ma,
            "cost_bps": args.cost_bps,
        },
        "period": {
            "start": str(frame.index[0].date()) if not frame.empty else "",
            "end": str(frame.index[-1].date()) if not frame.empty else "",
            "bar_count": int(len(frame)),
        },
        "ranking": {"rank_by": args.rank_by, "top_n": args.top_n},
        "results": results,
        "best": best,
        "insufficient_data": sorted(set(insufficient)),
        "errors": errors,
        "verdict": "insufficient_data" if insufficient else "parameter_scan_complete",
    }


def render_report(summary: dict[str, Any]) -> str:
    return f"""# Vectorbt Parameter Scan

- Symbol: {summary.get("symbol")}
- Engine status: {summary.get("engine_status")}
- Rule: {summary.get("rule")}
- Period: {summary["period"]["start"]} to {summary["period"]["end"]}
- Bar count: {summary["period"]["bar_count"]}
- Ranking: {summary.get("ranking")}
- Verdict: {summary.get("verdict")}
- Insufficient data: {summary.get("insufficient_data")}

## Best

```json
{json.dumps(summary.get("best", []), ensure_ascii=False, indent=2)}
```

## Errors

```json
{json.dumps(summary.get("errors", []), ensure_ascii=False, indent=2)}
```
"""


def main() -> int:
    args = parse_args()
    market_path = Path(args.market_data)
    out_dir = Path(args.out_dir) if args.out_dir else market_path.parent
    summary = scan(args)
    write_json(out_dir / "parameter_scan.json", summary)
    write_text(out_dir / "parameter_scan_report.md", render_report(summary))
    print(str(out_dir / "parameter_scan.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
