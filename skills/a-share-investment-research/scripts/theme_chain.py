#!/usr/bin/env python3
"""Map A-share themes and industry-chain evidence into a conservative score."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


THEME_KEYWORDS = {
    "AI算力": ["AI", "人工智能", "算力", "大模型", "服务器", "GPU", "IDC"],
    "CPO": ["CPO", "光模块", "光通信", "800G", "1.6T", "硅光"],
    "半导体": ["半导体", "芯片", "晶圆", "封测", "EDA", "光刻"],
    "机器人": ["机器人", "减速器", "伺服", "执行器", "人形机器人"],
    "电力设备": ["电力设备", "特高压", "变压器", "储能", "电网"],
    "新能源车": ["新能源车", "动力电池", "锂电", "电池", "充电桩"],
    "创新药": ["创新药", "临床", "IND", "NDA", "药品注册", "管线"],
    "低空经济": ["低空经济", "eVTOL", "无人机", "通航"],
    "数据要素": ["数据要素", "数据资产", "数据交易", "数据中心"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score theme and industry-chain evidence.")
    parser.add_argument("announcements", help="Path to announcements.json")
    parser.add_argument("--theme-input", default=None, help="Optional JSON with explicit themes and chain evidence.")
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--out", default=None, help="Output path. Defaults to theme_chain.json next to announcements.json.")
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


def confidence_weight(value: str) -> float:
    return {"high": 1.0, "medium": 0.6, "low": 0.3}.get(value.lower(), 0.3)


def announcement_items(announcements: dict[str, Any]) -> list[dict[str, Any]]:
    return announcements.get("announcements", []) if isinstance(announcements.get("announcements"), list) else []


def detect_themes_from_announcements(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    detected: dict[str, dict[str, Any]] = {}
    for item in items:
        title = str(item.get("title") or "")
        summary = str(item.get("summary") or "")
        text = f"{title} {summary}"
        for theme_name, keywords in THEME_KEYWORDS.items():
            if any(keyword.lower() in text.lower() for keyword in keywords):
                theme = detected.setdefault(
                    theme_name,
                    {
                        "name": theme_name,
                        "stage": "unknown",
                        "confidence": "low",
                        "revenue_exposure_pct": None,
                        "profit_transmission": "",
                        "evidence": [],
                        "policy_sources": [],
                        "risks": ["仅从公告标题/摘要识别主题，缺少收入暴露和产业链位置核验。"],
                        "source_type": "announcement_keyword",
                    },
                )
                theme["evidence"].append(
                    {
                        "source": "announcement",
                        "title": title,
                        "publish_time": item.get("publish_time", ""),
                        "source_url": item.get("source_url", ""),
                    }
                )
    return list(detected.values())


def normalize_theme(raw: dict[str, Any]) -> dict[str, Any]:
    evidence = raw.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [{"source": "manual", "title": evidence}]
    risks = raw.get("risks", [])
    if isinstance(risks, str):
        risks = [risks]
    return {
        "name": str(raw.get("name") or raw.get("theme") or "unknown"),
        "stage": str(raw.get("stage") or raw.get("chain_stage") or "unknown"),
        "confidence": str(raw.get("confidence") or "low").lower(),
        "revenue_exposure_pct": num(raw.get("revenue_exposure_pct")),
        "profit_transmission": str(raw.get("profit_transmission") or raw.get("transmission") or ""),
        "evidence": evidence if isinstance(evidence, list) else [],
        "policy_sources": raw.get("policy_sources", []) if isinstance(raw.get("policy_sources", []), list) else [],
        "risks": risks if isinstance(risks, list) else [],
        "source_type": str(raw.get("source_type") or "manual"),
    }


def normalize_chain(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "segment": str(raw.get("segment") or ""),
        "role": str(raw.get("role") or ""),
        "bottleneck": str(raw.get("bottleneck") or ""),
        "beneficiary_logic": str(raw.get("beneficiary_logic") or raw.get("beneficiary") or ""),
        "risk": str(raw.get("risk") or ""),
    }


def score_theme(themes: list[dict[str, Any]], chain: list[dict[str, Any]]) -> tuple[float, float, list[dict[str, Any]], list[str], list[str]]:
    insufficient: list[str] = []
    evidence_text: list[str] = []
    components: list[dict[str, Any]] = []
    if not themes:
        return 0.0, 1.0, components, ["缺少热点/产业链证据，不能进行主题评分。"], ["theme_chain.themes"]

    strongest = max(themes, key=lambda item: confidence_weight(str(item.get("confidence", "low"))) + min(len(item.get("evidence", [])), 5) * 0.1)
    score = 0.5
    risk_score = 3.0

    evidence_count = sum(len(item.get("evidence", [])) for item in themes)
    if evidence_count >= 3:
        score += 1.0
        components.append({"name": "evidence_depth", "score": 1.0, "evidence": f"主题证据 {evidence_count} 条。"})
    elif evidence_count:
        score += 0.5
        components.append({"name": "evidence_depth", "score": 0.5, "evidence": f"主题证据 {evidence_count} 条。"})
    else:
        insufficient.append("theme_evidence")

    confidence = confidence_weight(str(strongest.get("confidence", "low")))
    score += confidence
    components.append({"name": "confidence", "score": round(confidence, 4), "evidence": f"最高置信度主题：{strongest.get('name')}。"})

    exposure_values = [num(item.get("revenue_exposure_pct")) for item in themes if num(item.get("revenue_exposure_pct")) is not None]
    if exposure_values:
        exposure = max(value for value in exposure_values if value is not None)
        if exposure >= 30:
            score += 1.0
            risk_score += 0.3
            components.append({"name": "revenue_exposure", "score": 1.0, "evidence": f"最高收入暴露 {exposure:.2f}%。"})
        elif exposure >= 10:
            score += 0.6
            components.append({"name": "revenue_exposure", "score": 0.6, "evidence": f"最高收入暴露 {exposure:.2f}%。"})
        else:
            score += 0.2
            components.append({"name": "revenue_exposure", "score": 0.2, "evidence": f"收入暴露较低：{exposure:.2f}%。"})
    else:
        insufficient.append("theme_revenue_exposure")
        risk_score -= 0.4

    if chain:
        complete_chain = [item for item in chain if item.get("segment") and item.get("role")]
        if complete_chain:
            score += 0.8
            components.append({"name": "chain_position", "score": 0.8, "evidence": f"已识别产业链位置 {len(complete_chain)} 个。"})
        if any(item.get("bottleneck") for item in chain):
            score += 0.4
            components.append({"name": "bottleneck", "score": 0.4, "evidence": "存在瓶颈/稀缺环节描述。"})
    else:
        insufficient.append("industry_chain")

    if any(item.get("source_type") == "announcement_keyword" for item in themes) and not exposure_values:
        risk_score -= 0.5
        components.append({"name": "hype_risk", "score": -0.5, "evidence": "仅关键词命中且缺少业务暴露，主题炒作风险较高。"})

    for item in themes[:5]:
        evidence_text.append(f"主题 {item.get('name')}：stage={item.get('stage')} confidence={item.get('confidence')}")
    for item in chain[:3]:
        evidence_text.append(f"产业链 {item.get('segment')}：{item.get('role')}")

    return max(0.0, min(5.0, score)), max(0.0, min(5.0, risk_score)), components, evidence_text, sorted(set(insufficient))


def build_theme_chain(args: argparse.Namespace) -> dict[str, Any]:
    announcements_path = Path(args.announcements)
    theme_path = Path(args.theme_input) if args.theme_input else None
    announcements = read_json(announcements_path)
    theme_input = read_json(theme_path)

    manual_themes = [normalize_theme(item) for item in theme_input.get("themes", []) if isinstance(item, dict)]
    detected_themes = detect_themes_from_announcements(announcement_items(announcements))
    themes = manual_themes or detected_themes
    chain = [normalize_chain(item) for item in theme_input.get("industry_chain", []) if isinstance(item, dict)]

    score, risk_score, components, evidence, insufficient = score_theme(themes, chain)
    return {
        "symbol": args.symbol or announcements.get("symbol") or theme_input.get("symbol"),
        "name": args.name or announcements.get("name") or theme_input.get("name"),
        "created_at": datetime.now().isoformat(),
        "sources": {
            "announcements": str(announcements_path),
            "theme_input": str(theme_path) if theme_path else "",
        },
        "themes": themes,
        "industry_chain": chain,
        "scores": {"theme": round(score, 4), "risk": round(risk_score, 4)},
        "components": components,
        "evidence": evidence,
        "insufficient_data": insufficient,
        "verdict": "insufficient_data" if insufficient else "theme_chain_complete",
    }


def main() -> int:
    args = parse_args()
    announcements_path = Path(args.announcements)
    out_path = Path(args.out) if args.out else announcements_path.parent / "theme_chain.json"
    write_json(out_path, build_theme_chain(args))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
