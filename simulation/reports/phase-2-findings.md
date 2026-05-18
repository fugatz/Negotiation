# Phase 3 Findings Report

Generated from dry runs on May 18, 2026.

Source commands:

```bash
python3 -m simulation.src.runner --fail-on-validation
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json --fail-on-validation
```

## Executive Read

The Phase 3 simulator is now useful enough to support policy decisions before production integration.
The most important structural rule is working: after candidate matching, the pricing engine computes the
project-specific proposed rate and includes it in rate-quoted talent outreach. Talent must accept,
decline, or counter before the client sees the slate. Client-facing recommendations use locked,
talent-approved numbers only.

The current system protects against several core failure modes:

- no post-client talent repricing in normal flow
- no brand-facing leakage of hidden floors, negative behavior signals, or AI pricing math
- no job-specific talent-facing pricing rationale
- specialist value remains visible even when budget fit is weak
- project-size context now separates $500k+ large-scale and $1M+ flagship productions
- long-horizon work now includes confirmation checkpoints, hold expiration, and firm-hold requirements
- missed long-horizon checkpoints release holds and require fresh rate-quoted outreach before reactivation
- race-to-bottom candidates are flagged and penalized in ranking

The simulator also exposes policy work still needed before shadow-mode integration:

- low-budget firm projects can still close through a cheapest stress candidate, but now receive a
  `booked_with_market_health_warning` outcome instead of a clean healthy booking
- prestige and compliance-floor budget mismatches now become `needs_scope_calibration` instead of plain
  booking failures
- pre-presentation talent counters are now structurally safe, but repeated counters need to feed future
  reliability inputs
- long-horizon projects still need follow-up stress tests for late scope changes after confirmation
- admin review load is intentionally high in launch mode and needs exception-based narrowing later

## Current Base Run

Policy: `phase-3-hold-expiration-v1`

| Metric | Result |
| --- | ---: |
| Validation status | pass |
| Scenario count | 13 |
| Booked scenarios | 8 |
| Booking rate | 61.5% |
| Long-horizon scenarios | 3 |
| Pending holds | 2 |
| Confirmation checkpoints | 6 |
| Hold expirations | 6 |
| Expired holds | 1 |
| Availability checks | 50 |
| Pre-presentation talent counters | 4 |
| Admin approval required | 50 |
| Mature autonomy candidates | 23 |
| Budget-health warnings | 1 |
| Scope-calibration outcomes | 2 |
| Brand-facing leakage count | 0 |
| Talent-facing job-specific rationale count | 0 |
| Max shadow AI discretion | 1.0% |

## Scenario Findings

| Scenario | Outcome | Finding | Policy Read |
| --- | --- | --- | --- |
| Firm-Budget Food Social Campaign | booked | Generalist books cleanly; premium specialist remains visible but outside budget. | Healthy: slate can include value range without hiding premium expertise. |
| Flexible National Beauty Campaign | booked | Best-fit beauty talent books with no warnings. | Healthy: specialization, fit, and budget all align. |
| $500k+ Large-Scale Beauty Campaign | booked | Large-scale context creates wider expected ranges and a separate cohort signal. | Healthy: all-in scale affects assumption scrutiny without becoming a budget split. |
| $1M+ Flagship Automotive Launch | booked | Automotive specialist leads the slate with flagship range behavior. | Healthy: $1M+ projects are now separated from ordinary major campaigns. |
| Last-Minute Automotive Shoot | booked | Urgency premium applies; unavailable specialists are excluded. | Healthy: compression is priced, but impossible options are not shown. |
| Low-Cash Prestige Editorial | needs scope calibration | Opt-in filtering works, but all realistic options exceed client capacity. | Improved: prestige is treated as a scope/budget calibration problem, not talent underpricing pressure. |
| Exploratory Food Research Brief | pending hold | New/low-trust long-horizon work gets no soft hold until confirmation signals arrive. | Healthy: weak trust creates a tighter hold path without changing price. |
| Long-Horizon Beauty Campaign | pending hold | High-trust repeat client gets a 21-day soft hold and a 60-day-before-start checkpoint. | Healthy: trust offsets uncertainty without granting unlimited calendar hold. |
| Long-Horizon Missed Checkpoint | hold expired | High-trust soft hold expires after the client misses confirmation. | Healthy: expired holds require fresh rate-quoted outreach before reactivation. |
| Bad-Faith Repricing Stress Test | booked | Volatile talent counters before client presentation; client only sees locked quote. | Structurally fixed: now track this as a pre-presentation counter, not post-interest repricing. |
| Race-to-Bottom Social Content Test | booked with market-health warning | Higher-fit options exceed capacity; low-rate option can still book in stress path. | Improved: conversion remains possible, but the outcome is no longer treated as a clean marketplace win. |
| Background Extra Minimum Wage Smoke Test | needs scope calibration | Local minimum wage lifts the effective floor above the offered day rate. | Healthy: legal/compliance floors can force budget or scope recalibration. |
| Background Extra Unknown Wage Smoke Test | booked | Nullable wage input produces a validation warning, not a hard block. | Healthy as a smoke test; production should enrich wage data over time. |

## What Looks Validated

### 1. The Rate Commitment Flow Is Correct

Talent is presented with a project-specific proposed rate during WhatsApp/email outreach or availability
check. If they accept, that rate becomes the locked client-facing number. If they counter, the counter
happens before client presentation and is visible internally as an availability event. The client decision
simulation then evaluates the locked quote only.

Policy implication:

- this should become a non-negotiable production invariant
- any post-presentation talent-side movement requires a client-side fact-change reason code
- admin review should see pre-presentation counters, but clients and talent should not receive negative
  behavioral explanations

### 2. Behavior Nudges Are Small But Useful

Behavior adjustments appear in 82.6% of recommendations, but caps keep them non-dominant. Reliable
talent can receive small premiums, dependable clients can reduce transaction risk, and high-friction
clients can create small risk adjustments.

Policy implication:

- keep behavior as a minor pricing input
- keep behavior rationale admin-only
- consume upstream readiness/reliability/trust scores rather than making this engine the source of truth

### 3. AI Rationales Are Separated By Audience

The run generated 46 admin pricing rationales and 46 brand-facing match rationales. Brand-facing leakage
count was zero, and talent-facing job-specific rationale count was zero.

Policy implication:

- the audience split is correct
- admin rationales may mention percentages and hidden mechanics
- brand rationales should stay positive and fit-based
- talent education should remain upstream and score-based, not job-specific pricing disclosure

### 4. Shadow AI Discretion Is Properly Contained

AI discretion remains shadow-only with a max absolute proposal of 1.0%. Nonzero discretion triggers admin
review and does not apply to live quotes.

Policy implication:

- keep discretion in shadow mode through Phase 3
- require outcome evidence before any live discretion
- do not let AI discretion stack into a meaningful hidden price engine without caps and audit trails

### 5. Long-Horizon Confirmation Mechanics Work

The exploratory food brief from a weak-trust client becomes pending hold with no soft hold until
confirmation signals arrive. The long-horizon beauty campaign from a high-trust repeat client also stays
pending hold, but receives a 21-day soft hold and a 60-day-before-start checkpoint. A missed-checkpoint
fixture now expires the soft hold and requires fresh rate-quoted outreach before reactivation.

Policy implication:

- client trust should strongly offset long-horizon uncertainty
- even high-trust long-horizon work should not become an unconditional firm hold
- pending holds must define checkpoint timing, expiration, and what turns them into firm holds
- missed checkpoints should release the hold rather than silently preserving old rates

### 6. Budget-Driven Commodity Wins Are Now Labeled

The race-to-bottom social stress case now returns `booked_with_market_health_warning`. The booking still
counts as conversion, but it carries an internal warning when a market-health risk candidate books only
after stronger options fail client capacity.

Policy implication:

- do not block affordable talent simply for being affordable
- do not let the cheapest path masquerade as a healthy recommendation outcome
- use this label to trigger budget education, scope calibration, or admin review

### 7. All-Budget-Gap Paths Require Scope Calibration

When every evaluated candidate exceeds client capacity, the simulator now returns `needs_scope_calibration`.
This appears in the low-cash prestige case and the minimum-wage smoke case.

Policy implication:

- do not frame structurally underfunded projects as ordinary booking failures
- require budget, scope, usage, schedule, or opportunity-framing changes before presenting the path as viable
- keep talent rates intact when the client-side economics are the real constraint

## Exploit Paths And Risks

### Race-To-Bottom Survival Path

The low-rate fast responder is flagged, penalized, and pushed down by stricter market-health policy, but
can still book when higher-quality options exceed the client's capacity. This now becomes
`booked_with_market_health_warning` instead of a clean `booked` outcome.

Why it matters:

- a client with a too-low firm budget may still get a booking by selecting the cheapest acceptable option
- the system can say "not price-led" in ranking while the final client decision remains price-led
- this is the clearest remaining path toward commodity-market behavior

Recommended revision:

- require scope remediation, budget education, or admin review before treating this as a healthy booking
- track whether repeated warnings come from the same client, project type, or market
- consider escalation to `needs_scope_calibration` when warning patterns repeat

### Prestige As Underpricing Pressure

The prestige editorial scenario now requires scope calibration instead of failing as a plain budget gap.
The product language still needs to make clear that prestige does not justify suppressing cash rates unless
talent explicitly opted into that tradeoff.

Why it matters:

- prestige buyers can overpromise exposure and normalize low-cash asks
- even opted-in talent should not be silently pushed below dignity thresholds

Recommended revision:

- present low-cash prestige work as a special opportunity class, not a normal budget match
- require opt-in and a visible admin warning
- track repeated prestige-overpromising as client trust degradation

### Pre-Presentation Counter Pattern

Pre-presentation counters are acceptable because they happen before the client sees the slate. However,
repeated countering can still create friction and reduce predictability.

Why it matters:

- a talent can stay technically compliant while regularly increasing quotes during rate-quoted outreach
- if untracked, this recreates some instability earlier in the funnel

Recommended revision:

- feed repeated pre-presentation counters into upstream talent reliability/readiness inputs
- keep the pricing impact small
- never expose the negative reason to talent or client

### Long-Horizon Follow-Through Risk

Long-horizon work now has confirmation mechanics and a missed-checkpoint expiration path, but the simulator
does not yet test what happens when a client changes scope after confirmation or becomes more serious late.

Why it matters:

- clients booking 90+ days out can be serious or merely fishing
- talent should not lose calendar flexibility without commitment
- high-trust clients deserve smoother handling without getting unlimited soft holds

Recommended revision:

- test high-trust clients who later change dates, usage, or scope
- decide whether expired holds require a fresh rate-quoted outreach pass

### Admin Review Load

Launch mode requires admin approval for all 46 recommendations. That is correct for early validation, but
too heavy for a mature autonomous system.

Why it matters:

- full admin review is safe but operationally expensive
- the system needs to learn which recommendations are boring enough to run automatically

Recommended revision:

- keep launch admin approval for now
- use `matureAutonomyCandidate` as the migration path
- after Phase 3, define which exception-free recommendations can skip human approval

## Recommended Policy Revisions Before Integration

1. Track pre-presentation counter frequency as an upstream reliability signal with a small capped effect.
2. Preserve strict audience separation for rationales and keep all pricing mechanics admin-only.
3. Keep AI discretion shadow-only until outcome evidence shows it improves close rates without leakage,
   underpricing, or higher dispute rates.

## Phase 3 Stress Suite

The next simulation phase should intentionally try to break the policy.

Recommended additions:

- many low-rate candidates competing against one strong specialist
- repeated firm-budget clients whose only successful bookings are low-rate options
- prestige clients with repeated low-cash asks and weak follow-through
- high-trust long-horizon clients who later cancel or change scope after confirmation
- new long-horizon clients who become real after confirmation milestones
- pre-presentation counter patterns across multiple projects
- legitimate post-presentation renegotiation after client-side scope, usage, travel, exclusivity, or date
  changes
- client-side manager intervention that slows decisions, changes requirements, or creates ambiguity
- AI discretion proposals that conflict with recent failed outcomes
- market-health overrides where booking probability is high but ecosystem risk is unacceptable

## Phase 3 Exit Assessment

Phase 3 is now focused on repeated-warning stress tests, hold follow-through, and narrowing autonomy
exceptions.

Exit criteria status:

| Exit Criterion | Status |
| --- | --- |
| Repeatable scenario runs | met |
| Visible traces for individual deals | met |
| Aggregate metrics across runs | met |
| Comparison across policy variants | met |
| Identified exploit paths | met by this report |
| Recommended policy revisions | met by this report |

Recommended next move:

- add repeated-client stress fixtures to see whether warnings cluster around the same buyer behavior
- add late-scope-change long-horizon fixtures
