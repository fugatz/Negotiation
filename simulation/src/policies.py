from __future__ import annotations

from .common import clamp, money, weighted_average


def apply_nudges(score: dict, talent: dict, timing: dict, talent_behavior: dict, client_behavior: dict) -> dict:
    behavior_delta = clamp(
        float(talent_behavior["rate_delta"]) + float(client_behavior["rate_delta"]),
        -0.075,
        0.075,
    )
    timing_delta = clamp(float(timing["rate_delta"]), -0.02, 0.08)
    total_delta = timing_delta + behavior_delta

    quote = money(float(score["base_quote"]) * (1.0 + total_delta))
    quote = max(quote, int(talent["working_floor"]))

    confidence = clamp(
        float(score["acceptance_probability"])
        + float(timing["confidence_delta"])
        + float(talent_behavior["confidence_delta"])
        + float(client_behavior["confidence_delta"])
    )

    adjusted = dict(score)
    adjusted.update(
        {
            "final_quote": quote,
            "rate_delta": round(total_delta, 3),
            "timing_nudge": timing,
            "talent_behavior_nudge": talent_behavior,
            "client_behavior_nudge": client_behavior,
            "acceptance_probability": round(confidence, 3),
        }
    )
    return adjusted


def overall_score(rec: dict) -> float:
    return weighted_average(
        [
            (float(rec["creative_fit"]), 0.3),
            (float(rec["practical_fit"]), 0.18),
            (float(rec["price_fit"]), 0.2),
            (float(rec["trust_score"]), 0.14),
            (float(rec["market_health_score"]), 0.08),
            (float(rec["acceptance_probability"]), 0.1),
        ]
    )


def recommendation_lane(rec: dict, talent: dict, project: dict, index: int) -> str:
    if index == 0 and rec["creative_fit"] >= 0.62:
        return "Best Fit"
    if rec["creative_fit"] >= 0.86:
        return "Strong Specialist"
    if rec["price_fit"] >= 0.86 and rec["practical_fit"] >= 0.78:
        return "Budget-Confident"
    if rec["creative_fit"] >= 0.78 and rec["price_fit"] < 0.68 and project["budget_type"] in {"flexible", "exploratory"}:
        return "Premium Stretch"
    if talent["target_rate"] <= 8000 and rec["creative_fit"] >= 0.58:
        return "Emerging Value"
    if project["lead_time_days"] < 14 and rec["practical_fit"] >= 0.82:
        return "Fastest Viable Path"
    return "Viable Option"


def client_visible_price_state(rec: dict, project: dict) -> str:
    budget = float(project["budget"])
    quote = float(rec["final_quote"])

    if quote <= budget:
        return "within expected range"
    if quote <= budget * 1.12:
        return "likely workable with scoped flexibility"
    if quote <= budget * 1.3:
        return "premium stretch"
    return "outside stated budget"


def build_slate(recommendations: list[dict], talent_by_id: dict, project: dict, limit: int = 4) -> list[dict]:
    eligible = [rec for rec in recommendations if rec["eligible"]]
    ordered = sorted(eligible, key=overall_score, reverse=True)
    slate: list[dict] = []

    for index, rec in enumerate(ordered[:limit]):
        talent = talent_by_id[rec["talent_id"]]
        item = dict(rec)
        item["overall_score"] = round(overall_score(rec), 3)
        item["lane"] = recommendation_lane(rec, talent, project, index)
        item["client_visible_price_state"] = client_visible_price_state(rec, project)
        slate.append(item)

    return slate
