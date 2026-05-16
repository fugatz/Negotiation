from __future__ import annotations

from .common import clamp, money, weighted_average


def hard_eligible(talent: dict, project: dict) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    lead_time = int(project["lead_time_days"])

    if lead_time < int(talent["minimum_notice_days"]):
        reasons.append("below talent minimum notice window")

    if project["budget_type"] == "prestige" and not talent["prestige_opt_in"]:
        reasons.append("not opted into prestige/low-cash tradeoffs")

    return len(reasons) == 0, reasons


def category_fit(talent: dict, project: dict) -> float:
    category = project["category"]
    subcategory = project.get("subcategory", category)
    category_score = float(talent["categories"].get(category, 0.0))
    subcategory_score = float(talent["categories"].get(subcategory, category_score))
    return weighted_average([(category_score, 0.65), (subcategory_score, 0.35)])


def creative_fit(talent: dict, project: dict) -> float:
    base = category_fit(talent, project)
    specificity = float(project["creative_specificity"])
    specificity_bonus = 0.08 * specificity if base >= 0.75 else 0.02 * specificity
    return clamp(base + specificity_bonus)


def practical_fit(talent: dict, project: dict) -> float:
    lead_time = int(project["lead_time_days"])
    notice_fit = 1.0 if lead_time >= int(talent["minimum_notice_days"]) else 0.35
    return weighted_average(
        [
            (float(talent["availability_score"]), 0.32),
            (float(talent["responsiveness"]), 0.22),
            (float(talent["reliability_score"]), 0.26),
            (notice_fit, 0.2),
        ]
    )


def trust_score(talent: dict) -> float:
    reprice_penalty = min(float(talent["late_reprice_count"]) * 0.08, 0.32)
    cancel_penalty = min(float(talent["cancellation_count"]) * 0.05, 0.15)
    score = weighted_average(
        [
            (float(talent["reliability_score"]), 0.4),
            (float(talent["quote_stability"]), 0.35),
            (float(talent["responsiveness"]), 0.25),
        ]
    )
    return clamp(score - reprice_penalty - cancel_penalty)


def base_quote(talent: dict, project: dict, fit: float) -> int:
    category = project["category"]
    premium = float(talent.get("category_premiums", {}).get(category, 0.0))
    scarcity_premium = float(talent["scarcity"]) * float(project["schedule_urgency"]) * 0.04
    usage_premium = 0.08 if project["usage_scope"] in {"national", "campaign"} else 0.0
    exclusivity_premium = 0.05 if project.get("requires_exclusivity") else 0.0

    quote = float(talent["target_rate"]) * (1.0 + (premium * fit) + scarcity_premium + usage_premium + exclusivity_premium)

    if project["budget_type"] == "prestige" and talent["prestige_opt_in"]:
        prestige_discount = min(float(project["prestige_value"]) * 0.12, 0.1)
        quote *= 1.0 - prestige_discount

    return money(max(quote, float(talent["working_floor"])))


def price_fit(talent: dict, project: dict, quote: int) -> float:
    budget = float(project["budget"])
    floor = float(talent["working_floor"])

    if budget >= quote:
        return 0.95
    if budget >= quote * 0.85:
        return 0.78
    if budget >= floor:
        return clamp(0.42 + ((budget - floor) / max(quote - floor, 1.0)) * 0.28)
    if project["budget_type"] == "prestige" and talent["prestige_opt_in"]:
        return 0.36
    return 0.14


def market_health_score(talent: dict, project: dict, fit: float) -> float:
    specialist_bonus = 0.12 if fit >= 0.82 and talent["target_rate"] > project["budget"] * 0.75 else 0.0
    lowball_penalty = 0.08 if talent["negotiation_behavior"] == "lowball_accepter" and fit < 0.65 else 0.0
    idle_access_bonus = 0.03 if talent["utilization_state"] == "idle" and fit >= 0.65 else 0.0
    return clamp(0.68 + specialist_bonus + idle_access_bonus - lowball_penalty)


def score_talent(talent: dict, project: dict) -> dict:
    eligible, eligibility_reasons = hard_eligible(talent, project)
    creative = creative_fit(talent, project)
    practical = practical_fit(talent, project)
    quote = base_quote(talent, project, creative)
    pricing = price_fit(talent, project, quote)
    trust = trust_score(talent)
    market = market_health_score(talent, project, creative)
    acceptance = weighted_average(
        [
            (creative, 0.28),
            (practical, 0.22),
            (pricing, 0.28),
            (trust, 0.14),
            (float(project["booking_intent_strength"]), 0.08),
        ]
    )

    if not eligible:
        acceptance *= 0.25

    return {
        "talent_id": talent["id"],
        "eligible": eligible,
        "eligibility_reasons": eligibility_reasons,
        "creative_fit": round(creative, 3),
        "practical_fit": round(practical, 3),
        "price_fit": round(pricing, 3),
        "trust_score": round(trust, 3),
        "market_health_score": round(market, 3),
        "base_quote": quote,
        "acceptance_probability": round(clamp(acceptance), 3),
    }
