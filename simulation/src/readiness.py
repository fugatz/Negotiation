from __future__ import annotations


READY_THRESHOLD = 50
READY_TIERS = {"ready", "approved", "production_ready", "verified_ready"}
BLOCKING_TIERS = {"draft", "incomplete", "needs_scope", "scope_calibration_required"}


def project_credibility_score(project: dict) -> tuple[int, str]:
    if project.get("projectCredibilityScore") is not None:
        return max(0, min(int(project["projectCredibilityScore"]), 100)), "main_site_project_credibility_score"
    if project.get("project_credibility_score") is not None:
        return max(0, min(int(project["project_credibility_score"]), 100)), "main_site_project_credibility_score"
    if project.get("project_commitment_confidence") is not None:
        return (
            max(0, min(int(round(float(project["project_commitment_confidence"]) * 100)), 100)),
            "fixture_project_commitment_confidence_proxy",
        )
    return 0, "missing_project_credibility"


def project_readiness_tier(project: dict, score: int) -> tuple[str, str]:
    raw_tier = project.get("projectReadinessTier") or project.get("project_readiness_tier")
    if raw_tier:
        return str(raw_tier).lower(), "main_site_project_readiness_tier"
    if score >= READY_THRESHOLD:
        return "ready", "derived_from_project_credibility_score"
    return "needs_scope", "derived_from_project_credibility_score"


def project_readiness_context(project: dict) -> dict:
    score, score_source = project_credibility_score(project)
    tier, tier_source = project_readiness_tier(project, score)
    override = project.get("readiness_admin_override") or {}
    override_applied = bool(override.get("applied", False))
    tier_allows_binding = tier in READY_TIERS or (tier not in BLOCKING_TIERS and score >= READY_THRESHOLD)
    binding_allowed = tier_allows_binding or override_applied

    if binding_allowed and override_applied and not tier_allows_binding:
        gate_state = "admin_override_allowed"
        reason = "admin override allows binding Outreach & Lock despite low project readiness"
    elif binding_allowed:
        gate_state = "binding_quote_allowed"
        reason = "project is ready enough for binding Outreach & Lock"
    else:
        gate_state = "scope_calibration_required"
        reason = "project is not ready enough for binding Outreach & Lock"

    return {
        "projectCredibilityScore": score,
        "projectCredibilitySource": score_source,
        "projectReadinessTier": tier,
        "projectReadinessTierSource": tier_source,
        "bindingQuoteThreshold": READY_THRESHOLD,
        "bindingQuoteAllowed": binding_allowed,
        "gateState": gate_state,
        "reason": reason,
        "adminOverride": {
            "applied": override_applied,
            "reasonCode": override.get("reasonCode"),
            "reason": override.get("reason"),
            "actor": override.get("actor"),
        },
    }
