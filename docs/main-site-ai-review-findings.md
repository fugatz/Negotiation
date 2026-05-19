# Main Site AI Review Findings

## Purpose

This document records the main-site AI review of the negotiation engine exploration and turns the
feedback into integration requirements.

The review confirmed the broad architecture, but it also identified several main-site workflow changes
that must be explicit before production shadow mode.

## Accepted Findings

### 1. Add An Outreach & Lock State

The current main-site project flow does not have a clean gate between candidate matching and client
visibility.

The negotiation engine needs a new workflow state:

```text
Matched Candidates
  -> Pricing Engine Computes Project-Specific Offer
  -> Outreach & Lock
  -> Talent Accepts, Declines, Or Counters Before Client Visibility
  -> Locked Talent-Approved Quote
  -> Client Slate / Pitch Review Room
```

This is a product workflow change, not only a service call.

The locked quote must be created before the talent is visible to the client.

### 2. DFOS Reads The Locked Quote

The locked talent-approved quote becomes a one-way input to DFOS.

DFOS may enforce downstream rules such as the California 10% commission cap, but it should not
recalculate or regenerate the talent quote. The negotiation engine must therefore build quote records
from the correct gross-rate assumptions so DFOS does not need to back-calculate from net values.

### 3. Use Existing Talent Communication Rails

Rate-quoted outreach should ride the existing actor notification, opportunity inbox, email, and
call-for-details rails where possible.

The negotiation engine should not create a parallel communications system. Talent should experience one
coherent opportunity flow.

### 4. Add Quote Audit And Versioning

The main site already has agreement audit events. Quotes need an equivalent immutable audit trail.

Minimum audit facts:

- who or what generated the quote
- policy version and config version
- input snapshot or hash
- expected booking range and committed quote
- when the quote was sent to talent
- when talent accepted, declined, countered, or requested clarification
- when the quote locked
- when and why it reopened
- admin approvals, overrides, and manual edits
- quote version shown to the client

The Pitch Review Room should read a server-authoritative active quote version so stale client views
cannot display an outdated price.

### 5. Split Brand Prestige From Client Trust

`clientTrustScore` measures whether a client behaves reliably on the platform. It should not also carry
all brand desirability.

The engine should consume a separate upstream/admin field for brand prestige or strategic desirability,
for example:

- `brandPrestigeTier`: tier_1, tier_2, tier_3, none
- optional `brandPrestigeScore`: 0-100
- optional category-specific prestige notes

A regional brand can be high trust but low prestige. A famous or career-making brand can be high
prestige while still carrying payment or scope risk. Those signals should remain separable because they
can push pricing, acceptance probability, and outreach priority in different directions.

### 6. Gate Binding Quotes Behind Readiness

The engine should not generate binding client-presentable quotes for under-baked briefs by default.

Recommended launch rule:

- `projectReadinessTier >= Ready`, or `projectCredibilityScore >= 50`, allows binding Outreach & Lock.
- below that threshold, the engine can produce admin-only ranges, soft holds, or scope-calibration
  prompts.
- admin can override for known brands or strategic cases, but the override must be logged and reasoned.

Top talent declining vague opportunities burns goodwill. The readiness gate protects that relationship.

### 7. Expand The Handoff Fields

The current simulator already models many pricing drivers, but the production handoff contract must
include more explicit fields before integration:

- usage rights: web only, all media, paid social, broadcast, term length, perpetuity
- exclusivity: category, term, geography, competitor conflict risk
- shoot days, prep days, fitting days, travel days, post days
- union status, jurisdiction, SAG-AFTRA or other scale floor, local minimum wage input when known
- recent confirmed platform rates for the talent
- buyout versus day-rate structure
- conflict checks
- minor status and related legal path
- talent `rates_updated_at`

Profile rates drift stale. If `rates_updated_at` is old, the engine should request refresh or admin
review before trusting the profile range.

### 8. Make Pitch Review Room Policy Explicit

Once a talent-approved quote is presented, the default policy should be fixed accept/reject unless
client-side facts change.

If a client tries to negotiate down after quote lock, the system should not quietly haggle inside the
Pitch Review Room. It should either:

- reject the counter as outside the locked quote policy, or
- reopen the quote as a new client-side counter requiring fresh talent approval.

The recommended launch default is the second path only when the client submits a real scope, usage,
timing, or budget-change reason. Otherwise the client accepts the locked quote or chooses another slate
option.

### 9. Use One Pricing Gateway

Manual admin quotes must not become side doors that bypass policy.

Launch rule:

- normal manual adjustments go through the pricing gateway and are logged against the quote version
- exceptional off-engine quotes require an explicit `off_engine_exception` reason, admin attribution,
  and audit entry

Repeated off-engine exceptions should become policy recalibration signals.

### 10. Public Language Must Stay Agent-Judgment Shaped

User-facing language should not make the rate look algorithm-derived.

Brands should not see:

- rate math
- behavior or timing nudges
- hold expiration mechanics
- why other talent were not surfaced
- language like "the system calculated"

Talent should not see:

- client trust score
- client payment-history specifics
- behavior nudges against the talent
- private floor math
- job-specific negative pricing rationale

The public surfaces should read as professional recommendation and representation judgment, while
admin surfaces can remain precise and auditable.

### 11. Legal Language Needs Review

The architecture can be representation-shaped, but public language such as "agent" or "fiduciary" may
carry legal weight, especially for artist employment procurement in California.

Before external docs, ToS, or client/talent copy use that language, legal review is required.

Safer public framing to evaluate:

- representation-quality pricing
- negotiates project terms
- recommends talent with locked project terms
- structured pricing and deal support

### 12. Define Real Shadow Mode

Synthetic dry runs are necessary but not sufficient.

Production shadow mode should mean:

- real project data flows through the engine in parallel with current behavior
- the engine does not affect talent outreach, client visibility, or booked rates
- admins compare current behavior against engine output
- distribution issues are reviewed over several weeks before any live use

### 13. Formalize Outcome-Learning Graduation

Outcome learning should stay advisory until a review process promotes it into policy.

Recommended governance:

- weekly launch review of shadow-mode anomalies
- quarterly pricing-policy review for stable patterns
- two-admin approval for live policy changes
- legal review for changes affecting public claims, commission treatment, union/legal floors, or
  externally visible pricing language
- policy versioning so old outcomes can be replayed under the exact rules used at the time

## Immediate Backlog

1. Write the full integration handoff contract.
2. Add `Outreach & Lock` as the explicit main-site workflow state.
3. Add `brandPrestigeTier` or equivalent upstream brand desirability input.
4. Add `rates_updated_at` to talent rate ranges and design a refresh nudge.
5. Choose and document the Pitch Review Room post-lock policy.
6. Add quote audit events and active quote versioning.
7. Define the readiness gate for binding quotes.
8. Confirm DFOS gross-quote and commission-cap handoff.
9. Review public "agent" and "fiduciary" language with counsel before shipping externally.
