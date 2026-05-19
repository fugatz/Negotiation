from __future__ import annotations

from .policy_config import load_policy_config

ADMIN_INCLUSION_OVERRIDE_TRIGGER = "admin inclusion override"


def _admin_config() -> dict:
    return load_policy_config()["admin_governance"]


def _market_health_config() -> dict:
    return load_policy_config()["market_health"]


def build_admin_governance(rec: dict) -> dict:
    rationales = rec["ai_rationales"]
    admin_rationale = rationales["adminPricingRationale"]
    brand_rationale = rationales["brandFacingRationale"]
    discretion = rec["ai_discretion"]
    admin_config = _admin_config()
    market_health_config = _market_health_config()

    review_reasons = ["Launch mode requires admin approval before client presentation."]
    exception_triggers: list[str] = []

    if brand_rationale["leakageWarnings"]:
        exception_triggers.append("brand-facing rationale leakage warning")
    if admin_rationale["humanReviewRecommended"]:
        exception_triggers.append("admin pricing rationale flagged for review")
    if float(discretion["delta"]) != 0.0:
        exception_triggers.append("nonzero AI discretion proposal")
    if rec.get("availability_check", {}).get("status") == "countered_before_client_presentation":
        exception_triggers.append("pre-presentation talent counter")
    if rec.get("admin_inclusion_override"):
        exception_triggers.append(ADMIN_INCLUSION_OVERRIDE_TRIGGER)
    if "minimum_wage_floor_unknown" in rec.get("legal_floor", {}).get("warnings", []):
        exception_triggers.append("minimum wage floor unknown")
    market_health_flags = set(rec.get("market_health_flags", []))
    review_flags = set(market_health_config["review_flags"])
    if market_health_flags & review_flags or float(rec["market_health_score"]) < float(
        market_health_config["review_score_threshold"]
    ):
        exception_triggers.append("market-health guardrail")
    if rec["timing_nudge"]["horizon"] == "long_horizon" and rec["timing_nudge"]["platform_trust_tier"] in {
        "new_or_unproven",
        "limited_history",
    }:
        exception_triggers.append("long-horizon project without strong client trust")
    if rec.get("client_visible_price_state") == "outside stated budget":
        exception_triggers.append("outside stated budget")
    if rec.get("budget_context", {}).get("talentBudgetMayBeWrong"):
        exception_triggers.append("derived talent budget requires review")

    return {
        "mode": admin_config["mode"],
        "approvalRequired": bool(admin_config["approval_required"]),
        "autonomyTarget": admin_config["autonomy_target"],
        "allowedAdminSettings": list(admin_config["allowed_settings"]),
        "maxSmallSettingTweak": float(admin_config["small_setting_tweak_cap"]),
        "reviewReasons": review_reasons,
        "exceptionTriggers": sorted(set(exception_triggers)),
        "matureAutonomyCandidate": not exception_triggers,
        "auditRequired": bool(admin_config["audit_required"]),
    }
