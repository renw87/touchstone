#!/usr/bin/env python3
"""Compute a conservative technical snapshot from market_data.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute technical snapshot from market data.")
    parser.add_argument("market_data", help="Path to market_data.json")
    parser.add_argument("--out", default=None, help="Output path. Defaults to technical_snapshot.json next to input.")
    return parser.parse_args()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def round_or_none(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def ema_series(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    alpha = 2 / (window + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (1 - alpha) * out[-1])
    return out


def rsi(values: list[float], window: int = 14) -> float | None:
    if len(values) <= window:
        return None
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(abs(min(delta, 0)))
    avg_gain = sum(gains[-window:]) / window
    avg_loss = sum(losses[-window:]) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(bars: list[dict[str, Any]], window: int = 14) -> float | None:
    if len(bars) <= window:
        return None
    true_ranges: list[float] = []
    for i, bar in enumerate(bars):
        high = num(bar.get("high"))
        low = num(bar.get("low"))
        prev_close = num(bars[i - 1].get("close")) if i > 0 else num(bar.get("close"))
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return sum(true_ranges[-window:]) / window


def macd(values: list[float]) -> dict[str, float | None]:
    if len(values) < 35:
        return {"dif": None, "dea": None, "hist": None}
    ema12 = ema_series(values, 12)
    ema26 = ema_series(values, 26)
    dif_series = [a - b for a, b in zip(ema12, ema26, strict=True)]
    dea_series = ema_series(dif_series, 9)
    dif = dif_series[-1]
    dea = dea_series[-1]
    return {"dif": dif, "dea": dea, "hist": 2 * (dif - dea)}


def support_resistance(bars: list[dict[str, Any]], closes: list[float]) -> list[dict[str, Any]]:
    levels: list[dict[str, Any]] = []
    if not bars:
        return levels
    close = closes[-1]
    for window in (20, 60):
        if len(bars) >= window:
            recent = bars[-window:]
            low = min(num(bar.get("low")) for bar in recent)
            high = max(num(bar.get("high")) for bar in recent)
            levels.append(
                {
                    "price": round(low, 4),
                    "kind": "support",
                    "source": f"{window}d_low",
                    "invalidated_by": f"close_below_{round(low, 4)}",
                }
            )
            levels.append(
                {
                    "price": round(high, 4),
                    "kind": "resistance",
                    "source": f"{window}d_high",
                    "invalidated_by": f"close_above_{round(high, 4)}_confirmed",
                }
            )
    for window in (20, 60, 120):
        ma = sma(closes, window)
        if ma is None:
            continue
        levels.append(
            {
                "price": round(ma, 4),
                "kind": "support" if ma <= close else "resistance",
                "source": f"ma{window}",
                "invalidated_by": f"close_cross_ma{window}",
            }
        )
    return levels


def build_snapshot(path: Path) -> dict[str, Any]:
    market = json.loads(path.read_text(encoding="utf-8"))
    bars = sorted(market.get("bars", []), key=lambda item: str(item.get("date", "")))
    closes = [num(bar.get("close")) for bar in bars if num(bar.get("close")) > 0]
    amounts = [num(bar.get("amount")) for bar in bars]
    insufficient: list[str] = []

    if not bars:
        insufficient.append("market_data.bars")
    if len(closes) < 60:
        insufficient.append("at_least_60_daily_bars")
    if len(closes) < 120:
        insufficient.append("at_least_120_daily_bars")

    latest = bars[-1] if bars else {}
    macd_value = macd(closes)
    atr14 = atr(bars)
    indicators = {
        "ma5": round_or_none(sma(closes, 5)),
        "ma10": round_or_none(sma(closes, 10)),
        "ma20": round_or_none(sma(closes, 20)),
        "ma60": round_or_none(sma(closes, 60)),
        "ma120": round_or_none(sma(closes, 120)),
        "ma250": round_or_none(sma(closes, 250)),
        "rsi14": round_or_none(rsi(closes, 14)),
        "atr14": round_or_none(atr14),
        "amount_ma20": round_or_none(sma(amounts, 20)),
        "high_20": round_or_none(max((num(bar.get("high")) for bar in bars[-20:]), default=0)) if len(bars) >= 20 else None,
        "low_20": round_or_none(min((num(bar.get("low")) for bar in bars[-20:]), default=0)) if len(bars) >= 20 else None,
        "high_60": round_or_none(max((num(bar.get("high")) for bar in bars[-60:]), default=0)) if len(bars) >= 60 else None,
        "low_60": round_or_none(min((num(bar.get("low")) for bar in bars[-60:]), default=0)) if len(bars) >= 60 else None,
        "macd": {key: round_or_none(value) for key, value in macd_value.items()},
    }
    close = closes[-1] if closes else None
    trend = {
        "above_ma20": bool(close is not None and indicators["ma20"] is not None and close > indicators["ma20"]),
        "above_ma60": bool(close is not None and indicators["ma60"] is not None and close > indicators["ma60"]),
        "above_ma120": bool(close is not None and indicators["ma120"] is not None and close > indicators["ma120"]),
    }

    return {
        "symbol": market.get("symbol"),
        "name": market.get("name"),
        "as_of": str(latest.get("date", "")) if latest else "",
        "created_at": datetime.now().isoformat(),
        "source_market_data": str(path),
        "adjustment": market.get("adjustment"),
        "bar_count": len(bars),
        "latest_close": round_or_none(close),
        "indicators": indicators,
        "trend": trend,
        "support_resistance": support_resistance(bars, closes),
        "insufficient_data": insufficient,
    }


def main() -> int:
    args = parse_args()
    market_path = Path(args.market_data)
    out_path = Path(args.out) if args.out else market_path.parent / "technical_snapshot.json"
    write_json(out_path, build_snapshot(market_path))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
