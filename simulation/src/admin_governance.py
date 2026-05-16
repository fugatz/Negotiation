from __future__ import annotations


LAUNCH_ADMIN_SETTING_TWEAK_CAP = 0.02

TWEAKABLE_ADMIN_SETTINGS = (
    "timing thresholds and caps",
    "behavior nudge caps",
    "AI discretion mode and cap",
    "market-health override thresholds",
    "brand-facing rationale templates",
    "quote lock exception categories",
    "long-horizon hold policy settings",
)

MARKET_HEALTH_REVIEW_FLAGS = {
    "price_led_recommendation_risk",
    "race_to_bottom_risk",
}


def build_admin_governance(rec: dict) -> dict:
    rationales = rec["ai_rationales"]
    admin_rationale = rationales["adminPricingRationale"]
    brand_rationale = rationales["brandFacingRationale"]
    discretion = rec["ai_discretion"]

    review_reasons = ["Launch mode requires admin approval before client presentation."]
    exception_triggers: list[str] = []

    if brand_rationale["leakageWarnings"]:
        exception_triggers.append("brand-facing rationale leakage warning")
    if admin_rationale["humanReviewRecommended"]:
        exception_triggers.append("admin pricing rationale flagged for review")
    if float(discretion["delta"]) != 0.0:
        exception_triggers.append("nonzero AI discretion proposal")
    market_health_flags = set(rec.get("market_health_flags", []))
    if market_health_flags & MARKET_HEALTH_REVIEW_FLAGS or float(rec["market_health_score"]) < 0.6:
        exception_triggers.append("market-health guardrail")
    if rec["timing_nudge"]["horizon"] == "long_horizon" and rec["timing_nudge"]["platform_trust_tier"] in {
        "new_or_unproven",
        "limited_history",
    }:
        exception_triggers.append("long-horizon project without strong client trust")
    if rec.get("client_visible_price_state") == "outside stated budget":
        exception_triggers.append("outside stated budget")

    return {
        "mode": "launch_admin_approval",
        "approvalRequired": True,
        "autonomyTarget": "eventual autonomous execution with exception-based admin review",
        "allowedAdminSettings": list(TWEAKABLE_ADMIN_SETTINGS),
        "maxSmallSettingTweak": LAUNCH_ADMIN_SETTING_TWEAK_CAP,
        "reviewReasons": review_reasons,
        "exceptionTriggers": sorted(set(exception_triggers)),
        "matureAutonomyCandidate": not exception_triggers,
        "auditRequired": True,
    }
