from __future__ import annotations


CLIENT_TRUST_TIERS = {"premium", "established", "emerging", "new"}


def _bool_flag(client: dict, key: str) -> bool:
    if key in client:
        return bool(client[key])
    breakdown = client.get("clientTrustScoreBreakdown", {})
    return bool(breakdown.get(key, False))


def client_trust_score(client: dict) -> int:
    if client.get("clientTrustScore") is not None:
        return max(0, min(int(client["clientTrustScore"]), 100))
    if client.get("client_trust_score") is not None:
        return max(0, min(int(client["client_trust_score"]), 100))
    if client.get("platform_trust_score") is not None:
        return max(0, min(int(round(float(client["platform_trust_score"]) * 100)), 100))
    if client.get("upstream_client_trust_metric") is not None:
        return max(
            0,
            min(int(round(float(client["upstream_client_trust_metric"]) * 100)), 100),
        )
    return 0


def client_trust_tier(client: dict) -> str:
    raw_tier = client.get("clientTrustTier") or client.get("client_trust_tier")
    if raw_tier:
        tier = str(raw_tier).lower()
        if tier in CLIENT_TRUST_TIERS:
            return tier

    score = client_trust_score(client)
    if score >= 71 or _bool_flag(client, "verifiedBrand"):
        return "premium"
    if score >= 41 or _bool_flag(client, "agencyAccount"):
        return "established"
    if score > 0:
        return "emerging"
    return "new"


def normalized_client_trust(client: dict) -> float:
    return client_trust_score(client) / 100.0


def completed_project_count(client: dict) -> int:
    if client.get("clientTrustScoreBreakdown", {}).get("completedProjectCount") is not None:
        return int(client["clientTrustScoreBreakdown"]["completedProjectCount"])
    return int(client.get("platform_completed_projects", 0))


def timing_platform_trust_tier(client: dict) -> str:
    score = normalized_client_trust(client)
    tier = client_trust_tier(client)
    completed_projects = completed_project_count(client)

    if tier == "premium" and completed_projects >= 4 and score >= 0.71:
        return "high_repeat"
    if tier in {"premium", "established"}:
        return "known"
    if tier == "emerging":
        return "limited_history"
    return "new_or_unproven"


def client_credibility_context(client: dict, project: dict | None = None) -> dict:
    breakdown = client.get("clientTrustScoreBreakdown", {})
    score = client_trust_score(client)
    tier = client_trust_tier(client)
    project_score = None
    project_score_source = None
    if project is not None:
        if project.get("projectCredibilityScore") is not None:
            project_score = max(0, min(int(project["projectCredibilityScore"]), 100))
            project_score_source = "main_site_project_credibility_score"
        elif project.get("project_commitment_confidence") is not None:
            project_score = max(
                0,
                min(int(round(float(project["project_commitment_confidence"]) * 100)), 100),
            )
            project_score_source = "fixture_project_commitment_confidence_proxy"

    return {
        "clientTrustScore": score,
        "clientTrustTier": tier,
        "source": client.get("clientTrustScoreSource", "main_site_clientScoring"),
        "timingPlatformTrustTier": timing_platform_trust_tier(client),
        "completedProjectCount": completed_project_count(client),
        "verifiedBrand": _bool_flag(client, "verifiedBrand"),
        "agencyAccount": _bool_flag(client, "agencyAccount"),
        "scoreBreakdown": breakdown,
        "projectCredibilityScore": project_score,
        "projectCredibilitySource": project_score_source,
    }
