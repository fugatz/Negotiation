from __future__ import annotations

from .common import clamp, weighted_average
from .policy_config import load_policy_config


def behavior_rate_cap() -> float:
    return float(load_policy_config()["behavior"]["rate_cap"])


def _upstream_talent_behavior_score(talent: dict) -> float | None:
    if talent.get("talent_kind") == "actor" and talent.get("upstream_actor_readiness_score") is not None:
        return float(talent["upstream_actor_readiness_score"])
    if talent.get("upstream_non_actor_reliability_score") is not None:
        return float(talent["upstream_non_actor_reliability_score"])
    return None


def talent_behavior_nudge(talent: dict) -> dict:
    upstream_score = _upstream_talent_behavior_score(talent)
    if upstream_score is None:
        reliability = weighted_average(
            [
                (float(talent["reliability_score"]), 0.35),
                (float(talent["quote_stability"]), 0.35),
                (float(talent["responsiveness"]), 0.2),
                (1.0 - min(float(talent["late_reprice_count"]) / 5.0, 1.0), 0.1),
            ]
        )
        source = "fixture proxy behavior fields"
    else:
        reliability = upstream_score
        source = "upstream actor readiness score" if talent.get("talent_kind") == "actor" else "upstream talent reliability metric"

    if talent["late_reprice_count"] >= 3:
        return {
            "score": round(reliability, 3),
            "source": source,
            "rate_delta": -0.02,
            "confidence_delta": -0.14,
            "reason": "repeated unexplained late repricing; small talent-side friction tax",
        }

    if reliability >= 0.9:
        return {
            "score": round(reliability, 3),
            "source": source,
            "rate_delta": 0.03,
            "confidence_delta": 0.04,
            "reason": "high quote stability and reliability",
        }

    if reliability >= 0.8:
        return {
            "score": round(reliability, 3),
            "source": source,
            "rate_delta": 0.01,
            "confidence_delta": 0.02,
            "reason": "solid dependable behavior",
        }

    if reliability < 0.62:
        return {
            "score": round(reliability, 3),
            "source": source,
            "rate_delta": -0.02,
            "confidence_delta": -0.08,
            "reason": "high-friction talent behavior; small talent-side friction tax",
        }

    return {
        "score": round(reliability, 3),
        "source": source,
        "rate_delta": 0.0,
        "confidence_delta": 0.0,
        "reason": "neutral talent behavior",
    }


def client_behavior_nudge(client: dict) -> dict:
    if client.get("upstream_client_trust_metric") is not None:
        dependability = float(client["upstream_client_trust_metric"])
        source = "upstream client trust metric"
    else:
        dependability = weighted_average(
            [
                (float(client["brief_clarity"]), 0.22),
                (float(client["decision_speed"]), 0.18),
                (float(client["payment_reliability"]), 0.24),
                (float(client["scope_stability"]), 0.24),
                (1.0 - float(client["rate_shopping_frequency"]), 0.06),
                (1.0 - float(client["post_quote_scope_creep"]), 0.06),
            ]
        )
        source = "fixture proxy behavior fields"

    if dependability >= 0.88:
        return {
            "score": round(dependability, 3),
            "source": source,
            "rate_delta": -0.02,
            "confidence_delta": 0.04,
            "reason": "dependable client reduces transaction risk",
        }

    if dependability >= 0.78:
        return {
            "score": round(dependability, 3),
            "source": source,
            "rate_delta": -0.01,
            "confidence_delta": 0.02,
            "reason": "solid client reliability",
        }

    if dependability < 0.58:
        return {
            "score": round(dependability, 3),
            "source": source,
            "rate_delta": 0.03,
            "confidence_delta": -0.08,
            "reason": "high-friction client behavior risk",
        }

    return {
        "score": round(dependability, 3),
        "source": source,
        "rate_delta": 0.0,
        "confidence_delta": 0.0,
        "reason": "neutral client behavior",
    }


def cap_behavior_rate_delta(talent_delta: float, client_delta: float) -> float:
    cap = behavior_rate_cap()
    return clamp(talent_delta + client_delta, -cap, cap)
