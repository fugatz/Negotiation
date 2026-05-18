# Distinkt Deal Simulation

This is a standalone dry-run environment for testing late-stage pricing, timing, behavior, and
negotiation policies before any production integration.

The simulation is intentionally small and inspectable. It uses synthetic fixtures and deterministic
rules so policy changes are easy to understand.

Production boundary: this layer is expected to run after upstream matching has identified candidate
talent, but before rate-quoted WhatsApp/email outreach is complete. The simulator's eligibility checks
are a small stand-in for known candidate constraints and talent responses. The main purpose here is to
compute the project-specific rate, include it in outreach to matched talent, and build the client slate
only from talent-approved locked rates.

Admin-tweakable dry-run settings live in `simulation/config/policy.json`. The config currently owns
timing thresholds, behavior caps, AI discretion caps, market-health review flags, ranking penalties,
and launch approval settings.

## Run

From the repository root:

```bash
python3 -m simulation.src.runner
```

Write a JSON report:

```bash
python3 -m simulation.src.runner --out simulation/reports/sample-runs/latest.json
```

Run the report with policy validation:

```bash
python3 -m simulation.src.runner --fail-on-validation
```

Run with a policy variant:

```bash
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json
```

Run one scenario:

```bash
python3 -m simulation.src.runner --project last_minute_automotive
```

## Reports

- [Phase 2 Findings Report](reports/phase-2-findings.md)
- [Policy Comparison Report](reports/policy-comparison.md)
- [Outcome Learning Report](reports/outcome-learning.md)

## Current Scope

- synthetic rate-quoted outreach responses
- creative, practical, pricing, trust, and market-health scoring
- small timing-horizon nudges
- small talent and client behavior nudges
- deterministic admin-only AI pricing rationale over computed nudges
- separate brand-facing AI match rationale with no pricing or hidden-score logic
- no talent-facing job-specific pricing rationale from this layer
- launch-mode admin approval state and bounded setting-tweak controls
- validation checks for rationale leakage, approval state, discretion caps, behavior caps, and timing rules
- nullable local minimum wage smoke checks for actor legal floors
- expected booking ranges with assumptions and actualization triggers
- outcome-learning records that compare locked quotes, booking outcomes, and actualized costs
- market-health flags for race-to-bottom and price-led recommendation risk
- pre-presentation talent outreach checks at proposed project rates
- shadow-mode outcome-calibrated discretion deltas
- upstream-score placeholders for actor readiness, talent reliability, and client trust
- curated recommendation lanes
- simple deterministic client decision outcomes against locked presentation quotes
- scenario traces for manual review

This is not production pricing logic.
