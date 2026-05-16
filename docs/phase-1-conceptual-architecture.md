# Phase 1 Conceptual Architecture

## Purpose

This document defines the first-pass conceptual architecture for Distinkt's pricing and deal
intelligence system. It is intentionally not production implementation guidance yet. The goal is to
reason about incentives, marketplace behavior, negotiation structure, and trust before building
platform features.

## Core Thesis

Distinkt should optimize for successful, trusted, high-quality bookings rather than the cheapest
available talent. Pricing intelligence should make the market more legible without exposing private
talent desperation, hidden floor rates, or tactical weakness.

The system should act less like a bidding board and more like intelligent representation: it should
help clients understand realistic deal paths while protecting talent dignity and preserving bounded
negotiation.

## Marketplace Behaviors To Reward

- Accurate availability and pricing signals before a client becomes emotionally committed.
- Category specialization that materially improves project outcomes.
- Reliable booking behavior: fast confirmation, low cancellation risk, low surprise repricing.
- Professional counteroffers that stay within pre-declared bounds.
- Talent who consistently accept well-fit opportunities at rates near their stated expectations.
- Clients who provide realistic budgets, clear scopes, and respectful timelines.

## Marketplace Behaviors To Discourage

- Late-stage bait-and-switch repricing after the client has lost alternatives.
- Lowest-bid sorting that pressures talent into public undercutting.
- Repeated speculative submissions far below a talent's realistic acceptance range.
- Artificial fit inflation that turns every project into a premium opportunity.
- Client-side budget fishing that extracts hidden flexibility without booking intent.
- Talent-side strategic opacity that prevents producers from planning confidently.

## Important Distinction

The platform can be transparent about process without being transparent about private leverage.

Public or client-visible:

- Rate confidence bands.
- Why a talent is a strong match.
- Whether a quote is likely, stretched, or outside normal range.
- What deal variables may change price, such as usage, exclusivity, timing, scope, or travel.

Private or internal:

- Working floor.
- Utilization weakness.
- Desperation indicators.
- Exact willingness-to-concede profile.
- Internal risk or behavioral penalty scores.

## Proposed Conceptual Flow

```text
Project Brief
  -> Hard Eligibility Filtering
  -> Creative + Practical Match Scoring
  -> Pricing Intelligence Layer
  -> Timing Horizon Nudge Layer
  -> Behavior Reputation Nudge Layer
  -> Negotiation Structure Layer
  -> Curated Recommendation Layer
  -> Deal Outcome Feedback Loop
```

## Layer Responsibilities

### 1. Project Brief

Capture enough structure to prevent fake precision later:

- category and subcategory
- creative needs
- usage and rights
- timing
- location and travel requirements
- budget type: firm, flexible, exploratory, prestige, unknown
- client confidence: real booking intent vs early research
- deal constraints: exclusivity, conflicts, agency approvals, union/non-union, deliverables

The brief should produce a budget confidence state, not just a number.

### 2. Hard Eligibility Filtering

This layer should be deterministic where possible. It should remove talent who cannot reasonably do
the job, before price optimization begins.

Examples:

- unavailable for shoot dates
- location or travel impossible
- category conflict
- exclusivity conflict
- required credential missing
- budget fundamentally incompatible unless flagged as an intentional stretch

This is mostly SQL/business-rule territory.

### 3. Creative + Practical Match Scoring

This layer estimates fit and booking usefulness.

Signals:

- category specialization
- portfolio relevance
- past success in similar briefs
- client style match
- availability confidence
- responsiveness
- reliability
- production complexity fit
- risk of late-stage friction

This should not collapse into a single public rank. Internally, it can generate component scores and
reason codes; externally, it should support curated recommendations.

### 4. Pricing Intelligence Layer

Pricing should combine the talent's private pricing states with project context.

Possible internal states:

- target rate: what talent believes they are worth
- working floor: what talent might accept under the right conditions
- historical accepted range
- category premium potential
- scarcity premium
- urgency premium
- desirability adjustment for prestige or strategic value
- negotiation volatility risk

The output should be a recommendation state rather than a single mechanical number.

Example internal outputs:

- likely quote range
- defensible premium range
- client budget fit state
- talent acceptance probability
- timing horizon nudge
- counteroffer risk
- late-stage repricing risk
- recommended negotiation posture

### 5. Timing Horizon Nudge Layer

Timing should create small pricing and confidence adjustments, but it should not dominate fit,
specialization, or budget reality.

Near-term projects can reasonably cost more because they create disruption, scarcity, and opportunity
cost. Far-future projects can be less reliable because scope, budgets, approvals, and schedules often
shift before booking.

Initial timing hypotheses:

- projects inside 14 days may receive a small urgency premium
- projects inside 7 days may receive a slightly stronger but still capped urgency premium
- projects 90 or more days out may receive a small project-confidence reduction
- strong client or brand reliability can offset some long-horizon uncertainty
- weak client or brand reliability can increase long-horizon uncertainty

Possible timing nudges:

- last-minute urgency premium, for example 2% to 6%
- extreme last-minute premium, for example up to 8% when disruption is real
- long-horizon confidence reduction, for example 2% to 5% against booking certainty
- optional quote confirmation window for far-future work

Guardrails:

- timing should not become a blanket surcharge or discount
- long-horizon uncertainty should usually affect confidence, holds, and confirmation mechanics before
  it affects talent compensation
- timing should never push a deal below a talent's private working floor
- client-facing language should reference schedule certainty or urgency, not hidden reliability
  scoring

This layer is a small stub for simulation. The goal is to test whether timing nudges improve deal
realism without creating manipulative urgency pricing or unfair skepticism of early-planning clients.

### 6. Behavior Reputation Nudge Layer

Behavior should matter, but it should never become the dominant factor. This layer should apply small,
capped adjustments that reflect deal reliability on both sides.

The goal is to reward dependable marketplace behavior and price in friction risk without turning the
system into a punitive reputation machine.

Talent-side behavior signals might include:

- quote stability
- response consistency
- hold and cancellation reliability
- accurate availability
- professional counteroffer behavior
- scope-change reason quality
- post-interest repricing frequency

Client-side behavior signals might include:

- brief clarity
- scope stability
- decision speed
- payment reliability
- respectful negotiation behavior
- rate-shopping or budget-fishing patterns
- late scope creep after quote lock

Possible pricing nudges:

- dependable talent may receive a small reliability premium
- volatile talent may lose recommendation confidence or reliability premium
- dependable clients may receive slightly more favorable pricing because they reduce transaction risk
- high-friction clients may see a small risk premium or reduced flexibility

Initial guardrail hypothesis:

- behavior nudges should usually sit in the 1% to 5% range
- total behavior impact should be hard-capped, for example at 7.5%
- behavior should never move a deal below a talent's private working floor
- behavior should never override hard eligibility, creative fit, or major budget incompatibility
- client-facing explanations should describe process reliability, not expose hidden reputation scores

This layer is intentionally a stub for later policy design. The exact metrics, decay windows, caps,
and appeal/correction process should be decided after simulation.

### 7. Negotiation Structure Layer

Negotiation should remain possible, but bounded.

Possible mechanisms:

- pre-submission quote commitment window
- structured counteroffer bands
- quote expiration periods
- scope-change repricing rules
- explicit "new information" triggers for price changes
- post-interest repricing penalty when no project variable changed
- client budget revision flow when scope or expectations shift

The system should distinguish legitimate repricing from tactical repricing.

Legitimate repricing:

- usage expanded
- timeline compressed
- deliverables increased
- exclusivity added
- travel burden changed
- competitor conflict introduced

High-risk repricing:

- price rises only after strong client interest
- no scope change
- alternatives have expired
- pattern repeats across multiple deals

### 8. Curated Recommendation Layer

The client should see a curated slate, not a commodity auction.

Recommendation categories could include:

- Best Fit
- Strong Specialist
- Budget-Confident
- Premium Stretch
- Emerging Value
- Fastest Viable Path

Avoid labels that imply desperation or discounting.

Client-facing pricing language should communicate confidence and fit:

- "Within expected range"
- "Likely workable with scoped usage"
- "Premium specialist; budget may need adjustment"
- "Strong creative fit, lower booking confidence at current budget"

### 9. Deal Outcome Feedback Loop

Outcomes should update models slowly enough to avoid overreacting to one-off situations.

Track:

- quoted vs accepted rate
- number and size of counters
- reason for price movement
- timing horizon at inquiry and booking
- schedule changes after inquiry
- talent behavior events
- client behavior events
- booking success
- cancellation or hold release
- client satisfaction
- talent satisfaction
- production outcome
- repeat booking behavior

The feedback loop should improve prediction without turning private flexibility into public pressure.

## Pricing Model Concepts

### Target Rate

Talent's preferred economic anchor. This is useful for dignity, positioning, and premium logic.

Risk:

- If treated as fixed truth, it may overprice talent out of relevant opportunities.

Mitigation:

- Pair it with context and probability rather than using it as a hard rule.

### Working Floor

Private minimum viable acceptance under favorable conditions.

Risk:

- If exposed or optimized against, it creates commoditization and distrust.

Mitigation:

- Never expose it. Use it only to reason about feasibility and internal negotiation boundaries.

### Contextual Premium Potential

The value lift created by fit, scarcity, urgency, usage, and reputation.

Risk:

- Artificial inflation if every positive signal becomes a premium multiplier.

Mitigation:

- Require evidence-backed premiums and cap compounding effects.

### Acceptance Probability

Probability that the talent accepts a structured offer under current conditions.

Risk:

- If clients infer private floors from probability changes, it becomes a negotiation weapon.

Mitigation:

- Show coarse confidence states, not precise probabilities.

## Fit-Based Pricing

Fit should influence pricing when it reflects actual market value or outcome reliability.

Good fit-premium reasons:

- rare category expertise
- client requested a specific specialist profile
- proven results in similar campaign types
- high production complexity where expertise reduces execution risk
- category scarcity at the required time or location

Bad fit-premium reasons:

- keyword overlap alone
- generic popularity
- inflated scarcity without supply evidence
- using fit as a pretext to raise rates after interest

Recommended design:

- Use fit to strengthen the talent's positioning and quote confidence.
- Allow premium treatment when fit is evidence-backed.
- Keep the premium bounded and explainable internally.
- Prefer "premium specialist" framing over "more expensive because the algorithm says so."

## Budget Reality States

Client budget should be modeled as a state, not just a number.

- Firm: cannot move; recommend only realistic paths.
- Flexible: can move for a strong reason; include premium stretch options.
- Exploratory: use ranges and education; avoid treating stated budget as reliable.
- Prestige: may justify lower cash only if talent has opted into that kind of tradeoff.
- Unknown: require calibration before surfacing confidence.

Prestige work needs special care. It should not become a socially acceptable way to push down rates.
Talent should explicitly define when prestige, portfolio value, relationships, or strategic upside can
matter.

## Equilibrium Risks

### Race To The Bottom

Failure mode:

- Clients sort by price.
- Talent undercut each other.
- Specialists leave or disengage.
- Marketplace quality falls.

Defenses:

- Never present talent as a lowest-price list.
- Use curated slates with fit and reliability reasons.
- Keep private flexibility hidden.
- Reward bookings that succeed at fair, stable rates.

### Bait-And-Switch Repricing

Failure mode:

- Talent or reps submit within budget, wait for interest, then raise price sharply.

Defenses:

- Require pre-submission quote bounds.
- Allow repricing only with scoped reason codes.
- Track unexplained post-interest increases.
- Reduce future recommendation confidence for repeated patterns.

### Client Budget Fishing

Failure mode:

- Clients probe the marketplace to discover hidden floors without booking intent.

Defenses:

- Gate highly sensitive pricing intelligence behind brief quality and booking intent.
- Show coarse ranges early, sharper confidence later.
- Track repeated non-booking budget probes.

### Specialist Suppression

Failure mode:

- Broadly available generalists win because they are cheaper and faster.

Defenses:

- Include specialist value in match scoring.
- Create explicit specialist recommendation lanes.
- Measure outcome quality and repeat bookings, not just acceptance speed.

### Desperation Exploitation

Failure mode:

- Idle talent become systematically shown at lower rates.

Defenses:

- Utilization may inform internal feasibility, but should not be surfaced as discount logic.
- Avoid "available bargain" labels.
- Use long-term fairness and dignity constraints in ranking.

## Proposed Internal Scoring Families

The system should keep scores separable for explainability and simulation.

- Eligibility score: can this talent actually take the job?
- Creative fit score: how well does the work match the brief?
- Practical fit score: timing, location, scope, workflow.
- Price fit score: how realistic is a successful deal at this budget?
- Trust score: how stable and professional is negotiation behavior?
- Timing horizon nudge: small capped adjustment for urgent or far-future project timing.
- Talent behavior nudge: small capped adjustment for dependable or high-friction talent behavior.
- Client behavior nudge: small capped adjustment for dependable or high-friction client behavior.
- Market health score: does recommending this talent support long-term ecosystem quality?

The final recommendation should be a policy decision over these scores, not a blind weighted average.

## Initial Policy Hypotheses

These are hypotheses to test in simulation, not final rules.

1. A slightly over-budget specialist with high fit may be better than an in-budget generalist when the
   client budget is flexible.
2. A talent with repeated unexplained late repricing should lose recommendation confidence even if
   creative fit is high.
3. Idle status should increase internal booking feasibility but should not directly lower public
   pricing posture.
4. Prestige discounts should require talent-side opt-in and explicit project-quality signals.
5. Recommendation slates should include diverse deal paths, not only top-scoring talent.
6. Dependable talent should be able to earn a small reliability premium.
7. Dependable clients should be able to earn slightly more favorable pricing because they reduce
   transaction risk.
8. High-friction client or talent behavior should affect pricing and recommendation confidence only
   through capped, explainable nudges.
9. Last-minute projects should carry a small urgency premium when they create real disruption.
10. Projects roughly 90 or more days out should carry slightly lower confidence until the brief,
    approvals, and schedule become firmer.

## Open Questions

- How much pricing flexibility should talent declare directly versus be learned from outcomes?
- Should talent set separate floors by category, usage, client type, and timing?
- How should the system handle reps who manage multiple talent with inconsistent negotiation norms?
- What client-facing language creates trust without implying exact price guarantees?
- How should Distinkt distinguish strong negotiation from harmful repricing?
- What timing thresholds should define last-minute, normal, and long-horizon work?
- Should long-horizon uncertainty affect price, confidence, hold mechanics, or all three?
- How should brand/client reliability offset uncertainty for projects planned far in advance?
- What exact talent and client behavior metrics should feed reliability nudges?
- What cap keeps behavior meaningful but non-dominant?
- How should behavior scores decay, recover, or be appealed?
- What market health constraints should override short-term booking probability?
- How quickly should negative negotiation behavior decay after improved behavior?

## Phase 1 Exit Criteria

Before moving to simulation implementation, the team should agree on:

- private vs public pricing boundaries
- score families and definitions
- negotiation abuse definitions
- timing nudge boundaries for urgent and long-horizon work
- behavior nudge boundaries for talent and clients
- initial policy hypotheses
- synthetic scenario coverage
- what success and harm look like in dry runs
