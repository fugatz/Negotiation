from __future__ import annotations

from .ai_rationale import PUBLIC_FORBIDDEN_TERMS


SHADOW_DISCRETION_CAP = 0.01
BEHAVIOR_RATE_CAP = 0.05


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
    if lead_time_days < 14:
        return "extreme_last_minute"
    if lead_time_days < 21:
        return "last_minute"
    if lead_time_days >= 90:
        return "long_horizon"
    return "normal"


def _check(condition: bool, failures: list[dict], code: str, context: str, detail: str) -> None:
    if not condition:
        failures.append({"code": code, "context": context, "detail": detail})


def validate_report(report: dict) -> dict:
    failures: list[dict] = []
    warnings: list[dict] = []
    recommendation_count = 0

    for trace in report["traces"]:
        expected_horizon = _expected_timing_horizon(int(trace["leadTimeDays"]))
        _check(
            trace["timingHorizon"] == expected_horizon,
            failures,
            "timing_horizon_mismatch",
            trace["projectId"],
            f"expected {expected_horizon}, got {trace['timingHorizon']}",
        )

        for rec in _recommendations(trace):
            recommendation_count += 1
            context = _context(trace, rec)
            rationales = rec["aiRationales"]
            admin = rationales["adminPricingRationale"]
            brand = rationales["brandFacingRationale"]
            talent = rationales["talentFacingRationale"]
            governance = rec["adminGovernance"]

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
                discretion_delta <= SHADOW_DISCRETION_CAP,
                failures,
                "discretion_cap_exceeded",
                context,
                f"shadow discretion {discretion_delta} exceeds cap {SHADOW_DISCRETION_CAP}",
            )
            if discretion_delta > 0:
                _check(
                    "nonzero AI discretion proposal" in governance["exceptionTriggers"],
                    failures,
                    "discretion_exception_missing",
                    context,
                    "nonzero discretion must trigger admin exception review",
                )

            behavior_delta = abs(float(rec["behavior"]["combinedBehaviorRateDelta"]))
            _check(
                behavior_delta <= BEHAVIOR_RATE_CAP,
                failures,
                "behavior_cap_exceeded",
                context,
                f"combined behavior delta {behavior_delta} exceeds cap {BEHAVIOR_RATE_CAP}",
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
