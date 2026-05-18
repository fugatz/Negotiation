from __future__ import annotations

import argparse
import json
from pathlib import Path

from .admin_governance import build_admin_governance
from .ai_rationale import build_ai_rationales
from .behavior import cap_behavior_rate_delta, client_behavior_nudge, talent_behavior_nudge
from .common import FIXTURE_DIR
from .negotiation import apply_availability_commitment, simulate_availability_check, simulate_client_decision
from .outcome_calibration import propose_shadow_discretion
from .outcome_learning import build_cohort_learning, build_outcome_learning
from .policies import apply_nudges, build_slate, client_visible_price_state, overall_score
from .policy_config import active_policy_config_relative_path, configure_policy_config, policy_version
from .ranges import expected_booking_range, project_context
from .scoring import score_talent
from .timing import timing_nudge
from .validation import validate_report


def load_json(path: Path) -> list[dict]:
    with path.open() as handle:
        return json.load(handle)


def load_fixtures() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    return (
        load_json(FIXTURE_DIR / "talent.json"),
        load_json(FIXTURE_DIR / "clients.json"),
        load_json(FIXTURE_DIR / "projects.json"),
        load_json(FIXTURE_DIR / "outcomes.json"),
    )


def compact_recommendation(rec: dict, talent_by_id: dict) -> dict:
    talent = talent_by_id[rec["talent_id"]]
    return {
        "talent": talent["name"],
        "talentClass": rec["legal_floor"]["talentClass"],
        "role": talent.get("actor_role") or talent.get("production_role"),
        "lane": rec.get("lane", "Stress Test Candidate"),
        "quote": rec["final_quote"],
        "clientVisiblePriceState": rec.get("client_visible_price_state", "stress-test only"),
        "overallScore": rec.get("overall_score", round(overall_score(rec), 3)),
        "creativeFit": rec["creative_fit"],
        "priceFit": rec["price_fit"],
        "acceptanceProbability": rec["acceptance_probability"],
        "availabilityCheck": rec["availability_check"],
        "legalFloor": rec["legal_floor"],
        "expectedBookingRange": rec["expected_booking_range"],
        "marketHealth": {
            "score": rec["market_health_score"],
            "flags": rec.get("market_health_flags", []),
        },
        "timing": {
            "horizon": rec["timing_nudge"]["horizon"],
            "platformTrustTier": rec["timing_nudge"]["platform_trust_tier"],
            "rateDelta": round(rec["timing_nudge"]["rate_delta"], 3),
            "confidenceDelta": round(rec["timing_nudge"]["confidence_delta"], 3),
            "holdPolicy": rec["timing_nudge"]["hold_policy"],
            "reason": rec["timing_nudge"]["reason"],
        },
        "behavior": {
            "talentRateDelta": round(rec["talent_behavior_nudge"]["rate_delta"], 3),
            "clientRateDelta": round(rec["client_behavior_nudge"]["rate_delta"], 3),
            "combinedBehaviorRateDelta": round(
                cap_behavior_rate_delta(
                    rec["talent_behavior_nudge"]["rate_delta"],
                    rec["client_behavior_nudge"]["rate_delta"],
                ),
                3,
            ),
            "talentReason": rec["talent_behavior_nudge"]["reason"],
            "clientReason": rec["client_behavior_nudge"]["reason"],
            "talentSource": rec["talent_behavior_nudge"]["source"],
            "clientSource": rec["client_behavior_nudge"]["source"],
        },
        "aiRationales": rec["ai_rationales"],
        "adminGovernance": build_admin_governance(rec),
    }


def simulate_project(project: dict, talent: list[dict], clients_by_id: dict, outcomes: list[dict]) -> dict:
    client = clients_by_id[project["client_id"]]
    talent_by_id = {item["id"]: item for item in talent}
    timing = timing_nudge(project, client)

    recommendations: list[dict] = []
    excluded: list[dict] = []

    for person in talent:
        base_score = score_talent(person, project)
        adjusted = apply_nudges(
            base_score,
            person,
            timing,
            talent_behavior_nudge(person),
            client_behavior_nudge(client),
        )
        if adjusted["eligible"]:
            adjusted["expected_booking_range"] = expected_booking_range(project, person, adjusted)
            availability_check = simulate_availability_check(project, person, adjusted)
            adjusted = apply_availability_commitment(adjusted, availability_check)
            adjusted["expected_booking_range"] = expected_booking_range(project, person, adjusted)
            adjusted["availability_check"]["committedRange"] = adjusted["expected_booking_range"]
            discretion = propose_shadow_discretion(project, person, adjusted, outcomes)
            adjusted["ai_discretion"] = discretion
            adjusted["ai_rationales"] = build_ai_rationales(
                project,
                client,
                person,
                adjusted,
                discretion,
            )
            recommendations.append(adjusted)
        else:
            excluded.append(
                {
                    "talent": person["name"],
                    "reasons": adjusted["eligibility_reasons"],
                }
            )

    slate = build_slate(recommendations, talent_by_id, project)
    rec_by_talent_id = {item["talent_id"]: item for item in recommendations}

    stress_shortlist = []
    for talent_id in project.get("stress_shortlist_ids", []):
        rec = rec_by_talent_id.get(talent_id)
        if rec:
            item = dict(rec)
            item["client_visible_price_state"] = client_visible_price_state(item, project)
            item["overall_score"] = round(overall_score(item), 3)
            stress_shortlist.append(item)

    negotiation_candidates = slate[:2]
    seen = {item["talent_id"] for item in negotiation_candidates}
    for item in stress_shortlist:
        if item["talent_id"] not in seen:
            negotiation_candidates.append(item)
            seen.add(item["talent_id"])

    client_decisions = [
        simulate_client_decision(project, talent_by_id[item["talent_id"]], item)
        for item in negotiation_candidates
    ]
    outcome_learning = build_outcome_learning(
        project,
        talent_by_id,
        negotiation_candidates,
        client_decisions,
    )
    booked = next((item for item in client_decisions if item["status"] == "booked"), None)

    warnings = []
    for availability_check in [item["availability_check"] for item in negotiation_candidates]:
        warnings.extend(availability_check["warnings"])
    for item in negotiation_candidates:
        warnings.extend(item["legal_floor"].get("warnings", []))
    for client_decision in client_decisions:
        warnings.extend(client_decision["warnings"])

    return {
        "project": project["name"],
        "projectId": project["id"],
        "client": client["name"],
        "budget": project["budget"],
        "projectContext": project_context(project),
        "budgetType": project["budget_type"],
        "leadTimeDays": project["lead_time_days"],
        "timingHorizon": timing["horizon"],
        "eligibleTalentCount": len(recommendations),
        "excluded": excluded,
        "recommendedSlate": [compact_recommendation(item, talent_by_id) for item in slate],
        "stressShortlist": [compact_recommendation(item, talent_by_id) for item in stress_shortlist],
        "availabilityChecks": [item["availability_check"] for item in negotiation_candidates],
        "clientDecisions": client_decisions,
        "outcomeLearning": outcome_learning,
        "outcome": booked["status"] if booked else (client_decisions[0]["status"] if client_decisions else "no_viable_slate"),
        "warnings": sorted(set(warnings)),
    }


def aggregate_metrics(traces: list[dict]) -> dict:
    booked = sum(1 for trace in traces if trace["outcome"] == "booked")
    long_horizon = [trace for trace in traces if trace["timingHorizon"] == "long_horizon"]
    warnings = [warning for trace in traces for warning in trace["warnings"]]
    behavior_changed = 0
    timing_changed = 0
    discretion_deltas: list[float] = []
    rationale_count = 0
    brand_rationale_count = 0
    talent_job_specific_rationale_count = 0
    admin_approval_required_count = 0
    mature_autonomy_candidate_count = 0
    admin_exception_triggers: list[str] = []
    market_health_flags: list[str] = []
    availability_check_count = 0
    pre_presentation_counter_count = 0
    minimum_wage_floor_applied_count = 0
    minimum_wage_floor_unknown_count = 0
    expected_range_count = 0
    actualized_record_count = 0
    actualized_above_range_count = 0
    talent_guidance_count = 0
    actualization_lifts: list[float] = []
    leakage_count = 0
    human_review_count = 0

    for trace in traces:
        outcome_summary = trace["outcomeLearning"]["summary"]
        actualized_record_count += int(outcome_summary["actualizedRecordCount"])
        actualized_above_range_count += int(outcome_summary["actualizedAboveExpectedRangeCount"])
        talent_guidance_count += int(outcome_summary["talentGuidanceCount"])
        for record in trace["outcomeLearning"]["actualizationRecords"]:
            if record["actualizedCost"] is not None:
                locked_quote = max(int(record["lockedQuote"]), 1)
                actualization_lifts.append(
                    (int(record["actualizedCost"]) - int(record["lockedQuote"])) / locked_quote
                )
        traced_recommendations = trace["recommendedSlate"] + trace.get("stressShortlist", [])
        for rec in traced_recommendations:
            if rec["behavior"]["combinedBehaviorRateDelta"] != 0:
                behavior_changed += 1
            if rec["timing"]["rateDelta"] != 0 or rec["timing"]["confidenceDelta"] != 0:
                timing_changed += 1
            market_health_flags.extend(rec["marketHealth"]["flags"])
            availability_check_count += 1
            if rec["availabilityCheck"]["status"] == "countered_before_client_presentation":
                pre_presentation_counter_count += 1
            legal_floor = rec["legalFloor"]
            if legal_floor["basis"] == "local_minimum_wage":
                minimum_wage_floor_applied_count += 1
            if legal_floor["minimumWageStatus"] == "unknown":
                minimum_wage_floor_unknown_count += 1
            if rec.get("expectedBookingRange"):
                expected_range_count += 1
            rationales = rec["aiRationales"]
            admin_rationale = rationales["adminPricingRationale"]
            brand_rationale = rationales["brandFacingRationale"]
            talent_rationale = rationales["talentFacingRationale"]
            rationale_count += 1
            brand_rationale_count += 1
            discretion_deltas.append(abs(float(admin_rationale["discretionDelta"])))
            if brand_rationale["leakageWarnings"]:
                leakage_count += 1
            if talent_rationale.get("available"):
                talent_job_specific_rationale_count += 1
            if admin_rationale["humanReviewRecommended"] or brand_rationale["humanReviewRecommended"]:
                human_review_count += 1
            governance = rec["adminGovernance"]
            if governance["approvalRequired"]:
                admin_approval_required_count += 1
            if governance["matureAutonomyCandidate"]:
                mature_autonomy_candidate_count += 1
            admin_exception_triggers.extend(governance["exceptionTriggers"])

    total_recommendations = sum(
        len(trace["recommendedSlate"]) + len(trace.get("stressShortlist", []))
        for trace in traces
    ) or 1
    max_discretion = max(discretion_deltas) if discretion_deltas else 0.0
    avg_discretion = sum(discretion_deltas) / len(discretion_deltas) if discretion_deltas else 0.0
    avg_actualization_lift = (
        sum(actualization_lifts) / len(actualization_lifts)
        if actualization_lifts
        else 0.0
    )

    return {
        "scenarioCount": len(traces),
        "bookedCount": booked,
        "bookingRate": round(booked / max(len(traces), 1), 3),
        "longHorizonScenarioCount": len(long_horizon),
        "behaviorNudgeShareOfRecommendations": round(behavior_changed / total_recommendations, 3),
        "timingNudgeShareOfRecommendations": round(timing_changed / total_recommendations, 3),
        "aiRationaleCount": rationale_count,
        "brandFacingRationaleCount": brand_rationale_count,
        "brandFacingRationaleLeakageCount": leakage_count,
        "talentFacingJobSpecificRationaleCount": talent_job_specific_rationale_count,
        "adminApprovalRequiredCount": admin_approval_required_count,
        "matureAutonomyCandidateCount": mature_autonomy_candidate_count,
        "availabilityCheckCount": availability_check_count,
        "prePresentationTalentCounterCount": pre_presentation_counter_count,
        "minimumWageFloorAppliedCount": minimum_wage_floor_applied_count,
        "minimumWageFloorUnknownCount": minimum_wage_floor_unknown_count,
        "expectedBookingRangeCount": expected_range_count,
        "actualizedRecordCount": actualized_record_count,
        "actualizedAboveExpectedRangeCount": actualized_above_range_count,
        "talentGuidanceCount": talent_guidance_count,
        "averageActualizationLift": round(avg_actualization_lift, 4),
        "aiHumanReviewShareOfRecommendations": round(human_review_count / total_recommendations, 3),
        "averageAbsoluteShadowDiscretionDelta": round(avg_discretion, 4),
        "maxAbsoluteShadowDiscretionDelta": round(max_discretion, 4),
        "adminExceptionTriggerCounts": {
            trigger: admin_exception_triggers.count(trigger)
            for trigger in sorted(set(admin_exception_triggers))
        },
        "marketHealthFlagCounts": {
            flag: market_health_flags.count(flag)
            for flag in sorted(set(market_health_flags))
        },
        "warningCounts": {warning: warnings.count(warning) for warning in sorted(set(warnings))},
    }


def run(project_id: str | None = None, policy_path: str | None = None) -> dict:
    if policy_path:
        configure_policy_config(policy_path)

    talent, clients, projects, outcomes = load_fixtures()
    clients_by_id = {client["id"]: client for client in clients}

    selected = projects
    if project_id:
        selected = [project for project in projects if project["id"] == project_id]
        if not selected:
            raise SystemExit(f"Unknown project id: {project_id}")

    traces = [simulate_project(project, talent, clients_by_id, outcomes) for project in selected]
    cohort_learning = build_cohort_learning(traces)
    report = {
        "policy": policy_version(),
        "policyConfigPath": active_policy_config_relative_path(),
        "traces": traces,
        "cohortLearning": cohort_learning,
        "metrics": aggregate_metrics(traces),
    }
    report["metrics"]["cohortCount"] = cohort_learning["summary"]["cohortCount"]
    report["metrics"]["cohortGuidanceCount"] = cohort_learning["summary"]["cohortGuidanceCount"]
    report["validation"] = validate_report(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Distinkt pricing simulation scenarios.")
    parser.add_argument("--policy", help="Optional policy config or variant JSON path")
    parser.add_argument("--project", help="Run a single project id from simulation/fixtures/projects.json")
    parser.add_argument("--out", help="Optional path to write the JSON report")
    parser.add_argument(
        "--fail-on-validation",
        action="store_true",
        help="Exit nonzero if validation fails.",
    )
    args = parser.parse_args()

    report = run(args.project, args.policy)
    encoded = json.dumps(report, indent=2)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded + "\n")

    print(encoded)

    if args.fail_on_validation and report["validation"]["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
