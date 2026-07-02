# Crew Rate Scorer (stub_v1)

> Drafted 2026-07-02, revised same day after direction from Chris. Mirrors
> the live actor pattern
> (`distinkt-platform/server/services/deal-points/actor-worth.ts` "stub_v2" +
> `casting-rate-summary.ts`), which is canonical where this repo's docs have
> drifted. Feeds the negotiation engine's per-talent ask for crew
> (director, photographer/DP, editor, producer, creator) during
> availability-check outreach — the crew half of Outreach & Lock.

## Framing

Actors have decent baselines because SAG scale anchors the floor (at our
talent level). Crew don't — crew pricing runs on **per-market day-rate
norms** (a director is ~$5k/day in Atlanta, ~$6.5k/day in Chicago).
Percent-of-budget is **directional, not a rule**: a $500k commercial might
pay a director $10k while a $300k job pays $20k. So the scorer separates two
jobs that the earlier draft conflated:

1. **Setting the ask** — anchored on talent-declared rates first, per-market
   role norms second. Never on a budget split.
2. **Surfacing talent against budget** — budget (via the directional share
   guide) tells us which candidates to *present first*, and which to hold as
   stretch or value alternatives if the client passes on the first slate.

Talent-owned rates remain the authority throughout; conflicts trigger admin
review, never silent override.

## Anchor hierarchy for the ask

| Priority | Anchor | Source | Notes |
| --- | --- | --- | --- |
| 1 | Talent-declared rate | listed/target rate + operating band (−25% / +30%) | authority when fresh (`rates_updated_at`) |
| 2 | Paid-rate actuals | platform bookings by market × role | override norms when sample size permits |
| 3 | Per-market role norm | new `market_rate_norms` table: `(market, role, day_rate_norm, currency, source, updated_at)` | e.g. director: Atlanta $5,000/day, Chicago $6,500/day |
| 4 | Cost-of-living prior | `market_cost_indexes.json` ratio vs a normed market | only when no market norm exists; bounded ±20% |

Legal floor (unchanged from first draft): new `market_legal_floors` table,
day floor = local hourly minimum wage × 8. `effective_floor = max(legal day
floor, talent private working floor, platform floor)`. The ask never goes
below it; a budget that can't clear the floor → `budget_below_floor`
(decline or client budget-revision path, not a quiet under-floor quote).
Unknown wage → `minimum_wage_floor_unknown` warning → admin exception
(mirrors sim `admin_governance.py`).

## Budget-share guide → slate surfacing, not rates

The share guide (director ~10% of shoot budget, lesser for other roles;
admin-tunable) converts project budget into an **implied talent-spend band**
per role. Each candidate's expected ask is classified against that band:

| Classification | Meaning | Use |
| --- | --- | --- |
| `first_slate` | expected ask sits inside the implied band | present first |
| `stretch` | above the band | offered when the client wants stronger options — carries brand-safe "why they're worth it" rationale from worth signals |
| `value` | below the band | offered when the client passes on price — never framed as desperation pricing; floors still apply |

Since talent spans all ranges, this classification — not exclusion — is how
budget shapes matching: the first slate is budget-coherent, and the curation
layer can widen to stretch/value candidates on client reaction. This slots
into the Curated Recommendation Layer in the phase-1 architecture.

Consistency with `project-class-pricing-rules.md` ("don't mechanically
allocate a percentage of the all-in budget"): the share guide never sets a
rate; it only bands the slate and sanity-checks asks (an ask wildly outside
the implied band adds an admin-review warning with both numbers).

## Computation (mirrors actor stub_v2 shape)

1. `anchor` = first available of: fresh talent-declared rate → actuals-based
   market rate → `market_rate_norms` day rate → cost-index-adjusted nearest
   norm (±20% bound). Record which anchor was used in the output
   (`anchor_basis`), like the actor summary's `floorSource`.
2. `base_ask` = clamp(anchor, talent operating band when declared rates
   exist). Stale `rates_updated_at` → downgrade confidence / request refresh
   per the integration contract.
3. `effective_floor` as above; ask never below.
4. `ask` = base_ask × worth multiplier, bounded **[1.05, 1.30]** — same
   bounds as actor-worth; worth only moves the ask UP from the anchored
   base. Worth signals: category specialization match, reliability score,
   quote stability, verified credits, TIAS `availability_accuracy`.
5. `budget_fit` = classify ask vs implied talent-spend band
   (`first_slate | stretch | value`); attach to the match record for slate
   ordering.
6. Output mirrors the actor summary: `status`
   (`ready_for_model | missing_budget | missing_talent_floor | budget_below_floor`),
   ask (day rate + total), expected booking range, `askMultiplier`,
   `anchor_basis`, `budget_fit`, brand-safe `rationale` strings (no scores,
   no internals, no floors), warnings.

`missing_budget` no longer blocks the ask (the anchor doesn't need budget) —
it only disables `budget_fit` classification, with a warning.

## Integration

- Called from the crew availability-check flow at outreach time, creating a
  quote version in state `outreach` (same lifecycle as
  `storage/casting/quotes.ts`: draft → outreach → locked). "Available" =
  rate acceptance → lock. This is the crew-parity work identified in
  `BE/files/docs/TALENT_ROLE_MODEL_AUDIT.md`.
- `budget_fit` feeds slate ordering in curation; stretch/value candidates
  surface on demand, not by default.
- Buyers never see listed rates, floors, or internals — presented price is
  the ask (same guardrail as `casting-rate-summary.ts`).

## Market norms: small seed, not a catalogue

Concern raised: maintaining a daily-rate catalogue across 30+ countries is
not realistic. Production data (2026-07-02) says we don't need one — crew
talent concentrates in ~4 markets: LA (~49), London (~28), NY (~12), then a
short tail (Sydney 5, Cape Town 4); 116 crew profiles have no location at
all, and `projects.shoot_country` is almost entirely unpopulated.

So the norm table is a **seed of ~4-5 markets × 5 roles (~25 rows)**, owned
by admin, and everything else resolves through the anchor hierarchy without
it: most crew declare their own rates (anchor 1); actuals accumulate
(anchor 2); an unseeded market scales from the nearest seeded one via the
cost-of-living index (anchor 4) — which is exactly the pattern
`market_cost_indexes.json` was built for (reference market + index, actuals
override). The `market_legal_floors` table is per-country but it's small,
objective public data — seed lazily, only for countries a shoot actually
lands in.

The real data problem is upstream of any catalogue: location is free text
("Los Angeles" appears six different ways) and a sixth of crew have none.
The users table already carries `home_city_normalized` /
`home_country_code` (OneSignal sync) — the scorer should key markets on a
normalized market id, and profile completeness nudges (TIAS) should chase
the missing locations.

## Open questions

1. ~~**Market norm seed values**~~ **RESOLVED 2026-07-02**: seeded from the
   commercial crew rate card workbook
   (`~/Desktop/commercial_crew_rates_top_30_cities.xlsx` — 30 cities × 5
   roles, low/mid/high USD/day planning ranges, sourced from DGA/AICP scale
   notices, APA/BECTU UK ratecards, NeedaCrew city guides, et al). Lives in
   the platform `market_rate_norms` table
   (migration `0035_market_rate_norms.sql`, applied to prod), admin-editable
   at `/admin/market-rates` (Talent Operations sidebar), API
   `/api/admin/market-rate-norms`.
2. **Share-guide defaults** per role for the implied-spend band (director
   10% is directional-confirmed; photographer/editor/producer placeholders
   need a pass).
3. **Shoot days**: `projects.timing` is free text; no structured
   `shoot_days`. Needed to size day-rate totals and the legal floor. Add a
   structured field, or estimate from project size band?
4. **Which budget** the share guide reads: all-in `budget_min/max` vs a
   captured shoot budget; and how wide min/max spreads degrade the band.
5. **Slate mechanics**: how many `first_slate` candidates before stretch/
   value unlock; does client rejection auto-widen or admin-gate?
6. **Minimum wage granularity**: country-level to start, or US-state (CA at
   minimum) from day one?
