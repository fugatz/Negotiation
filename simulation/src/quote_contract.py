from __future__ import annotations

import hashlib
import json

from .policy_config import active_policy_config_relative_path, policy_version


def _snapshot_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _event(event_type: str, quote_id: str, quote_version: int, actor: str, reason_code: str) -> dict:
    return {
        "eventType": event_type,
        "quoteId": quote_id,
        "quoteVersion": quote_version,
        "actor": actor,
        "reasonCode": reason_code,
        "timestamp": "simulation_clock",
        "policyVersion": policy_version(),
    }


def _talent_response_event(status: str) -> tuple[str, str]:
    if status == "countered_before_client_presentation":
        return "talent_countered_before_presentation", "talent_countered_inside_outreach_and_lock"
    if status == "accepted_after_scope_confirmation":
        return "talent_requested_clarification", "talent_requested_scope_confirmation"
    return "talent_accepted_quote", "accepted_project_specific_rate"


def build_quote_contract(project: dict, client: dict, talent: dict, rec: dict) -> dict:
    quote_version = 1
    quote_id = f"quote_{project['id']}__{talent['id']}__v{quote_version}"
    availability = rec["availability_check"]
    response_event, response_reason = _talent_response_event(availability["status"])
    snapshot = {
        "projectId": project["id"],
        "clientId": client["id"],
        "talentId": talent["id"],
        "projectCredibilityScore": project.get("projectCredibilityScore")
        or project.get("project_credibility_score"),
        "projectReadinessTier": project.get("projectReadinessTier")
        or project.get("project_readiness_tier"),
        "clientTrustScore": client.get("clientTrustScore"),
        "clientTrustTier": client.get("clientTrustTier"),
        "brandPrestigeTier": client.get("brandPrestigeTier"),
        "targetRate": talent.get("target_rate"),
        "quote": rec["final_quote"],
        "budgetContext": rec.get("budget_context"),
        "expectedBookingRange": rec["expected_booking_range"],
        "timingNudge": rec["timing_nudge"],
        "talentBehaviorNudge": rec["talent_behavior_nudge"],
        "clientBehaviorNudge": rec["client_behavior_nudge"],
    }
    audit_events = [
        _event("quote_generated", quote_id, quote_version, "pricing_engine", "computed_project_rate"),
        _event("quote_sent_to_talent", quote_id, quote_version, "main_site", "outreach_and_lock"),
        _event(response_event, quote_id, quote_version, "talent", response_reason),
    ]
    if response_event == "talent_requested_clarification":
        audit_events.append(
            _event(
                "talent_accepted_quote",
                quote_id,
                quote_version,
                "talent",
                "accepted_after_scope_confirmation",
            )
        )
    audit_events.extend(
        [
            _event("quote_locked", quote_id, quote_version, "main_site", "accepted_before_client_visibility"),
            _event("quote_presented_to_client", quote_id, quote_version, "main_site", "client_slate_visible"),
        ]
    )

    return {
        "quoteId": quote_id,
        "quoteVersion": quote_version,
        "activeQuoteVersion": quote_version,
        "quoteState": "locked",
        "sourceOfTruth": "server_authoritative_active_quote",
        "policyVersion": policy_version(),
        "policyConfigPath": active_policy_config_relative_path(),
        "inputSnapshotHash": _snapshot_hash(snapshot),
        "lockedGrossQuote": int(rec["final_quote"]),
        "dfosHandoff": {
            "source": "locked_gross_quote",
            "lockedGrossQuote": int(rec["final_quote"]),
            "dfosMayRecalculateQuote": False,
            "commissionCapHandledDownstream": True,
            "notes": "DFOS consumes the locked gross quote and applies downstream commission rules.",
        },
        "auditEvents": audit_events,
    }
