#!/usr/bin/env python3
"""Map A-share themes into chain layers, bottlenecks, and research priorities."""

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


LAYER_BLUEPRINTS = {
    "AI算力": [
        {"segment": "AI服务器/整机", "role": "系统集成与需求落点", "bottleneck": "订单兑现、交付节奏、客户集中度", "risk": "整机竞争激烈，毛利率可能被压缩。"},
        {"segment": "算力芯片/加速卡", "role": "核心算力供给", "bottleneck": "先进制程、HBM、封装和软件生态", "risk": "迭代快、研发和客户验证不确定。"},
        {"segment": "互连/光模块/CPO", "role": "集群带宽和延迟约束", "bottleneck": "高速光器件、DSP、良率、客户认证", "risk": "价格竞争和海外客户资本开支波动。"},
        {"segment": "电源/散热/IDC", "role": "功耗密度和运行稳定性约束", "bottleneck": "液冷、供配电、机柜和交付能力", "risk": "项目制收入和回款周期。"},
    ],
    "CPO": [
        {"segment": "高速光模块", "role": "数据中心带宽升级", "bottleneck": "800G/1.6T 良率、客户认证、规模交付", "risk": "技术路线变化和价格下行。"},
        {"segment": "光芯片/激光器", "role": "光模块上游核心器件", "bottleneck": "高端器件供应、封装良率、可靠性验证", "risk": "国产替代节奏和海外供应约束。"},
        {"segment": "硅光/封装测试", "role": "下一代光互连集成", "bottleneck": "工艺平台、测试设备、封装一致性", "risk": "商业化节奏慢于主题热度。"},
    ],
    "半导体": [
        {"segment": "设备平台", "role": "晶圆厂扩产和工艺迁移约束", "bottleneck": "验证周期、反应腔/平台能力、客户重复订单", "risk": "客户扩产放缓或验证周期延长。"},
        {"segment": "关键工艺设备", "role": "刻蚀、薄膜、CMP、清洗等工艺瓶颈", "bottleneck": "高深宽比、先进封装、良率爬坡", "risk": "研发投入转订单速度慢。"},
        {"segment": "材料/耗材", "role": "制程复购型卡点", "bottleneck": "纯度、配方、客户认证和稳定供应", "risk": "二供导入和价格压力。"},
        {"segment": "先进封测", "role": "Chiplet/HBM/高性能封装产能", "bottleneck": "产能、良率、客户验证和资本开支", "risk": "客户集中和毛利率兑现慢。"},
    ],
    "机器人": [
        {"segment": "执行器/关节模组", "role": "人形机器人运动能力约束", "bottleneck": "集成设计、良率、重量和成本", "risk": "量产节奏和客户方案变化。"},
        {"segment": "减速器/丝杠", "role": "精密传动核心零部件", "bottleneck": "加工精度、寿命、规模交付", "risk": "竞争扩产和降价。"},
        {"segment": "传感器/控制器", "role": "感知和控制闭环", "bottleneck": "可靠性、算法适配、客户认证", "risk": "技术路线快速变化。"},
    ],
    "电力设备": [
        {"segment": "变压器/开关设备", "role": "电网和数据中心供配电约束", "bottleneck": "交付周期、认证、产能和铜/硅钢片", "risk": "原材料波动和招标价格压力。"},
        {"segment": "特高压/电网自动化", "role": "大规模电力传输和调度", "bottleneck": "项目核准、招标节奏、技术资质", "risk": "项目延期。"},
        {"segment": "储能/变流器", "role": "新能源消纳和备用电源", "bottleneck": "安全、循环寿命、系统集成", "risk": "价格竞争和应收回款。"},
    ],
    "创新药": [
        {"segment": "核心管线", "role": "临床和商业化价值来源", "bottleneck": "疗效、安全性、适应症竞争格局", "risk": "临床失败或审批延迟。"},
        {"segment": "CDMO/工艺开发", "role": "生产工艺和放大约束", "bottleneck": "客户项目质量、产能利用率、合规体系", "risk": "海外订单和价格压力。"},
        {"segment": "上游耗材/设备", "role": "研发和生产配套", "bottleneck": "质量体系、客户认证、国产替代", "risk": "需求周期和库存调整。"},
    ],
}


FACTOR_WEIGHTS = {
    "demand_inflection": 15,
    "architecture_coupling": 10,
    "bottleneck_severity": 15,
    "supplier_concentration": 12,
    "expansion_difficulty": 12,
    "evidence_quality": 15,
    "valuation_disconnect": 11,
    "catalyst_timing": 10,
}


PENALTY_KEYS = (
    "dilution_financing",
    "governance",
    "geopolitics",
    "liquidity",
    "hype_risk",
    "accounting_quality",
    "cyclicality",
    "alternative_design_risk",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score theme, scarce layers, and industry-chain evidence.")
    parser.add_argument("announcements", help="Path to announcements.json")
    parser.add_argument("--theme-input", default=None, help="Optional JSON with explicit themes, layers, candidates, and evidence.")
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


def clamp(value: float, low: float = 0.0, high: float = 5.0) -> float:
    return max(low, min(high, value))


def confidence_weight(value: str) -> float:
    return {"high": 1.0, "medium": 0.6, "low": 0.3}.get(value.lower(), 0.3)


def announcement_items(announcements: dict[str, Any]) -> list[dict[str, Any]]:
    return announcements.get("announcements", []) if isinstance(announcements.get("announcements"), list) else []


def normalize_evidence(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, str):
        return [{"source": "manual", "claim": raw, "strength": "weak"}]
    if not isinstance(raw, list):
        return []
    evidence: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, str):
            evidence.append({"source": "manual", "claim": item, "strength": "weak"})
        elif isinstance(item, dict):
            evidence.append(
                {
                    "source": str(item.get("source") or item.get("source_type") or ""),
                    "claim": str(item.get("claim") or item.get("title") or item.get("summary") or ""),
                    "strength": str(item.get("strength") or item.get("evidence_strength") or infer_source_strength(item)).lower(),
                    "source_url": str(item.get("source_url") or item.get("url") or ""),
                    "publish_time": str(item.get("publish_time") or item.get("date") or ""),
                }
            )
    return evidence


def infer_source_strength(item: dict[str, Any]) -> str:
    source_text = " ".join(str(item.get(key, "")) for key in ("source", "source_type", "title", "claim", "source_url")).lower()
    strong_terms = ("filing", "exchange", "announcement", "annual", "quarter", "regulator", "contract", "tender", "patent", "standard", "公告", "年报", "季报", "交易所", "问询函", "合同", "招投标", "专利")
    medium_terms = ("media", "trade", "analysis", "ir", "company", "协会", "媒体", "行业", "官网", "调研")
    weak_terms = ("social", "rumor", "kol", "forum", "manual", "keyword", "传闻", "社媒", "论坛")
    if any(term in source_text for term in strong_terms):
        return "strong"
    if any(term in source_text for term in medium_terms):
        return "medium"
    if any(term in source_text for term in weak_terms):
        return "weak"
    return "weak"


def evidence_quality(evidence: list[dict[str, Any]]) -> float:
    if not evidence:
        return 0.0
    values = []
    for item in evidence:
        strength = str(item.get("strength") or infer_source_strength(item)).lower()
        values.append({"strong": 5.0, "primary": 5.0, "medium": 3.0, "analysis": 3.0, "weak": 1.0, "social": 1.0, "rumor": 0.5}.get(strength, 1.0))
    depth_bonus = min(len(evidence), 5) * 0.25
    return clamp(max(values) * 0.7 + (sum(values) / len(values)) * 0.3 + depth_bonus)


def supplier_concentration_score(raw: dict[str, Any]) -> float:
    explicit = num(raw.get("supplier_concentration"))
    if explicit is not None:
        return clamp(explicit)
    supplier_count = num(raw.get("supplier_count"))
    if supplier_count is None:
        return 0.0
    if supplier_count <= 2:
        return 5.0
    if supplier_count <= 5:
        return 4.0
    if supplier_count <= 10:
        return 3.0
    return 1.0


def rating(raw: dict[str, Any], key: str, *aliases: str, default: float = 0.0) -> float:
    factors = raw.get("factors", {}) if isinstance(raw.get("factors"), dict) else {}
    for candidate in (key, *aliases):
        value = num(factors.get(candidate))
        if value is not None:
            return clamp(value)
        value = num(raw.get(candidate))
        if value is not None:
            return clamp(value)
    return clamp(default)


def bottleneck_scorecard(raw: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    has_bottleneck = bool(str(raw.get("bottleneck") or raw.get("scarce_layer") or "").strip())
    qualification_months = num(raw.get("qualification_months"))
    default_expansion = 3.0 if qualification_months is not None and qualification_months >= 12 else 0.0
    default_catalyst = 2.0 if raw.get("near_term_catalyst") or raw.get("catalyst") else 0.0

    factors = {
        "demand_inflection": rating(raw, "demand_inflection", "demand_pressure", default=2.0 if evidence else 0.0),
        "architecture_coupling": rating(raw, "architecture_coupling", "system_coupling", default=2.0 if raw.get("role") else 0.0),
        "bottleneck_severity": rating(raw, "bottleneck_severity", "chokepoint_severity", "scarcity", default=3.0 if has_bottleneck else 0.0),
        "supplier_concentration": supplier_concentration_score(raw),
        "expansion_difficulty": rating(raw, "expansion_difficulty", "capacity_difficulty", default=default_expansion),
        "evidence_quality": rating(raw, "evidence_quality", default=evidence_quality(evidence)),
        "valuation_disconnect": rating(raw, "valuation_disconnect", "valuation_gap", default=0.0),
        "catalyst_timing": rating(raw, "catalyst_timing", "timing", default=default_catalyst),
    }

    raw_penalties = raw.get("penalties", {}) if isinstance(raw.get("penalties"), dict) else {}
    penalties = {key: clamp(num(raw_penalties.get(key)) or num(raw.get(key)) or 0.0) for key in PENALTY_KEYS}
    if raw.get("source_type") == "announcement_keyword" and factors["evidence_quality"] < 3:
        penalties["hype_risk"] = max(penalties["hype_risk"], 3.0)

    factor_details = {}
    raw_points = 0.0
    for key, weight in FACTOR_WEIGHTS.items():
        points = factors[key] / 5 * weight
        raw_points += points
        factor_details[key] = {"rating": round(factors[key], 4), "weight": weight, "points": round(points, 4)}

    penalty_details = {}
    penalty_points = 0.0
    for key, value in penalties.items():
        points = value * 2.0
        penalty_points += points
        penalty_details[key] = {"rating": round(value, 4), "points": round(points, 4)}

    final_score = max(0.0, min(100.0, raw_points - penalty_points))
    if final_score >= 85:
        verdict = "top_research_priority"
    elif final_score >= 70:
        verdict = "high_research_priority"
    elif final_score >= 55:
        verdict = "worth_tracking"
    else:
        verdict = "early_lead_or_low_priority"

    return {
        "raw_factor_points": round(raw_points, 4),
        "penalty_points": round(penalty_points, 4),
        "final_score": round(final_score, 4),
        "verdict": verdict,
        "factor_details": factor_details,
        "penalty_details": penalty_details,
    }


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
                        "claim": title,
                        "strength": "strong" if item.get("source_url") else "medium",
                        "publish_time": item.get("publish_time", ""),
                        "source_url": item.get("source_url", ""),
                    }
                )
    return list(detected.values())


def normalize_theme(raw: dict[str, Any]) -> dict[str, Any]:
    evidence = normalize_evidence(raw.get("evidence", []))
    risks = raw.get("risks", [])
    if isinstance(risks, str):
        risks = [risks]
    return {
        "name": str(raw.get("name") or raw.get("theme") or "unknown"),
        "stage": str(raw.get("stage") or raw.get("chain_stage") or "unknown"),
        "confidence": str(raw.get("confidence") or "low").lower(),
        "revenue_exposure_pct": num(raw.get("revenue_exposure_pct")),
        "profit_transmission": str(raw.get("profit_transmission") or raw.get("transmission") or ""),
        "evidence": evidence,
        "policy_sources": raw.get("policy_sources", []) if isinstance(raw.get("policy_sources", []), list) else [],
        "risks": risks if isinstance(risks, list) else [],
        "source_type": str(raw.get("source_type") or "manual"),
    }


def blueprint_layers(themes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for theme in themes:
        for layer in LAYER_BLUEPRINTS.get(str(theme.get("name")), []):
            key = str(layer.get("segment"))
            if key in seen:
                continue
            seen.add(key)
            layers.append({**layer, "source_type": "method_blueprint", "evidence": [], "factors": {"architecture_coupling": 2, "bottleneck_severity": 2}})
    return layers


def normalize_chain(raw: dict[str, Any]) -> dict[str, Any]:
    evidence = normalize_evidence(raw.get("evidence", []))
    item = {
        "segment": str(raw.get("segment") or raw.get("layer") or raw.get("name") or ""),
        "role": str(raw.get("role") or raw.get("chain_role") or ""),
        "bottleneck": str(raw.get("bottleneck") or raw.get("scarce_layer") or raw.get("constraint") or ""),
        "beneficiary_logic": str(raw.get("beneficiary_logic") or raw.get("beneficiary") or raw.get("logic") or ""),
        "risk": str(raw.get("risk") or ""),
        "demand_driver": str(raw.get("demand_driver") or raw.get("system_change") or ""),
        "supplier_count": num(raw.get("supplier_count")),
        "qualification_months": num(raw.get("qualification_months")),
        "evidence": evidence,
        "source_type": str(raw.get("source_type") or "manual"),
        "next_checks": raw.get("next_checks", []) if isinstance(raw.get("next_checks", []), list) else [],
    }
    item["scorecard"] = bottleneck_scorecard({**raw, **item}, evidence)
    return item


def normalize_candidate(raw: dict[str, Any]) -> dict[str, Any]:
    evidence = normalize_evidence(raw.get("evidence", []))
    risks = raw.get("risks", raw.get("risk", []))
    if isinstance(risks, str):
        risks = [risks]
    candidate = {
        "symbol": str(raw.get("symbol") or raw.get("ticker") or ""),
        "name": str(raw.get("name") or raw.get("company") or ""),
        "market": str(raw.get("market") or "A-share"),
        "layer": str(raw.get("layer") or raw.get("segment") or ""),
        "chain_position": str(raw.get("chain_position") or raw.get("position") or ""),
        "relation": str(raw.get("relation") or raw.get("role") or ""),
        "what_it_constrains": str(raw.get("what_it_constrains") or raw.get("bottleneck") or ""),
        "evidence": evidence,
        "risks": risks if isinstance(risks, list) else [],
        "next_checks": raw.get("next_checks", []) if isinstance(raw.get("next_checks", []), list) else [],
        "fund_direction": str(raw.get("fund_direction") or ""),
    }
    candidate["scorecard"] = bottleneck_scorecard({**raw, **candidate}, evidence)
    return candidate


def layer_ranking(chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(chain, key=lambda item: item.get("scorecard", {}).get("final_score", 0), reverse=True)
    return [
        {
            "rank": index + 1,
            "segment": item.get("segment", ""),
            "role": item.get("role", ""),
            "bottleneck": item.get("bottleneck", ""),
            "final_score": item.get("scorecard", {}).get("final_score", 0),
            "verdict": item.get("scorecard", {}).get("verdict", ""),
            "main_risk": item.get("risk", ""),
        }
        for index, item in enumerate(ranked)
    ]


def priority_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda item: item.get("scorecard", {}).get("final_score", 0), reverse=True)
    return [
        {
            "rank": index + 1,
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "market": item.get("market", ""),
            "layer": item.get("layer", ""),
            "what_it_constrains": item.get("what_it_constrains", ""),
            "final_score": item.get("scorecard", {}).get("final_score", 0),
            "verdict": item.get("scorecard", {}).get("verdict", ""),
            "main_risk": "; ".join(str(risk) for risk in item.get("risks", [])[:2]),
        }
        for index, item in enumerate(ranked)
    ]


def default_next_checks(themes: list[dict[str, Any]], ranked_layers: list[dict[str, Any]]) -> list[str]:
    if not themes:
        return ["先确认主题是否真实进入公司业务和公告口径。"]
    top_theme = themes[0].get("name", "主题")
    checks = [
        f"核验 {top_theme} 对应业务在年报/半年报/季报中的收入、毛利率和订单变化。",
        "检查公告、问询函、互动易/上证 e 互动中的客户认证、订单、产能和项目进度。",
        "交叉验证应收、存货、合同负债和经营现金流，避免只看到主题叙事。",
    ]
    if ranked_layers:
        checks.insert(0, f"优先核验排名第一的产业链层级：{ranked_layers[0].get('segment')}。")
    return checks


def score_theme(
    themes: list[dict[str, Any]],
    chain: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    ranked_layers: list[dict[str, Any]],
) -> tuple[float, float, list[dict[str, Any]], list[str], list[str]]:
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
        components.append({"name": "theme_evidence_depth", "score": 1.0, "evidence": f"主题证据 {evidence_count} 条。"})
    elif evidence_count:
        score += 0.5
        components.append({"name": "theme_evidence_depth", "score": 0.5, "evidence": f"主题证据 {evidence_count} 条。"})
    else:
        insufficient.append("theme_evidence")

    confidence = confidence_weight(str(strongest.get("confidence", "low")))
    score += confidence
    components.append({"name": "theme_confidence", "score": round(confidence, 4), "evidence": f"最高置信度主题：{strongest.get('name')}。"})

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
            score += 0.6
            components.append({"name": "chain_position", "score": 0.6, "evidence": f"已识别产业链位置 {len(complete_chain)} 个。"})
        top_layer_score = ranked_layers[0]["final_score"] if ranked_layers else 0
        if top_layer_score >= 70:
            score += 1.1
            risk_score += 0.4
            components.append({"name": "scarce_layer_score", "score": 1.1, "evidence": f"最高瓶颈层级得分 {top_layer_score:.2f}/100。"})
        elif top_layer_score >= 55:
            score += 0.7
            components.append({"name": "scarce_layer_score", "score": 0.7, "evidence": f"最高瓶颈层级得分 {top_layer_score:.2f}/100。"})
        else:
            score += 0.2
            insufficient.append("scarce_layer_evidence")
    else:
        insufficient.append("industry_chain")

    if candidates:
        score += 0.4 if len(candidates) < 3 else 0.7
        components.append({"name": "candidate_universe", "score": 0.4 if len(candidates) < 3 else 0.7, "evidence": f"候选研究对象 {len(candidates)} 个。"})
    else:
        insufficient.append("candidate_universe")

    if any(item.get("source_type") == "announcement_keyword" for item in themes) and not exposure_values:
        risk_score -= 0.5
        components.append({"name": "hype_risk", "score": -0.5, "evidence": "仅关键词命中且缺少业务暴露，主题炒作风险较高。"})

    if ranked_layers:
        layer_names = "、".join(item["segment"] for item in ranked_layers[:3] if item.get("segment"))
        evidence_text.append(f"先排产业链层级：{layer_names}。")
    for item in themes[:5]:
        evidence_text.append(f"主题 {item.get('name')}：stage={item.get('stage')} confidence={item.get('confidence')}")
    for item in ranked_layers[:3]:
        evidence_text.append(f"瓶颈层级 {item.get('segment')}：score={item.get('final_score')} verdict={item.get('verdict')}")

    return max(0.0, min(5.0, score)), max(0.0, min(5.0, risk_score)), components, evidence_text, sorted(set(insufficient))


def build_theme_chain(args: argparse.Namespace) -> dict[str, Any]:
    announcements_path = Path(args.announcements)
    theme_path = Path(args.theme_input) if args.theme_input else None
    announcements = read_json(announcements_path)
    theme_input = read_json(theme_path)

    manual_themes = [normalize_theme(item) for item in theme_input.get("themes", []) if isinstance(item, dict)]
    detected_themes = detect_themes_from_announcements(announcement_items(announcements))
    themes = manual_themes or detected_themes

    raw_layers = []
    for key in ("industry_chain", "layers", "chain_layers"):
        raw = theme_input.get(key, [])
        if isinstance(raw, list):
            raw_layers.extend(item for item in raw if isinstance(item, dict))
    if not raw_layers and themes:
        raw_layers = blueprint_layers(themes)
    chain = [normalize_chain(item) for item in raw_layers]

    raw_candidates = []
    for key in ("candidates", "stocks", "companies"):
        raw = theme_input.get(key, [])
        if isinstance(raw, list):
            raw_candidates.extend(item for item in raw if isinstance(item, dict))
    candidates = [normalize_candidate(item) for item in raw_candidates]

    ranked_layers = layer_ranking(chain)
    priorities = priority_candidates(candidates)
    score, risk_score, components, evidence, insufficient = score_theme(themes, chain, candidates, ranked_layers)
    next_checks = theme_input.get("next_checks") if isinstance(theme_input.get("next_checks"), list) else default_next_checks(themes, ranked_layers)

    return {
        "symbol": args.symbol or announcements.get("symbol") or theme_input.get("symbol"),
        "name": args.name or announcements.get("name") or theme_input.get("name"),
        "created_at": datetime.now().isoformat(),
        "methodology": "layer_first_supply_chain_bottleneck_research",
        "sources": {
            "announcements": str(announcements_path),
            "theme_input": str(theme_path) if theme_path else "",
        },
        "system_change": str(theme_input.get("system_change") or ""),
        "themes": themes,
        "industry_chain": chain,
        "layer_ranking": ranked_layers,
        "candidate_universe": candidates,
        "priority_research_list": priorities,
        "fund_directions": theme_input.get("fund_directions", []) if isinstance(theme_input.get("fund_directions", []), list) else [],
        "lower_priority_popular_areas": theme_input.get("lower_priority_popular_areas", []) if isinstance(theme_input.get("lower_priority_popular_areas", []), list) else [],
        "next_checks": next_checks,
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
