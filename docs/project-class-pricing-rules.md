# Project And Talent Class Pricing Rules

These rules extract the current pricing philosophy into a shape the simulator can test.

They are hypotheses, not final production policy. The goal is to prevent the pricing engine from
treating every project, role, and talent class as the same kind of negotiation.

## Core Realization

Distinkt is not building a traditional production budgeting tool.

It is building a structured talent pricing and negotiation layer that operates inside incomplete and
evolving production information.

The platform should not pretend production uncertainty can be eliminated. It should make uncertainty
structured:

- what is assumed
- what is included
- what is excluded
- what changes the price
- what rate or range talent accepted before client presentation
- what actualized later and why

## Pricing Philosophy

### Expected Ranges, Not Fake Certainty

Commercial production pricing should usually be presented as an expected range, not a fixed guaranteed
number.

Useful labels:

- Expected Booking Range
- Estimated Production Range
- Expected Talent Range

Avoid:

- teaser "starting at" pricing
- artificially low anchor numbers
- exact guarantees before scope is stable
- exposing talent floors or hidden flexibility

Reason:

- buyers anchor to the first number they see
- a low first number followed by a higher actual number feels like escalation
- a realistic expected range followed by a close inside that range feels trustworthy

### Assumptions Make Ranges Trustworthy

Every expected range should travel with assumptions.

Common assumptions:

- prep days included
- shoot days included
- fitting days included or excluded
- travel included or excluded
- location assumptions
- standard usage assumptions
- exclusivity assumptions
- revision count
- overtime treatment
- union or non-union status
- role hierarchy or screen-time assumptions for actors
- buyout versus day-rate structure
- conflict and category-exclusivity checks
- minor status, when applicable

Pricing changes should map to assumption changes or production events. If the assumption did not change,
the price should not move after presentation except through an approved policy exception.

## Internal Pricing Concepts

The engine should keep these concepts separate.

| Concept | Purpose | Visibility |
| --- | --- | --- |
| Talent listed rate | Talent-declared market anchor or comfort posture. | Internal and talent-owned; not a public floor. |
| Legal or policy floor | SAG, state minimum wage, private working floor, or platform floor. | Internal/admin; never exposed as desperation pricing. |
| Starting offer rate | Strategic opening posture used in negotiation. | Admin/talent outreach when appropriate. |
| Expected booking range | Likely close range under current assumptions. | Useful for talent outreach and client expectation setting. |
| Expected close rate | Most likely booked rate inside the expected range. | Internal/admin, may inform the presented quote. |
| Expanded scope rate | Expected actualization if known production events occur. | Admin/client assumption language when scoped. |
| Actualized cost | Final booked plus approved production-event changes. | Historical data asset. |

Important rule:

- Distinkt can position a quote above a private floor to preserve negotiation flexibility and talent
  leverage.
- This should be treated as strategic opening positioning, not hidden markup.
- The literal private floor should not be exposed to clients or talent-facing job rationales.
- Talent-owned rate ranges remain the authority. Outcome data should create guidance, coaching, and
  admin calibration signals, not unilateral system rules that override talent-declared pricing.
- Future talent guidance should be framed as optional market intelligence, for example: similar people
  in your city are closing higher, or consider testing a small rate increase next quarter.
- Admin inclusion overrides are curation controls, not rate controls. They can make a talent visible for
  manual review when default ranking would omit them, but they cannot override talent-owned rates, legal
  floors, or rate-quoted outreach acceptance.

## Project Size Rules

All-in project size matters, but it is not the same as talent budget.

A $50k all-in project and a $100k all-in project can support different talent rates because they imply
different production scale, client sophistication, usage expectations, and risk. The engine should infer
project size bands and use them as context, not as a direct budget split.

Initial simulation bands:

| Project Size Band | All-In Budget Hypothesis | Pricing Meaning |
| --- | ---: | --- |
| Low-cash | under $25k | High constraint; risk of underpricing pressure; often needs scope education. |
| Small | $25k to $50k | Limited flexibility; talent pricing must be tightly tied to role and usage. |
| Mid | $50k to $100k | Meaningful room for specialists or leads, but still needs allocation discipline. |
| Premium | $100k to $250k | Stronger talent pricing support; higher usage and complexity expected. |
| Major | $250k to $500k | High sophistication; usage, exclusivity, and prominence can materially lift rates. |
| Large-scale | $500k to $1M | Serious production scale; stronger assumption tracking for usage, travel, approvals, and scope variance. |
| Flagship | $1M+ | Highest scale signal; expect senior stakeholders, meaningful usage/exclusivity risk, and wider actualization exposure. |

The $500k+ and $1M+ bands should remain contextual signals. They can widen expected ranges and
increase scrutiny on assumptions, but they should not mechanically allocate a percentage of the all-in
budget to talent.

These bands should be calibrated later by category, market, and actual outcomes.

Rules:

- do not divide all-in budget evenly across talent
- do not assume the client has shared the full production budget
- treat project size as a scale signal, not as proof of exact willingness to pay
- let project type and role hierarchy shape the talent allocation
- when talent budget is derived from all-in budget, carry low-confidence budget context and require
  admin review because the allocation may be wrong

## Project Type Rules

Project type changes the meaning of the same budget.

| Project Type | Pricing Implication |
| --- | --- |
| Social content | Often budget-constrained; usage may be narrower, but volume, speed, and paid usage can add cost. |
| Editorial or prestige | Can justify special handling only with talent opt-in and clear project-quality signals. |
| Commercial campaign | Usage, exclusivity, schedule, and client sophistication usually matter more. |
| National or high-usage campaign | Raises usage and exclusivity risk, especially for actors and visible creative leads. |
| Tabletop or product specialist work | Specialization can justify a premium when category fit is strong. |
| Automotive, beauty, food, fashion specialty | Category depth should lift confidence and sometimes price posture. |
| Post-production or edit-heavy work | Revisions, delivery count, and turnaround assumptions are central. |

Rules:

- project type modifies the expected range
- project type should not silently push talent below floor
- prestige should not become a generic discount mechanism
- usage and exclusivity should be explicit assumptions

## Talent Class Split

The biggest structural divide is between actor talent and production talent.

### Production Talent

Production talent includes:

- directors
- producers
- editors
- photographers
- DPs
- similar commercial production labor roles

Typical pricing behavior:

- harder private floors
- more stable day or project rates
- narrower concession space
- somewhat smaller ceilings relative to actors
- strong specialization premiums in the right category
- actualization often driven by prep days, shoot days, travel, overtime, revisions, and turnaround

Production talent pricing should consider:

- listed rate
- private working floor
- project size band
- project type
- category specialization
- usage and exclusivity
- prep/shoot/post assumptions
- schedule compression
- client trust and scope stability
- historical close rates by role and category

Production talent should not be treated as fungible labor. A food tabletop director, automotive DP, or
beauty photographer can be materially more valuable on matching projects.

### Actor Talent

Actor pricing behaves differently.

Actor floors may be driven by:

- SAG minimums
- state minimum wage
- non-union legal minimums
- union affiliation
- platform minimums
- role type and work hours

Minimum wage should be treated as an optional upstream compliance input, not a built-in wage-law
database. State, city, and local wage rules change over time and should be supplied by a compliance
service or admin input when available.

Initial smoke-test rule:

- if `local_minimum_wage_hourly` and `estimated_work_hours` are supplied, actor quotes must not fall
  below `local_minimum_wage_hourly * estimated_work_hours`
- if either value is null, the recommendation may continue but should carry an admin warning
  `minimum_wage_floor_unknown`
- the pricing engine should not infer local wage law from location text by itself

Actor upside may be driven by:

- role hierarchy
- screen time
- campaign visibility
- usage term
- paid media
- exclusivity
- conflicts
- fame or recognizability
- buyout structure
- travel and fittings

Actor pricing should not reuse production-talent floor and ceiling logic. Actors may have legal or union
floors that are lower than commercial value, and their ceiling can expand significantly with usage,
prominence, exclusivity, and brand reach.

### Country Market-Cost Priors

Until Distinkt has enough paid-rate actuals by market, country-level pricing should use a provisional
market-cost prior. The current simulation fixture stores the user-provided European cost-of-living table
in `simulation/fixtures/market_cost_indexes.json` and uses France as the baseline because the first
directional actor example was a featured actor in France at about 2500 EUR for the day.

The prior is intentionally advisory:

- it does not override talent-owned rate ranges
- it does not override union, wage, or legal floors
- it does not move a live quote automatically
- it should trigger admin review until paid-rate actuals exist
- it should be hidden from brand-facing and talent-facing explanation surfaces

Current actor prior formula:

```text
talent_cost_prior_vs_france =
  (country_cost_of_living_index / france_cost_of_living_index)
  * (country_local_purchasing_power_index / france_local_purchasing_power_index)
```

The formula is capped and labeled `cost_of_living_prior_only`. It is a bridge, not a truth source. For
example, Bulgaria currently produces a prior of about 0.413 versus France and a local budget leverage
signal of about 2.42x. That is directionally close to the idea that a production dollar can go much
further in Bulgaria, but it still may overstate or understate actual talent cost until real paid rates
arrive.

For featured actors, the simulator can turn the prior into a rough session fee and buyout context:

- reference high featured day rate in France: 2500 EUR
- pan-European 12 month usage buyout multiplier: 3.0x
- France prior one-shoot-day total: 2500 + 7500 buyout = 10000
- Bulgaria cost-prior one-shoot-day total: about 1050 + 3150 buyout = 4200

Those numbers are admin calibration context only. If Coke actuals show Bulgaria featured actors actually
top out closer to 800 for the day, the paid-rate actual should override the cost-of-living prior.

### Paid-Rate Actual Overrides

Paid-rate actuals are now modeled as their own fixture at
`simulation/fixtures/paid_rate_actuals.json`. Matching actuals take priority over the country
cost-of-living proxy for actor market context.

Initial source priority:

1. paid-rate actuals by country, role, project type, usage scope, territory, and term
2. published actor rate cards, when applicable
3. country cost-of-living proxy

This means Coke Europe or similar real paid-rate data can be imported without changing code. The actual
record supplies observed local day rate, buyout multiplier, one-shoot-day total, currency, sample size,
and confidence. It still remains advisory:

- it replaces the proxy as market evidence
- it does not override talent-owned rate ranges
- it does not move a live quote automatically
- it remains admin-facing calibration context
- broader samples should eventually increase confidence and reduce manual review

The seed fixture currently includes directional France and Bulgaria featured commercial examples so the
shape is ready for verified paid-rate imports.

### Published Actor Rate Cards

When a market has a published actor rate card for the relevant role and work pattern, that rate card
should take priority over the country cost-of-living prior when no matching paid-rate actual exists.

The first modeled example is the 2026 UK PACT/FAA background/supporting-artist card from the user-provided
PDF. For a standard day / continuous working day, the simulator uses:

- basic daily rate: 111.21 GBP
- holiday pay on the basic daily rate: 13.42 GBP
- modeled agreement floor: 124.63 GBP, rounded to a 125 GBP project quote floor
- overtime per 30 minutes, including holiday pay: 11.69 GBP
- travel allowances from 1 March 2026: 17.09, 23.89, and 20.91 GBP depending on travel band

This is not a commercial featured/lead buyout model. It is a published agreement floor for applicable UK
background or supporting-artist work. Supplementary fees, meal penalties, overtime, and travel allowances
remain event-based actualization triggers.

### Distinkt Talent Advocacy Uplift

For actors, Distinkt should not behave as a neutral price calculator. The engine should estimate a fair
local baseline and then try to improve the outcome for talent when booking realism allows.

Initial simulation policy:

- default actor talent-advocacy uplift: 3%
- background role uplift: 2%
- featured role uplift: 3%
- supporting role uplift: 4%
- lead or co-lead uplift: 5%
- hard cap: 8%
- published rate-card cases may use a smaller 2% uplift over the agreement floor

The uplift is internal/admin context only. It is not shown to brands as pricing math and it is not shown
to talent as a job-specific rationale. It is still subject to talent acceptance during rate-quoted
outreach, and it does not override talent-owned rate authority.

## Actor Role Hierarchy

Actor pricing needs role-weighted logic. A lead budget does not imply supporting cast share the same
rate, and a total casting budget should not be divided evenly.

Initial role hierarchy:

| Role | Pricing Meaning |
| --- | --- |
| Lead | Highest prominence, screen time, usage risk, and campaign association. |
| Co-Lead | Major visibility, often close to lead logic but with slightly lower prominence. |
| Supporting | Meaningful appearance, but lower visibility and usually lower allocation. |
| Featured | Noticeable but limited use; often narrower usage and lower allocation. |
| Background | Lowest role-weighted allocation; legal minimums and working conditions dominate. |

Rules:

- role hierarchy should affect expected range
- role hierarchy should affect usage and exclusivity risk
- lead allocation should not set the rate for every actor
- background and featured work should still respect legal and platform floors
- actor role pricing must be compatible with union and state rules

## Talent Outreach Rule

The pricing engine should run after candidate matching and before rate-quoted outreach is complete.

Talent outreach should include:

- job basics
- expected shoot or work dates
- project type
- role or production role
- key assumptions
- proposed rate or expected booking range
- what is included
- known events that would change the rate

Talent can then:

- accept at the proposed rate or range
- decline
- counter before the client sees them
- ask for assumption clarification before commitment

The talent response establishes the project-specific talent rate or range for client presentation.
The simulator records both the proposed outreach range and the committed range after any
pre-presentation counter, so later reports can separate normal upfront negotiation from prohibited
post-interest repricing.

Admin-curated inclusion overrides still enter through this outreach rule. A manually included talent is
not client-presentable until they have accepted or countered the project-specific rate before the client
sees them.

## Client-Facing Range Rule

Clients should see contextual transparency, not total economic transparency.

Client-facing language may explain:

- expected booking range
- included assumptions
- why a talent is a strong match
- why a specialist may sit higher in range
- what scope changes would affect the estimate

Client-facing language should not expose:

- talent floors
- hidden flexibility
- desperation or utilization
- behavior penalties
- exact internal negotiation math
- AI discretion percentages

## Event-Based Actualization

Pricing changes should be tied to known production events.

Allowed actualization triggers:

- fitting added
- prep day added
- shoot day added
- travel required
- overtime triggered
- usage expanded
- paid media added
- exclusivity added
- additional revision round requested
- delivery count expanded
- turnaround compressed
- union or legal requirement changes
- scope materially changes after quote lock

Not valid as normal repricing triggers:

- client showed strong interest
- alternatives disappeared
- talent or rep wants more without new facts
- vague "production got bigger" without assumption changes
- internal floors or hidden flexibility changed

This turns repricing from arbitrary negotiation into explainable operational logic.

## Data Collection Rules

Structured historical pricing intelligence is the moat.

The system should eventually record:

- project size band
- project type
- market or location cohort supplied by upstream project data
- talent class
- production role or actor role
- union/non-union status where relevant
- assumptions at quote time
- talent-visible proposed rate or range
- talent response: accept, decline, counter, clarification requested
- client-facing expected range
- booked rate
- actualized cost
- actualization events
- variance from expected range
- variance reason
- client trust and behavior signals
- talent readiness or reliability signals
- outcome: booked, held, cancelled, lost, revised, actualized over range

Outcome learning should separate:

- admin calibration, which can review range width, assumptions, and formula pressure
- talent guidance, which can suggest optional market tests without changing rates automatically
- client trust learning, which can separate real budget misses from talent pricing problems

Over time this enables:

- expected actualization curves
- role-specific pricing behavior
- category-specific negotiation patterns
- market-specific pricing guidance
- project-type pricing calibration
- actor vs production-talent model separation
- buyer behavior forecasting
- market-health monitoring
- talent-facing rate guidance that is positive, optional, and non-revealing

Examples of future learned insights:

- food photographers actualize 12% above expected range when added prep appears
- union actors with travel exceed estimate 28% of the time
- automotive directors close near the upper end of the range on premium projects
- prestige editorial clients with weak trust frequently fail budget calibration
- people with similar experience in a talent's city tend to close at higher rates
- a talent may want to test a small rate increase next quarter based on recent outcomes

## Creator Economy Exclusion

Creators, influencers, and UGC talent should remain outside this pricing substrate for now.

Reason:

- deliverable-based pricing
- audience valuation
- platform-specific usage
- whitelisting
- amplification
- affiliate economics
- revision-heavy content workflows

These economics behave differently enough that they should eventually get a separate pricing model.

Current focus:

- actors
- directors
- photographers
- editors
- DPs
- producers
- traditional commercial production labor structures

## Simulation Implications

The next simulation pass should add explicit fields before adding more scoring complexity.

Recommended fixture fields:

Project:

- `all_in_budget`
- `project_size_band`
- `project_type`
- `talent_class_scope`: actor, production_talent, or mixed
- `actor_role_scope`: nullable, for actor role-targeted projects
- `assumptions`
- `project_readiness_tier`
- `project_credibility_score`
- `expected_actualization_events`
- `shoot_country`
- `local_talent_market`
- `usage_territory`
- `usage_term`
- `paid_media`
- `exclusivity`
- `local_minimum_wage_hourly`: nullable
- `local_minimum_wage_source`: nullable
- `estimated_work_hours`: nullable
- `usage_rights`
- `buyout_or_day_rate`
- `conflict_check_required`
- `minor_status`

Client:

- `clientTrustScore`
- `clientTrustTier`
- `brandPrestigeTier` or `brandPrestigeScore`, separate from trust

Talent:

- `talent_class`: `actor` or `production_talent`
- `production_role`: director, photographer, DP, editor, producer
- `actor_role`: lead, co_lead, supporting, featured, background
- `union_status`
- `legal_floor_basis`
- `range_width_preference`
- `rates_updated_at`
- `recent_confirmed_platform_rates`

Recommendation:

- `expectedBookingRange`
- `assumptionsIncluded`
- `actualizationTriggers`
- `talentOutreachRateState`
- `clientRangeState`
- `activeQuoteVersion`
- `quoteAuditRequired`

Validation:

- actor recommendations must respect actor floor basis
- production talent recommendations must respect working floors
- client-facing ranges must include assumptions
- actualization must cite an allowed event trigger
- creator/influencer fixtures should be rejected or marked out of scope
- stale talent rates should trigger refresh, confidence reduction, or admin review
- below-ready project credibility should block binding quotes or require logged admin override

## Near-Term Rule To Test

Before building a full pricing matrix, test this:

```text
same budget + different project type + different talent class = different expected range behavior
```

Example:

- $50k social project with a production photographer
- $50k national usage actor role
- $100k campaign with a production director
- $100k campaign with a lead actor
- $500k large-scale campaign with high assumption complexity
- $1M+ flagship campaign with senior-stakeholder and usage risk

The system should not price these by a single budget-fit formula.
