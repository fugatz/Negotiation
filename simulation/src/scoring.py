from __future__ import annotations

from .common import clamp, rate_amount, weighted_average
from .market_cost import actor_agreement_floor


def talent_class(talent: dict) -> str:
    if talent.get("talent_class"):
        return talent["talent_class"]
    if talent.get("talent_kind") == "actor":
        return "actor"
    return "production_talent"


def hard_eligible(talent: dict, project: dict) -> tuple[bool, list[str]]:
    """Small simulation stub for known constraints before rate-quoted outreach."""
    reasons: list[str] = []
    lead_time = int(project["lead_time_days"])
    talent_scope = project.get("talent_class_scope", "production_talent")

    if talent_scope != "mixed" and talent_class(talent) != talent_scope:
        reasons.append("outside upstream matched talent class")

    actor_role_scope = project.get("actor_role_scope")
    if (
        actor_role_scope
        and actor_role_scope not in {"any", "mixed"}
        and talent_class(talent) == "actor"
        and talent.get("actor_role") != actor_role_scope
    ):
        reasons.append("outside actor role scope")

    local_talent_market = project.get("local_talent_market")
    if local_talent_market and talent_class(talent) == "actor" and talent.get("home_market") != local_talent_market:
        reasons.append("outside local talent market")

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


def legal_floor_state(talent: dict, project: dict) -> dict:
    private_floor = int(talent["working_floor"])
    local_minimum_wage = project.get("local_minimum_wage_hourly")
    estimated_hours = project.get("estimated_work_hours")
    agreement_floor = actor_agreement_floor(project) if talent_class(talent) == "actor" else None
    minimum_wage_floor = None
    minimum_wage_status = "not_applicable"
    warnings: list[str] = []

    if talent_class(talent) == "actor":
        if local_minimum_wage is None or estimated_hours is None:
            if agreement_floor:
                minimum_wage_status = "not_supplied_rate_card_available"
            else:
                minimum_wage_status = "unknown"
                warnings.append("minimum_wage_floor_unknown")
        else:
            minimum_wage_floor = int(round(float(local_minimum_wage) * float(estimated_hours)))
            minimum_wage_status = "known"

    floor_priority = {
        "private_working_floor": 1,
        "published_actor_rate_card": 2,
        "local_minimum_wage": 3,
    }
    floor_candidates = [("private_working_floor", private_floor)]
    if agreement_floor:
        floor_candidates.append(("published_actor_rate_card", int(agreement_floor["amount"])))
    if minimum_wage_floor:
        floor_candidates.append(("local_minimum_wage", minimum_wage_floor))

    basis, effective_floor = max(
        floor_candidates,
        key=lambda item: (item[1], floor_priority[item[0]]),
    )

    return {
        "talentClass": talent_class(talent),
        "basis": basis,
        "privateWorkingFloor": private_floor,
        "localMinimumWageHourly": local_minimum_wage,
        "localMinimumWageSource": project.get("local_minimum_wage_source"),
        "estimatedWorkHours": estimated_hours,
        "minimumWageFloor": minimum_wage_floor,
        "minimumWageStatus": minimum_wage_status,
        "agreementFloor": agreement_floor["amount"] if agreement_floor else None,
        "agreementFloorExactAmount": agreement_floor["exactAmount"] if agreement_floor else None,
        "agreementFloorCurrency": agreement_floor["currency"] if agreement_floor else None,
        "agreementFloorSource": agreement_floor["source"] if agreement_floor else None,
        "agreementFloorSourceUrl": agreement_floor["sourceUrl"] if agreement_floor else None,
        "agreementFloorStatus": "known" if agreement_floor else "not_applicable",
        "effectiveFloor": effective_floor,
        "warnings": warnings,
    }


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

    floor = legal_floor_state(talent, project)
    return max(rate_amount(quote), int(floor["effectiveFloor"]))


def price_fit(talent: dict, project: dict, quote: int, floor: dict) -> float:
    budget = float(project["budget"])
    effective_floor = float(floor["effectiveFloor"])

    if budget >= quote:
        return 0.95
    if budget >= quote * 0.85:
        return 0.78
    if budget >= effective_floor:
        return clamp(0.42 + ((budget - effective_floor) / max(quote - effective_floor, 1.0)) * 0.28)
    if project["budget_type"] == "prestige" and talent["prestige_opt_in"]:
        return 0.36
    return 0.14


def market_health(talent: dict, project: dict, fit: float, pricing: float) -> dict:
    flags: list[str] = []
    score = 0.68

    if fit >= 0.82 and talent["target_rate"] > project["budget"] * 0.75:
        score += 0.12
        flags.append("specialist_value_protected")

    if talent["negotiation_behavior"] == "lowball_accepter" and pricing >= 0.86:
        if fit < 0.75:
            score -= 0.16
            flags.append("race_to_bottom_risk")
        elif fit < 0.82:
            score -= 0.08
            flags.append("price_led_recommendation_risk")

    if talent["utilization_state"] == "idle" and fit >= 0.65:
        score += 0.03
        flags.append("idle_access_without_discounting")

    return {
        "score": round(clamp(score), 3),
        "flags": flags,
    }


def score_talent(talent: dict, project: dict) -> dict:
    eligible, eligibility_reasons = hard_eligible(talent, project)
    creative = creative_fit(talent, project)
    practical = practical_fit(talent, project)
    floor = legal_floor_state(talent, project)
    quote = base_quote(talent, project, creative)
    pricing = price_fit(talent, project, quote, floor)
    trust = trust_score(talent)
    market = market_health(talent, project, creative, pricing)
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
        "market_health_score": market["score"],
        "market_health_flags": market["flags"],
        "legal_floor": floor,
        "base_quote": quote,
        "acceptance_probability": round(clamp(acceptance), 3),
    }
