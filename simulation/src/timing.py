from __future__ import annotations

from .policy_config import load_policy_config


def _timing_config() -> dict:
    return load_policy_config()["timing"]


def classify_timing(lead_time_days: int) -> str:
    config = _timing_config()
    if lead_time_days < int(config["extreme_last_minute_days"]):
        return "extreme_last_minute"
    if lead_time_days < int(config["last_minute_days"]):
        return "last_minute"
    if lead_time_days >= int(config["long_horizon_days"]):
        return "long_horizon"
    return "normal"


def platform_trust_tier(client: dict) -> str:
    completed_projects = int(client.get("platform_completed_projects", 0))
    trust_score = float(client.get("platform_trust_score", 0.0))
    tiers = _timing_config()["platform_trust_tiers"]

    high_repeat = tiers["high_repeat"]
    if completed_projects >= int(high_repeat["min_completed_projects"]) and trust_score >= float(
        high_repeat["min_trust_score"]
    ):
        return "high_repeat"
    known = tiers["known"]
    if completed_projects >= int(known["min_completed_projects"]) and trust_score >= float(
        known["min_trust_score"]
    ):
        return "known"
    limited_history = tiers["limited_history"]
    if completed_projects >= int(limited_history["min_completed_projects"]):
        return "limited_history"
    return "new_or_unproven"


def _confirmation_plan(horizon: str, trust_tier: str, nudge: dict | None = None) -> dict:
    if horizon != "long_horizon" or not nudge:
        return {
            "required": False,
            "state": "not_applicable",
            "checkpointDaysBeforeStart": None,
            "softHoldExpiresInDays": None,
            "expiresWithoutConfirmation": False,
            "firmHoldMinimumConfidence": None,
            "firmHoldRequires": [],
        }

    soft_hold_days = int(nudge["soft_hold_expires_in_days"])
    return {
        "required": True,
        "state": "confirmation_required",
        "checkpointDaysBeforeStart": int(nudge["checkpoint_days_before_start"]),
        "softHoldExpiresInDays": soft_hold_days,
        "expiresWithoutConfirmation": True,
        "firmHoldMinimumConfidence": float(nudge["firm_hold_min_confidence"]),
        "firmHoldRequires": list(nudge["firm_hold_requires"]),
        "platformTrustTier": trust_tier,
    }


def timing_nudge(project: dict, client: dict) -> dict:
    lead_time = int(project["lead_time_days"])
    horizon = classify_timing(lead_time)
    trust_tier = platform_trust_tier(client)
    config = _timing_config()

    if horizon == "extreme_last_minute":
        nudge = config["extreme_last_minute"]
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": float(nudge["rate_delta"]),
            "confidence_delta": float(nudge["confidence_delta"]),
            "hold_policy": nudge["hold_policy"],
            "confirmation": _confirmation_plan(horizon, trust_tier),
            "reason": nudge["reason"],
        }

    if horizon == "last_minute":
        nudge = config["last_minute"]
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": float(nudge["rate_delta"]),
            "confidence_delta": float(nudge["confidence_delta"]),
            "hold_policy": nudge["hold_policy"],
            "confirmation": _confirmation_plan(horizon, trust_tier),
            "reason": nudge["reason"],
        }

    if horizon == "long_horizon":
        nudge = config["platform_trust_tiers"][trust_tier]
        return {
            "horizon": horizon,
            "platform_trust_tier": trust_tier,
            "rate_delta": 0.0,
            "confidence_delta": float(nudge["long_horizon_confidence_delta"]),
            "hold_policy": nudge["hold_policy"],
            "confirmation": _confirmation_plan(horizon, trust_tier, nudge),
            "reason": nudge["reason"],
        }

    nudge = config["normal"]
    return {
        "horizon": horizon,
        "platform_trust_tier": trust_tier,
        "rate_delta": float(nudge["rate_delta"]),
        "confidence_delta": float(nudge["confidence_delta"]),
        "hold_policy": nudge["hold_policy"],
        "confirmation": _confirmation_plan(horizon, trust_tier),
        "reason": nudge["reason"],
    }
