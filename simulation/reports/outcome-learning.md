# Outcome Learning Report

Generated from dry runs on May 18, 2026.

Source commands:

```bash
python3 -m simulation.src.runner --fail-on-validation
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json --fail-on-validation
```

## Executive Read

Outcome learning now runs after client decision simulation. It compares the locked talent-approved quote
against the expected booking range, applies event-based actualization, and produces two separate signals:

- admin calibration notes for range width, assumptions, and formula pressure
- optional talent guidance that never changes rates automatically

The important boundary is intact: outcome data is guidance, not pricing authority. Talent-owned rate
ranges remain the source of authority.

## Current Dry-Run Signal

| Metric | Base | Stricter Market Health |
| --- | ---: | ---: |
| Validation status | pass | pass |
| Actualized records | 13 | 13 |
| Actualized above expected range | 2 | 2 |
| Optional talent-guidance messages | 8 | 8 |
| Cohort summaries | 27 | 27 |
| Optional cohort-guidance messages | 12 | 12 |
| Budget-health warnings | 1 | 1 |
| Average actualization lift | 10.77% | 10.77% |
| Validation failures | 0 | 0 |

The two above-range records still come from the last-minute automotive stress case, where prep, travel,
turnaround compression, and overtime stack beyond the expected range. The new $500k+ and $1M+ scenarios
stay inside their wider expected ranges while creating separate large-scale and flagship cohort signals.
The race-to-bottom stress case now actualizes as `booked_with_market_health_warning`, so it remains part
of conversion learning while preserving the market-health warning.

## Talent Guidance Boundary

Talent-facing guidance is generated only as optional market intelligence.

Example shape:

```text
Similar automotive outcomes are landing about 25% above the accepted project rate in this simulation cohort.
Consider testing a 3% listed-rate increase next quarter if deal flow remains healthy; this is optional guidance, not an automatic change.
```

Validation enforces:

- guidance authority is `guidance_only`
- rate authority is `talent_owned_rate_range`
- guidance does not apply automatically
- actualization events must cite allowed triggers from the expected booking range
- unbooked outcomes do not produce actualized costs

## Cohort Learning

The report now also groups outcome learning by:

- role
- category
- project size band
- market
- client trust tier

Current directional signals:

| Cohort | Signal |
| --- | --- |
| Category: automotive | 20.08% average actualization lift, above-range actualization in the last-minute stress case |
| Category: beauty | 13.52% average actualization lift, medium-confidence sample |
| Market: Detroit | 20.08% average actualization lift, medium-confidence sample |
| Market: New York | 13.52% average actualization lift, medium-confidence sample |
| Project size: flagship | 14.83% average actualization lift, directional-only sample |
| Project size: large-scale | 13.96% average actualization lift, directional-only sample |
| Project size: premium | 19.20% average actualization lift, medium-confidence sample |
| Role: DP | 12.19% average actualization lift, medium-confidence sample |
| Role: director | 17.32% average actualization lift, directional-only sample |
| Role: photographer | 9.04% average actualization lift, directional-only sample |
| Client trust: high repeat | 14.40% average actualization lift, medium-confidence sample |
| Client trust: known | 16.49% average actualization lift, medium-confidence sample |

These are intentionally weak early signals. The simulator labels small cohorts as `directional_only`; they
can create admin review and optional talent guidance, but they should not change rates automatically.

## Product Implication

This creates the first loop toward pricing intelligence without turning Distinkt into a rate-setting
authority. Over time, the same structure can support:

- "people with similar experience in your market are closing higher"
- "your beauty work supports a stronger next-quarter rate test"
- "this client repeatedly misses budget calibration"
- "this project type actualizes above range when travel appears"

The next useful pass is to define confidence thresholds for graduating cohort guidance from
`directional_only` to stronger advisory language.
