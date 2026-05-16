from __future__ import annotations


def classify_timing(lead_time_days: int) -> str:
    if lead_time_days < 7:
        return "extreme_last_minute"
    if lead_time_days < 14:
        return "last_minute"
    if lead_time_days >= 90:
        return "long_horizon"
    return "normal"


def timing_nudge(project: dict, client: dict) -> dict:
    lead_time = int(project["lead_time_days"])
    horizon = classify_timing(lead_time)
    brand_reliability = float(client.get("brand_reliability", 0.5))

    if horizon == "extreme_last_minute":
        return {
            "horizon": horizon,
            "rate_delta": 0.08,
            "confidence_delta": -0.02,
            "reason": "under 7 days; real schedule disruption premium",
        }

    if horizon == "last_minute":
        return {
            "horizon": horizon,
            "rate_delta": 0.04,
            "confidence_delta": 0.0,
            "reason": "under 14 days; modest urgency premium",
        }

    if horizon == "long_horizon":
        offset = 0.02 if brand_reliability >= 0.85 else 0.0
        penalty = -0.05 + offset
        if brand_reliability < 0.6:
            penalty -= 0.02
        return {
            "horizon": horizon,
            "rate_delta": 0.0,
            "confidence_delta": penalty,
            "reason": "90+ days out; confidence reduced until commitments firm up",
        }

    return {
        "horizon": horizon,
        "rate_delta": 0.0,
        "confidence_delta": 0.0,
        "reason": "normal lead time",
    }
