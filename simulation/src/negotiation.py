from __future__ import annotations

from .common import money
from .timing import classify_timing


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
        status = "booked"
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
