from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ai_rationale import build_pricing_rationale
from .behavior import cap_behavior_rate_delta, client_behavior_nudge, talent_behavior_nudge
from .common import FIXTURE_DIR
from .negotiation import simulate_negotiation
from .outcome_calibration import propose_shadow_discretion
from .policies import apply_nudges, build_slate, client_visible_price_state, overall_score
from .scoring import score_talent
from .timing import timing_nudge


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
        "lane": rec.get("lane", "Stress Test Candidate"),
        "quote": rec["final_quote"],
        "clientVisiblePriceState": rec.get("client_visible_price_state", "stress-test only"),
        "overallScore": rec.get("overall_score", round(overall_score(rec), 3)),
        "creativeFit": rec["creative_fit"],
        "priceFit": rec["price_fit"],
        "acceptanceProbability": rec["acceptance_probability"],
        "timing": {
            "horizon": rec["timing_nudge"]["horizon"],
            "rateDelta": round(rec["timing_nudge"]["rate_delta"], 3),
            "confidenceDelta": round(rec["timing_nudge"]["confidence_delta"], 3),
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
        },
        "aiPricingRationale": rec["ai_pricing_rationale"],
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
        discretion = propose_shadow_discretion(project, person, adjusted, outcomes)
        adjusted["ai_discretion"] = discretion
        adjusted["ai_pricing_rationale"] = build_pricing_rationale(
            project,
            client,
            person,
            adjusted,
            discretion,
        )
        if adjusted["eligible"]:
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

    negotiations = [
        simulate_negotiation(project, talent_by_id[item["talent_id"]], item)
        for item in negotiation_candidates
    ]
    booked = next((item for item in negotiations if item["status"] == "booked"), None)

    warnings = []
    for negotiation in negotiations:
        warnings.extend(negotiation["warnings"])

    return {
        "project": project["name"],
        "projectId": project["id"],
        "client": client["name"],
        "budget": project["budget"],
        "budgetType": project["budget_type"],
        "leadTimeDays": project["lead_time_days"],
        "timingHorizon": timing["horizon"],
        "eligibleTalentCount": len(recommendations),
        "excluded": excluded,
        "recommendedSlate": [compact_recommendation(item, talent_by_id) for item in slate],
        "stressShortlist": [compact_recommendation(item, talent_by_id) for item in stress_shortlist],
        "negotiations": negotiations,
        "outcome": booked["status"] if booked else (negotiations[0]["status"] if negotiations else "no_viable_slate"),
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
    leakage_count = 0
    human_review_count = 0

    for trace in traces:
        traced_recommendations = trace["recommendedSlate"] + trace.get("stressShortlist", [])
        for rec in traced_recommendations:
            if rec["behavior"]["combinedBehaviorRateDelta"] != 0:
                behavior_changed += 1
            if rec["timing"]["rateDelta"] != 0 or rec["timing"]["confidenceDelta"] != 0:
                timing_changed += 1
            rationale = rec["aiPricingRationale"]
            rationale_count += 1
            discretion_deltas.append(abs(float(rationale["discretionDelta"])))
            if rationale["leakageWarnings"]:
                leakage_count += 1
            if rationale["humanReviewRecommended"]:
                human_review_count += 1

    total_recommendations = sum(
        len(trace["recommendedSlate"]) + len(trace.get("stressShortlist", []))
        for trace in traces
    ) or 1
    max_discretion = max(discretion_deltas) if discretion_deltas else 0.0
    avg_discretion = sum(discretion_deltas) / len(discretion_deltas) if discretion_deltas else 0.0

    return {
        "scenarioCount": len(traces),
        "bookedCount": booked,
        "bookingRate": round(booked / max(len(traces), 1), 3),
        "longHorizonScenarioCount": len(long_horizon),
        "behaviorNudgeShareOfRecommendations": round(behavior_changed / total_recommendations, 3),
        "timingNudgeShareOfRecommendations": round(timing_changed / total_recommendations, 3),
        "aiRationaleCount": rationale_count,
        "aiRationaleLeakageCount": leakage_count,
        "aiHumanReviewShareOfRecommendations": round(human_review_count / total_recommendations, 3),
        "averageAbsoluteShadowDiscretionDelta": round(avg_discretion, 4),
        "maxAbsoluteShadowDiscretionDelta": round(max_discretion, 4),
        "warningCounts": {warning: warnings.count(warning) for warning in sorted(set(warnings))},
    }


def run(project_id: str | None = None) -> dict:
    talent, clients, projects, outcomes = load_fixtures()
    clients_by_id = {client["id"]: client for client in clients}

    selected = projects
    if project_id:
        selected = [project for project in projects if project["id"] == project_id]
        if not selected:
            raise SystemExit(f"Unknown project id: {project_id}")

    traces = [simulate_project(project, talent, clients_by_id, outcomes) for project in selected]
    return {
        "policy": "phase-2-initial-dry-run",
        "traces": traces,
        "metrics": aggregate_metrics(traces),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Distinkt pricing simulation scenarios.")
    parser.add_argument("--project", help="Run a single project id from simulation/fixtures/projects.json")
    parser.add_argument("--out", help="Optional path to write the JSON report")
    args = parser.parse_args()

    report = run(args.project)
    encoded = json.dumps(report, indent=2)

    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded + "\n")

    print(encoded)


if __name__ == "__main__":
    main()
