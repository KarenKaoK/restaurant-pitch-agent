# Data Model: Restaurant Visit Card Agent

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-11-26

In-memory types are Python dataclasses (frozen where practical). The card's JSON form is defined in [contracts/visit-card.md](contracts/visit-card.md); this document defines the fields, rules and how they are derived.

## Input entities (read-only)

### Restaurant — `data/processed/restaurants.csv`

| Field | Type | Rule |
|---|---|---|
| `restaurant_id` | str | Unique; required |
| `name` | str | Required |
| `city` | str | Required |
| `address` | str | May be empty; not shown on the card |
| `status` | str | `closed` makes the restaurant ineligible; any other value (`unknown`, …) is treated as open |
| `segment` | str | `chain` makes the restaurant ineligible; `independent` otherwise |

Derived: `is_closed = status == "closed"`, `is_chain = segment == "chain"`, `eligible = not (is_closed or is_chain)`.

### Review — `data/processed/reviews.csv`

| Field | Type | Rule |
|---|---|---|
| `review_id` | str | Unique; required |
| `restaurant_id` | str | Must exist in restaurants |
| `text` | str | Source for verbatim quotes |
| `text_source` | str | `original` / `translated` / `expanded` |
| `review_date`, `date_imputed`, `rating`, `rating_imputed` | — | Loaded but never sent to the model nor shown on the card (FR-019) |
| `platform`, `source_url` | str | Kept (constitution V); not shown on the card in v1 |

No reviewer identity fields exist; the loader does not accept or expose any (FR-005).

### Product — `data/products/*.md` frontmatter

| Field | Type | Rule |
|---|---|---|
| `product_id` | str | Unique; required |
| `name` | str | Required; shown on the card |
| `category` | str | Required |
| `requires` | str \| None | If present, must be another catalog `product_id` (load error otherwise, TC-D07) |

Only `.md` files are products; other files in the folder are ignored (TC-D06).

### PainPointCategory — `data/products/pain-point-product-mapping.json` → `categories[]`

| Field | Type | Rule |
|---|---|---|
| `category_id` | str | Unique (TC-D09); required |
| `definition` | str | Required (TC-D11) |
| `product_ids` | list[str] | Required, may be empty; every ID must be in the catalog (TC-D10) |
| `example_signals`, `exclusions` | list[str] | Optional; sent to the model as classification guidance only |
| `catalog_reference` | str | Optional; ignored |

Derived: `repeatable = len(product_ids) == 0` (research R11).

The file's top-level `rules` object is sent to the model as classification guidance; it never changes rule-based behaviour (FR-013a, TC-D12).

### GoldLabel — `data/eval/expected.csv` (evaluation only)

| Field | Type | Rule (FR-027, FR-028) |
|---|---|---|
| `restaurant_id` | str | Must exist in restaurants; must not repeat |
| `decision` | str | `recommend` / `no_recommendation` / `insufficient_evidence` |
| `must_include` | list[str] | `;`-separated; may be empty; each a catalog product; empty unless `decision` = `recommend` |
| `acceptable` | list[str] | `;`-separated; may be empty; each a catalog product; no overlap with `must_include` |
| `rationale` | str | Free text |

Missing columns reject the whole file. Validation collects **all** invalid rows (`LabelError(row_number, restaurant_id, reason)`) before stopping (TC-G11).

## Intermediate entity: ModelAnalysis (parsed model output)

The shape the model must return is in [contracts/model-output.md](contracts/model-output.md). After parsing:

| Field | Type |
|---|---|
| `restaurant_description` | str |
| `pain_points` | list of `RawPainPoint(ref, category_id, description, evidence: list[RawEvidence(review_id, quote)])` |
| `opening_pitch` | str |
| `discovery_questions` | list of `(pain_point_ref, question)` |
| `general_questions` | list of `(category_id, question)` |

Parsing raises `GenerationError` only for invalid JSON or wrong shape (research R8). Unknown extra keys are ignored (TC-S06).

## Output entities (the visit card)

### VisitCard

| Field | Type | Rule |
|---|---|---|
| `schema_version` | str | `"1"` |
| `restaurant` | RestaurantSummary | Always present |
| `decision` | str | `recommend` / `no_recommendation` / `insufficient_evidence` (FR-020) |
| `decision_reasons` | list[str] | Codes: `closed`, `chain` (both when both apply) for `no_recommendation`; `["insufficient_evidence"]` for `insufficient_evidence`; `[]` for `recommend` |
| `pain_points` | list[PainPoint] | `[]` on short cards |
| `recommendations` | list[Recommendation] | Primaries in rank order, then prerequisites; `[]` unless `recommend` (FR-021) |
| `candidates_not_selected` | list[Candidate] | In rank order; non-empty only when there are 2 primaries (check 15) |
| `opening_pitch` | str \| null | `null` on short cards and on eligible cards with no pain points ("Not applicable") |
| `discovery_questions` | list[DiscoveryQuestion] | `[]` on short cards |

### RestaurantSummary

| Field | Type | Rule |
|---|---|---|
| `restaurant_id`, `name`, `city`, `status`, `segment` | str | Copied from the restaurant |
| `reviews_analysed` | int \| null | Number of the restaurant's reviews sent to the model; `null` on short cards ("Reviews not analysed") |
| `description` | str \| null | Model-written; `null` on short cards (FR-007) |

### PainPoint

| Field | Type | Rule |
|---|---|---|
| `pain_point_id` | str | `PP1`, `PP2`, … assigned by rule in order of first appearance after merging |
| `category_id` | str | From the model; must be in the category list (check 16) |
| `description` | str | From the model; when merging, the first description is kept |
| `confidence` | `high` \| `medium` \| null | By rule: >1 distinct cited review → `high`; exactly 1 → `medium`; 0 → `null` (fails check 1) |
| `evidence` | list[Evidence] | ≥ 1 required (check 1) |

### Evidence

| Field | Type | Rule |
|---|---|---|
| `review_id` | str | From the model |
| `quote` | str | From the model, unchanged (no silent correction) |
| `text_source` | str \| null | By rule, from the restaurant's review with that ID; `null` if not one of the restaurant's reviews |

### Recommendation

| Field | Type | Rule |
|---|---|---|
| `product_id` | str | Catalog ID |
| `name` | str | Catalog `name` |
| `role` | `primary` \| `prerequisite` | FR-015 |
| `required_by` | list[str] | Primaries that require this product; `[]` for primaries |
| `pain_point_ids` | list[str] | Primary: pain points whose category maps to the product. Prerequisite: union of the requiring products' pain points and its own (FR-012) |
| `supporting_review_ids` | list[str] | Distinct review IDs cited by those pain points, sorted |
| `support_count` | int | `len(supporting_review_ids)` (check 13) |
| `confidence` | `high` \| `medium` | Primary: highest among its pain points. Prerequisite: that of the requiring product (highest if several) |

### Candidate (not selected)

| Field | Type |
|---|---|
| `product_id` | str |
| `confidence` | `high` \| `medium` |
| `support_count` | int |
| `pain_point_ids` | list[str] |

### DiscoveryQuestion

| Field | Type | Rule |
|---|---|---|
| `question` | str | Model-written |
| `pain_point_id` | str \| null | Set for review-based questions; the model's ref is translated to the merged `PPn` ID, or kept as given if it matches no pain point (fails check 12) |
| `category_id` | str \| null | Set for general questions |
| `based_on_reviews` | bool | `false` → rendered with the label "Not based on reviews" (FR-017a) |

### Relationships

```text
Restaurant 1 ─── * Review
Restaurant 1 ─── 1 VisitCard (per run)
VisitCard 1 ─── * PainPoint 1 ─── * Evidence * ─── 1 Review
PainPoint * ─── 1 PainPointCategory * ─── * Product   (mapping table)
VisitCard 1 ─── * Recommendation * ─── 1 Product
VisitCard 1 ─── * Candidate * ─── 1 Product
DiscoveryQuestion * ─── 0..1 PainPoint | 0..1 PainPointCategory
```

## Card derivation (rule pipeline)

```text
restaurant_id
  │
  ├─ unknown ID ───────────────────────────────▶ UnknownRestaurantError (no card)       FR-004
  │
  ├─ closed and/or chain ──▶ short card (no model call)                                 FR-020a
  │      decision = no_recommendation, reasons = [closed][chain],
  │      reviews_analysed = null, description = null, all lists empty, pitch = null
  │
  └─ eligible
       1. load the restaurant's reviews                                                 FR-003
       2. build prompt + JSON schema; llm.generate()  ── LLMError / bad JSON / bad shape ─▶ GenerationError
       3. parse → ModelAnalysis (extra keys ignored)
       4. merge pain points: same non-repeatable category → one pain point,            FR-008
          evidence concatenated in order; refs remapped; IDs PP1..n assigned
       5. attach text_source to each evidence item from the restaurant's reviews
       6. confidence per pain point (distinct review IDs)                              FR-011
       7. candidates: for each product mapped from a pain point category on the card:  FR-013a
          pain_point_ids, distinct supporting reviews, support_count, confidence = max
       8. rank by (confidence desc, support_count desc, product_id asc);               FR-015a
          top 2 → primary; rest → candidates_not_selected
       9. prerequisites: for each primary with `requires` R not already primary,       FR-015, FR-012
          add/extend prerequisite R and remove R from candidates_not_selected
      10. decision = recommend if any primary, else insufficient_evidence              FR-020
      11. questions: if pain points exist → model's linked questions;                  FR-017, FR-017a
          else → pitch = null and the model's general questions (based_on_reviews = false)
      12. VisitCard
```

Steps 4–11 are pure functions of (ModelAnalysis, restaurant, reviews, catalog, mapping), so they are developed test-first without a model.

## Evaluation entities

### CheckResult

| Field | Type |
|---|---|
| `check_id` | int (1–18) |
| `passed` | bool |
| `reasons` | list[str] (empty when passed) |

All 18 checks always run; a failure in one does not stop the others (TC-K19). If check 1 finds the structure too broken for a later check to read a field, that check fails with the reason "not evaluated: invalid structure".

### CaseResult (one per labelled restaurant)

| Field | Type |
|---|---|
| `restaurant_id` | str |
| `card` | VisitCard dict \| null (null on generation failure) |
| `error` | str \| null |
| `checks` | list[CheckResult] (on generation failure: check 1 failed with the error, others "not evaluated") |
| `expected_decision`, `actual_decision` | str (actual is `error` on generation failure) |
| `recommended_products` | list[str] (primary + prerequisite) |
| `missed_must_include` | list[str] |
| `outside_expected` | list[str] (recommended products not in `must_include` ∪ `acceptable`) |

### Metrics (SC-001 – SC-005)

| Metric | Definition | Target |
|---|---|---|
| SC-001 | Cards passing all 18 checks / labelled restaurants (generation failure = fail) | 100% |
| SC-002 | Closed/chain cards with no recommended products / closed/chain cards | 100% |
| SC-003 | Restaurants whose decision matches the gold label (generation failure = mismatch) | Reported as count/total; met when count/total ≥ 13/15 (on the real 15-restaurant run: ≥ 13) |
| SC-004 | `must_include` products recommended (primary or prerequisite) / all `must_include` products | ≥ 80% |
| SC-005 | Restaurants with ≥ 1 recommended product outside `must_include` ∪ `acceptable` | ≤ 1 |

### RunMetadata

`run_id` (UTC timestamp), `git_commit`, `git_dirty`, `provider`, `model`, `run_date`, `labels_path`, `labels_sha256`, `unlabelled_restaurants` (in the dataset but not in the labels, TC-V03).
