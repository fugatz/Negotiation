# Policy Comparison Report

Generated from dry runs on May 19, 2026.

Compared policies:

- Base: `phase-3-hold-expiration-v1`
- Variant: `phase-3-hold-expiration-stricter-market-health-v1`

Source commands:

```bash
python3 -m simulation.src.runner --fail-on-validation
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json --fail-on-validation
```

## Summary

The stricter market-health variant is directionally useful, but it is not sufficient by itself. It reduces
race-to-bottom visibility in the slate by applying stronger ranking penalties, yet the low-rate candidate
can still close in the race-to-bottom stress path when higher-quality options exceed client capacity. The
new budget-health layer now labels that close as `booked_with_market_health_warning`.
All-budget-gap paths now become `needs_scope_calibration`, so structurally underfunded projects are
separated from ordinary candidate-level budget gaps.
Long-horizon pending holds now include confirmation checkpoints, hold expiration, and firm-hold
requirements.
Missed checkpoints now produce `hold_expired`, which releases the hold and requires fresh rate-quoted
outreach before reactivation.
Admin-curated inclusion overrides now add a separate manual curation surface without changing the
talent-owned rate or bypassing rate-quoted outreach.

The interpretation is important:

- stricter ranking helps presentation quality
- stricter ranking does not solve client budget reality
- budget-driven commoditization now has an outcome-level warning, not only a ranking penalty

## Policy Differences

| Setting | Base | Stricter Variant |
| --- | ---: | ---: |
| Market-health review score threshold | 0.60 | 0.68 |
| `race_to_bottom_risk` ranking penalty | 0.12 | 0.18 |
| `price_led_recommendation_risk` ranking penalty | 0.06 | 0.10 |

All other config inherits from the base policy.

## Aggregate Comparison

| Metric | Base | Stricter | Read |
| --- | ---: | ---: | --- |
| Validation | pass | pass | No policy validity regressions. |
| Scenarios | 13 | 13 | Same fixture set. |
| Booked scenarios | 8 | 8 | Stricter ranking did not reduce booking count. |
| Booking rate | 61.5% | 61.5% | New missed-checkpoint fixture lowers aggregate conversion. |
| Availability checks | 51 | 51 | Same recommendation volume including the manual override candidate. |
| Pre-presentation counters | 4 | 4 | Market-health policy does not affect counter behavior. |
| Brand-facing leakage count | 0 | 0 | Audience separation remains intact. |
| Talent-facing job-specific rationales | 0 | 0 | No talent pricing-rationale leakage. |
| Human review share | 33.3% | 35.3% | Stricter policy slightly increases admin attention. |
| Mature autonomy candidates | 23 | 23 | No autonomy readiness gain yet. |
| Admin inclusion overrides | 1 | 1 | Manual curation is policy-stable across variants. |
| Pending holds | 2 | 2 | Long-horizon work stays out of normal booking flow. |
| Confirmation checkpoints | 6 | 6 | Pending and expired holds carry checkpoint plans. |
| Hold expirations | 6 | 6 | Pending and expired holds expire without confirmation signals. |
| Expired holds | 1 | 1 | Missed checkpoint fixture releases the hold. |
| Budget-health warnings | 1 | 1 | Race-to-bottom stress booking is now labeled rather than treated as clean. |
| Scope-calibration outcomes | 2 | 2 | Prestige and compliance-floor cases require budget/scope recalibration. |
| Race-to-bottom flags in traced recs | 3 | 2 | Stricter penalties demote at least one flagged candidate out of traced slate. |
| Market-health guardrail triggers | 3 | 2 | Fewer flagged recs reach reviewed recommendation surfaces. |
| Outside-budget triggers | 17 | 17 | Budget mismatch is unchanged. |
| Max shadow AI discretion | 1.0% | 1.0% | AI discretion remains capped and shadow-only. |

## Scenario-Level Differences

### Last-Minute Automotive Shoot

Base policy includes the Low-Rate Fast Responder in the fourth slate position with a
`race_to_bottom_risk` flag. The stricter variant demotes that candidate out of the top four and replaces
the slot with Volatile Rep-Managed Talent.

Read:

- stricter market-health ranking does reduce cheap-option visibility
- the replacement candidate carries admin-review friction, so stricter ranking can trade one risk for
  another
- this is acceptable in simulation, but Phase 3 should test broader slates where there are more than two
  imperfect alternatives

### Race-To-Bottom Social Content Test

Base policy ranks the Low-Rate Fast Responder second. The stricter variant pushes that candidate to
fourth. However, the stress harness still tests the candidate, and the candidate still closes after
higher-quality options fail budget capacity. The difference now is that the final outcome is
`booked_with_market_health_warning`.

Read:

- the ranking penalty is working
- the low-rate booking path still exists, but it is now explicitly labeled
- the outcome layer can distinguish conversion from marketplace health

Recommended follow-up:

- decide when repeated budget-health warnings should become `needs_scope_calibration`
- consider requiring budget education before presenting a warning-labeled option as a normal success path

### Other Scenarios

Firm food, flexible beauty, $500k+ beauty, $1M+ automotive, prestige editorial, long-horizon, minimum
wage, and bad-faith repricing scenarios have the same high-level outcomes under both policies. Prestige
and the minimum-wage smoke case resolve as `needs_scope_calibration`; the missed-checkpoint fixture
resolves as `hold_expired` under both policies.

Flexible beauty now also carries one admin-curated inclusion override: Premium Food Tabletop Director.
That candidate appears in the admin override slate at a locked talent-approved quote, remains outside
the stated budget, and fails budget capacity under both policies. This confirms the override affects
visibility, not rate authority.

Read:

- stricter market-health settings are narrowly targeted
- timing, behavior, AI rationale, and quote-lock rules remain stable
- this is good; policy variants should have focused blast radius

## Recommendation

Keep the stricter market-health variant as the better default for Phase 3 exploration, but do not treat it
as sufficient.

Recommended next policy variant:

```text
phase-3-warning-cluster-stress-v1
```

Suggested changes:

- inherit from `phase-3-hold-expiration-stricter-market-health-v1`
- add repeated-client stress fixtures for budget-health warnings and scope calibration
- add late-scope-change long-horizon fixtures after confirmation
- define when `needs_scope_calibration` becomes budget education, scope reduction, or client-side budget revision
- track repeated warning patterns by client and project type
- keep race-to-bottom ranking penalties at the stricter level until more stress data exists

## Decision Notes

The stricter variant should not simply block low-rate talent. The goal is not to punish affordable talent
or remove emerging people from consideration. The healthier rule is narrower:

- affordable talent can win when fit is real and the project is appropriately scoped
- low price should not be the hidden reason a weak-fit option wins
- when the system sees that pattern, it should slow down, educate, or require admin review

That preserves access for emerging talent while protecting Distinkt from becoming a cheapest-available
marketplace.
