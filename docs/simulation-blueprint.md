# Simulation Blueprint

## Purpose

The simulation engine should stress-test Distinkt pricing and negotiation policies before they are
integrated into the live platform. It should use synthetic talent, projects, clients, and reps so the
team can observe incentives, exploitability, and equilibrium risks in a safe environment.

This is a standalone research tool, not production code.

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
- target rate
- private working floor
- rate history
- availability
- responsiveness
- reliability
- negotiation behavior type
- behavior history
- category premium potential
- prestige-work preference
- utilization state
- conflict constraints

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

- brief clarity
- decision speed
- payment reliability
- scope stability
- rate-shopping frequency
- post-quote scope creep frequency

### Negotiation Agent

Talent-side negotiation behavior should be simulated separately from talent quality.

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
- creative fit score
- practical fit score
- price fit score
- acceptance probability
- expected final price band
- repricing risk
- trust score
- timing horizon nudge
- talent behavior nudge
- client behavior nudge
- AI pricing rationale
- AI rationale visibility: client-facing, internal-only, or human-review
- AI discretion delta
- AI discretion evidence summary
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

Require quote bands and only allow repricing outside the band when scoped variables change.

Expected risk:

- may reduce flexibility for nuanced human deals

### Curated Slate Marketplace

Return multiple deal paths rather than a single ranked list.

Expected risk:

- needs careful client UX to avoid appearing indecisive

### Behavior-Nudged Marketplace

Apply small capped pricing adjustments for talent and client reliability.

Expected behavior:

- dependable talent can earn a modest reliability premium
- dependable clients can receive slightly more favorable pricing
- high-friction clients can trigger a small risk premium
- volatile talent can lose recommendation confidence without being automatically underpriced

Expected risk:

- behavior scores become too influential
- clients or talent infer hidden scores from pricing changes
- one bad event has too much long-term impact without decay

### Timing-Horizon-Nudged Marketplace

Apply small capped adjustments for project timing.

Expected behavior:

- projects under 14 days can receive a modest urgency premium
- projects under 7 days can receive a stronger but capped urgency premium
- projects 90 or more days out receive a small project-confidence reduction
- strong brand or client reliability can offset some far-future uncertainty

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
6. Generate AI pricing rationale from computed adjustments and structured policy outputs.
7. Optionally apply shadow-mode AI discretion deltas based on outcome evidence.
8. Build a curated recommendation slate.
9. Simulate client shortlist behavior.
10. Simulate talent response and negotiation.
11. Resolve booking, no-booking, repricing, or cancellation.
12. Update historical outcomes.
13. Repeat across many rounds.
14. Evaluate market-level metrics.
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
- number of deals where behavior would have changed the recommendation lane
- number of deals where behavior was blocked by a cap or floor guardrail

Timing nudge safety metrics:

- percentage of deals where timing changed pricing or confidence
- average urgency premium for projects under 14 days
- average confidence reduction for projects 90 or more days out
- number of long-horizon projects later confirmed, changed, or cancelled
- number of timing nudges blocked by cap or floor guardrails

AI pricing rationale and discretion safety metrics:

- number of AI rationales generated by adjustment type
- number of AI rationales that mention private/internal-only signals
- number of AI rationales that imply the AI set the price instead of explaining computed math
- number of cases where AI recommends human review
- agreement rate between computed nudges and AI rationale text
- average AI discretion delta in shadow mode
- maximum AI discretion delta proposed
- number of AI discretion deltas blocked by caps or floor guardrails
- estimated lift or harm from AI discretion versus no-discretion baseline
- number of AI discretion recommendations lacking sufficient outcome evidence
- number of "talent should get more this time" recommendations and their later outcomes

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

- Does a project under 7 days get a stronger but still capped urgency premium?

Expected behavior:

- Apply a slightly larger urgency nudge only when schedule disruption or scarcity is real.

### Long-Horizon Project

Question:

- Does a project 90 or more days out carry lower confidence until approvals and schedule are firm?

Expected behavior:

- Reduce project confidence slightly, prefer confirmation windows, and let strong brand or client
  reliability offset part of the uncertainty.

### Unavailable Perfect Match

Question:

- Does the system preserve trust by excluding impossible options?

Expected behavior:

- Do not recommend unless alternate timing is viable.

### Post-Interest Repricing

Question:

- Can the system distinguish scope-driven repricing from tactical repricing?

Expected behavior:

- Allow reason-coded repricing for changed variables; penalize unexplained repeated behavior.

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

## Dry-Run Output Format

Each simulated scenario should produce a compact trace:

- project summary
- eligible talent count
- recommended slate with lanes
- hidden internal reasons
- client shortlist
- negotiation events
- final outcome
- policy warnings
- AI pricing rationale notes
- AI discretion notes
- metric updates

Example trace shape:

```json
{
  "project": "national food tabletop campaign",
  "budgetState": "flexible",
  "recommendedSlate": [
    {
      "talent": "premium_food_director",
      "lane": "Strong Specialist",
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
  "aiPricingRationale": {
    "summary": "The +3% reliability premium reflects a strong history of quote stability and low booking friction.",
    "visibility": "client-facing",
    "discretionDelta": "+0.5% shadow-mode",
    "discretionEvidence": "Similar projects have closed slightly above the computed quote in recent dry runs.",
    "humanReviewRecommended": false
  },
  "warnings": []
}
```

## Implementation Shape For Phase 2

When ready, keep the first simulation small and inspectable:

```text
simulation/
  README.md
  fixtures/
    talent.json
    projects.json
    clients.json
  src/
    scoring.*
    timing.*
    behavior.*
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
