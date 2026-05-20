# Phase 3 Findings Report

Generated from dry runs on May 20, 2026.

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
- low-readiness projects are blocked before binding Outreach & Lock
- client-visible recommendations now carry active quote versions and quote audit events
- brand prestige/desirability is tracked separately from client trust
- project-size context now separates $500k+ large-scale and $1M+ flagship productions
- European country market-cost priors are available for actor pricing context, with France as the
  current baseline and Bulgaria showing materially lower local rate pressure
- paid-rate actual fixtures now override the country cost proxy when role, market, project type, usage
  territory, and term match
- the UK PACT/FAA background actor rate card is now modeled as a published agreement floor, so it
  overrides the country cost prior for applicable UK background/supporting-artist work
- actor recommendations now carry a bounded Distinkt talent-advocacy uplift, reflecting the explicit
  representation posture of trying to improve talent outcomes when booking realism allows
- long-horizon work now includes confirmation checkpoints, hold expiration, and firm-hold requirements
- missed long-horizon checkpoints release holds and require fresh rate-quoted outreach before reactivation
- admin-curated inclusion overrides can surface edge-case talent without changing their owned rate
- race-to-bottom candidates are flagged and penalized in ranking

The simulator also exposes policy work still needed before shadow-mode integration:

- low-budget firm projects can still close through a cheapest stress candidate, but now receive a
  `booked_with_market_health_warning` outcome instead of a clean healthy booking
- readiness-blocked projects now require scope calibration before talent outreach instead of consuming
  top-talent attention with vague opportunities
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
| Scenario count | 17 |
| Booked scenarios | 12 |
| Booking rate | 70.6% |
| Long-horizon scenarios | 3 |
| Pending holds | 1 |
| Confirmation checkpoints | 4 |
| Hold expirations | 4 |
| Expired holds | 1 |
| Availability checks | 52 |
| Pre-presentation talent counters | 4 |
| Admin approval required | 52 |
| Mature autonomy candidates | 21 |
| Admin inclusion overrides | 1 |
| Readiness-blocked scenarios | 1 |
| Quote audit events | 264 |
| Derived talent budget review triggers | 4 |
| Market-cost prior review triggers | 0 |
| Actor market-prior recommendations | 3 |
| Actor rate-card recommendations | 1 |
| Paid-rate actual recommendations | 2 |
| Published agreement floors applied | 1 |
| Talent advocacy uplift count | 5 |
| Average talent advocacy uplift | 2.4% |
| Max talent advocacy uplift | 3.0% |
| Budget-health warnings | 1 |
| Scope-calibration outcomes | 3 |
| Brand-facing leakage count | 0 |
| Talent-facing job-specific rationale count | 0 |
| Max shadow AI discretion | 1.0% |

## Scenario Findings

| Scenario | Outcome | Finding | Policy Read |
| --- | --- | --- | --- |
| Firm-Budget Food Social Campaign | booked | Generalist books cleanly; premium specialist remains visible but outside budget. | Healthy: slate can include value range without hiding premium expertise. |
| Flexible National Beauty Campaign | booked | Best-fit beauty talent books; a manually curated high-profile food director appears only in the admin override slate and fails budget at their locked rate. | Healthy: admin can rescue visibility without overriding talent-owned pricing. |
| $500k+ Large-Scale Beauty Campaign | booked | Large-scale context creates wider expected ranges and a separate cohort signal. | Healthy: all-in scale affects assumption scrutiny without becoming a budget split. |
| $1M+ Flagship Automotive Launch | booked | Automotive specialist leads the slate with flagship range behavior. | Healthy: $1M+ projects are now separated from ordinary major campaigns. |
| Ingested Mike and Ike Campaign | booked | Real-shaped brief extraction maps to a major all-in CPG campaign; trust is emerging while brand prestige is tier 2. | Healthy: project readiness can allow Outreach & Lock while all-in budget stays separate from talent allocation. |
| UK PACT/FAA Background Rate Card Smoke Test | booked | Published UK PACT/FAA standard-day rate card creates a GBP 125 agreement floor and GBP expected range. | Healthy: published rate card beats the country-cost prior for applicable UK actor work. |
| France Featured Actor Market Prior Smoke Test | booked | France now matches a seed paid-rate actual: 2500 session / 7500 buyout for pan-European usage, then applies a bounded actor advocacy uplift. | Healthy as admin context: actuals replace the proxy while talent-owned rate remains authoritative. |
| Bulgaria Featured Actor Market Prior Smoke Test | booked | Bulgaria now matches a seed paid-rate actual: 800 session / 2400 buyout for pan-European usage, then applies a bounded actor advocacy uplift. | Healthy placeholder: Coke actuals can replace the seed fixture without code changes. |
| Last-Minute Automotive Shoot | booked | Urgency premium applies; unavailable specialists are excluded. | Healthy: compression is priced, but impossible options are not shown. |
| Low-Cash Prestige Editorial | needs scope calibration | Opt-in filtering works, but all realistic options exceed client capacity. | Improved: prestige is treated as a scope/budget calibration problem, not talent underpricing pressure. |
| Exploratory Food Research Brief | needs scope calibration | Project readiness score is 38, so binding Outreach & Lock is blocked before talent outreach. | Healthy: vague long-horizon projects should calibrate scope before consuming talent attention. |
| Long-Horizon Beauty Campaign | pending hold | High-trust repeat client gets a 21-day soft hold and a 60-day-before-start checkpoint. | Healthy: trust offsets uncertainty without granting unlimited calendar hold. |
| Long-Horizon Missed Checkpoint | hold expired | High-trust soft hold expires after the client misses confirmation. | Healthy: expired holds require fresh rate-quoted outreach before reactivation. |
| Bad-Faith Repricing Stress Test | booked | Volatile talent counters before client presentation; client only sees locked quote. | Structurally fixed: now track this as a pre-presentation counter, not post-interest repricing. |
| Race-to-Bottom Social Content Test | booked with market-health warning | Higher-fit options exceed capacity; low-rate option can still book in stress path. | Improved: conversion remains possible, but the outcome is no longer treated as a clean marketplace win. |
| Background Extra Minimum Wage Smoke Test | needs scope calibration | Local minimum wage lifts the effective floor above the offered day rate. | Healthy: legal/compliance floors can force budget or scope recalibration. |
| Background Extra Unknown Wage Smoke Test | booked | Nullable wage input produces a validation warning, not a hard block. | Healthy as a smoke test; production should enrich wage data over time. |

## What Looks Validated

### 1. The Rate Commitment Flow Is Correct

Talent is presented with a project-specific proposed rate during a call for details, an emailed offer, or
availability check. If they accept, that rate becomes the locked client-facing number. If they counter,
the counter happens before client presentation and is visible internally as an availability event. The
client decision simulation then evaluates the locked quote only.

Policy implication:

- this should become a non-negotiable production invariant
- any post-presentation talent-side movement requires a client-side fact-change reason code
- admin review should see pre-presentation counters, but clients and talent should not receive negative
  behavioral explanations

### 2. Behavior Nudges Are Small But Useful

Behavior adjustments appear in most recommendations, but caps keep them non-dominant. Reliable
talent can receive small premiums, dependable clients can reduce transaction risk, and high-friction
clients can create small risk adjustments.

Policy implication:

- keep behavior as a minor pricing input
- keep behavior rationale admin-only
- consume upstream readiness/reliability and main-site `clientTrustScore` / `clientTrustTier` rather
  than making this engine the source of truth

### 3. Client Trust Is Now Product-Owned Input

The simulator now consumes `clientTrustScore` and `clientTrustTier` from the main product scoring system.
Fixture traces include the score breakdown for audit, but the pricing engine does not own the formula.
Verified Brand and Agency Account remain powerful admin fast-track flags, and validation checks that
those flags produce the expected tier behavior.

The simulator also consumes `brandPrestigeTier` and `brandPrestigeScore` as separate context. Prestige
may explain why talent interest is higher, but it does not rewrite client trust or automatically move
rates in launch mode.

Policy implication:

- keep score calculation in the main app
- pass score, tier, flags, and project credibility into this engine as structured context
- do not mix client trust with brand desirability; a prestigious brand can still have messy project data
- use score/tier to shape confidence and holds, not to bypass talent-owned rates

### 4. Readiness Gate Protects Talent Attention

The exploratory food brief now stops at `needs_scope_calibration` because the readiness score is 38,
below the binding threshold of 50. No client-presentable quote is created, no talent-facing outreach is
simulated, and the project receives a scope calibration warning instead.

Policy implication:

- binding Outreach & Lock should require ready-enough project data
- admin-only ranges can still help operators calibrate the project
- under-baked briefs should not reach top talent simply because a brand is curious
- admin override should exist, but it must be logged and reasoned

### 5. Quote Lifecycle Is Now Auditable

Each client-presentable recommendation now includes a `quoteLifecycle` with active quote version,
locked gross quote, input snapshot hash, DFOS handoff contract, and append-only quote audit events.
The base run produced 264 quote audit events across 52 recommendations.

Policy implication:

- Pitch Review Room should read the active locked quote version, not transient pricing output
- client decisions should bind to the quote version they saw
- DFOS should consume the locked gross quote and apply downstream commission rules without
  recalculating the quote

### 6. Derived Talent Budgets Stay Reviewable

The ingested Mike and Ike sample provides a $400K all-in production/post/talent budget, but not a
talent-only budget. The simulator construes a placeholder talent budget so the scenario can run, marks
that budget as low-confidence, and triggers admin review on all four client-presentable recommendations.

Policy implication:

- extracting a talent budget is better than deriving one
- deriving from all-in budget is acceptable as a temporary estimate only when the uncertainty travels
  with the quote
- client-facing confidence should not imply that a construed budget is exact

### 7. AI Rationales Are Separated By Audience

The run generated 52 admin pricing rationales and 52 brand-facing match rationales. Brand-facing leakage
count was zero, and talent-facing job-specific rationale count was zero.

Policy implication:

- the audience split is correct
- admin rationales may mention percentages and hidden mechanics
- brand rationales should stay positive and fit-based
- talent education should remain upstream and score-based, not job-specific pricing disclosure

### 8. Shadow AI Discretion Is Properly Contained

AI discretion remains shadow-only with a max absolute proposal of 1.0%. Nonzero discretion triggers admin
review and does not apply to live quotes.

Policy implication:

- keep discretion in shadow mode through Phase 3
- require outcome evidence before any live discretion
- do not let AI discretion stack into a meaningful hidden price engine without caps and audit trails

### 9. Long-Horizon Confirmation Mechanics Work

The long-horizon beauty campaign from a high-trust repeat client stays pending hold, receives a 21-day
soft hold, and carries a 60-day-before-start checkpoint. A missed-checkpoint fixture expires the soft
hold and requires fresh rate-quoted outreach before reactivation.

Policy implication:

- client trust should strongly offset long-horizon uncertainty
- even high-trust long-horizon work should not become an unconditional firm hold
- pending holds must define checkpoint timing, expiration, and what turns them into firm holds
- missed checkpoints should release the hold rather than silently preserving old rates

### 10. Budget-Driven Commodity Wins Are Now Labeled

The race-to-bottom social stress case now returns `booked_with_market_health_warning`. The booking still
counts as conversion, but it carries an internal warning when a market-health risk candidate books only
after stronger options fail client capacity.

Policy implication:

- do not block affordable talent simply for being affordable
- do not let the cheapest path masquerade as a healthy recommendation outcome
- use this label to trigger budget education, scope calibration, or admin review

### 11. All-Budget-Gap Paths Require Scope Calibration

When every evaluated candidate exceeds client capacity, the simulator now returns `needs_scope_calibration`.
This appears in the low-cash prestige case, the exploratory low-readiness case, and the minimum-wage
smoke case.

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

### Manual Inclusion Abuse

Admin inclusion overrides now let a human surface a high-profile or strategically requested talent who
would otherwise be omitted by default ranking. The current stress path keeps this safe: the override is
admin-only, rate-owned by talent, and still requires rate-quoted outreach before client presentation.

Why it matters:

- manual inclusion could become a hidden way to bypass ranking quality if it is not audited
- high-profile talent can be worth reviewing even when fit or budget is weak
- the override should create a learning signal when repeated manual picks fail or calibrate policy gaps

Recommended revision:

- track override reason codes and later outcomes
- require launch approval on every override
- separate "policy missed this person" from "admin wanted a one-off review"

### Admin Review Load

Launch mode requires admin approval for all 52 recommendations. That is correct for early validation, but
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
- admin inclusion overrides for high-profile talent with weak fit, high price, or client-specific demand
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
