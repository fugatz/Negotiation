from __future__ import annotations

from .common import clamp
from .policy_config import load_policy_config


def shadow_discretion_cap() -> float:
    return float(load_policy_config()["ai_discretion"]["shadow_cap"])


def _similar_outcomes(project: dict, talent: dict, outcomes: list[dict]) -> list[dict]:
    return [
        outcome
        for outcome in outcomes
        if outcome["talent_id"] == talent["id"]
        and outcome["category"] == project["category"]
    ]


def _gap(outcome: dict) -> float:
    computed = max(float(outcome["computed_quote"]), 1.0)
    return (float(outcome["final_quote"]) - computed) / computed


def propose_shadow_discretion(project: dict, talent: dict, rec: dict, outcomes: list[dict]) -> dict:
    similar = _similar_outcomes(project, talent, outcomes)
    booked = [outcome for outcome in similar if outcome["status"] == "booked"]
    failed = [outcome for outcome in similar if outcome["status"] != "booked"]

    proposal = {
        "mode": "shadow",
        "appliesToLiveQuote": False,
        "delta": 0.0,
        "cappedDelta": 0.0,
        "evidenceCount": len(similar),
        "direction": "none",
        "evidence": "No sufficient similar outcome evidence yet.",
        "humanReviewRecommended": False,
        "blockedByGuardrail": False,
    }

    if len(booked) >= 2:
        average_gap = sum(_gap(outcome) for outcome in booked) / len(booked)
        if average_gap >= 0.02 and float(rec["creative_fit"]) >= 0.82:
            cap = shadow_discretion_cap()
            delta = min(average_gap / 3.0, cap)
            proposal.update(
                {
                    "delta": round(delta, 4),
                    "cappedDelta": round(delta, 4),
                    "direction": "upside",
                    "evidence": "Similar booked outcomes closed slightly above computed quote.",
                    "humanReviewRecommended": delta >= cap,
                }
            )
            return proposal

    if len(failed) >= 2 and float(rec["price_fit"]) < 0.6:
        average_gap = sum(_gap(outcome) for outcome in failed) / len(failed)
        cap = shadow_discretion_cap()
        delta = max(min(average_gap / 4.0, 0.0), -cap)
        if delta == 0.0:
            delta = -0.005

        hypothetical_quote = float(rec["final_quote"]) * (1.0 + delta)
        if hypothetical_quote < float(talent["working_floor"]):
            proposal.update(
                {
                    "direction": "soften",
                    "evidence": "Similar failed outcomes suggest softer posture, but floor guardrail blocks the delta.",
                    "humanReviewRecommended": True,
                    "blockedByGuardrail": True,
                }
            )
            return proposal

        proposal.update(
            {
                "delta": round(delta, 4),
                "cappedDelta": round(clamp(delta, -cap, cap), 4),
                "direction": "soften",
                "evidence": "Similar failed outcomes suggest this deal may need a softer posture.",
                "humanReviewRecommended": True,
            }
        )
        return proposal

    return proposal
