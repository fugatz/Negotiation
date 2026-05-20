from __future__ import annotations

from .admin_governance import ADMIN_INCLUSION_OVERRIDE_TRIGGER
from .ai_rationale import PUBLIC_FORBIDDEN_TERMS
from .client_context import BRAND_PRESTIGE_TIERS, CLIENT_TRUST_TIERS
from .negotiation import (
    BUDGET_DRIVEN_COMMODITY_WARNING,
    HOLD_EXPIRED_WARNING,
    RATE_QUOTED_OUTREACH_CHANNEL,
    SCOPE_CALIBRATION_WARNING,
)
from .policy_config import load_policy_config
from .statuses import (
    BOOKED_WITH_MARKET_HEALTH_WARNING,
    HOLD_EXPIRED,
    NEEDS_SCOPE_CALIBRATION,
    is_booked_status,
)


def _recommendations(trace: dict) -> list[dict]:
    return (
        trace["recommendedSlate"]
        + trace.get("stressShortlist", [])
        + trace.get("adminOverrideSlate", [])
    )


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
        credibility = trace.get("clientCredibility", {})
        readiness = trace.get("readinessGate", {})
        _check(
            0 <= int(credibility.get("clientTrustScore", -1)) <= 100,
            failures,
            "client_trust_score_invalid",
            trace["projectId"],
            "clientTrustScore must be a 0-100 upstream score",
        )
        _check(
            credibility.get("clientTrustTier") in CLIENT_TRUST_TIERS,
            failures,
            "client_trust_tier_invalid",
            trace["projectId"],
            "clientTrustTier must be one of premium, established, emerging, or new",
        )
        _check(
            credibility.get("brandPrestigeTier") in BRAND_PRESTIGE_TIERS,
            failures,
            "brand_prestige_tier_invalid",
            trace["projectId"],
            "brandPrestigeTier must be separate from clientTrustTier and use a supported value",
        )
        _check(
            0 <= int(credibility.get("brandPrestigeScore", -1)) <= 100,
            failures,
            "brand_prestige_score_invalid",
            trace["projectId"],
            "brandPrestigeScore must be a 0-100 upstream/admin score",
        )
        if credibility.get("verifiedBrand"):
            _check(
                credibility.get("clientTrustTier") == "premium",
                failures,
                "verified_brand_not_premium",
                trace["projectId"],
                "verified brand flag should fast-track clientTrustTier to premium",
            )
        if credibility.get("agencyAccount"):
            _check(
                credibility.get("clientTrustTier") in {"premium", "established"},
                failures,
                "agency_account_not_established",
                trace["projectId"],
                "agency account flag should fast-track clientTrustTier to established or better",
            )
        project_score = credibility.get("projectCredibilityScore")
        if project_score is not None:
            _check(
                0 <= int(project_score) <= 100,
                failures,
                "project_credibility_score_invalid",
                trace["projectId"],
                "projectCredibilityScore must be null or a 0-100 upstream score",
            )
        _check(
            trace["timingHorizon"] == expected_horizon,
            failures,
            "timing_horizon_mismatch",
            trace["projectId"],
            f"expected {expected_horizon}, got {trace['timingHorizon']}",
        )
        _check(
            0 <= int(readiness.get("projectCredibilityScore", -1)) <= 100,
            failures,
            "readiness_project_credibility_invalid",
            trace["projectId"],
            "readiness gate must carry a 0-100 project credibility score",
        )
        _check(
            isinstance(readiness.get("bindingQuoteAllowed"), bool),
            failures,
            "readiness_binding_flag_invalid",
            trace["projectId"],
            "readiness gate must state whether binding Outreach & Lock is allowed",
        )
        if not readiness.get("bindingQuoteAllowed", True):
            _check(
                trace["outcome"] == NEEDS_SCOPE_CALIBRATION,
                failures,
                "readiness_blocked_wrong_outcome",
                trace["projectId"],
                "projects below the readiness gate should stop at scope calibration",
            )
            _check(
                not _recommendations(trace),
                failures,
                "readiness_blocked_has_client_recommendations",
                trace["projectId"],
                "projects below the readiness gate must not create client-presentable locked quotes",
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
            budget_context = rec["budgetContext"]
            talent_advocacy = rec["talentAdvocacy"]
            admin_override = rec.get("adminInclusionOverride")
            quote_lifecycle = rec["quoteLifecycle"]

            _check(
                int(rec["timing"]["clientTrustScore"]) == int(credibility["clientTrustScore"]),
                failures,
                "recommendation_client_trust_score_mismatch",
                context,
                "recommendation timing should carry the same upstream clientTrustScore as the trace",
            )
            _check(
                rec["timing"]["clientTrustTier"] == credibility["clientTrustTier"],
                failures,
                "recommendation_client_trust_tier_mismatch",
                context,
                "recommendation timing should carry the same upstream clientTrustTier as the trace",
            )

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
                "talent must see the pricing-engine rate during call-for-details or email-offer outreach",
            )
            _check(
                availability_check["outreachChannel"] == RATE_QUOTED_OUTREACH_CHANNEL,
                failures,
                "outreach_channel_invalid",
                context,
                "rate-quoted outreach should be modeled as call for details or email offer",
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
                talent_advocacy["clientVisible"] is False,
                failures,
                "talent_advocacy_client_visible",
                context,
                "talent advocacy uplift is internal/admin context and should not be client-facing",
            )
            _check(
                talent_advocacy["rateAuthority"] == "talent_owned_rate_range",
                failures,
                "talent_advocacy_rate_authority_invalid",
                context,
                "talent advocacy cannot override talent-owned rate authority",
            )
            _check(
                0.0 <= float(talent_advocacy["rateDelta"]) <= float(talent_advocacy["cap"]),
                failures,
                "talent_advocacy_cap_violation",
                context,
                "talent advocacy uplift must stay inside the configured cap",
            )
            if budget_context.get("talentBudgetMayBeWrong"):
                _check(
                    "derived talent budget requires review" in governance["exceptionTriggers"],
                    failures,
                    "derived_talent_budget_exception_missing",
                    context,
                    "talent budgets construed from all-in budgets must trigger admin review",
                )
                _check(
                    budget_context.get("talentBudgetConfidence") in {"low", "estimated", "directional"},
                    failures,
                    "derived_talent_budget_confidence_invalid",
                    context,
                    "derived talent budget should carry low or directional confidence",
                )
            market_cost = budget_context.get("marketCostContext", {})
            if market_cost.get("available"):
                _check(
                    market_cost.get("confidence") in {
                        "cost_of_living_prior_only",
                        "paid_rate_actuals_available",
                    },
                    failures,
                    "market_cost_confidence_invalid",
                    context,
                    "country market-cost context should identify either cost-prior-only or paid-actuals-available confidence",
                )
                _check(
                    market_cost.get("appliesAutomatically") is False,
                    failures,
                    "market_cost_applied_automatically",
                    context,
                    "country market-cost priors should not automatically override talent-owned rates",
                )
                if rec["talentClass"] == "actor":
                    actor_market_prior = market_cost.get("actorMarketRatePrior")
                    _check(
                        actor_market_prior is not None,
                        failures,
                        "actor_market_prior_missing",
                        context,
                        "actor country market-cost context should include role-level market-rate prior details",
                    )
                    if actor_market_prior:
                        source_type = actor_market_prior.get("sourceType")
                        _check(
                            source_type in {
                                "cost_of_living_prior",
                                "paid_rate_actuals",
                                "published_rate_card",
                            },
                            failures,
                            "actor_market_prior_source_invalid",
                            context,
                            "actor market-rate priors should identify whether they come from paid actuals, a cost prior, or a published card",
                        )
                        if source_type == "cost_of_living_prior":
                            _check(
                                "market cost prior requires actuals review" in governance["exceptionTriggers"],
                                failures,
                                "market_cost_review_exception_missing",
                                context,
                                "actor country market-cost priors should require actuals review before autonomy",
                            )
                        if source_type == "paid_rate_actuals":
                            paid_actual = market_cost.get("paidRateActual")
                            _check(
                                paid_actual is not None,
                                failures,
                                "paid_rate_actual_context_missing",
                                context,
                                "paid-rate actual source should include the matched actual record context",
                            )
                            if paid_actual:
                                _check(
                                    paid_actual.get("appliesAutomatically") is False,
                                    failures,
                                    "paid_rate_actual_applies_automatically",
                                    context,
                                    "paid-rate actuals should override the proxy as advisory context, not automatic live pricing",
                                )
                                _check(
                                    paid_actual.get("rateAuthority") == "talent_owned_rate_range",
                                    failures,
                                    "paid_rate_actual_rate_authority_invalid",
                                    context,
                                    "paid-rate actuals must not override talent-owned rate authority",
                                )
                        _check(
                            actor_market_prior.get("rateAuthority") == "talent_owned_rate_range",
                            failures,
                            "actor_market_prior_rate_authority_invalid",
                            context,
                            "actor market-rate priors must remain guidance and not override talent-owned rates",
                        )
                        _check(
                            actor_market_prior.get("calibrationAuthority")
                            in {"advisory_prior", "paid_rate_actuals", "published_rate_card"},
                            failures,
                            "actor_market_prior_calibration_authority_invalid",
                            context,
                            "actor market-rate priors should remain advisory, cite paid actuals, or cite a published rate card",
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
            _check(
                quote_lifecycle["quoteState"] == "locked",
                failures,
                "quote_lifecycle_not_locked",
                context,
                "client-presentable recommendations must carry a locked quote lifecycle",
            )
            _check(
                int(quote_lifecycle["activeQuoteVersion"]) == int(quote_lifecycle["quoteVersion"]),
                failures,
                "active_quote_version_mismatch",
                context,
                "active quote version should match the locked quote version presented to the client",
            )
            _check(
                int(quote_lifecycle["lockedGrossQuote"]) == int(rec["quote"]),
                failures,
                "locked_gross_quote_mismatch",
                context,
                "locked gross quote must equal the client-presented quote",
            )
            _check(
                quote_lifecycle["dfosHandoff"]["dfosMayRecalculateQuote"] is False,
                failures,
                "dfos_recalculation_allowed",
                context,
                "DFOS should consume the locked gross quote, not recalculate it",
            )
            event_types = {event["eventType"] for event in quote_lifecycle["auditEvents"]}
            required_events = {
                "quote_generated",
                "quote_sent_to_talent",
                "quote_locked",
                "quote_presented_to_client",
            }
            _check(
                required_events.issubset(event_types),
                failures,
                "quote_audit_events_missing",
                context,
                f"quote audit events must include {sorted(required_events)}",
            )
            if availability_check["status"] == "countered_before_client_presentation":
                _check(
                    "talent_countered_before_presentation" in event_types,
                    failures,
                    "quote_audit_counter_event_missing",
                    context,
                    "pre-presentation counters must be captured as quote audit events",
                )
            else:
                _check(
                    "talent_accepted_quote" in event_types
                    or "talent_requested_clarification" in event_types,
                    failures,
                    "quote_audit_talent_response_missing",
                    context,
                    "quote audit events must capture talent acceptance or clarification before lock",
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

            if admin_override:
                _check(
                    admin_override["visibility"] == "admin-only",
                    failures,
                    "admin_override_visibility",
                    context,
                    "admin inclusion overrides must remain admin-only",
                )
                _check(
                    admin_override["clientVisible"] is False,
                    failures,
                    "admin_override_public",
                    context,
                    "admin inclusion overrides must not be client-facing",
                )
                _check(
                    admin_override["curationOnly"] is True,
                    failures,
                    "admin_override_not_curation_only",
                    context,
                    "admin inclusion overrides should only affect curation visibility",
                )
                _check(
                    admin_override["doesNotOverrideRate"] is True,
                    failures,
                    "admin_override_rate_override",
                    context,
                    "admin inclusion overrides must not override talent-owned rates",
                )
                _check(
                    admin_override["doesNotOverrideTalentAcceptance"] is True,
                    failures,
                    "admin_override_acceptance_override",
                    context,
                    "admin inclusion overrides must not bypass talent acceptance",
                )
                _check(
                    admin_override["doesNotOverrideHardEligibility"] is True,
                    failures,
                    "admin_override_hard_eligibility_override",
                    context,
                    "admin inclusion overrides must not bypass hard eligibility constraints",
                )
                _check(
                    admin_override["requiresRateQuotedOutreach"] is True,
                    failures,
                    "admin_override_outreach_missing",
                    context,
                    "admin inclusion overrides must still go through rate-quoted outreach",
                )
                _check(
                    ADMIN_INCLUSION_OVERRIDE_TRIGGER in governance["exceptionTriggers"],
                    failures,
                    "admin_override_exception_missing",
                    context,
                    "admin inclusion overrides must trigger admin exception review",
                )
                _check(
                    rec["candidateSource"] in {
                        "admin_inclusion_override",
                        "algorithmic_with_admin_inclusion_override",
                    },
                    failures,
                    "admin_override_source_invalid",
                    context,
                    "override recommendations must carry an admin override candidate source",
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
                confirmation = rec["timing"]["confirmation"]
                _check(
                    confirmation["required"] is True,
                    failures,
                    "long_horizon_confirmation_missing",
                    context,
                    "long-horizon recommendations must include confirmation mechanics",
                )
                _check(
                    int(confirmation["checkpointDaysBeforeStart"]) > 0,
                    failures,
                    "long_horizon_checkpoint_missing",
                    context,
                    "long-horizon confirmation should include a checkpoint before start",
                )
                _check(
                    bool(confirmation["firmHoldRequires"]),
                    failures,
                    "long_horizon_firm_hold_requirements_missing",
                    context,
                    "long-horizon firm holds must list required confirmation signals",
                )
                _check(
                    confirmation["expiresWithoutConfirmation"] is True,
                    failures,
                    "long_horizon_hold_should_expire",
                    context,
                    "long-horizon holds should expire without confirmation signals",
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
                _check(
                    talent_advocacy["applies"] is True,
                    failures,
                    "actor_talent_advocacy_missing",
                    context,
                    "actor recommendations should carry the bounded Distinkt talent advocacy posture",
                )
                if legal_floor["agreementFloorStatus"] == "known":
                    _check(
                        int(rec["quote"]) >= int(legal_floor["agreementFloor"]),
                        failures,
                        "agreement_floor_violation",
                        context,
                        "actor quote must not fall below supplied published agreement rate card floor",
                    )
                    _check(
                        int(expected_range["low"]) >= int(legal_floor["agreementFloor"]),
                        failures,
                        "range_below_agreement_floor",
                        context,
                        "actor expected booking range must not dip below supplied published agreement rate card floor",
                    )
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

        recommendation_by_quote_id = {
            item["quoteLifecycle"]["quoteId"]: item
            for item in _recommendations(trace)
        }
        for decision in trace["clientDecisions"]:
            _check(
                decision.get("quote_id") in recommendation_by_quote_id,
                failures,
                "decision_quote_id_missing",
                f"{trace['projectId']} / {decision['talent_id']}",
                "client decisions must reference a locked quote id from the recommendation slate",
            )
            if decision.get("quote_id") in recommendation_by_quote_id:
                lifecycle = recommendation_by_quote_id[decision["quote_id"]]["quoteLifecycle"]
                _check(
                    int(decision["active_quote_version"]) == int(lifecycle["activeQuoteVersion"]),
                    failures,
                    "decision_active_quote_version_mismatch",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "client decisions must bind to the server-authoritative active quote version",
                )
                _check(
                    decision["dfos_handoff"]["dfosMayRecalculateQuote"] is False,
                    failures,
                    "decision_dfos_recalculation_allowed",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "decision handoff should preserve the DFOS no-recalculation contract",
                )
            if decision["status"] == "pending_hold":
                hold = decision.get("hold_management", {})
                _check(
                    hold.get("state") == "pending_confirmation",
                    failures,
                    "pending_hold_management_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "pending holds must include confirmation checkpoint and expiration mechanics",
                )
                _check(
                    bool(hold.get("firmHoldRequires")),
                    failures,
                    "pending_hold_requirements_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "pending holds must define what turns them into firm holds",
                )
                _check(
                    hold.get("expiresWithoutConfirmation") is True,
                    failures,
                    "pending_hold_expiration_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "pending holds must expire without confirmation",
                )
            if decision["status"] == HOLD_EXPIRED:
                hold = decision.get("hold_management", {})
                _check(
                    HOLD_EXPIRED_WARNING in decision["warnings"],
                    failures,
                    "hold_expired_warning_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "expired holds must include the explicit warning label",
                )
                _check(
                    hold.get("state") == "expired",
                    failures,
                    "hold_expired_management_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "expired holds must preserve hold-management state",
                )
                _check(
                    "fresh rate-quoted outreach" in hold.get("nextAction", ""),
                    failures,
                    "hold_expired_reactivation_rule_missing",
                    f"{trace['projectId']} / {decision['talent_id']}",
                    "expired holds must require fresh rate-quoted outreach before reactivation",
                )
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
