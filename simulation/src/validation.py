from __future__ import annotations

from .ai_rationale import PUBLIC_FORBIDDEN_TERMS
from .policy_config import load_policy_config


def _recommendations(trace: dict) -> list[dict]:
    return trace["recommendedSlate"] + trace.get("stressShortlist", [])


def _context(trace: dict, rec: dict) -> str:
    return f"{trace['projectId']} / {rec['talent']}"


def _public_forbidden_hits(text: str) -> list[str]:
    lowered = text.lower()
    hits = [term for term in PUBLIC_FORBIDDEN_TERMS if term in lowered]
    if "%" in text:
        hits.append("percentage")
    return sorted(set(hits))


def _expected_timing_horizon(lead_time_days: int) -> str:
    timing = load_policy_config()["timing"]
    if lead_time_days < int(timing["extreme_last_minute_days"]):
        return "extreme_last_minute"
    if lead_time_days < int(timing["last_minute_days"]):
        return "last_minute"
    if lead_time_days >= int(timing["long_horizon_days"]):
        return "long_horizon"
    return "normal"


def _check(condition: bool, failures: list[dict], code: str, context: str, detail: str) -> None:
    if not condition:
        failures.append({"code": code, "context": context, "detail": detail})


def validate_report(report: dict) -> dict:
    config = load_policy_config()
    failures: list[dict] = []
    warnings: list[dict] = []
    recommendation_count = 0
    shadow_discretion_cap = float(config["ai_discretion"]["shadow_cap"])
    behavior_rate_cap = float(config["behavior"]["rate_cap"])
    market_health = config["market_health"]
    market_health_review_flags = set(market_health["review_flags"])

    for trace in report["traces"]:
        expected_horizon = _expected_timing_horizon(int(trace["leadTimeDays"]))
        _check(
            trace["timingHorizon"] == expected_horizon,
            failures,
            "timing_horizon_mismatch",
            trace["projectId"],
            f"expected {expected_horizon}, got {trace['timingHorizon']}",
        )
        if trace["recommendedSlate"]:
            top_rec = trace["recommendedSlate"][0]
            _check(
                "race_to_bottom_risk" not in top_rec["marketHealth"]["flags"],
                failures,
                "race_to_bottom_default_winner",
                _context(trace, top_rec),
                "market-health override should prevent low-price/low-fit options from defaulting to top rank",
            )

        for rec in _recommendations(trace):
            recommendation_count += 1
            context = _context(trace, rec)
            rationales = rec["aiRationales"]
            admin = rationales["adminPricingRationale"]
            brand = rationales["brandFacingRationale"]
            talent = rationales["talentFacingRationale"]
            governance = rec["adminGovernance"]
            availability_check = rec["availabilityCheck"]

            _check(
                availability_check["completedBeforeClientPresentation"] is True,
                failures,
                "availability_check_missing",
                context,
                "talent must opt into the rate before client presentation",
            )
            _check(
                availability_check["clientVisible"] is False,
                failures,
                "availability_check_public",
                context,
                "availability check details must not be client-facing",
            )
            _check(
                int(availability_check["committedQuote"]) == int(rec["quote"]),
                failures,
                "presentation_quote_not_committed",
                context,
                "client-facing quote must equal the pre-presentation talent committed quote",
            )
            event_text = " ".join(
                availability_check.get("events", []) + availability_check.get("warnings", [])
            ).lower()
            _check(
                "post-interest" not in event_text,
                failures,
                "post_interest_talent_repricing",
                context,
                "talent-side rate movement must happen before client presentation",
            )

            _check(
                admin["visibility"] == "admin-only",
                failures,
                "admin_rationale_visibility",
                context,
                "admin pricing rationale must remain admin-only",
            )
            _check(
                brand["visibility"] == "brand-facing",
                failures,
                "brand_rationale_visibility",
                context,
                "brand match rationale must be the only public rationale surface",
            )
            _check(
                talent.get("available") is False and talent["visibility"] == "not-generated",
                failures,
                "talent_pricing_rationale_generated",
                context,
                "this pricing layer must not generate talent-facing job-specific rationale",
            )

            brand_text = " ".join([brand.get("summary", "")] + brand.get("reasons", []))
            forbidden_hits = sorted(set(brand.get("leakageWarnings", []) + _public_forbidden_hits(brand_text)))
            _check(
                not forbidden_hits,
                failures,
                "brand_rationale_leakage",
                context,
                f"brand-facing rationale leaked forbidden terms: {forbidden_hits}",
            )

            _check(
                governance["approvalRequired"] is True,
                failures,
                "launch_admin_approval_missing",
                context,
                "launch mode requires admin approval before client presentation",
            )
            _check(
                governance["auditRequired"] is True,
                failures,
                "admin_audit_missing",
                context,
                "launch mode must require audit logging for approvals and tweaks",
            )

            discretion_delta = abs(float(admin["discretionDelta"]))
            _check(
                admin["discretionMode"] == "shadow" and admin["discretionAppliesToLiveQuote"] is False,
                failures,
                "discretion_not_shadow",
                context,
                "launch discretion must remain shadow/advisory unless separately approved",
            )
            _check(
                discretion_delta <= shadow_discretion_cap,
                failures,
                "discretion_cap_exceeded",
                context,
                f"shadow discretion {discretion_delta} exceeds cap {shadow_discretion_cap}",
            )
            if discretion_delta > 0:
                _check(
                    "nonzero AI discretion proposal" in governance["exceptionTriggers"],
                    failures,
                    "discretion_exception_missing",
                    context,
                    "nonzero discretion must trigger admin exception review",
                )
            if availability_check["status"] == "countered_before_client_presentation":
                _check(
                    "pre-presentation talent counter" in governance["exceptionTriggers"],
                    failures,
                    "pre_presentation_counter_exception_missing",
                    context,
                    "pre-presentation talent counters must trigger admin exception review",
                )

            behavior_delta = abs(float(rec["behavior"]["combinedBehaviorRateDelta"]))
            _check(
                behavior_delta <= behavior_rate_cap,
                failures,
                "behavior_cap_exceeded",
                context,
                f"combined behavior delta {behavior_delta} exceeds cap {behavior_rate_cap}",
            )

            market_flags = rec["marketHealth"]["flags"]
            market_score = float(rec["marketHealth"]["score"])
            review_score_threshold = float(market_health["review_score_threshold"])
            if set(market_flags) & market_health_review_flags or market_score < review_score_threshold:
                _check(
                    "market-health guardrail" in governance["exceptionTriggers"],
                    failures,
                    "market_health_exception_missing",
                    context,
                    "market-health flags or low score must trigger admin exception review",
                )

            if rec["clientVisiblePriceState"] == "outside stated budget":
                _check(
                    "outside stated budget" in governance["exceptionTriggers"],
                    failures,
                    "outside_budget_exception_missing",
                    context,
                    "outside-budget recommendations must trigger admin exception review",
                )

            if rec["timing"]["horizon"] == "long_horizon":
                _check(
                    float(rec["timing"]["rateDelta"]) == 0.0,
                    failures,
                    "long_horizon_price_nudge",
                    context,
                    "long-horizon uncertainty should affect confidence/holds, not direct price",
                )

            if governance["matureAutonomyCandidate"] and governance["exceptionTriggers"]:
                warnings.append(
                    {
                        "code": "autonomy_candidate_has_triggers",
                        "context": context,
                        "detail": "autonomy candidates should have no exception triggers",
                    }
                )

    return {
        "status": "pass" if not failures else "fail",
        "checkedRecommendationCount": recommendation_count,
        "failureCount": len(failures),
        "warningCount": len(warnings),
        "failures": failures,
        "warnings": warnings,
    }
