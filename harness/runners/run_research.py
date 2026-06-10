#!/usr/bin/env python3
"""Create a Harness run directory for one A-share research task.

The runner does not call an LLM. It prepares deterministic inputs and a prompt
that Codex, Claude Code, Cursor, or another agent can execute.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "harness"
SKILL_ROOT = ROOT / "skills" / "a-share-investment-research"
DATA_ROOT = ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an A-share research Harness run.")
    parser.add_argument("symbol_arg", nargs="?", help="A-share symbol, for example 300750.SZ")
    parser.add_argument("--symbol", default=None, help="A-share symbol, for example 300750.SZ")
    parser.add_argument("--name", required=True, help="Stock name")
    parser.add_argument("--horizon", default="swing", choices=["short", "swing", "medium", "long"])
    parser.add_argument("--risk-style", default="balanced", choices=["conservative", "balanced", "aggressive"])
    parser.add_argument("--account-equity", type=float, default=100000)
    parser.add_argument("--max-single-stock-weight", type=float, default=0.15)
    parser.add_argument("--risk-per-trade", type=float, default=0.01)
    parser.add_argument("--shares", type=int, default=0)
    parser.add_argument("--cost-price", type=float, default=None)
    parser.add_argument("--adapter", default="codex", choices=["codex", "claude-code", "cursor", "local"])
    parser.add_argument("--date", default=None, help="Run date, YYYY-MM-DD. Defaults to today in local time.")
    parser.add_argument("--market-data", default=None, help="Path to market_data.json")
    parser.add_argument("--financials", default=None, help="Path to financials.json")
    parser.add_argument("--announcements", default=None, help="Path to announcements.json")
    parser.add_argument("--lhb", default=None, help="Path to lhb.json")
    parser.add_argument("--fundamental-score", default=None, help="Path to fundamental_score.json")
    parser.add_argument("--valuation-score", default=None, help="Path to valuation_score.json")
    parser.add_argument("--theme-chain", default=None, help="Path to theme_chain.json")
    parser.add_argument("--technical-snapshot", default=None, help="Path to technical_snapshot.json")
    parser.add_argument("--backtest-summary", default=None, help="Path to backtest_summary.json")
    parser.add_argument("--parameter-scan", default=None, help="Path to parameter_scan.json")
    parser.add_argument("--collection-status", default=None, help="Path to collection_status.json")
    args = parser.parse_args()
    args.symbol = args.symbol or args.symbol_arg
    if not args.symbol:
        parser.error("symbol is required, either as positional argument or --symbol")
    return args


def resolved_data_context(args: argparse.Namespace) -> dict:
    symbol_dir = DATA_ROOT / args.symbol
    candidates = {
        "market_data": Path(args.market_data) if args.market_data else symbol_dir / "market_data.json",
        "financials": Path(args.financials) if args.financials else symbol_dir / "financials.json",
        "announcements": Path(args.announcements) if args.announcements else symbol_dir / "announcements.json",
        "lhb": Path(args.lhb) if args.lhb else symbol_dir / "lhb.json",
        "fundamental_score": Path(args.fundamental_score) if args.fundamental_score else symbol_dir / "fundamental_score.json",
        "valuation_score": Path(args.valuation_score) if args.valuation_score else symbol_dir / "valuation_score.json",
        "theme_chain": Path(args.theme_chain) if args.theme_chain else symbol_dir / "theme_chain.json",
        "technical_snapshot": Path(args.technical_snapshot) if args.technical_snapshot else symbol_dir / "technical_snapshot.json",
        "backtest_summary": Path(args.backtest_summary) if args.backtest_summary else symbol_dir / "backtest_summary.json",
        "parameter_scan": Path(args.parameter_scan) if args.parameter_scan else symbol_dir / "parameter_scan.json",
        "collection_status": Path(args.collection_status) if args.collection_status else symbol_dir / "collection_status.json",
    }
    files = {key: str(path) for key, path in candidates.items() if path.exists()}
    missing = [key for key, path in candidates.items() if not path.exists()]
    return {
        "data_root": str(DATA_ROOT),
        "symbol_dir": str(symbol_dir),
        "files": files,
        "missing": missing,
    }


def build_input(args: argparse.Namespace, created_at: str) -> dict:
    return {
        "task_id": "single_stock_research",
        "task_type": "research",
        "symbol": args.symbol,
        "name": args.name,
        "horizon": args.horizon,
        "risk_style": args.risk_style,
        "account": {
            "equity": args.account_equity,
            "max_single_stock_weight": args.max_single_stock_weight,
            "risk_per_trade": args.risk_per_trade,
        },
        "current_position": {
            "shares": args.shares,
            "cost_price": args.cost_price,
        },
        "requested_outputs": ["report.md", "signal.json", "audit.json"],
        "skill_context": {
            "skill": str(SKILL_ROOT / "SKILL.md"),
            "references": [
                str(SKILL_ROOT / "references" / "workflow.md"),
                str(SKILL_ROOT / "references" / "agent-roles.md"),
                str(SKILL_ROOT / "references" / "a-share-data.md"),
                str(SKILL_ROOT / "references" / "signal-policy.md"),
                str(SKILL_ROOT / "references" / "backtest.md"),
                str(SKILL_ROOT / "references" / "project-map.md"),
            ],
            "report_template": str(SKILL_ROOT / "templates" / "stock_report.md"),
            "signal_schema": str(SKILL_ROOT / "schemas" / "signal.schema.json"),
        },
        "data_context": resolved_data_context(args),
        "created_at": created_at,
        "runtime_adapter": args.adapter,
        "constraints": {
            "output_is_research_assistance": True,
            "no_unconditional_buy_sell": True,
            "max_signal_without_backtest": "watch",
        },
    }


def build_prompt(run_dir: Path, run_input: dict) -> str:
    data_files = run_input["data_context"]["files"]
    data_block = "\n".join(f"- {key}: {value}" for key, value in data_files.items()) or "- no structured data files found"
    missing_block = ", ".join(run_input["data_context"]["missing"]) or "none"
    return f"""# Harness Task: Single-stock A-share Research

Use the A-share investment research Skill:

```text
{run_input["skill_context"]["skill"]}
```

Read this run input:

```text
{run_dir / "input.json"}
```

Analyze:

- Symbol: {run_input["symbol"]}
- Name: {run_input["name"]}
- Horizon: {run_input["horizon"]}
- Risk style: {run_input["risk_style"]}
- Account equity: {run_input["account"]["equity"]}
- Max single-stock weight: {run_input["account"]["max_single_stock_weight"]}
- Risk per trade: {run_input["account"]["risk_per_trade"]}
- Current position: {run_input["current_position"]}

Structured data context:

{data_block}

Missing data files: {missing_block}

Required outputs in this directory:

```text
{run_dir / "report.md"}
{run_dir / "signal.json"}
{run_dir / "audit.json"}
```

Hard boundaries:

- Keep every signal conditional.
- If evidence, financials, valuation, theme-chain, technical data, or backtest data is missing, mark it as `insufficient_data`.
- Without a credible backtest summary, cap the signal at `watch`.
- Without valuation and theme-chain assessment, cap `pilot_build` and `add`.
- Any `pilot_build` or `add` signal must include trigger condition, stop condition, position limit, take-profit plan, evidence, bear case, and next review time.
- Treat the output as research assistance, not investment advice.
"""


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc)
    created_at = now.isoformat()
    run_date = args.date or datetime.now().strftime("%Y-%m-%d")
    run_id = f"{run_date}/{args.symbol}"
    run_dir = HARNESS_ROOT / "runs" / run_date / args.symbol
    run_dir.mkdir(parents=True, exist_ok=True)

    run_input = build_input(args, created_at)
    (run_dir / "input.json").write_text(
        json.dumps(run_input, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "prompt.md").write_text(build_prompt(run_dir, run_input), encoding="utf-8")

    run_record = {
        "run_id": run_id,
        "created_at": created_at,
        "input": str(run_dir / "input.json"),
        "outputs": {
            "report": str(run_dir / "report.md"),
            "signal": str(run_dir / "signal.json"),
            "audit": str(run_dir / "audit.json"),
        },
        "status": "created",
        "runtime_adapter": args.adapter,
    }
    (run_dir / "run_record.json").write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
