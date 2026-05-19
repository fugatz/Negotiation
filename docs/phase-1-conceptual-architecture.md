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
  -> Upstream Candidate Matching
  -> Matched Talent Candidate Set
  -> Late-Stage Creative + Practical Scoring
  -> Pricing Intelligence Layer
  -> Timing Horizon Nudge Layer
  -> Behavior Reputation Nudge Layer
  -> AI Pricing Rationale Layer
  -> Rate-Quoted Talent Outreach / Availability Check
  -> Talent Project-Rate Commitment
  -> Curated Recommendation Layer
  -> Deal Outcome Feedback Loop
```

## Layer Responsibilities

### System Boundary

This pricing and deal intelligence layer should run late in the booking workflow. It is not the
top-of-funnel matcher and should not be responsible for initial outreach.

By the time this engine runs, Distinkt has already done most of the work:

- the brief has been structured
- candidate talent has been matched by upstream systems or human operators
- obvious pre-outreach constraints have been screened where available
- upstream services have supplied readiness, reliability, and client trust signals

This engine then determines the project-specific rate posture for matched talent. That rate is included
in the talent outreach or availability-check message through channels such as WhatsApp and email, along
with the job basics. The talent's response establishes whether they want to be considered for that
project at that rate before the client sees the slate.

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

### 2. Matched Candidate Inputs

This stage should be treated as an input from upstream matching, not as the primary job of the pricing
engine. The pricing engine should receive matched talent candidates plus any known constraints before
rate-quoted outreach begins.

The pricing engine consumes enough context to decide the project-specific rate to put in front of talent
during outreach. The final eligibility signal for client presentation comes from the rate-quoted
availability response: accept, decline, or counter before the client sees the talent.

Examples:

- unavailable for shoot dates
- location or travel impossible
- category conflict
- exclusivity conflict
- required credential missing
- budget fundamentally incompatible unless flagged as an intentional stretch

The simulation may keep a tiny deterministic eligibility stub so test scenarios remain inspectable, but
that stub represents known pre-outreach constraints plus the later rate-quoted availability response. It
should not be interpreted as the future production matching system.

### 3. Creative + Practical Match Scoring

This layer estimates fit and booking usefulness for the already-matched candidate set before rate-quoted
talent outreach.

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

Project context should include project size, project type, assumptions, and talent class. Actor pricing
and production-talent pricing should not share the same floor and ceiling logic. See
[Project And Talent Class Pricing Rules](project-class-pricing-rules.md) for the working rule set.

Possible internal states:

- listed rate: the talent-declared market anchor
- talent-approved operating band: normally 25% below to 30% above listed rate
- working floor: what talent might accept under the right conditions
- historical accepted range
- category premium potential
- scarcity premium
- urgency premium
- desirability adjustment for prestige or strategic value
- negotiation volatility risk

The output should be a recommendation state rather than a single mechanical number.

Example internal outputs:

- expected booking range
- estimated production range when assumptions are broad enough
- defensible premium range
- client budget fit state
- talent acceptance probability
- timing horizon nudge
- counteroffer risk
- late-stage repricing risk
- recommended negotiation posture
- assumption set and allowed actualization triggers

Pricing should not be a single fixed number unless scope is stable enough to justify it. Ranges are
often more honest and more trustworthy because production assumptions change.

### 5. Timing Horizon Nudge Layer

Timing should create small pricing and confidence adjustments, but it should not dominate fit,
specialization, or budget reality.

Near-term projects can reasonably cost more because they create disruption, scarcity, and opportunity
cost. Far-future projects can be less reliable because scope, budgets, approvals, and schedules often
shift before booking.

Initial timing hypotheses:

- projects inside 21 days should be treated as last-minute for the platform
- projects inside 14 days may receive a stronger but still capped urgency premium
- projects 90 or more days out may signal exploration rather than serious booking intent
- platform client trust should heavily offset long-horizon uncertainty
- a client with no Distinkt history should remain low-confidence at 90+ days
- a repeat client, especially around a 4th project and beyond, should receive much more benefit of
  the doubt

Possible timing nudges:

- last-minute urgency premium under 21 days, for example 2% to 6%
- extreme compression premium under 14 days, for example up to 8% when disruption is real
- long-horizon seriousness reduction at 90+ days, for example 2% to 5% against booking certainty
- optional quote confirmation window for far-future work

Guardrails:

- timing should not become a blanket surcharge or discount
- 90+ day uncertainty should affect seriousness scoring, confidence, holds, and confirmation mechanics
  first
- platform client trust should drive how much 90+ day uncertainty matters
- 90+ day uncertainty should not directly change talent price unless client-side facts change or a
  quote/hold expires and must be revalidated
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

This layer should primarily consume behavior scores from upstream Distinkt services rather than
recreate those metrics locally.

Known upstream inputs:

- actor readiness score
- non-actor talent reliability metric
- client trust metric

Those inputs are still immature and may need to be nudged, recalibrated, or versioned over time, but
they already exist and should be passed into this pricing/deal layer from outside processes.

Underlying talent-side signals that may feed upstream services include:

- quote stability
- response consistency
- hold and cancellation reliability
- accurate availability
- professional counteroffer behavior
- scope-change reason quality
- attempted post-presentation repricing frequency

Underlying client-side signals that may feed upstream services include:

- brief clarity
- scope stability
- decision speed
- payment reliability
- respectful negotiation behavior
- rate-shopping or budget-fishing patterns
- late scope creep after quote lock
- client-side manager, procurement, or approval-chain intervention that creates friction, delay, or
  unexplained repricing pressure

Possible pricing nudges:

- dependable talent may receive a small reliability premium
- difficult talent may receive small downward quote pressure, for example -2%
- dependable clients may receive slightly more favorable pricing because they reduce transaction risk
- high-friction clients may see a small risk premium, for example +2%, or reduced flexibility
- both talent-side and client-side behavior can apply on the same deal, subject to the total cap
- disruptive client-side manager or procurement behavior should be attributed to the client side

Initial guardrail hypothesis:

- behavior is a small friction tax, not a moral ranking system
- difficult-but-valuable people should not be made unbookable just because they are difficult
- behavior nudges should usually sit in the 1% to 3% range
- severe behavior impact should be hard-capped around 5%
- total behavior impact should not dominate creative fit, specialization, budget reality, or client
  demand
- this layer should not silently redefine upstream readiness, reliability, or trust scores
- this layer may send outcome feedback back to those upstream services for later calibration
- there should be no separate appeal process inside this pricing layer because the nudge is small and
  not exposed as a visible penalty
- recovery should happen as upstream readiness, reliability, or trust scores improve from positive
  behavior data
- behavior should never move a deal below a talent's private working floor
- behavior should never override outreach eligibility, creative fit, or major budget incompatibility
- client-facing explanations should describe process reliability, not expose hidden reputation scores

This layer is intentionally a stub for later policy design. Exact metric definitions and decay
windows should live in the upstream services that own readiness, reliability, and trust.

### 7. AI Pricing Rationale Layer

Distinkt already has brief extraction, so this layer should not duplicate brief parsing,
normalization, missing-field detection, category identification, or creative-fit extraction.

Instead, AI reasoning should operate after structured project data, eligibility results, match scores,
pricing intelligence, timing nudges, and behavior nudges already exist.

The useful role for AI is admin-only pricing rationale. The math decides the primary bounded
adjustment; AI explains to Distinkt operators why that adjustment is reasonable.

Admin-only pricing rationale examples:

- explain why a dependable talent earns a 2% reliability premium
- explain why a dependable client receives a 1% or 2% transaction-risk benefit
- explain why an under-14-day project has a small urgency premium
- explain why a 90+ day project has lower seriousness confidence until commitments firm up
- explain why a specialist premium is defensible for a highly relevant category match
- explain why a high-friction client creates a small risk premium or reduced flexibility

That pricing rationale should not be shown to talent or brands. It can mention deltas, timing nudges,
behavior nudges, trust, discretion, and "why X instead of Y" because it is an internal admin surface.

AI may also generate a separate brand-facing match rationale, but that rationale should be
deliberately positive and non-pricing. It can say:

- strong category experience
- relevant specialist background
- creative fit for the brief
- production fit
- confidence in the path to confirmation

It should not say:

- why the rate moved by a specific percentage
- whether behavior, reliability, readiness, or client trust changed the quote
- anything about hidden flexibility, floors, discount posture, or willingness to concede
- why one talent is getting more or less on this job in pricing terms

Talent should not receive a job-specific pricing rationale from this layer. Talent-facing education
about readiness, reliability, or other score items belongs to the upstream score systems that own
those metrics. Even then, the talent should never see a negative pricing penalty framed as the reason
they got less on a specific job.

Optional future extension:

- AI may receive a small outcome-calibrated discretion band that can add or subtract a tiny residual
  adjustment over time based on observed booking outcomes.

This should be treated as a learned residual, not base pricing authority. For example, if repeated
outcomes show that a specific kind of deal closes reliably at slightly higher rates, or routinely
fails unless a small concession is made, the AI can recommend a narrow discretion delta.
Talent-owned rate ranges remain the authority; outcome data should become guidance and coaching, not a
rule that silently overrides what talent declared.

The core use case is contextual upside recognition:

- "this talent should get more this time" because the current opportunity is unusually well matched,
  the market has accepted similar premiums, or recent outcomes show that this talent is underpriced in
  this context
- "this deal may need a softer posture this time" because similar opportunities have repeatedly
  failed at the computed quote despite otherwise strong fit

This is different from exposing a private floor or asking who will concede. It is an evidence-backed
way to recognize context-specific value or friction that the fixed scoring model has not fully
learned yet.

Initial discretion guardrails:

- default discretion starts at 0%
- early shadow-mode discretion should be advisory only
- launch-mode live discretion should require admin approval
- initial live discretion should be very small, for example +/-1%
- mature discretion might expand only with evidence, for example up to +/-3%
- discretion must be auditable and tied to outcome evidence
- discretion must decay when outcomes change
- discretion must never push below a talent floor
- discretion must never bypass timing, behavior, or market-health caps
- discretion should require human review when rationale is sensitive or confidence is low

AI should not:

- extract or normalize the original brief
- decide category fit or creative nuance when that already exists upstream
- decide base adjustments such as whether the timing or behavior nudge is 1%, 2%, 5%, or 8%
- apply discretion outside the approved outcome-calibrated band
- expose floor rates or hidden flexibility
- expose admin pricing rationale to brands or talent
- generate negative job-specific score explanations for talent
- override outreach eligibility
- create uncapped pricing changes
- invent client or talent reputation facts
- convert a low-price option into the default winner without policy support

The operating principle:

- AI reasons about the policy output.
- AI justifies bounded math with admin-only human-readable rationale.
- AI generates separate brand-facing match language that is positive, creative, and non-pricing.
- AI may eventually recommend a tiny outcome-calibrated residual adjustment.
- The policy engine governs actual eligibility, caps, floors, and pricing movement.

### 8. Admin Governance and Launch Approval Layer

These remaining questions are admin-only governance questions:

- which rationales require human review before anything is shown to a client
- how to audit public explanations for leakage
- what outcome evidence allows AI discretion to move from advisory to live
- what cap governs AI discretion
- how discretion decays when outcomes contradict older patterns
- what market-health constraints override short-term booking probability

In the ideal mature state, the pricing and negotiation engine should run autonomously inside policy
guardrails, with admins reviewing exceptions rather than approving every normal deal.

Launch mode should be more conservative:

- every generated slate and pricing posture requires admin approval before client presentation
- AI discretion remains shadow/advisory unless explicitly approved
- brand-facing rationale copy is reviewed or at least leakage-checked before presentation
- admin users can make small bounded adjustments to settings, not arbitrary uncapped price changes
- every admin approval, rejection, override, and setting tweak is logged with actor, timestamp,
  reason, policy version, and before/after values

Admin interface controls can include:

- timing threshold and cap settings
- behavior nudge cap settings
- AI discretion cap and mode: off, shadow, admin-approved live, or autonomous live
- market-health override thresholds
- brand-facing rationale wording/templates
- quote lock and scope-change exception categories
- hold policy settings for long-horizon work
- admin-curated inclusion overrides for edge-case talent who should be manually reviewed even when
  default ranking would not surface them

Admin adjustment guardrails:

- admin tweaks must remain inside talent-approved operating bands and floor guardrails
- admin tweaks must not expose private floors, hidden flexibility, or behavior penalties
- admin tweaks must not weaken the client presentation price lock
- admin inclusion overrides may affect curation visibility only; they must not override the talent's
  owned rate, hard eligibility constraints, or rate-quoted outreach acceptance
- settings should be versioned so simulations and real outcomes can be replayed against the exact
  policy used
- repeated manual overrides should become a signal that the underlying policy needs recalibration

Initial admin-only governance defaults:

- Human review: launch requires approval for all client-presented slates. Mature mode can move to
  exception review for brand-facing leakage, nonzero AI discretion, weak evidence, low market health,
  long-horizon uncertainty, or outside-band pricing.
- Leakage audit: public payloads should be generated from a separate schema, scanned for forbidden
  terms, checked for percentage/rate language, and regression-tested against synthetic edge cases.
- Evidence threshold: AI discretion should move from advisory to live only after enough similar
  outcomes show consistent lift without higher cancellation, repricing, trust damage, or quality
  degradation.
- Discretion cap: launch live discretion should be 0% by default, then at most about +/-1% with admin
  approval; mature autonomous discretion should remain tiny unless outcome evidence is very strong.
- Decay: discretion should shrink toward 0 when recent outcomes contradict older patterns, when
  evidence gets stale, or when market conditions change.
- Market health override: protect specialist value, avoid lowest-bidder ranking, block floor leakage,
  avoid desperation pricing, preserve slate diversity, and prevent behavior/timing nudges from
  dominating creative fit.

### 9. Negotiation Structure Layer

Negotiation should remain possible, but bounded.

The core rule: pricing is negotiated and finalized before a talent is presented to the client. At talent
outreach or availability check, Distinkt shows the talent the job basics and the proposed rate for that
project. The proposed rate comes from this pricing engine at that point in the workflow. The talent can
opt in at that rate, decline, or counter before the client ever sees them. Once a talent appears in the
client-facing slate, that presented number should be treated as locked.

Possible mechanisms:

- pre-presentation availability and quote commitment window
- structured internal counteroffer bands before presentation
- quote expiration periods
- presentation price lock
- scope-change repricing rules when client-side facts change
- explicit "new information" triggers for price changes after presentation
- client budget revision flow when scope or expectations shift

Strong negotiation means being willing to hold the presented price or let the client walk away. It can
also mean choosing not to present a talent if the project is not economically credible.

Because the client receives a range of talent options, the talent-approved economics should already
be baked into the slate at presentation time. The slate itself provides alternatives; late talent-side
repricing should be structurally blocked after the client has shown interest.

Legitimate renegotiation after presentation should require client-side fact changes.

Examples:

- usage expanded
- timeline compressed
- deliverables increased
- exclusivity added
- travel burden changed
- competitor conflict introduced
- client approval chain changes the scope, timing, or requirements

Harmful repricing:

- price rises only after strong client interest
- no client-side fact change
- alternatives have expired
- pattern repeats across multiple deals
- the change is driven by leverage rather than scope, usage, timing, or requirements

### 10. Curated Recommendation Layer

The client should see a curated slate, not a commodity auction.

Each slate option should carry the negotiated/priced posture at the moment of presentation. The client
can compare different talent paths, but they should not experience a hidden second negotiation after
choosing an option unless they change the facts of the project.

Recommendation categories could include:

- Best Fit
- Strong Specialist
- Budget-Confident
- Premium Stretch
- Emerging Value
- Fastest Viable Path

Avoid labels that imply desperation or discounting.

Client-facing trust should be expressed through a composite talent score rather than exact price
guarantees or pricing explanations.

Possible framing:

- Distinkt Score
- Match Confidence Score
- Booking Confidence Score

The exact name can be decided later, but the behavior should be simple: higher is better.

The internal score can combine many factors, such as:

- creative fit
- category specialization
- availability confidence
- pricing confidence
- professionalism and reliability
- timing fit
- relevant outcome history
- client-side friction risk
- deal complexity

This score should adjust over time as Distinkt gathers more outcome data. It should not expose exact
internal components, private floors, negotiation flexibility, behavior penalties, or pricing nudges.
It should also not imply a guaranteed final price. Its job is to help the client understand which
options are stronger and more dependable without turning the slate into a lowest-price auction.

The brand-facing AI rationale that accompanies this score should stay positive: experience, creative
fit, specialist background, production fit, and confidence. Any rationale about why the quoted price
is 2% higher, 2% lower, or shaped by behavior/trust inputs remains admin-only.

Admins may add an inclusion override when a high-profile, infamous, unusually requested, or strategically
important talent should be considered despite default ranking or matching not surfacing them. This is a
curation override, not a rate override. The talent still controls their rate, the system still computes
the project-specific offer, and the talent must still opt in during rate-quoted outreach before any
client-facing presentation.

Client-facing pricing language should communicate confidence and fit:

- "Within expected range"
- "Likely workable with scoped usage"
- "Premium specialist; budget may need adjustment"
- "Strong creative fit, lower booking confidence at current budget"

### 11. Deal Outcome Feedback Loop

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
- actualized cost against the expected booking range
- optional talent guidance generated from repeated market signals

The feedback loop should improve prediction without turning private flexibility into public pressure.
It should also create optional talent-facing market guidance, such as "people with similar experience in
your city tend to close higher" or "consider testing a small rate increase next quarter." That guidance
is educational and talent-owned, not an automatic rate change.

## Pricing Model Concepts

### Listed Rate

Talent's declared economic anchor. This is useful for dignity, positioning, and premium logic.

Talent sets this rate with the understanding that Distinkt may operate within a normal band around the
listed rate:

- up to 25% below listed rate
- up to 30% above listed rate

This band serves two purposes:

- availability-check routing
- bounded negotiation wiggle room

It is still not a public/client-visible negotiation range and not a disclosed floor.

Example:

- listed rate: $10,000
- normal availability-check window: $7,500 to $13,000

The purpose is to avoid asking talent about every low-fit or unrealistic opportunity while preserving
practical flexibility around real projects. Within the band, Distinkt can reason about likely deal
paths without treating every movement as bespoke renegotiation.

Risk:

- If treated as fixed truth, it may overprice talent out of relevant opportunities.
- If the lower edge is exposed, clients may treat it as a discount target.

Mitigation:

- Pair it with context and probability rather than using it as a hard rule.
- Keep the band internal and use it for availability-check routing and bounded negotiation, not
  client-facing pricing.
- Let outcomes calibrate where inside or outside the band successful deals actually close.
- Use outcome calibration as market guidance, not as a replacement for talent-declared pricing.

### Working Floor

Private minimum viable acceptance under favorable conditions.

Talent should not be asked to maintain separate floor rates for every combination of category, usage,
client type, timing, exclusivity, and urgency. That would create too much operational burden and too
much false precision.

Preferred approach:

- talent declares a listed rate
- Distinkt uses the internal 25% below to 30% above operating band
- context-specific factors are handled by scoring, pricing intelligence, timing nudges, behavior
  nudges, and outcome calibration
- talent can still define explicit exceptions later for truly special cases

Risk:

- If exposed or optimized against, it creates commoditization and distrust.
- If the system asks for too many floor variants, talent data becomes stale, inconsistent, or unused.

Mitigation:

- Never expose it. Use it only to reason about feasibility and internal negotiation boundaries.
- Keep talent input simple, then let system intelligence and outcomes handle contextual nuance.

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

- Require pre-presentation availability checks at project-specific rates.
- Allow post-presentation repricing only with scoped client-side change reason codes.
- Track pre-presentation counters separately from attempted post-presentation price changes.
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
- Client-facing talent score: composite higher-is-better score that summarizes match quality and
  booking confidence without exposing private inputs.
- Timing horizon nudge: small capped adjustment for urgent or far-future project timing.
- Talent behavior nudge: small capped adjustment for dependable or high-friction talent behavior.
- Client behavior nudge: small capped adjustment for dependable or high-friction client behavior.
- Admin pricing rationale: internal human-readable explanation of computed pricing, timing, behavior
  nudges, and discretion within hard policy guardrails.
- Brand-facing match rationale: positive explanation of experience, creative fit, specialist value,
  and production fit, with no pricing or hidden-score logic.
- Talent-facing score education: handled by upstream score systems, not by the job-specific pricing
  layer.
- AI discretion delta: optional tiny learned residual adjustment based on outcome evidence, bounded by
  separate caps.
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
10. Projects under 21 days should be treated as last-minute for the platform, and projects roughly 90
    or more days out should carry lower seriousness confidence until the brief, approvals, and
    schedule become firmer.
11. AI discretion should start at 0%, run in shadow mode first, and only graduate to tiny live
    adjustments when outcome data shows consistent improvement.
12. Talent declares a listed rate, and the normal internal operating band is 25% below to 30% above
    that listed rate for availability checks and bounded negotiation.
13. Outcome data may inform guidance and coaching, but talent-owned ranges remain the pricing
    authority.
14. Talent should not need to maintain separate floor-rate matrices by category, usage, client type,
    and timing; those contextual differences should be handled by pricing intelligence and outcomes.
15. Distinkt is the talent-side agent. If a client-side manager, procurement team, or approval chain
    creates friction, delay, repricing pressure, or bad-faith negotiation behavior, the client side
    absorbs the same trust/desirability impact as if the client did it directly.
16. Client-facing trust should be expressed through a composite talent score that improves with fit,
    reliability, and outcome data, without implying an exact price guarantee.
17. Once pricing is presented to the client, it is locked unless client-side facts change. Strong
    negotiation happens before presentation and includes being willing to let a client walk away.
18. Talent sees the project-specific proposed rate during outreach or availability check and decides
    whether to be considered at that rate before the client sees the slate.
19. The pricing engine should run after upstream matching but before talent outreach is complete, because
    the WhatsApp/email outreach should include the proposed project rate.
20. Long-horizon uncertainty should affect seriousness confidence and hold/confirmation mechanics,
    not direct talent price, unless facts change or a quote/hold expires and must be revalidated.
21. For projects planned 90+ days out, platform client trust should strongly offset uncertainty: a new
    client is low-confidence, while a high-trust repeat client around their 4th project or later is
    much more credible.
22. Talent/client behavior nudges should consume upstream service scores: actor readiness,
    non-actor talent reliability, and client trust. This layer applies capped nudges; it does not own
    the raw metric definitions.
23. Behavior should function like a small friction tax. It should be meaningful but not terribly
    detrimental; difficult but valuable talent or clients should not be excluded by behavior scoring
    alone.
24. Behavior nudge recovery should happen through positive upstream data improving readiness,
    reliability, or trust scores. There should not be a separate appeal process in this pricing layer.
25. Admins may see the detailed pricing rationale, including nudges and discretion. Brands should see
    separate positive match rationale only. Talent should not see negative job-specific pricing
    rationale from this layer.
26. Launch mode should require admin approval before client presentation. The long-term target is an
    autonomous engine with exception-based admin review.
27. Admins may tune small policy settings, but all adjustments must be bounded, versioned, logged, and
    replayable in simulation.
28. Market-health overrides should prevent low-price/low-fit options from becoming the default winner
    by price alone, while still allowing them to appear for admin review when relevant.

## Admin-Only Governance Decisions

These are not brand-facing or talent-facing questions. They belong in admin tooling, policy
configuration, simulation review, and audit logs.

- Human review threshold: launch requires approval for all slates and pricing. Mature mode should
  require review only for exceptions such as public-rationale leakage, nonzero AI discretion,
  low-confidence evidence, market-health overrides, or unusual deal risk.
- Leakage tests: audit brand-facing outputs for forbidden terms, percentage/rate language, hidden
  score references, floor/flexibility language, and any implication that AI set the price.
- Outcome evidence: require repeated similar outcomes, positive close-rate or value lift, no increase
  in cancellations/repricing, and no market-health harm before discretion becomes live.
- AI discretion cap: keep launch at 0% live by default, allow only tiny admin-approved movement, and
  keep mature autonomous discretion separately capped from timing and behavior nudges.
- Decay: weight recent outcomes more heavily, shrink discretion toward 0 when newer data contradicts
  older patterns, and expire stale evidence.
- Market-health overrides: block decisions that create lowest-bidder dynamics, specialist
  underpricing, floor leakage, desperation pricing, quote instability, or over-reliance on behavior
  and timing nudges.

## Phase 1 Exit Criteria

Before moving to simulation implementation, the team should agree on:

- private vs public pricing boundaries
- score families and definitions
- negotiation abuse definitions
- timing nudge boundaries for urgent and long-horizon work
- behavior nudge boundaries for talent and clients
- launch admin approval workflow and tweakable policy settings
- initial policy hypotheses
- synthetic scenario coverage
- what success and harm look like in dry runs
