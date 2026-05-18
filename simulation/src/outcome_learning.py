from __future__ import annotations

from .common import money


GUIDANCE_AUTHORITY = "guidance_only"
RATE_AUTHORITY = "talent_owned_rate_range"
COHORT_DIMENSIONS = ["role", "category", "projectSizeBand", "market", "clientTrustTier"]
COHORT_DIMENSION_LABELS = {
    "role": "role",
    "category": "category",
    "projectSizeBand": "project-size",
    "market": "market",
    "clientTrustTier": "client-trust",
}


def _event_delta(project: dict, talent: dict, event: str) -> float:
    if talent.get("talent_class") == "actor":
        actor_deltas = {
            "fitting added": 0.08,
            "overtime triggered": 0.12,
            "usage expanded": 0.18,
            "paid media added": 0.16,
            "exclusivity added": 0.14,
            "union or legal requirement changes": 0.1,
        }
        return actor_deltas.get(event, 0.0)

    production_deltas = {
        "prep day added": 0.06,
        "travel required": 0.05,
        "overtime triggered": 0.08,
        "usage expanded": 0.05,
        "additional revision round requested": 0.04,
        "turnaround compressed": 0.04,
    }
    if (
        project.get("project_size_band") in {"premium", "major"}
        and event in {"usage expanded", "travel required"}
    ):
        return production_deltas.get(event, 0.0) + 0.02
    return production_deltas.get(event, 0.0)


def _booked_events(project: dict, talent: dict, rec: dict) -> list[str]:
    allowed = set(rec["expected_booking_range"]["actualizationTriggers"])
    events: list[str] = []
    project_type = project.get("project_type", project["usage_scope"])

    if talent.get("talent_class") == "actor":
        if project.get("requires_exclusivity") and "exclusivity added" in allowed:
            events.append("exclusivity added")
        if project["usage_scope"] in {"national", "campaign"} and "usage expanded" in allowed:
            events.append("usage expanded")
        return events

    if project_type in {"commercial_campaign", "national_campaign"} and "prep day added" in allowed:
        events.append("prep day added")
    if project_type == "national_campaign" and "usage expanded" in allowed:
        events.append("usage expanded")
    if project["category"] == "automotive" and "travel required" in allowed:
        events.append("travel required")
    if int(project["lead_time_days"]) < 14 and "turnaround compressed" in allowed:
        events.append("turnaround compressed")
    if int(project["lead_time_days"]) < 14 and "overtime triggered" in allowed:
        events.append("overtime triggered")

    return events


def _range_state(actualized_cost: int | None, expected_range: dict) -> str:
    if actualized_cost is None:
        return "not_actualized"
    if actualized_cost < int(expected_range["low"]):
        return "below_expected_range"
    if actualized_cost > int(expected_range["high"]):
        return "above_expected_range"
    return "inside_expected_range"


def _range_variance(actualized_cost: int | None, expected_range: dict) -> float | None:
    if actualized_cost is None:
        return None
    low = int(expected_range["low"])
    high = int(expected_range["high"])
    if actualized_cost < low:
        return round((actualized_cost - low) / max(low, 1), 4)
    if actualized_cost > high:
        return round((actualized_cost - high) / max(high, 1), 4)
    return 0.0


def _admin_notes(status: str, range_state: str, events: list[str]) -> list[str]:
    if status == "booked" and range_state == "inside_expected_range" and events:
        return ["Actualized inside the expected range; assumption language covered the event-driven variance."]
    if status == "booked" and range_state == "inside_expected_range":
        return ["Booked at the locked quote inside the expected range; no formula pressure."]
    if status == "booked" and range_state == "above_expected_range":
        return ["Actualized above expected range; review range width or assumption language for similar future deals."]
    if status == "failed_budget_gap":
        return ["Budget gap before booking; use as client budget calibration signal, not an automatic talent rate cut."]
    if status == "pending_hold":
        return ["Hold did not become an actualized outcome; keep it in seriousness-confidence data."]
    if status == "tentative":
        return ["Tentative outcome needs follow-up before being used for rate learning."]
    return ["No actualization learning signal yet."]


def _talent_guidance(project: dict, actualized_cost: int | None, locked_quote: int, range_state: str) -> dict:
    guidance = {
        "visibility": "talent-guidance",
        "available": False,
        "appliesAutomatically": False,
        "guidanceAuthority": GUIDANCE_AUTHORITY,
        "rateAuthority": RATE_AUTHORITY,
        "messages": [],
    }
    if actualized_cost is None:
        return guidance

    lift = (actualized_cost - locked_quote) / max(locked_quote, 1)
    if range_state == "above_expected_range" or lift >= 0.08:
        category = str(project.get("subcategory") or project["category"]).replace("_", " ")
        guidance["available"] = True
        guidance["messages"] = [
            (
                f"Similar {category} outcomes are landing about {round(lift * 100)}% above "
                "the accepted project rate in this simulation cohort."
            ),
            (
                "Consider testing a 3% listed-rate increase next quarter if deal flow "
                "remains healthy; this is optional guidance, not an automatic change."
            ),
        ]
    return guidance


def _cohort_signals(project: dict, talent: dict, rec: dict) -> dict:
    return {
        "role": talent.get("actor_role") or talent.get("production_role") or "unknown_role",
        "category": project["category"],
        "projectSizeBand": project.get("project_size_band", "unknown_size"),
        "market": project.get("market", "unknown_market"),
        "clientTrustTier": rec["timing_nudge"]["platform_trust_tier"],
    }


def simulate_actualization(project: dict, talent: dict, rec: dict, decision: dict) -> dict:
    expected_range = rec["expected_booking_range"]
    status = decision["status"]
    locked_quote = int(decision["locked_quote"])
    events: list[str] = []
    actualized_cost = None

    if status == "booked":
        events = _booked_events(project, talent, rec)
        event_delta = sum(_event_delta(project, talent, event) for event in events)
        actualized_cost = money(locked_quote * (1.0 + event_delta))

    range_state = _range_state(actualized_cost, expected_range)
    return {
        "talent_id": talent["id"],
        "status": status,
        "cohortSignals": _cohort_signals(project, talent, rec),
        "lockedQuote": locked_quote,
        "expectedRange": {
            "low": expected_range["low"],
            "high": expected_range["high"],
            "expectedClose": expected_range["expectedClose"],
            "currency": expected_range["currency"],
        },
        "actualizedCost": actualized_cost,
        "actualizationEvents": events,
        "allowedActualizationTriggers": expected_range["actualizationTriggers"],
        "rangeState": range_state,
        "varianceFromExpectedRange": _range_variance(actualized_cost, expected_range),
        "adminCalibrationNotes": _admin_notes(status, range_state, events),
        "talentGuidance": _talent_guidance(project, actualized_cost, locked_quote, range_state),
        "calibrationAuthority": GUIDANCE_AUTHORITY,
        "rateAuthority": RATE_AUTHORITY,
    }


def summarize_outcome_learning(records: list[dict]) -> dict:
    booked = [record for record in records if record["status"] == "booked"]
    actualized = [record for record in booked if record["actualizedCost"] is not None]
    above_range = [record for record in actualized if record["rangeState"] == "above_expected_range"]
    guidance = [record for record in records if record["talentGuidance"]["available"]]
    deltas = [
        (int(record["actualizedCost"]) - int(record["lockedQuote"])) / max(int(record["lockedQuote"]), 1)
        for record in actualized
    ]

    return {
        "bookedRecordCount": len(booked),
        "actualizedRecordCount": len(actualized),
        "actualizedAboveExpectedRangeCount": len(above_range),
        "talentGuidanceCount": len(guidance),
        "averageActualizationLift": round(sum(deltas) / len(deltas), 4) if deltas else 0.0,
        "calibrationAuthority": GUIDANCE_AUTHORITY,
        "rateAuthority": RATE_AUTHORITY,
    }


def build_outcome_learning(project: dict, talent_by_id: dict, candidates: list[dict], decisions: list[dict]) -> dict:
    records = [
        simulate_actualization(project, talent_by_id[candidate["talent_id"]], candidate, decision)
        for candidate, decision in zip(candidates, decisions)
    ]
    return {
        "summary": summarize_outcome_learning(records),
        "actualizationRecords": records,
        "talentGuidanceExamples": [
            record["talentGuidance"]
            for record in records
            if record["talentGuidance"]["available"]
        ],
    }


def _actualization_lift(record: dict) -> float:
    return (int(record["actualizedCost"]) - int(record["lockedQuote"])) / max(int(record["lockedQuote"]), 1)


def _cohort_confidence(actualized_count: int) -> str:
    if actualized_count >= 10:
        return "strong"
    if actualized_count >= 4:
        return "medium"
    return "directional_only"


def _cohort_guidance(dimension: str, value: str, average_lift: float, actualized_count: int) -> dict:
    guidance = {
        "visibility": "talent-guidance",
        "available": False,
        "appliesAutomatically": False,
        "guidanceAuthority": GUIDANCE_AUTHORITY,
        "rateAuthority": RATE_AUTHORITY,
        "confidence": _cohort_confidence(actualized_count),
        "messages": [],
    }
    if actualized_count == 0 or average_lift < 0.08:
        return guidance

    label = value.replace("_", " ")
    dimension_label = COHORT_DIMENSION_LABELS.get(dimension, dimension)
    guidance["available"] = True
    guidance["messages"] = [
        (
            f"Directional {dimension_label} cohort signal: {label} outcomes are landing about "
            f"{round(average_lift * 100)}% above accepted project rates in this simulation sample."
        ),
        (
            "Use this as optional market guidance only; talent-owned rates remain the authority "
            "and no rate changes apply automatically."
        ),
    ]
    return guidance


def _summarize_cohort(dimension: str, value: str, records: list[dict]) -> dict:
    booked = [record for record in records if record["status"] == "booked"]
    actualized = [record for record in booked if record["actualizedCost"] is not None]
    above_range = [record for record in actualized if record["rangeState"] == "above_expected_range"]
    lifts = [_actualization_lift(record) for record in actualized]
    average_lift = round(sum(lifts) / len(lifts), 4) if lifts else 0.0
    guidance = _cohort_guidance(dimension, value, average_lift, len(actualized))

    notes = []
    if above_range:
        notes.append("Above-range actualization appeared in this cohort; review range width and assumptions.")
    elif actualized:
        notes.append("Actualized outcomes stayed inside expected ranges for this cohort.")
    else:
        notes.append("No booked actualization evidence yet; keep this cohort advisory-only.")

    return {
        "dimension": dimension,
        "value": value,
        "recordCount": len(records),
        "bookedRecordCount": len(booked),
        "actualizedRecordCount": len(actualized),
        "actualizedAboveExpectedRangeCount": len(above_range),
        "averageActualizationLift": average_lift,
        "confidence": _cohort_confidence(len(actualized)),
        "adminCalibrationNotes": notes,
        "talentGuidance": guidance,
        "calibrationAuthority": GUIDANCE_AUTHORITY,
        "rateAuthority": RATE_AUTHORITY,
    }


def _all_actualization_records(traces: list[dict]) -> list[dict]:
    return [
        record
        for trace in traces
        for record in trace["outcomeLearning"]["actualizationRecords"]
    ]


def build_cohort_learning(traces: list[dict]) -> dict:
    records = _all_actualization_records(traces)
    by_dimension: dict[str, list[dict]] = {}
    total_guidance = 0

    for dimension in COHORT_DIMENSIONS:
        values = sorted({record["cohortSignals"][dimension] for record in records})
        cohort_records = [
            _summarize_cohort(
                dimension,
                value,
                [record for record in records if record["cohortSignals"][dimension] == value],
            )
            for value in values
        ]
        total_guidance += sum(1 for record in cohort_records if record["talentGuidance"]["available"])
        by_dimension[dimension] = cohort_records

    return {
        "dimensions": list(COHORT_DIMENSIONS),
        "summary": {
            "cohortCount": sum(len(records) for records in by_dimension.values()),
            "cohortGuidanceCount": total_guidance,
            "calibrationAuthority": GUIDANCE_AUTHORITY,
            "rateAuthority": RATE_AUTHORITY,
        },
        "byDimension": by_dimension,
    }
