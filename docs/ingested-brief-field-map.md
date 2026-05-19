# Ingested Brief Field Map

## Source Sample

Sample file reviewed:

```text
/Users/gibbin/Downloads/brief-extraction-mike-and-ike.json
```

The file contains two `extracted_briefs` records for the Mike and Ike "We Got'chew" campaign. It is
test data, but it appears close enough to main-site brief extraction output to use as an integration
shape sample.

## What The Sample Confirms

The extraction output already contains several fields the pricing simulator needs:

| Source Field | Simulator / Contract Use |
| --- | --- |
| `project_credibility_score` | Readiness gate and admin confidence context. |
| `project_readiness_tier` | Binding Outreach & Lock gate. |
| `funding_status` | Budget confidence and readiness context. |
| `funding_source` | Client/project credibility context. |
| `budget_min`, `budget_max` | Stated budget range, but not necessarily talent-only. |
| `extracted_budget_min`, `extracted_budget_max` | Extracted budget range with source evidence. |
| `intel.budgetWithEvidence` | Budget confidence, evidence, and whether budget is confirmed. |
| `project_type` | Project type mapping, though sometimes array/empty. |
| `intel.mapped_tags` | Category, style, production complexity, and creative context. |
| `location` | Free-text market/location input that needs normalization. |
| `timing`, `award_date`, `deadline` | Timing context, but dates may be null or ambiguous. |

## Important Integration Lessons

### 1. Field Names Are Snake Case

The main extraction sample uses `project_credibility_score` and `project_readiness_tier`, while the
integration contract previously used camelCase examples.

Simulator support now accepts both shapes:

- `projectCredibilityScore`
- `project_credibility_score`
- `projectReadinessTier`
- `project_readiness_tier`

### 2. Budget Is All-In, Not Talent-Only

The Mike and Ike brief states:

```text
Budget for production / post / talent - $400K
```

That is not the same as a talent quote budget. It should map to `all_in_budget`, project size, and
assumption scrutiny. A separate talent budget, role budget, or admin allocation is still needed before
the pricing engine can safely treat it as direct quote capacity.

For the simulator fixture, the mapped project uses:

- `all_in_budget`: 400000
- `project_size_band`: `major`
- `budget`: 40000 placeholder talent budget
- `budget_source`: placeholder derived for simulation only
- `talent_budget_is_estimated`: true
- `talent_budget_confidence`: low

This is intentionally marked as a placeholder so we do not forget that production needs a cleaner
handoff field.

Production can either extract a talent-specific budget directly or construe one from all-in budget,
project type, role class, usage, and category. When it construes the budget, the engine should carry a
confidence flag because the estimate can be wrong. Derived talent budgets should require admin review
until outcome data proves the derivation is reliable.

### 3. Readiness Is Useful But Tier Values Need A Shared Enum

The sample includes:

- `project_readiness_tier`: `strong`
- `project_readiness_tier`: `ready`

The simulator treats non-blocking tiers with sufficient credibility as eligible for binding Outreach &
Lock, but production should define the canonical tier enum and threshold behavior.

Recommended canonical direction:

- blocking: draft, incomplete, needs_scope, scope_calibration_required
- allowed: ready, strong, approved, production_ready

### 4. Project Type Can Be Missing Or Multi-Valued

One brief has:

```json
["Television Commercial", "Social Media Campaign"]
```

The other has an empty `project_type` array.

The contract should tolerate:

- array values
- empty arrays
- fallback from mapped tags
- admin/human normalization

### 5. Location And Timing Are Still Mostly Text

The source location is a descriptive string with multiple settings. Timing also includes mixed milestone
text, date strings, and sometimes null normalized dates.

The pricing engine should not infer wage law, travel, or market rules from this text alone. It should
consume normalized market/jurisdiction fields from the main site or compliance layer when available.

### 6. Missing Fields Are Expected

The brief extraction payload does not include:

- `clientTrustScore`
- `clientTrustTier`
- `brandPrestigeTier`
- matched talent candidates
- talent rates
- union/jurisdiction floor data
- normalized usage rights
- exclusivity terms
- DFOS quote or commission fields
- active opportunity/outreach state

That is fine. It confirms this pricing engine should run after brief extraction, client scoring, matching,
and enough project normalization have happened.

## Fixture Added

The simulator now includes:

- client: `mike_and_ike_test_brand`
- project: `ingested_mike_and_ike_campaign`

The fixture is not claiming the $400K all-in budget is a direct talent budget. It exists to stress the
handoff boundary: project size is strong, readiness is strong, but talent budget remains an allocation
that must be supplied or approved before production integration.
