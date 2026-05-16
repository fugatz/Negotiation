# Distinkt Deal Simulation

This is a standalone dry-run environment for testing pricing, timing, behavior, and negotiation
policies before any production integration.

The simulation is intentionally small and inspectable. It uses synthetic fixtures and deterministic
rules so policy changes are easy to understand.

## Run

From the repository root:

```bash
python3 -m simulation.src.runner
```

Write a JSON report:

```bash
python3 -m simulation.src.runner --out simulation/reports/sample-runs/latest.json
```

Run one scenario:

```bash
python3 -m simulation.src.runner --project last_minute_automotive
```

## Current Scope

- hard eligibility checks
- creative, practical, pricing, trust, and market-health scoring
- small timing-horizon nudges
- small talent and client behavior nudges
- curated recommendation lanes
- simple deterministic negotiation outcomes
- scenario traces for manual review

This is not production pricing logic.
