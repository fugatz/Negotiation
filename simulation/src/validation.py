from __future__ import annotations

from .ai_rationale import PUBLIC_FORBIDDEN_TERMS
from .negotiation import BUDGET_DRIVEN_COMMODITY_WARNING, SCOPE_CALIBRATION_WARNING
from .policy_config import load_policy_config
from .statuses import BOOKED_WITH_MARKET_HEALTH_WARNING, NEEDS_SCOPE_CALIBRATION, is_booked_status


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


def _talent_guidance_forbidden_hits(text: str) -> list[str]:
    forbidden = [
        "behavior",
        "desperation",
        "failure",
        "floor",
        "hidden",
        "penalty",
        "punish",
    ]
    lowered = text.lower()
    return sorted(term for term in forbidden if term in lowered)


def validate_report(report: dict) -> dict:
    config = load_policy_config()
    failures: list[dict] = []
    warnings: list[dict] = []
    recommendation_count = 0
    shadow_discretion_cap = float(config["ai_discretion"]["shadow_cap"])
    behavior_rate_cap = float(config["behavior"]["rate_cap"])
    market_health = config["market_health"]
    market_health_review_flags = set(market_health["review_flags"])
    expected_cohort_dimensions = {"role", "category", "projectSizeBand", "market", "clientTrustTier"}

    cohort_learning = report["cohortLearning"]
    _check(
        set(cohort_learning["dimensions"]) == expected_cohort_dimensions,
        failures,
        "cohort_dimensions_invalid",
        "cohortLearning",
        "cohort learning should split by role, category, project size, market, and client trust tier",
    )
    _check(
        cohort_learning["summary"]["calibrationAuthority"] == "guidance_only",
        failures,
        "cohort_calibration_authority_invalid",
        "cohortLearning",
        "cohort learning should produce guidance, not binding price rules",
    )
    _check(
        cohort_learning["summary"]["rateAuthority"] == "talent_owned_rate_range",
        failures,
        "cohort_rate_authority_invalid",
        "cohortLearning",
        "talent-owned rate ranges remain the cohort-learning pricing authority",
    )
    for dimension, cohorts in cohort_learning["byDimension"].items():
        for cohort in cohorts:
            context = f"{dimension} / {cohort['value']}"
            _check(
                cohort["calibrationAuthority"] == "guidance_only",
                failures,
                "cohort_record_calibration_authority_invalid",
                context,
                "cohort records must stay advisory",
            )
            _check(
                cohort["rateAuthority"] == "talent_owned_rate_range",
                failures,
                "cohort_record_rate_authority_invalid",
                context,
                "cohort records must keep talent-owned rates as authority",
            )
            guidance = cohort["talentGuidance"]
            _check(
                guidance["appliesAutomatically"] is False,
                failures,
                "cohort_guidance_applies_automatically",
                context,
                "cohort guidance must never change rates automatically",
            )
            if guidance["available"]:
                guidance_text = " ".join(guidance["messages"])
                _check(
                    "optional" in guidance_text.lower(),
                    failures,
                    "cohort_guidance_not_optional",
                    context,
                    "cohort guidance should state that it is optional",
                )
                forbidden_hits = _talent_guidance_forbidden_hits(guidance_text)
                _check(
                    not forbidden_hits,
                    failures,
                    "cohort_guidance_leakage",
                    context,
                    f"cohort guidance leaked private or negative terms: {forbidden_hits}",
                )

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

        outcome_learning = trace["outcomeLearning"]
        actualization_records = outcome_learning["actualizationRecords"]
        _check(
            len(actualization_records) == len(trace["clientDecisions"]),
            failures,
            "actualization_record_count_mismatch",
            trace["projectId"],
            "each client decision should have an outcome-learning actualization record",
        )
        for record in actualization_records:
            context = f"{trace['projectId']} / {record['talent_id']}"
            _check(
                record["calibrationAuthority"] == "guidance_only",
                failures,
                "actualization_calibration_authority_invalid",
                context,
                "actualization learning should produce guidance, not binding price rules",
            )
            _check(
                record["rateAuthority"] == "talent_owned_rate_range",
                failures,
                "actualization_rate_authority_invalid",
                context,
                "talent-owned rate ranges remain the outcome-learning pricing authority",
            )
            if is_booked_status(record["status"]):
                _check(
                    record["actualizedCost"] is not None,
                    failures,
                    "booked_without_actualized_cost",
                    context,
                    "booked outcomes should receive an actualized cost for learning",
                )
            else:
                _check(
                    record["actualizedCost"] is None,
                    failures,
                    "unbooked_actualized_cost",
                    context,
                    "unbooked outcomes should not produce an actualized cost",
                )
            _check(
                set(record["actualizationEvents"]).issubset(
                    set(record["allowedActualizationTriggers"])
                ),
                failures,
                "actualization_event_not_allowed",
                context,
                "actualization events must cite allowed triggers from the expected booking range",
            )
            guidance = record["talentGuidance"]
            _check(
                guidance["guidanceAuthority"] == "guidance_only"
                and guidance["rateAuthority"] == "talent_owned_rate_range",
                failures,
                "talent_guidance_authority_invalid",
                context,
                "talent-facing guidance must remain advisory and talent-owned",
            )
            _check(
                guidance["appliesAutomatically"] is False,
                failures,
                "talent_guidance_applies_automatically",
                context,
                "talent-facing rate guidance must never change rates automatically",
            )
            if guidance["available"]:
                guidance_text = " ".join(guidance["messages"])
                _check(
                    "optional" in guidance_text.lower(),
                    failures,
                    "talent_guidance_not_optional",
                    context,
                    "talent-facing guidance should state that it is optional",
                )
                forbidden_hits = _talent_guidance_forbidden_hits(guidance_text)
                _check(
                    not forbidden_hits,
                    failures,
                    "talent_guidance_leakage",
                    context,
                    f"talent-facing guidance leaked private or negative terms: {forbidden_hits}",
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
            legal_floor = rec["legalFloor"]
            expected_range = rec["expectedBookingRange"]

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
                availability_check["ratePresentedDuringOutreach"] is True,
                failures,
                "rate_not_presented_during_outreach",
                context,
                "talent must see the pricing-engine rate during WhatsApp/email outreach",
            )
            _check(
                availability_check["rateSource"] == "pricing_engine_project_rate",
                failures,
                "availability_rate_source_invalid",
                context,
                "outreach quote must be generated by the pricing engine before talent commitment",
            )
            _check(
                int(availability_check["committedQuote"]) == int(rec["quote"]),
                failures,
                "presentation_quote_not_committed",
                context,
                "client-facing quote must equal the pre-presentation talent committed quote",
            )
            _check(
                availability_check.get("proposedRange") is not None,
                failures,
                "outreach_range_missing",
                context,
                "rate-quoted outreach should include an expected booking range",
            )
            _check(
                availability_check.get("committedRange") == expected_range,
                failures,
                "committed_range_mismatch",
                context,
                "final trace range must reflect the talent-approved locked quote after outreach",
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
                admin["calibrationAuthority"] == "guidance_only",
                failures,
                "calibration_authority_invalid",
                context,
                "outcome calibration should produce guidance, not binding price rules",
            )
            _check(
                admin["rateAuthority"] == "talent_owned_rate_range",
                failures,
                "rate_authority_invalid",
                context,
                "talent-owned rate ranges remain the pricing authority",
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

            _check(
                int(expected_range["low"]) <= int(rec["quote"]) <= int(expected_range["high"]),
                failures,
                "quote_outside_expected_booking_range",
                context,
                "committed quote must sit inside the expected booking range",
            )
            _check(
                bool(expected_range["assumptionsIncluded"]),
                failures,
                "range_assumptions_missing",
                context,
                "expected booking ranges must include assumptions",
            )
            _check(
                bool(expected_range["actualizationTriggers"]),
                failures,
                "range_actualization_triggers_missing",
                context,
                "expected booking ranges must list allowed actualization triggers",
            )

            if rec["talentClass"] == "actor":
                if legal_floor["minimumWageStatus"] == "known":
                    _check(
                        int(rec["quote"]) >= int(legal_floor["minimumWageFloor"]),
                        failures,
                        "minimum_wage_floor_violation",
                        context,
                        "actor quote must not fall below supplied local minimum wage floor",
                    )
                    _check(
                        int(expected_range["low"]) >= int(legal_floor["minimumWageFloor"]),
                        failures,
                        "range_below_minimum_wage_floor",
                        context,
                        "actor expected booking range must not dip below supplied local minimum wage floor",
                    )
                elif legal_floor["minimumWageStatus"] == "unknown":
                    _check(
                        "minimum wage floor unknown" in governance["exceptionTriggers"],
                        failures,
                        "minimum_wage_unknown_exception_missing",
                        context,
                        "unknown actor minimum wage should remain an admin exception before autonomy",
                    )
                    warnings.append(
                        {
                            "code": "minimum_wage_floor_unknown",
                            "context": context,
                            "detail": "actor quote could not be checked against local minimum wage because wage input is null",
                        }
                    )

            if governance["matureAutonomyCandidate"] and governance["exceptionTriggers"]:
                warnings.append(
                    {
                        "code": "autonomy_candidate_has_triggers",
                        "context": context,
                        "detail": "autonomy candidates should have no exception triggers",
                    }
                )

        for decision in trace["clientDecisions"]:
            if decision["status"] == BOOKED_WITH_MARKET_HEALTH_WARNING:
                _check(
                    BUDGET_DRIVEN_COMMODITY_WARNING in decision["warnings"],
                    failures,
                    "budget_health_warning_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "budget-health warning outcomes must include the explicit warning label",
                )
            if decision["status"] == NEEDS_SCOPE_CALIBRATION:
                _check(
                    SCOPE_CALIBRATION_WARNING in decision["warnings"],
                    failures,
                    "scope_calibration_warning_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "scope calibration outcomes must include the explicit warning label",
                )

        if trace["outcome"] == NEEDS_SCOPE_CALIBRATION:
            _check(
                all(decision["status"] == NEEDS_SCOPE_CALIBRATION for decision in trace["clientDecisions"]),
                failures,
                "scope_calibration_decision_mismatch",
                trace["projectId"],
                "project-level scope calibration should apply when all evaluated decisions require calibration",
            )

    return {
        "status": "pass" if not failures else "fail",
        "checkedRecommendationCount": recommendation_count,
        "failureCount": len(failures),
        "warningCount": len(warnings),
        "failures": failures,
        "warnings": warnings,
    }
