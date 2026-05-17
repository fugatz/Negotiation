# Phase 2 Findings Report

Generated from dry runs on May 17, 2026.

Source commands:

```bash
python3 -m simulation.src.runner --fail-on-validation
python3 -m simulation.src.runner --policy simulation/config/variants/stricter_market_health.json --fail-on-validation
```

## Executive Read

The Phase 2 simulator is now useful enough to support policy decisions before production integration.
The most important structural rule is working: talent sees the project-specific proposed rate during
availability check and must accept, decline, or counter before the client sees the slate. Client-facing
recommendations use locked, talent-approved numbers only.

The current system protects against several core failure modes:

- no post-client talent repricing in normal flow
- no brand-facing leakage of hidden floors, negative behavior signals, or AI pricing math
- no job-specific talent-facing pricing rationale
- specialist value remains visible even when budget fit is weak
- long-horizon work is held as uncertain rather than treated as a normal booking
- race-to-bottom candidates are flagged and penalized in ranking

The simulator also exposes policy work still needed before shadow-mode integration:

- low-budget firm projects can still book the cheapest stress candidate after stronger options exceed
  client capacity
- prestige projects need clearer "not viable at stated cash" language instead of appearing like normal
  booking failures
- pre-presentation talent counters are now structurally safe, but repeated counters need to feed future
  reliability inputs
- long-horizon projects need concrete confirmation mechanics, not just confidence penalties
- admin review load is intentionally high in launch mode and needs exception-based narrowing later

## Current Base Run

Policy: `phase-2-admin-config-v1`

| Metric | Result |
| --- | ---: |
| Validation status | pass |
| Scenario count | 8 |
| Booked scenarios | 5 |
| Booking rate | 62.5% |
| Long-horizon scenarios | 2 |
| Availability checks | 34 |
| Pre-presentation talent counters | 4 |
| Admin approval required | 34 |
| Mature autonomy candidates | 13 |
| Brand-facing leakage count | 0 |
| Talent-facing job-specific rationale count | 0 |
| Max shadow AI discretion | 1.0% |

## Scenario Findings

| Scenario | Outcome | Finding | Policy Read |
| --- | --- | --- | --- |
| Firm-Budget Food Social Campaign | booked | Generalist books cleanly; premium specialist remains visible but outside budget. | Healthy: slate can include value range without hiding premium expertise. |
| Flexible National Beauty Campaign | booked | Best-fit beauty talent books with no warnings. | Healthy: specialization, fit, and budget all align. |
| Last-Minute Automotive Shoot | booked | Urgency premium applies; unavailable specialists are excluded. | Healthy: compression is priced, but impossible options are not shown. |
| Low-Cash Prestige Editorial | failed budget gap | Opt-in filtering works, but all realistic options exceed client capacity. | Needs policy: prestige should not become a pressure mechanism to suppress rates. |
| Exploratory Food Research Brief | pending hold | New/low-trust long-horizon work stays tentative. | Healthy direction, but confirmation mechanics need definition. |
| Long-Horizon Beauty Campaign | pending hold | High-trust repeat client receives much softer uncertainty treatment. | Healthy: trust offsets timing uncertainty without forcing a hard booking. |
| Bad-Faith Repricing Stress Test | booked | Volatile talent counters before client presentation; client only sees locked quote. | Structurally fixed: now track this as a pre-presentation counter, not post-interest repricing. |
| Race-to-Bottom Social Content Test | booked | Higher-fit options exceed capacity; low-rate option can still book in stress path. | Needs stronger policy: ranking penalty alone does not prevent budget-driven commoditization. |

## What Looks Validated

### 1. The Rate Commitment Flow Is Correct

Talent is presented with a project-specific proposed rate at availability check. If they accept, that
rate becomes the locked client-facing number. If they counter, the counter happens before client
presentation and is visible internally as an availability event. The client decision simulation then
evaluates the locked quote only.

Policy implication:

- this should become a non-negotiable production invariant
- any post-presentation talent-side movement requires a client-side fact-change reason code
- admin review should see pre-presentation counters, but clients and talent should not receive negative
  behavioral explanations

### 2. Behavior Nudges Are Small But Useful

Behavior adjustments appear in 76.5% of recommendations, but caps keep them non-dominant. Reliable
talent can receive small premiums, dependable clients can reduce transaction risk, and high-friction
clients can create small risk adjustments.

Policy implication:

- keep behavior as a minor pricing input
- keep behavior rationale admin-only
- consume upstream readiness/reliability/trust scores rather than making this engine the source of truth

### 3. AI Rationales Are Separated By Audience

The run generated 34 admin pricing rationales and 34 brand-facing match rationales. Brand-facing leakage
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

### 5. Long-Horizon Trust Differentiation Works

The exploratory food brief from a weak-trust client becomes pending hold with a stronger uncertainty
warning. The long-horizon beauty campaign from a high-trust repeat client also stays pending hold, but
with softer confidence impact and a more workable hold policy.

Policy implication:

- client trust should strongly offset long-horizon uncertainty
- even high-trust long-horizon work should not become an unconditional firm hold
- the next design task is confirmation mechanics

## Exploit Paths And Risks

### Race-To-Bottom Survival Path

The low-rate fast responder is flagged, penalized, and pushed down by stricter market-health policy, but
can still book when higher-quality options exceed the client's capacity.

Why it matters:

- a client with a too-low firm budget may still get a booking by selecting the cheapest acceptable option
- the system can say "not price-led" in ranking while the final client decision remains price-led
- this is the clearest remaining path toward commodity-market behavior

Recommended revision:

- add a firm-budget market-health rule that detects "only low-rate option can clear capacity"
- require scope remediation, budget education, or admin review before calling that a healthy booking
- distinguish "booked" from "booked under market-health warning"

### Prestige As Underpricing Pressure

The prestige editorial scenario correctly fails budget fit, but the product language needs to make clear
that prestige does not justify suppressing cash rates unless talent explicitly opted into that tradeoff.

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

- a talent can stay technically compliant while regularly increasing quotes after availability check
- if untracked, this recreates some instability earlier in the funnel

Recommended revision:

- feed repeated pre-presentation counters into upstream talent reliability/readiness inputs
- keep the pricing impact small
- never expose the negative reason to talent or client

### Long-Horizon Hold Ambiguity

Long-horizon work is correctly marked as pending hold, but the simulator does not yet define what turns a
pending hold into a firm hold.

Why it matters:

- clients booking 90+ days out can be serious or merely fishing
- talent should not lose calendar flexibility without commitment
- high-trust clients deserve smoother handling without getting unlimited soft holds

Recommended revision:

- define confirmation checkpoints
- consider deposits, scope locks, or production milestone requirements
- expire soft holds automatically unless the client reconfirms

### Admin Review Load

Launch mode requires admin approval for all 34 recommendations. That is correct for early validation, but
too heavy for a mature autonomous system.

Why it matters:

- full admin review is safe but operationally expensive
- the system needs to learn which recommendations are boring enough to run automatically

Recommended revision:

- keep launch admin approval for now
- use `matureAutonomyCandidate` as the migration path
- after Phase 3, define which exception-free recommendations can skip human approval

## Recommended Policy Revisions Before Phase 3

1. Add a "budget-driven commodity booking" warning when a low-rate candidate books only after stronger
   options fail client capacity.
2. Split final outcome labels into `booked`, `booked_with_market_health_warning`, `pending_hold`,
   `failed_budget_gap`, and `needs_scope_calibration`.
3. Define long-horizon confirmation mechanics: checkpoint timing, hold expiration, and what counts as
   enough commitment.
4. Track pre-presentation counter frequency as an upstream reliability signal with a small capped effect.
5. Preserve strict audience separation for rationales and keep all pricing mechanics admin-only.
6. Keep AI discretion shadow-only until outcome evidence shows it improves close rates without leakage,
   underpricing, or higher dispute rates.

## Phase 3 Stress Suite

The next simulation phase should intentionally try to break the policy.

Recommended additions:

- many low-rate candidates competing against one strong specialist
- repeated firm-budget clients whose only successful bookings are low-rate options
- prestige clients with repeated low-cash asks and weak follow-through
- high-trust long-horizon clients who later cancel or change scope
- new long-horizon clients who become real after confirmation milestones
- pre-presentation counter patterns across multiple projects
- legitimate post-presentation renegotiation after client-side scope, usage, travel, exclusivity, or date
  changes
- client-side manager intervention that slows decisions, changes requirements, or creates ambiguity
- AI discretion proposals that conflict with recent failed outcomes
- market-health overrides where booking probability is high but ecosystem risk is unacceptable

## Phase 2 Exit Assessment

Phase 2 is close to complete but should not exit until the reports drive at least one more simulator pass.

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

- implement the budget-driven commodity booking warning
- add one or two Phase 3 stress fixtures
- rerun base and strict policies to see whether the warning changes outcomes cleanly
