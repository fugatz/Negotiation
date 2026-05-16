# Simulation Blueprint

## Purpose

The simulation engine should stress-test Distinkt pricing and negotiation policies before they are
integrated into the live platform. It should use synthetic talent, projects, clients, and reps so the
team can observe incentives, exploitability, and equilibrium risks in a safe environment.

This is a standalone research tool, not production code.

Admin-tweakable policy settings should live in an explicit versioned config file rather than being
buried as code constants. The config should cover timing thresholds, behavior caps, AI discretion
caps, market-health review flags, ranking penalties, launch approval settings, and later any admin UI
knobs used in dry runs.

## Simulation Questions

The first simulation should answer:

- Does the recommendation policy reward specialists without always pricing them out?
- Does bounded negotiation reduce late-stage repricing without killing legitimate flexibility?
- Do clients with firm budgets get realistic options instead of false hope?
- Does hidden floor pricing stay protected from client inference?
- Do idle talent get access to opportunities without being framed as discounted inventory?
- Do repeated bad-faith repricing patterns reduce future recommendation confidence?
- Do last-minute projects receive a small realistic urgency premium?
- Do far-future projects carry slightly lower confidence until commitment signals firm up?
- Do talent and client behavior nudges affect pricing without becoming dominant factors?
- Does the marketplace avoid collapsing into cheapest-available matching over many rounds?

## Core Entities

### Talent

Synthetic talent profiles should include:

- id and display archetype
- categories and specialization depth
- listed rate
- talent-approved operating band, initially 25% below to 30% above listed rate
- private working floor
- rate history
- availability
- upstream actor readiness score, when applicable
- upstream non-actor reliability score, when applicable
- negotiation behavior type
- behavior history
- category premium potential
- prestige-work preference
- utilization state
- conflict constraints

The first simulation should avoid a full matrix of talent-entered floor rates by category, usage,
client type, and timing. Those differences should be represented as contextual scoring and outcome
calibration, with optional explicit exceptions added later only if needed.

Example archetypes:

- premium food tabletop director
- emerging beauty photographer
- reliable generalist DP
- automotive specialist with scarce availability
- luxury fashion editor
- idle but high-quality director
- volatile rep-managed talent
- low-rate fast responder

### Project

Synthetic project briefs should include:

- category
- budget
- budget type
- lead time in days
- timing horizon: last-minute, normal, long-horizon
- project commitment confidence
- brand reliability signal
- schedule urgency
- location
- usage scope
- creative specificity
- prestige value
- client flexibility
- booking intent strength
- conflict or exclusivity requirements

Example briefs:

- firm-budget food social campaign
- flexible-budget national beauty campaign
- low-cash prestige editorial opportunity
- last-minute automotive shoot
- exploratory brand research brief
- high-usage luxury fashion campaign

### Client

Client behavior types should include:

- realistic professional buyer
- firm-budget producer
- flexible premium buyer
- budget fisher
- prestige-overpromiser
- slow decision-maker
- high-trust repeat client

Synthetic client profiles should also include behavior history:

- upstream client trust metric
- brief clarity
- decision speed
- payment reliability
- scope stability
- rate-shopping frequency
- post-quote scope creep frequency
- completed Distinkt project count
- platform client trust score

### Negotiation Agent

Talent-side negotiation behavior should be simulated separately from talent quality.
Distinkt is the talent-side agent, so the relevant third-party behavior risk is usually on the client
side: client-side managers, procurement teams, or approval chains that create friction, delay, or
repricing pressure. That behavior should be attributed to the client side for trust, desirability, and
recommendation confidence. Client-side intermediaries should not create a loophole where bad
negotiation behavior becomes unscored.

Behavior types:

- stable professional
- principled premium negotiator
- flexible but bounded
- opportunistic late repricer
- slow responder
- lowball accepter
- scope-sensitive repricer

## Recommendation Policy Inputs

The simulation should generate these internal values:

- hard eligibility pass/fail
- operating band state: below band, in band, above band, or intentional stretch
- creative fit score
- practical fit score
- price fit score
- client-facing talent score
- acceptance probability
- expected final price band
- repricing risk
- trust score
- timing horizon nudge
- talent behavior nudge
- client behavior nudge
- admin-only AI pricing rationale
- brand-facing AI match rationale
- talent-facing rationale state: not generated by this pricing layer
- AI discretion delta
- AI discretion evidence summary
- admin approval state
- admin exception triggers
- bounded admin setting tweak controls
- market health score
- recommendation lane

Recommendation lanes:

- Best Fit
- Strong Specialist
- Budget-Confident
- Premium Stretch
- Emerging Value
- Fastest Viable Path

## Negotiation Policy Variants To Test

### Baseline Marketplace

Sort mostly by price fit and availability.

Expected risk:

- race to the bottom
- specialist suppression
- underpricing

### Fit-Weighted Marketplace

Strongly weight creative fit and category specialization.

Expected risk:

- over-budget recommendations
- premium inflation

### Trust-Gated Marketplace

Discount recommendation confidence for repeated unexplained repricing.

Expected risk:

- may punish legitimate tough negotiators if reason codes are weak

### Bounded Negotiation Marketplace

Require pre-presentation quote bands, present locked numbers to the client, and only allow
renegotiation after presentation when client-side facts change.

Expected risk:

- may reduce flexibility for nuanced human deals
- may require better upfront confidence before a talent is included in a slate

### Curated Slate Marketplace

Return multiple deal paths rather than a single ranked list.

Expected risk:

- needs careful client UX to avoid appearing indecisive

### Behavior-Nudged Marketplace

Apply small capped pricing adjustments for talent and client reliability.

Expected behavior:

- dependable talent can earn a modest reliability premium
- dependable clients can receive slightly more favorable pricing
- difficult talent can receive small downward quote pressure
- high-friction clients can trigger a small risk premium
- both sides can contribute to the net behavior adjustment, subject to the cap
- volatile talent can lose recommendation confidence without being automatically underpriced

Expected risk:

- behavior scores become too influential
- clients or talent infer hidden scores from pricing changes
- one bad event has too much long-term impact if upstream readiness/reliability/trust scores do not
  recover with positive data

### Timing-Horizon-Nudged Marketplace

Apply small capped adjustments for project timing.

Expected behavior:

- projects under 21 days receive a modest urgency premium
- projects under 14 days receive a stronger but capped compression premium
- projects 90 or more days out receive a small seriousness/confidence reduction
- 90+ day timing affects hold/confirmation mechanics rather than direct price
- platform client trust heavily offsets 90+ day uncertainty
- new clients remain low-confidence at 90+ days
- high-trust repeat clients around their 4th project or later are treated as much more credible

Expected risk:

- urgency premiums become too automatic
- long-horizon projects are unfairly penalized despite serious planning signals
- clients infer that early planning weakens their negotiating position

## Simulation Loop

```text
1. Generate synthetic project brief.
2. Filter eligible synthetic talent.
3. Score creative, practical, pricing, trust, and market-health dimensions.
4. Apply capped timing-horizon nudges.
5. Apply capped talent and client behavior nudges.
6. Generate admin-only AI pricing rationale from computed adjustments and structured policy outputs.
7. Generate separate brand-facing AI match rationale that avoids pricing and hidden-score logic.
8. Record that this layer does not generate talent-facing job-specific pricing rationale.
9. Optionally apply shadow-mode AI discretion deltas based on outcome evidence.
10. Add launch-mode admin governance: approval required, exception triggers, and tweakable settings.
11. Build a curated recommendation slate.
12. Simulate client shortlist behavior.
13. Simulate talent response and negotiation.
14. Resolve booking, no-booking, repricing, or cancellation.
15. Update historical outcomes.
16. Repeat across many rounds.
17. Evaluate market-level metrics.
```

## Success Metrics

Booking metrics:

- booking success rate
- time to confident shortlist
- quote-to-close rate
- accepted price vs expected range
- cancellation rate

Talent health metrics:

- specialist booking rate
- average accepted rate by specialization level
- under-floor pressure frequency
- idle-talent opportunity access
- prestige discount abuse frequency

Client trust metrics:

- late-stage repricing frequency
- budget surprise frequency
- slate realism
- number of failed negotiations per booking
- long-horizon project follow-through rate
- client behavior nudge distribution

Marketplace health metrics:

- rate compression over time
- concentration of bookings among cheapest talent
- retention of premium specialists
- repeat booking rate
- distribution of recommendation lanes
- timing horizon nudge distribution
- talent behavior nudge distribution
- total pricing impact from behavior nudges

Abuse metrics:

- unexplained post-interest repricing
- client budget fishing
- repeated non-booking probes
- fake prestige offers
- scope creep after quote lock

Behavior nudge safety metrics:

- percentage of deals where behavior changed pricing
- average behavior impact as percentage of final quote
- maximum behavior impact as percentage of final quote
- percentage of behavior impacts above 3%
- number of behavior impacts capped at 5%
- number of deals where behavior would have changed the recommendation lane
- number of deals where behavior was blocked by a cap or floor guardrail
- number of cases where improved upstream scores reduced or removed the behavior nudge

Timing nudge safety metrics:

- percentage of deals where timing changed pricing or confidence
- average urgency premium for projects under 21 days
- average confidence reduction for projects 90 or more days out
- number of long-horizon projects later confirmed, changed, or cancelled
- number of timing nudges blocked by cap or floor guardrails

AI rationale and discretion safety metrics:

- number of admin pricing rationales generated by adjustment type
- number of brand-facing rationales generated
- number of brand-facing rationales that mention pricing nudges, hidden-score inputs, floors, or
  negotiation flexibility
- number of brand-facing rationales that imply the AI set the price
- number of cases where AI recommends human review
- agreement rate between computed nudges and admin-only AI rationale text
- positive-language coverage for brand-facing rationales
- number of talent-facing job-specific pricing rationales generated, which should remain zero
- average AI discretion delta in shadow mode
- maximum AI discretion delta proposed
- number of AI discretion deltas blocked by caps or floor guardrails
- estimated lift or harm from AI discretion versus no-discretion baseline
- number of AI discretion recommendations lacking sufficient outcome evidence
- number of "talent should get more this time" recommendations and their later outcomes

Admin governance metrics:

- number of recommendations requiring launch admin approval
- number of recommendations that would be mature-mode autonomy candidates
- exception trigger counts by reason
- number of admin setting tweaks used in dry runs
- number of manual overrides that later imply policy recalibration
- difference between admin-approved outcomes and fully autonomous simulated outcomes

Validation checks:

- brand-facing rationale leakage count must be zero
- talent-facing job-specific pricing rationale count must be zero
- launch-mode recommendations must require admin approval and audit logging
- nonzero AI discretion must remain shadow/advisory unless separately approved
- AI discretion must stay inside its separate cap
- combined behavior nudges must stay inside behavior caps
- long-horizon uncertainty must not directly change talent price
- outside-budget recommendations must trigger admin exception review
- race-to-bottom risk must not become the default top recommendation
- market-health risk flags or low market-health scores must trigger admin exception review

## Edge Case Matrix

### Premium Specialist, Firm Budget

Question:

- Should the specialist appear as a premium stretch, or be excluded to avoid false hope?

Expected behavior:

- Show only if there is a credible path, and label internally as low price-fit confidence.

### Premium Specialist, Flexible Budget

Question:

- Does the system help justify a higher rate through fit and outcome confidence?

Expected behavior:

- Recommend strongly if specialization is evidence-backed.

### Low-Budget Prestige Project

Question:

- Does prestige become an excuse to suppress rates?

Expected behavior:

- Only include talent who opted into prestige tradeoffs; track abuse by clients.

### Idle Talent

Question:

- Does utilization quietly improve opportunity access without public discounting?

Expected behavior:

- Improve internal feasibility, never expose desperation.

### Last-Minute Booking

Question:

- Does urgency increase price when scarcity and disruption justify it?

Expected behavior:

- Apply urgency premiums where defensible; avoid penalizing talent for being available.

### Extreme Last-Minute Booking

Question:

- Does a project under 14 days get a stronger but still capped compression premium?

Expected behavior:

- Apply a slightly larger urgency nudge only when schedule disruption or scarcity is real.

### Long-Horizon Project

Question:

- Does a project 90 or more days out look more exploratory until approvals and schedule are firm?

Expected behavior:

- Reduce project seriousness/confidence slightly, prefer confirmation windows, and let strong brand or
  client reliability offset part of the uncertainty.
- Greatly reduce the penalty for high-trust repeat clients, especially on their 4th project or later.
- Keep the penalty high for clients with no Distinkt history.
- Do not directly change talent price just because the project is far out.

### Unavailable Perfect Match

Question:

- Does the system preserve trust by excluding impossible options?

Expected behavior:

- Do not recommend unless alternate timing is viable.

### Post-Interest Repricing

Question:

- Does the system prevent repricing after client presentation unless client-side facts changed?

Expected behavior:

- Bake negotiated numbers into the slate at presentation time.
- Treat the presented number as locked.
- Allow renegotiation only for client-side changes to usage, scope, timing, exclusivity, travel, or
  requirements.
- Treat any talent-side price movement after interest, without client-side fact changes, as harmful
  repricing.

### Exploratory Client Budget

Question:

- Does the system avoid overfitting to unreliable early budget signals?

Expected behavior:

- Show broader education ranges and require calibration before precise confidence.

### Dependable Talent, Similar Creative Fit

Question:

- Does a reliable talent receive a small premium without crowding out stronger creative fit?

Expected behavior:

- Apply a capped reliability premium only when the talent is already a credible match.

### Contextual Talent Upside

Question:

- Can outcome evidence support "this talent should get more this time" without exposing hidden floors
  or creating uncapped AI pricing?

Expected behavior:

- Propose a tiny shadow-mode AI discretion increase only when similar recent outcomes support the
  premium and policy caps allow it.

### Dependable Client

Question:

- Does a reliable client receive slightly more favorable pricing or flexibility?

Expected behavior:

- Apply a small client reliability benefit while preserving the talent's floor and target posture.

### High-Friction Client

Question:

- Does scope creep, slow decisions, or budget fishing create a risk premium?

Expected behavior:

- Apply a small risk nudge or reduce flexibility, then monitor whether this discourages abuse.

### Race-To-Bottom Pressure

Question:

- Does a low-rate, fast-response option become the default winner even when creative fit is weaker?

Expected behavior:

- Flag low-price/low-fit options as a market-health risk.
- Prevent race-to-bottom risk from taking the top rank by price alone.
- Trigger admin exception review when market-health flags appear.

### Autonomy-Ready Recommendation

Question:

- Which recommendations could eventually run without admin approval once launch review is no longer
  required?

Expected behavior:

- Mark recommendations as mature autonomy candidates only when there are no exception triggers:
  leakage, nonzero discretion, outside-budget posture, weak long-horizon trust, or market-health
  guardrails.

## Dry-Run Output Format

Each simulated scenario should produce a compact trace:

- project summary
- eligible talent count
- recommended slate with lanes
- client-facing talent scores
- hidden internal reasons
- client shortlist
- negotiation events
- final outcome
- policy warnings
- admin-only AI pricing rationale notes
- brand-facing AI match rationale notes
- talent-facing rationale state
- AI discretion notes
- admin approval state
- admin exception triggers
- metric updates

Example trace shape:

```json
{
  "project": "national food tabletop campaign",
  "budgetState": "flexible",
  "priceLockPolicy": "locked at client presentation unless client-side facts change",
  "recommendedSlate": [
    {
      "talent": "premium_food_director",
      "lane": "Strong Specialist",
      "clientFacingTalentScore": 92,
      "clientVisiblePriceState": "premium stretch",
      "internalAcceptanceProbability": 0.62,
      "internalRepricingRisk": "low"
    }
  ],
  "outcome": "booked",
  "finalPriceVsBudget": "+18%",
  "timingNudges": {
    "leadTimeDays": 10,
    "rateImpact": "+4% urgency premium",
    "confidenceImpact": "none"
  },
  "behaviorNudges": {
    "talent": "+3% reliability premium",
    "client": "-2% dependable client adjustment",
    "totalImpact": "+1%"
  },
  "aiRationales": {
    "adminPricingRationale": {
      "summary": "The +3% reliability premium reflects a strong history of quote stability and low booking friction.",
      "visibility": "admin-only",
      "discretionDelta": "+0.5% shadow-mode",
      "discretionEvidence": "Similar projects have closed slightly above the computed quote in recent dry runs.",
      "humanReviewRecommended": false
    },
    "brandFacingRationale": {
      "summary": "Deep food tabletop experience and a strong creative match for the brief.",
      "visibility": "brand-facing",
      "humanReviewRecommended": false
    },
    "talentFacingRationale": {
      "visibility": "not-generated"
    }
  },
  "adminGovernance": {
    "mode": "launch_admin_approval",
    "approvalRequired": true,
    "autonomyTarget": "eventual autonomous execution with exception-based admin review",
    "maxSmallSettingTweak": 0.02,
    "exceptionTriggers": [
      "nonzero AI discretion proposal"
    ],
    "matureAutonomyCandidate": false
  },
  "warnings": []
}
```

## Implementation Shape For Phase 2

When ready, keep the first simulation small and inspectable:

```text
simulation/
  config/
    policy.json
  README.md
  fixtures/
    talent.json
    projects.json
    clients.json
  src/
    scoring.*
    timing.*
    behavior.*
    admin_governance.*
    ai_rationale.*
    outcome_calibration.*
    negotiation.*
    policies.*
    runner.*
  reports/
    sample-runs/
```

Avoid production dependencies. The first version should prioritize clarity, traceability, and easy
policy changes over model sophistication.

## Phase 2 Exit Criteria

The simulation phase should produce:

- repeatable scenario runs
- visible traces for individual deals
- aggregate metrics across many rounds
- comparison across policy variants
- identified exploit paths
- recommended policy revisions before production integration
