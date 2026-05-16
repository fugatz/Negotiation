from __future__ import annotations


def classify_timing(lead_time_days: int) -> str:
    if lead_time_days < 14:
        return "extreme_last_minute"
    if lead_time_days < 21:
        return "last_minute"
    if lead_time_days >= 90:
        return "long_horizon"
    return "normal"


def platform_trust_tier(client: dict) -> str:
    completed_projects = int(client.get("platform_completed_projects", 0))
    trust_score = float(client.get("platform_trust_score", 0.0))

    if completed_projects >= 4 and trust_score >= 0.85:
        return "high_repeat"
    if completed_projects >= 2 and trust_score >= 0.7:
        return "known"
    if completed_projects >= 1:
        return "limited_history"
    return "new_or_unproven"


def timing_nudge(project: dict, client: dict) -> dict:
    lead_time = int(project["lead_time_days"])
    horizon = classify_timing(lead_time)
    trust_tier = platform_trust_tier(client)

    if horizon == "extreme_last_minute":
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": 0.08,
            "confidence_delta": -0.02,
            "hold_policy": "confirm immediately before presenting",
            "reason": "under 14 days; extreme platform compression premium",
        }

    if horizon == "last_minute":
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": 0.04,
            "confidence_delta": 0.0,
            "hold_policy": "short confirmation window",
            "reason": "under 21 days; platform last-minute urgency premium",
        }

    if horizon == "long_horizon":
        if trust_tier == "high_repeat":
            penalty = -0.01
            hold_policy = "soft hold with scheduled confirmation checkpoint"
            reason = "90+ days out, but high platform trust makes the project materially more credible"
        elif trust_tier == "known":
            penalty = -0.04
            hold_policy = "confirmation checkpoint before firm hold"
            reason = "90+ days out with some platform history; seriousness confidence modestly reduced"
        elif trust_tier == "limited_history":
            penalty = -0.06
            hold_policy = "short hold only after confirmation milestone"
            reason = "90+ days out with limited platform history; seriousness confidence reduced"
        else:
            penalty = -0.09
            hold_policy = "no firm hold without stronger confirmation"
            reason = "90+ days out with no platform history; likely exploratory until proven otherwise"
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": 0.0,
            "confidence_delta": penalty,
            "hold_policy": hold_policy,
            "reason": reason,
        }

    return {
        "horizon": horizon,
        "platform_trust_tier": trust_tier,
        "rate_delta": 0.0,
        "confidence_delta": 0.0,
        "hold_policy": "standard",
        "reason": "normal lead time",
    }
