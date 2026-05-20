# Integration Contract

## Purpose

This contract defines how the standalone pricing and negotiation engine should connect to the main
Distinkt platform after dry-run confidence improves.

It is not production code. It is the boundary document that keeps matching, outreach, quote locking,
Pitch Review Room, DFOS, admin review, and outcome learning from stepping on each other.

## Workflow Boundary

The engine runs late in the process, after upstream matching and before client slate visibility.

```text
Structured Brief
  -> Upstream Matching
  -> Matched Candidate Set
  -> Pricing Engine Computes Project-Specific Offer
  -> Outreach & Lock
  -> Talent Accepts, Declines, Counters, Or Requests Clarification
  -> Active Locked Quote Version
  -> Client Slate / Pitch Review Room
  -> DFOS Reads Locked Quote
  -> Booking / Hold / Scope Reopen / No Booking
  -> Outcome Learning
```

The pricing engine owns the project-specific quote recommendation. The main site owns workflow state,
user communication, project data, talent profiles, client scores, quote audit storage, and user-facing
surfaces.

## State Model

Recommended states:

| State | Meaning |
| --- | --- |
| `matched_candidates` | Upstream matching has produced possible talent. |
| `pricing_ready` | Project has enough structured data to compute a project-specific offer. |
| `scope_calibration_required` | Brief is too incomplete for binding Outreach & Lock. |
| `outreach_and_lock` | Talent is contacted with job basics and the proposed rate/range. |
| `talent_declined` | Talent declined the project or rate. |
| `talent_countered` | Talent countered before client visibility. Admin review may be needed. |
| `quote_locked` | Talent accepted the project-specific rate/range before client visibility. |
| `client_slate_visible` | Client can view only talent with locked active quote versions. |
| `quote_reopened` | Client-side facts changed and fresh talent approval is required. |
| `booked` | Deal booked from the active locked quote version. |
| `cancelled_or_released` | Hold, booking, or slate option expired or was released. |

The Pitch Review Room should not read directly from transient pricing calculations. It should read only
from active locked quote records.

## Readiness Gate

Binding quote generation should require adequate project readiness.

Launch default:

- `projectReadinessTier >= Ready`, or
- `projectCredibilityScore >= 50`

If readiness is below threshold, the engine may return:

- admin-only expected ranges
- missing-assumption prompts
- scope-calibration warnings
- soft-hold guidance
- no client-presentable quote

Admin override is allowed only with a logged reason, for example known buyer, strategic brand, urgent
manual curation, or human-confirmed scope details not yet structured.

## Required Inputs

### Project Inputs

- `project_id`
- `projectCredibilityScore` or `projectReadinessTier`
- category and subcategory
- project type
- talent class scope: actor, production talent, or mixed
- actor role scope when the opportunity targets lead, supporting, featured, or background talent
- all-in project size band
- stated talent budget or role budget, if available
- budget type: firm, flexible, exploratory, prestige, unknown
- market or jurisdiction
- shoot country and local talent market, when known
- shoot/work dates and lead time
- prep days, shoot days, fitting days, travel days, post days, when known
- usage rights: channel, media type, paid media, term length, territory, perpetuity flag
- exclusivity: category, term, territory, competitor conflict scope
- buyout versus day-rate structure
- optional market-cost prior context or a country key the pricing engine can resolve
- optional published actor rate-card id or source document for market/role-specific floors
- union status and applicable jurisdiction
- local minimum wage inputs when known; null is allowed and should create admin review
- minor status or minor-role flag when applicable
- pricing assumptions included
- expected actualization triggers
- conflict-check requirements
- admin inclusion override ids and reason codes, if any

### Client Inputs

- `client_id`
- `clientTrustScore`: 0-100, owned by the main site
- `clientTrustTier`: premium, established, emerging, or new
- trust score breakdown for admin audit, when available
- Verified Brand admin flag
- Agency Account admin flag
- completed Distinkt project count
- payment speed signal, when available
- `brandPrestigeTier`: tier_1, tier_2, tier_3, none, or equivalent
- optional `brandPrestigeScore`: 0-100
- optional category-specific brand desirability notes

Client trust and brand prestige must remain separate. Trust measures transaction reliability. Prestige
measures strategic desirability and talent attraction value.

### Talent Inputs

- `talent_id`
- talent class: actor or production talent
- production role or actor role
- home/local market, when relevant for actor market-specific pricing
- listed rate
- talent-approved operating band, initially 25% below to 30% above listed rate
- private working floor or policy floor
- `rates_updated_at`
- recent confirmed platform rates, last N bookings when available
- union status and legal floor basis
- local jurisdiction constraints, when available
- actor minor status, when applicable
- upstream actor readiness score, when applicable
- upstream non-actor reliability score, when applicable
- category specialization scores
- minimum notice window
- availability constraints
- conflict or exclusivity constraints
- prestige/low-cash opt-in state

If `rates_updated_at` is stale, the engine should either request a rate refresh, downgrade confidence,
or require admin review before binding Outreach & Lock.

## Quote Output

The pricing engine should return a quote candidate record, not only a number.

Recommended fields:

- `quote_id`
- `project_id`
- `talent_id`
- `quote_version`
- `policy_version`
- `policy_config_version`
- `input_snapshot_hash`
- `quote_state`
- `expectedBookingRange`
- `expectedClose`
- `currency`
- `assumptionsIncluded`
- `actualizationTriggers`
- `clientVisiblePriceState`
- `adminPricingRationale`
- `brandFacingMatchRationale`
- `talentFacingRationaleState`: not generated by this layer
- `aiDiscretionDelta`
- `aiDiscretionMode`
- `approvalRequired`
- `exceptionTriggers`
- `auditRequired`

After Outreach & Lock, the main site should attach:

- outreach channel: call-for-details, email offer, in-app opportunity, or approved equivalent
- talent response state
- talent committed quote/range
- locked timestamp
- quote expiration or confirmation checkpoint
- active quote version
- admin approval state

## Active Quote Version

There must be one server-authoritative active quote version for a project/talent pair.

Rules:

- client slate reads only the active locked quote version
- stale quote versions cannot be client-visible
- client acceptance must include the quote version it accepted
- if client-side facts change, create a new quote version rather than mutating history
- if a quote is reopened, client visibility pauses until the new rate is talent-approved

This prevents race conditions where talent accepts at one price while the client sees another.

## Audit Events

Quote audit events should be append-only.

Minimum event types:

- `quote_generated`
- `quote_sent_to_talent`
- `talent_accepted_quote`
- `talent_declined_quote`
- `talent_countered_before_presentation`
- `talent_requested_clarification`
- `quote_locked`
- `quote_presented_to_client`
- `client_counter_requested`
- `quote_reopened_for_scope_change`
- `admin_approved_quote`
- `admin_adjusted_policy_setting`
- `admin_inclusion_override_added`
- `off_engine_exception_created`
- `dfos_consumed_locked_quote`
- `booking_completed`
- `hold_expired_or_released`

Each event should include actor, timestamp, previous version, new version when applicable, reason code,
policy version, and relevant before/after values.

## Pitch Review Room Policy

Launch default:

- locked quote is fixed accept/reject
- client can choose another slate option
- client can request a scope, usage, timing, or budget change
- real client-side fact changes reopen the quote and require fresh talent approval
- quiet post-lock haggling is not allowed

If the client submits a lower counter without a material fact change, it should not silently alter the
quote. It can be logged as client-side negotiation behavior and routed to admin review if the team wants
to pursue it manually.

## DFOS Contract

DFOS consumes the locked gross quote and associated assumptions.

DFOS should not:

- regenerate the quote
- infer private floors
- back-calculate talent net from platform commission
- overwrite the active quote version

The negotiation engine and quote record should carry enough gross-rate context for DFOS to apply
commission rules, including the California 10% cap, without fighting upstream pricing logic.

## Single Pricing Gateway

All client-presentable quotes should come through the pricing gateway.

Admin manual quote paths:

- preferred: admin changes settings or approved inputs, then regenerates a quote through the engine
- exception: admin creates an `off_engine_exception` with reason, attribution, and audit trail

Repeated manual exceptions should be reviewed as evidence that policy, fields, or workflow are missing
something.

## User-Facing Language Boundaries

Brands may see:

- positive match rationale
- expected range labels
- assumptions included
- high-level scope-change triggers
- confidence and fit language

Brands must not see:

- percentage nudges
- behavior or timing math
- hidden flexibility
- talent floors
- client trust math
- why other talent were not surfaced
- language implying an algorithm set the price

Talent may see:

- job basics
- proposed project rate or range
- assumptions included
- obvious scope-change triggers
- whether they are accepting, declining, countering, or asking for clarification

Talent must not see:

- client trust score or payment details
- hidden pricing math
- behavior penalties
- private floor inference
- job-specific negative rationale

Admin may see the full pricing rationale, policy output, nudges, discretion proposals, exception
triggers, audit trail, and replay context.

## Shadow Mode Definition

Real shadow mode means production project data flows through the engine in parallel with current
operations.

Shadow mode requirements:

- no effect on talent outreach
- no effect on client slate visibility
- no effect on booked rates
- admin comparison against actual human/current-system behavior
- distribution review over several weeks
- logs saved with policy and input versions

Synthetic validation remains useful, but it is not enough to graduate to live pricing.

## Outcome-Learning Graduation

Outcome learning is guidance-only until promoted through governance.

Recommended path:

- launch: advisory only
- weekly anomaly review during shadow mode
- quarterly pricing-policy review for stable patterns
- two-admin approval for live formula changes
- legal review for claims, commission behavior, public language, union/legal floors, or regulated talent
  categories
- new policy version for every promoted change
- replay tests before rollout

Outcome data can inform talent guidance, for example "similar people in your city are closing higher,"
but it must not automatically change a talent-owned rate range.
