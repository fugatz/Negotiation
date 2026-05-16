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


def simulate_negotiation(project: dict, talent: dict, rec: dict) -> dict:
    quote = int(rec["final_quote"])
    capacity = client_capacity(project)
    events: list[str] = []
    warnings: list[str] = []

    final_quote = quote
    if talent["negotiation_behavior"] == "opportunistic_late_repricer" and rec["creative_fit"] >= 0.75:
        final_quote = money(quote * 1.2)
        events.append("talent attempted a 20% post-interest increase")
        warnings.append("unexplained post-interest repricing")
    elif talent["negotiation_behavior"] == "scope_sensitive_repricer" and project["usage_scope"] in {"national", "campaign"}:
        events.append("talent requested usage confirmation before holding quote")
    elif talent["negotiation_behavior"] == "principled_premium" and quote > project["budget"]:
        events.append("talent held premium rate and offered scope tradeoffs")
    else:
        events.append("quote stayed inside expected band")

    if classify_timing(int(project["lead_time_days"])) == "long_horizon" and project["project_commitment_confidence"] < 0.8:
        return {
            "talent_id": talent["id"],
            "status": "pending_hold",
            "final_quote": final_quote,
            "client_capacity": capacity,
            "events": events + ["long-horizon project needs confirmation window"],
            "warnings": warnings + ["long-horizon commitment uncertainty"],
        }

    if final_quote <= capacity and rec["acceptance_probability"] >= 0.48:
        status = "booked"
    elif final_quote <= capacity:
        status = "tentative"
        warnings.append("low acceptance confidence despite workable budget")
    else:
        status = "failed_budget_gap"
        warnings.append("final quote exceeded client capacity")

    return {
        "talent_id": talent["id"],
        "status": status,
        "final_quote": final_quote,
        "client_capacity": capacity,
        "events": events,
        "warnings": warnings,
    }
