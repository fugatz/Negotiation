from __future__ import annotations

from .policy_config import load_policy_config
from .scoring import talent_class


def _config() -> dict:
    return load_policy_config()["actor_pricing"]["talent_advocacy"]


def actor_talent_advocacy_uplift(talent: dict, project: dict, score: dict) -> dict:
    config = _config()

    if talent_class(talent) != "actor":
        return {
            "applies": False,
            "rateDelta": 0.0,
            "cap": float(config["max_uplift"]),
            "reason": "not an actor pricing context",
            "source": "distinkt_talent_advocacy_policy",
            "rateAuthority": "talent_owned_rate_range",
            "clientVisible": False,
        }

    role = talent.get("actor_role") or project.get("actor_role_scope") or "unknown_role"
    role_uplift = float(config["role_uplifts"].get(role, config["default_uplift"]))
    cap = float(config["max_uplift"])
    delta = min(max(role_uplift, 0.0), cap)
    floor_basis = score.get("legal_floor", {}).get("basis")

    if floor_basis == "published_actor_rate_card":
        delta = min(delta, float(config["published_rate_card_uplift"]))

    return {
        "applies": True,
        "rateDelta": round(delta, 4),
        "cap": cap,
        "reason": "Distinkt representation posture seeks a modest lift over the computed actor baseline when booking realism allows.",
        "source": "distinkt_talent_advocacy_policy",
        "role": role,
        "floorBasis": floor_basis,
        "rateAuthority": "talent_owned_rate_range",
        "clientVisible": False,
    }
