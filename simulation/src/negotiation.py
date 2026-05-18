from __future__ import annotations

from .common import money
from .statuses import BOOKED, BOOKED_WITH_MARKET_HEALTH_WARNING
from .timing import classify_timing


BUDGET_DRIVEN_COMMODITY_WARNING = "budget-driven commodity booking risk"
MARKET_HEALTH_RISK_FLAGS = {"price_led_recommendation_risk", "race_to_bottom_risk"}


def client_capacity(project: dict) -> int:
    budget = float(project["budget"])
    budget_type = project["budget_type"]

    if budget_type == "firm":
        multiplier = 1.04
    elif budget_type == "flexible":
        multiplier = 1.0 + float(project["client_flexibility"])
    elif budget_type == "exploratory":
        multiplier = 1.08
    elif budget_type == "prestige":
        multiplier = 1.02
    else:
        multiplier = 1.0

    return money(budget * multiplier)


def simulate_availability_check(project: dict, talent: dict, rec: dict) -> dict:
    quote = int(rec["final_quote"])
    committed_quote = quote
    events: list[str] = []
    warnings: list[str] = []

    if talent["negotiation_behavior"] == "opportunistic_late_repricer" and rec["creative_fit"] >= 0.75:
        committed_quote = money(quote * 1.2)
        status = "countered_before_client_presentation"
        events.append("talent countered during rate-quoted outreach before client presentation")
        warnings.append("pre-presentation counter increased locked quote")
    elif talent["negotiation_behavior"] == "scope_sensitive_repricer" and project["usage_scope"] in {"national", "campaign"}:
        status = "accepted_after_scope_confirmation"
        events.append("talent requested usage confirmation before quote commitment")
    elif talent["negotiation_behavior"] == "principled_premium" and quote > project["budget"]:
        status = "accepted_at_presented_rate"
        events.append("talent accepted premium rate and offered scope tradeoffs before presentation")
    else:
        status = "accepted_at_presented_rate"
        events.append("talent accepted rate-quoted outreach before presentation")

    return {
        "talent_id": talent["id"],
        "status": status,
        "outreachChannel": "whatsapp_or_email",
        "rateSource": "pricing_engine_project_rate",
        "ratePresentedDuringOutreach": True,
        "talentVisibleRate": True,
        "proposedQuote": quote,
        "proposedRange": rec.get("expected_booking_range"),
        "committedQuote": committed_quote,
        "completedBeforeClientPresentation": True,
        "clientVisible": False,
        "events": events,
        "warnings": warnings,
    }


def apply_availability_commitment(rec: dict, availability_check: dict) -> dict:
    adjusted = dict(rec)
    adjusted["availability_check"] = availability_check
    adjusted["final_quote"] = int(availability_check["committedQuote"])
    if availability_check["status"] == "countered_before_client_presentation":
        adjusted["acceptance_probability"] = round(
            max(float(adjusted["acceptance_probability"]) - 0.08, 0.0),
            3,
        )
    return adjusted


def simulate_client_decision(project: dict, talent: dict, rec: dict) -> dict:
    quote = int(rec["final_quote"])
    capacity = client_capacity(project)
    events: list[str] = ["client evaluated locked presentation quote"]
    warnings: list[str] = []

    if classify_timing(int(project["lead_time_days"])) == "long_horizon" and project["project_commitment_confidence"] < 0.8:
        return {
            "talent_id": talent["id"],
            "status": "pending_hold",
            "locked_quote": quote,
            "client_capacity": capacity,
            "events": events + ["long-horizon project needs confirmation window"],
            "warnings": warnings + ["long-horizon commitment uncertainty"],
        }

    if quote <= capacity and rec["acceptance_probability"] >= 0.48:
        status = BOOKED
    elif quote <= capacity:
        status = "tentative"
        warnings.append("low acceptance confidence despite workable budget")
    else:
        status = "failed_budget_gap"
        warnings.append("final quote exceeded client capacity")

    return {
        "talent_id": talent["id"],
        "status": status,
        "locked_quote": quote,
        "client_capacity": capacity,
        "events": events,
        "warnings": warnings,
    }


def _candidate_strength(candidate: dict) -> float:
    return float(candidate.get("overall_score", 0.0))


def _risk_flags(candidate: dict) -> set[str]:
    return set(candidate.get("market_health_flags", [])) & MARKET_HEALTH_RISK_FLAGS


def apply_budget_health_review(project: dict, candidates: list[dict], decisions: list[dict]) -> list[dict]:
    """Flag bookings where client budget reality makes the low-price risk path win."""
    if not decisions:
        return decisions

    candidate_by_id = {candidate["talent_id"]: candidate for candidate in candidates}
    reviewed: list[dict] = []

    for decision in decisions:
        if decision["status"] != BOOKED:
            reviewed.append(decision)
            continue

        booked_candidate = candidate_by_id[decision["talent_id"]]
        risk_flags = _risk_flags(booked_candidate)
        if not risk_flags:
            reviewed.append(decision)
            continue

        booked_strength = _candidate_strength(booked_candidate)
        stronger_failed_options = [
            other["talent_id"]
            for other, other_decision in zip(candidates, decisions)
            if other["talent_id"] != booked_candidate["talent_id"]
            and other_decision["status"] == "failed_budget_gap"
            and _candidate_strength(other) > booked_strength
        ]
        if not stronger_failed_options:
            reviewed.append(decision)
            continue

        reviewed_decision = dict(decision)
        reviewed_decision["status"] = BOOKED_WITH_MARKET_HEALTH_WARNING
        reviewed_decision["events"] = list(decision["events"]) + [
            "market-health review: lower-price risk option booked after stronger options exceeded client capacity"
        ]
        reviewed_decision["warnings"] = sorted(
            set(decision["warnings"] + [BUDGET_DRIVEN_COMMODITY_WARNING])
        )
        reviewed_decision["market_health_review"] = {
            "reason": "A market-health risk candidate booked after stronger options failed client capacity.",
            "riskFlags": sorted(risk_flags),
            "strongerFailedTalentIds": stronger_failed_options,
            "clientBudgetType": project["budget_type"],
        }
        reviewed.append(reviewed_decision)

    return reviewed
