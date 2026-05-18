from __future__ import annotations

from .common import money
from .scoring import talent_class


def infer_project_size_band(all_in_budget: int | float) -> str:
    amount = float(all_in_budget)
    if amount < 25000:
        return "low_cash"
    if amount <= 50000:
        return "small"
    if amount <= 100000:
        return "mid"
    if amount <= 250000:
        return "premium"
    return "major"


def project_context(project: dict) -> dict:
    all_in_budget = int(project.get("all_in_budget", project["budget"]))
    return {
        "allInBudget": all_in_budget,
        "projectSizeBand": project.get("project_size_band", infer_project_size_band(all_in_budget)),
        "projectType": project.get("project_type", project["usage_scope"]),
        "talentClassScope": project.get("talent_class_scope", "production_talent"),
    }


def pricing_assumptions(project: dict) -> list[str]:
    explicit = project.get("pricing_assumptions")
    if explicit:
        return list(explicit)

    assumptions = [
        f"{project['usage_scope']} usage assumed",
        "standard production scope assumed",
        "travel excluded unless listed",
    ]
    if project.get("requires_exclusivity"):
        assumptions.append("exclusivity included in current scope")
    else:
        assumptions.append("no exclusivity assumed")
    return assumptions


def actualization_triggers(project: dict, talent: dict) -> list[str]:
    triggers = ["scope materially changes after quote lock"]
    if talent_class(talent) == "actor":
        triggers.extend(
            [
                "fitting added",
                "shoot day added",
                "overtime triggered",
                "usage expanded",
                "paid media added",
                "exclusivity added",
                "union or legal requirement changes",
            ]
        )
    else:
        triggers.extend(
            [
                "prep day added",
                "shoot day added",
                "travel required",
                "overtime triggered",
                "usage expanded",
                "additional revision round requested",
                "turnaround compressed",
            ]
        )

    if project.get("expected_actualization_events"):
        triggers.extend(project["expected_actualization_events"])

    return sorted(set(triggers))


def _range_amount(value: float) -> int:
    if value < 1000:
        return int(round(value))
    return money(value)


def _range_width(project: dict, talent: dict) -> float:
    project_type = project.get("project_type", project["usage_scope"])
    size_band = project_context(project)["projectSizeBand"]

    if talent_class(talent) == "actor":
        role = talent.get("actor_role")
        if role in {"background", "featured"}:
            return 0.08
        if role == "supporting":
            return 0.14
        return 0.2

    width = 0.1
    if project_type in {"national_campaign", "commercial_campaign"}:
        width = 0.14
    elif project_type in {"editorial_prestige", "exploratory_research"}:
        width = 0.16
    elif project_type in {"social_content", "background_casting"}:
        width = 0.08

    if size_band in {"premium", "major"}:
        width += 0.03
    if project["budget_type"] == "exploratory":
        width += 0.04

    return min(width, 0.24)


def expected_booking_range(project: dict, talent: dict, rec: dict) -> dict:
    quote = int(rec["final_quote"])
    floor = int(rec["legal_floor"]["effectiveFloor"])
    width = _range_width(project, talent)
    low = max(floor, _range_amount(quote * (1.0 - width)))
    high = max(quote, _range_amount(quote * (1.0 + width)))

    return {
        "label": "Expected Booking Range",
        "low": low,
        "high": high,
        "expectedClose": quote,
        "currency": "USD",
        "rangeWidth": round(width, 3),
        "assumptionsIncluded": pricing_assumptions(project),
        "actualizationTriggers": actualization_triggers(project, talent),
        "visibility": "talent-outreach-and-admin",
    }
