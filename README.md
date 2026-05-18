# Distinkt Pricing & Deal Intelligence Exploration

This repository is an exploration workspace for Distinkt's pricing and deal intelligence system.

The project should reason through marketplace incentives, pricing structures, negotiation dynamics,
and equilibrium risks before touching production platform code.

## Current Focus

1. Phase 1: conceptual architecture and incentive design
2. Phase 2: standalone simulation engine with synthetic talent and project fixtures
3. Phase 3: edge case and abuse-pattern stress testing
4. Phase 4: controlled shadow-mode integration

## Guiding Principle

Distinkt should feel like intelligent representation and high-trust matchmaking, not a commodity
freelancer marketplace or an opaque agency system.

## Documents

- [Phase 1 Conceptual Architecture](docs/phase-1-conceptual-architecture.md)
- [Simulation Blueprint](docs/simulation-blueprint.md)
- [Project And Talent Class Pricing Rules](docs/project-class-pricing-rules.md)
- [Phase 2 Findings Report](simulation/reports/phase-2-findings.md)
- [Policy Comparison Report](simulation/reports/policy-comparison.md)

## Simulation

Run the standalone dry-run simulation:

```bash
python3 -m simulation.src.runner
```

Run with validation:

```bash
python3 -m simulation.src.runner --fail-on-validation
```

Admin-tweakable dry-run settings live in `simulation/config/policy.json`.

Run with a policy variant:

```bash
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json
```
