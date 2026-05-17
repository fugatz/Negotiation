# Policy Comparison Report

Generated from dry runs on May 17, 2026.

Compared policies:

- Base: `phase-2-admin-config-v1`
- Variant: `phase-2-stricter-market-health-v1`

Source commands:

```bash
python3 -m simulation.src.runner --fail-on-validation
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json --fail-on-validation
```

## Summary

The stricter market-health variant is directionally useful, but it is not sufficient by itself. It reduces
race-to-bottom visibility in the slate by applying stronger ranking penalties, yet the low-rate candidate
can still book in the race-to-bottom stress path when higher-quality options exceed client capacity.

The interpretation is important:

- stricter ranking helps presentation quality
- stricter ranking does not solve client budget reality
- budget-driven commoditization needs an outcome-level guardrail, not only a ranking penalty

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
| Scenarios | 8 | 8 | Same fixture set. |
| Booked scenarios | 5 | 5 | Stricter ranking did not reduce booking count. |
| Booking rate | 62.5% | 62.5% | No aggregate conversion change in this fixture set. |
| Availability checks | 34 | 34 | Same recommendation volume. |
| Pre-presentation counters | 4 | 4 | Market-health policy does not affect counter behavior. |
| Brand-facing leakage count | 0 | 0 | Audience separation remains intact. |
| Talent-facing job-specific rationales | 0 | 0 | No talent pricing-rationale leakage. |
| Human review share | 44.1% | 47.1% | Stricter policy slightly increases admin attention. |
| Mature autonomy candidates | 13 | 13 | No autonomy readiness gain yet. |
| Race-to-bottom flags in traced recs | 3 | 2 | Stricter penalties demote at least one flagged candidate out of traced slate. |
| Market-health guardrail triggers | 3 | 2 | Fewer flagged recs reach reviewed recommendation surfaces. |
| Outside-budget triggers | 14 | 14 | Budget mismatch is unchanged. |
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
fourth. However, the stress harness still tests the candidate, and the candidate still books after
higher-quality options fail budget capacity.

Read:

- the ranking penalty is working
- the low-rate booking exploit still exists
- the missing guardrail is at the client decision/outcome layer, not only the recommendation ranking layer

Recommended change:

- add a warning or outcome state when the only bookable option is a low-rate market-health risk
- consider requiring admin approval, scope calibration, or budget education before presenting that as a
  normal successful booking

### Other Scenarios

Firm food, flexible beauty, prestige editorial, long-horizon, and bad-faith repricing scenarios have the
same high-level outcomes under both policies.

Read:

- stricter market-health settings are narrowly targeted
- timing, behavior, AI rationale, and quote-lock rules remain stable
- this is good; policy variants should have focused blast radius

## Recommendation

Keep the stricter market-health variant as the better default for Phase 3 exploration, but do not treat it
as sufficient.

Recommended next policy variant:

```text
phase-3-budget-health-v1
```

Suggested changes:

- inherit from `phase-2-stricter-market-health-v1`
- add an outcome warning for budget-driven commodity bookings
- optionally change outcome from `booked` to `booked_with_market_health_warning`
- add a firm-budget rule that detects when all higher-fit recommendations fail capacity and only a
  low-rate flagged candidate books
- keep race-to-bottom ranking penalties at the stricter level until more stress data exists

## Decision Notes

The stricter variant should not simply block low-rate talent. The goal is not to punish affordable talent
or remove emerging people from consideration. The healthier rule is narrower:

- affordable talent can win when fit is real and the project is appropriately scoped
- low price should not be the hidden reason a weak-fit option wins
- when the system sees that pattern, it should slow down, educate, or require admin review

That preserves access for emerging talent while protecting Distinkt from becoming a cheapest-available
marketplace.
