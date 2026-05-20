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
- talent class: actor or production talent
- production role, when applicable: director, photographer, DP, editor, producer
- actor role, when applicable: lead, co-lead, supporting, featured, background
- union status and legal floor basis, when applicable
- categories and specialization depth
- listed rate
- talent-approved operating band, initially 25% below to 30% above listed rate
- talent-owned rate authority; platform outcome data guides but does not override declared pricing
- private working floor
- rate history
- rates updated timestamp
- recent confirmed platform rates, when available
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
- all-in budget
- project size band
- project type
- market or location cohort supplied by upstream project data
- country market-cost context, when supplied or inferable from market/country fields
- talent class scope: actor, production talent, or mixed
- actor role scope for actor-only opportunities
- budget type
- pricing assumptions: prep, shoot days, fitting, travel, usage, exclusivity, revisions, overtime
- lead time in days
- timing horizon: last-minute, normal, long-horizon
- project commitment confidence
- project readiness tier or project credibility score
- brand reliability signal
- schedule urgency
- location
- usage scope
- usage territory and usage term, especially for actor buyouts
- creative specificity
- prestige value
- client flexibility
- booking intent strength
- conflict or exclusivity requirements
- admin inclusion override ids and reason codes, when a human wants an edge-case talent reviewed
  despite default ranking

Example briefs:

- firm-budget food social campaign
- flexible-budget national beauty campaign
- low-cash prestige editorial opportunity
- last-minute automotive shoot
- exploratory brand research brief
- high-usage luxury fashion campaign

Project size, project type, and talent class should be modeled explicitly before adding more scoring
complexity. The system should not price a $50k social project, a $50k national actor role, a $100k
director-led campaign, and a $100k lead-actor campaign with one generic budget-fit formula.

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

- main-site `clientTrustScore`, from 0 to 100
- main-site `clientTrustTier`: Premium, Established, Emerging, or New
- client trust score breakdown, when available for admin audit
- Verified Brand and Agency Account admin flags
- brand prestige tier or brand desirability score, separate from client trust
- brief clarity
- decision speed
- payment reliability
- scope stability
- rate-shopping frequency
- post-quote scope creep frequency
- completed Distinkt project count

The simulator treats `clientTrustScore` and `clientTrustTier` as upstream product inputs. It does not
own the formula. The current product score gives up to 30 points for completed projects, 20 for payment
speed, 15 for Persona ID verification, 5 for website presence, 20 for the Verified Brand admin flag, and
10 for the Agency Account admin flag. Score tiers are Premium at 71+ or Verified Brand, Established at
41+ or Agency Account, Emerging at 1-40, and New at 0.

There is also a separate project credibility score in the main product. This simulator can consume it
when supplied; otherwise fixtures may use project commitment confidence as a proxy.

Production integration should also consume a separate brand prestige or strategic desirability signal.
The simulator should not overload `clientTrustScore` with brand desirability because trust and prestige
can push deal posture in opposite directions.

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

- rate-quoted outreach response state
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
- outcome guidance authority: guidance-only, talent-owned rate range
- admin approval state
- admin exception triggers
- bounded admin setting tweak controls
- market health score
- recommendation lane
- country market-cost prior state
- actor market-rate prior state, when role, country, and usage are available

Recommendation lanes:

- Best Fit
- Strong Specialist
- Budget-Confident
- Premium Stretch
- Emerging Value
- Fastest Viable Path
- Admin Curated

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

Require pre-presentation availability checks at a proposed rate, present locked talent-approved
numbers to the client, and only allow renegotiation after presentation when client-side facts change.

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
- `clientTrustScore` and `clientTrustTier` heavily offset 90+ day uncertainty
- new clients remain low-confidence at 90+ days
- high-trust repeat clients around their 4th project or later are treated as much more credible

Expected risk:

- urgency premiums become too automatic
- long-horizon projects are unfairly penalized despite serious planning signals
- clients infer that early planning weakens their negotiating position

## Simulation Loop

```text
1. Generate synthetic project brief.
2. Import or emulate an upstream-matched talent candidate set.
3. Consume known candidate constraints: minimum notice, opt-ins, conflicts, and upstream scores.
4. Score creative, practical, pricing, trust, and market-health dimensions for that late-stage set.
5. Apply capped timing-horizon nudges.
6. Apply capped talent and client behavior nudges.
7. Compute the proposed project rate for each matched talent.
8. Enter `Outreach & Lock`: simulate call-for-details or email-offer talent outreach that includes job basics and the proposed project rate.
9. Record opt-in, decline, or pre-presentation counter as the committed talent-side quote state.
10. Generate admin-only AI pricing rationale from computed adjustments and structured policy outputs.
11. Generate separate brand-facing AI match rationale that avoids pricing and hidden-score logic.
12. Record that this layer does not generate talent-facing job-specific pricing rationale.
13. Optionally apply shadow-mode AI discretion deltas based on outcome evidence.
14. Add launch-mode admin governance: approval required, exception triggers, and tweakable settings.
15. Add any admin inclusion overrides as a separate curation surface from talent-approved rates only.
16. Build a curated recommendation slate from talent-approved rates only.
17. Simulate client shortlist and decision behavior against locked active quote versions.
18. Resolve booking, no-booking, hold, repricing exception, or cancellation.
19. Update historical outcomes.
20. Repeat across many rounds.
21. Evaluate market-level metrics.
```

Production boundary:

- the real system should enter this flow after candidate matching, but before rate-quoted outreach is
  complete
- production should represent this as an explicit `Outreach & Lock` workflow state before Pitch Review
  Room visibility
- hard eligibility for client presentation is established by the call-for-details or email-offer response at
  the proposed project rate
- the simulation's deterministic eligibility checks only emulate known candidate constraints and
  rate-quoted outreach responses so edge cases remain easy to inspect
- this layer's key action is to compute the project-specific rate and include that rate in talent
  outreach before the client sees the slate
- DFOS should consume the locked gross quote as a one-way input, not recalculate the quote
- quote records should be versioned and audit logged so client slates cannot display stale values
- binding Outreach & Lock should be gated by project readiness; under-baked briefs should produce
  admin-only ranges or scope calibration unless an admin override is logged

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

- post-presentation repricing exception frequency
- pre-presentation talent counter frequency
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

- attempted post-presentation repricing without client-side fact changes
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

Outcome-learning metrics:

- number of booked outcomes that receive actualized cost records
- number of actualized costs inside, above, or below the expected booking range
- average actualization lift over locked quote
- number of actualization events tied to allowed triggers
- number of optional talent-guidance messages generated
- number of guidance messages that would automatically change talent rates, which should remain zero
- cohort summaries by role, category, project size band, market, and client trust tier
- number of optional cohort-guidance messages generated

Admin governance metrics:

- number of recommendations requiring launch admin approval
- number of recommendations that would be mature-mode autonomy candidates
- exception trigger counts by reason
- number of admin setting tweaks used in dry runs
- number of admin inclusion overrides and whether they later booked, failed, or required calibration
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
- admin inclusion overrides must be admin-only, curation-only, and unable to bypass rates, hard
  eligibility, or rate-quoted talent acceptance
- client-visible quote version must match the talent-approved active quote version
- binding quote generation should be blocked or exception-reviewed when project readiness is below the
  agreed threshold
- public rationales must not make the price appear algorithm-derived

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

### Admin-Curated High-Profile Talent

Question:

- Can an admin rescue a famous, infamous, or strategically requested talent from being invisible without
  changing their rate?

Expected behavior:

- Add the talent to an admin-only curation lane, require launch approval, keep the rate talent-owned,
  and still require rate-quoted outreach acceptance before client presentation.

### Post-Interest Repricing

Question:

- Does the system prevent repricing after client presentation unless client-side facts changed?

Expected behavior:

- Bake negotiated numbers into the slate at presentation time.
- Talent sees the proposed project rate in outreach or availability check and decides whether to be
  considered at that rate before the client ever sees the option.
- Treat the presented number as locked.
- Allow renegotiation only for client-side changes to usage, scope, timing, exclusivity, travel, or
  requirements.
- Treat any talent-side price movement after client presentation, without client-side fact changes, as
  a policy failure rather than a normal negotiation event.

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
- project context and expected booking ranges
- pre-presentation rate-quoted outreach checks
- client decision events
- post-decision outcome-learning and actualization records
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
      "expectedBookingRange": {
        "label": "Expected Booking Range",
        "low": 18000,
        "high": 24000,
        "expectedClose": 21000,
        "assumptionsIncluded": ["1 shoot day assumed", "campaign usage assumed"],
        "actualizationTriggers": ["prep day added", "travel required", "usage expanded"]
      },
      "availabilityCheck": {
        "status": "accepted_at_presented_rate",
        "proposedRange": {
          "label": "Expected Booking Range"
        },
        "committedRange": {
          "label": "Expected Booking Range"
        },
        "completedBeforeClientPresentation": true,
        "clientVisible": false
      }
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
    ranges.*
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
