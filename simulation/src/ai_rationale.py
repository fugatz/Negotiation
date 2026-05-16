from __future__ import annotations


PRIVATE_SIGNAL_TERMS = (
    "working floor",
    "floor rate",
    "desperation",
    "hidden flexibility",
    "private floor",
)


def _pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f}%"


def _visibility(rec: dict, discretion: dict, reasons: list[str]) -> str:
    reason_text = " ".join(reasons).lower()
    sensitive_reason = any(
        phrase in " ".join(reasons).lower()
        for phrase in ("high-friction", "repeated unexplained", "risk premium", "budget fishing")
    )
    sensitive_reason = sensitive_reason or "keeps the rationale internal" in reason_text
    sensitive_reason = sensitive_reason or float(rec["talent_behavior_nudge"]["confidence_delta"]) < 0
    sensitive_reason = sensitive_reason or float(rec["client_behavior_nudge"]["confidence_delta"]) < 0

    if discretion["delta"] != 0:
        return "human-review"
    if sensitive_reason:
        return "internal-only"
    return "client-facing"


def _leakage_warnings(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in PRIVATE_SIGNAL_TERMS if term in lowered]


def build_pricing_rationale(project: dict, client: dict, talent: dict, rec: dict, discretion: dict) -> dict:
    reasons: list[str] = []

    timing = rec["timing_nudge"]
    if timing["rate_delta"] > 0:
        reasons.append(
            f"A {_pct(timing['rate_delta'])} timing premium reflects the short lead time and schedule disruption."
        )
    if timing["confidence_delta"] < 0:
        if timing["horizon"] == "long_horizon":
            reasons.append(
                "The long planning horizon lowers confidence until approvals, scope, and schedule are firmer."
            )
        else:
            reasons.append(
                "The short lead time slightly lowers confidence because availability and coordination risk are higher."
            )

    talent_behavior = rec["talent_behavior_nudge"]
    if talent_behavior["rate_delta"] > 0:
        reasons.append(
            f"A {_pct(talent_behavior['rate_delta'])} talent reliability premium reflects stable quotes and low booking friction."
        )
    elif talent_behavior["confidence_delta"] < 0:
        reasons.append(
            "Talent-side negotiation history reduces confidence and keeps the rationale internal."
        )

    client_behavior = rec["client_behavior_nudge"]
    if client_behavior["rate_delta"] < 0:
        reasons.append(
            f"A {_pct(client_behavior['rate_delta'])} client reliability adjustment reflects lower transaction risk."
        )
    elif client_behavior["rate_delta"] > 0:
        reasons.append(
            f"A {_pct(client_behavior['rate_delta'])} client risk adjustment reflects added negotiation or scope uncertainty."
        )

    if rec["creative_fit"] >= 0.86 and rec["price_fit"] < 0.8:
        reasons.append(
            "The premium posture is defensible because creative fit is unusually strong for this category."
        )

    if discretion["delta"] > 0:
        reasons.append(
            f"Shadow discretion proposes {_pct(discretion['delta'])}: this talent may get more this time because similar outcomes closed above the computed quote."
        )
    elif discretion["delta"] < 0:
        reasons.append(
            f"Shadow discretion proposes {_pct(discretion['delta'])}: similar outcomes suggest a softer posture may improve close probability."
        )

    if not reasons:
        reasons.append("No special pricing rationale beyond the base computed fit and budget posture.")

    visibility = _visibility(rec, discretion, reasons)
    summary = reasons[0]
    text = " ".join(reasons)

    return {
        "summary": summary,
        "reasons": reasons,
        "visibility": visibility,
        "discretionDelta": round(float(discretion["delta"]), 4),
        "discretionMode": discretion["mode"],
        "discretionAppliesToLiveQuote": discretion["appliesToLiveQuote"],
        "discretionEvidence": discretion["evidence"],
        "humanReviewRecommended": visibility == "human-review" or bool(discretion["humanReviewRecommended"]),
        "leakageWarnings": _leakage_warnings(text),
    }
