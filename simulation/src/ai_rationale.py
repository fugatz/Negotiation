from __future__ import annotations

from .client_context import brand_prestige_context
from .timing import classify_timing


PRIVATE_SIGNAL_TERMS = (
    "working floor",
    "floor rate",
    "desperation",
    "hidden flexibility",
    "private floor",
)

PUBLIC_FORBIDDEN_TERMS = PRIVATE_SIGNAL_TERMS + (
    "adjustment",
    "behavior",
    "client risk",
    "delta",
    "discount",
    "floor",
    "friction",
    "penalty",
    "premium",
    "price",
    "pricing",
    "quote",
    "rate",
    "repricing",
    "risk premium",
    "shadow",
    "trust tier",
    "upstream",
)


def _pct(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f}%"


def _leakage_warnings(text: str, terms: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    warnings = [term for term in terms if term in lowered]
    if "%" in text:
        warnings.append("percentage")
    return sorted(set(warnings))


def _admin_review_needed(rec: dict, discretion: dict, reasons: list[str]) -> bool:
    reason_text = " ".join(reasons).lower()
    sensitive_reason = any(
        phrase in reason_text
        for phrase in ("high-friction", "repeated unexplained", "risk premium", "budget fishing")
    )
    sensitive_reason = sensitive_reason or float(rec["talent_behavior_nudge"]["confidence_delta"]) < 0
    sensitive_reason = sensitive_reason or float(rec["client_behavior_nudge"]["confidence_delta"]) < 0
    return bool(discretion["humanReviewRecommended"]) or discretion["delta"] != 0 or sensitive_reason


def _build_admin_pricing_rationale(
    project: dict,
    client: dict,
    talent: dict,
    rec: dict,
    discretion: dict,
) -> dict:
    del project, talent
    reasons: list[str] = []
    prestige = brand_prestige_context(client)

    timing = rec["timing_nudge"]
    if timing["rate_delta"] > 0:
        reasons.append(
            f"A {_pct(timing['rate_delta'])} timing premium reflects the short lead time and schedule disruption."
        )
    if timing["confidence_delta"] < 0:
        if timing["horizon"] == "long_horizon":
            if timing["platform_trust_tier"] == "high_repeat":
                reasons.append(
                    "The 90+ day horizon only slightly lowers confidence because this is a high-trust repeat client."
                )
            elif timing["platform_trust_tier"] == "new_or_unproven":
                reasons.append(
                    "The 90+ day horizon materially lowers seriousness confidence because there is no platform history yet."
                )
            else:
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
    elif talent_behavior["rate_delta"] < 0:
        reasons.append(
            f"A {_pct(talent_behavior['rate_delta'])} talent-side friction adjustment reflects added deal friction."
        )
    elif talent_behavior["confidence_delta"] < 0:
        reasons.append("Talent-side negotiation history reduces confidence.")

    client_behavior = rec["client_behavior_nudge"]
    if client_behavior["rate_delta"] < 0:
        reasons.append(
            f"A {_pct(client_behavior['rate_delta'])} client reliability adjustment reflects lower transaction risk."
        )
    elif client_behavior["rate_delta"] > 0:
        reasons.append(
            f"A {_pct(client_behavior['rate_delta'])} client risk adjustment reflects added negotiation or scope uncertainty."
        )

    if prestige["brandPrestigeTier"] == "tier_1":
        reasons.append(
            "Brand prestige is high, but launch policy keeps desirability separate from client trust and does not apply automatic rate movement from prestige alone."
        )
    elif prestige["brandPrestigeTier"] == "tier_2":
        reasons.append(
            "Brand prestige may improve talent interest, but it remains a separate context signal rather than a client reliability score."
        )

    availability_check = rec.get("availability_check", {})
    if availability_check.get("status") == "countered_before_client_presentation":
        reasons.append(
            "Talent countered during the pre-presentation availability check; the client slate uses the committed quote only."
        )

    market_cost = rec.get("budget_context", {}).get("marketCostContext", {})
    actor_market_prior = market_cost.get("actorMarketRatePrior") if market_cost else None
    if actor_market_prior:
        if actor_market_prior.get("sourceType") == "published_rate_card":
            reasons.append(
                f"{market_cost['country']} has a published {actor_market_prior['sourceAgreement']} rate card available for this actor context."
            )
        else:
            reasons.append(
                f"{market_cost['country']} market-cost context is available as an advisory prior only; paid-rate actuals should override it when available."
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

    text = " ".join(reasons)
    return {
        "audience": "admin",
        "visibility": "admin-only",
        "summary": reasons[0],
        "reasons": reasons,
        "discretionDelta": round(float(discretion["delta"]), 4),
        "discretionMode": discretion["mode"],
        "discretionAppliesToLiveQuote": discretion["appliesToLiveQuote"],
        "discretionEvidence": discretion["evidence"],
        "calibrationAuthority": discretion["calibrationAuthority"],
        "rateAuthority": discretion["rateAuthority"],
        "guidanceNote": discretion["guidanceNote"],
        "humanReviewRecommended": _admin_review_needed(rec, discretion, reasons),
        "leakageWarningsIfSurfaced": _leakage_warnings(text, PRIVATE_SIGNAL_TERMS),
    }


def _category_label(project: dict) -> str:
    return str(project.get("subcategory") or project.get("category") or "category").replace("_", " ")


def _build_brand_facing_rationale(project: dict, talent: dict, rec: dict) -> dict:
    category = _category_label(project)
    reasons: list[str] = []

    if rec["creative_fit"] >= 0.86:
        reasons.append(f"Deep {category} experience and a strong creative match for the brief.")
    elif rec["creative_fit"] >= 0.72:
        reasons.append(f"Relevant {category} background with a clear connection to the brief.")
    else:
        reasons.append("Useful adjacent experience for the creative direction.")

    category_strength = float(talent["categories"].get(project.get("category", ""), 0.0))
    subcategory_strength = float(talent["categories"].get(project.get("subcategory", ""), category_strength))
    if max(category_strength, subcategory_strength) >= 0.9:
        reasons.append("Specialized portfolio depth supports a confident recommendation.")
    elif max(category_strength, subcategory_strength) >= 0.75:
        reasons.append("The portfolio shows meaningful experience in this kind of work.")

    if rec["practical_fit"] >= 0.84:
        reasons.append("Production fit is strong across availability, scope, and schedule needs.")
    elif classify_timing(int(project.get("lead_time_days", 999))) in {"last_minute", "extreme_last_minute"}:
        reasons.append("The profile remains workable for the compressed production window.")

    if rec["trust_score"] >= 0.82:
        reasons.append("The profile supports a confident path through confirmation.")

    if not reasons:
        reasons.append("A credible creative option for this brief.")

    text = " ".join(reasons)
    leakage_warnings = _leakage_warnings(text, PUBLIC_FORBIDDEN_TERMS)
    return {
        "audience": "brand",
        "visibility": "brand-facing",
        "summary": reasons[0],
        "reasons": reasons,
        "humanReviewRecommended": bool(leakage_warnings),
        "leakageWarnings": leakage_warnings,
    }


def _build_talent_facing_rationale() -> dict:
    return {
        "audience": "talent",
        "visibility": "not-generated",
        "available": False,
        "adminNote": (
            "This pricing layer does not generate job-specific pricing rationales for talent. "
            "Talent-facing score education is handled by upstream readiness or reliability systems."
        ),
    }


def build_ai_rationales(project: dict, client: dict, talent: dict, rec: dict, discretion: dict) -> dict:
    return {
        "adminPricingRationale": _build_admin_pricing_rationale(project, client, talent, rec, discretion),
        "brandFacingRationale": _build_brand_facing_rationale(project, talent, rec),
        "talentFacingRationale": _build_talent_facing_rationale(),
    }
