# Spec Changes

Behaviour changes to a committed spec are logged here, newest first. Each entry names the spec, the baseline commit, what changed and why.

## 2026-11-26 — 001-visit-card-agent: LLM provider as configuration

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `1b2650d`
- **Source**: owner decision at the start of `/speckit-plan`, 2026-11-26.

| Area | Before | After | Reason |
|---|---|---|---|
| Run metadata (FR-032, Story 3 #5, Evaluation Report entity) | Report records git commit, model name and run date | Also records the LLM provider | The provider is chosen by configuration, so the model name alone does not identify the run |
| Model access (Assumptions, Clarifications) | Undefined | The provider and model are configuration; v1 runs with a local model or a test stand-in; no paid API key is required to develop, test or run the agent | Development and testing must not depend on a paid cloud API |

## 2026-11-26 — 001-visit-card-agent: test-case review

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `a8a6526`
- **Source**: open questions Q1–Q6 found while writing `specs/001-visit-card-agent/test-cases.md`; decided by the owner on 2026-11-26.

| Area | Before | After | Reason |
|---|---|---|---|
| One pain point per category (FR-008, FR-025 #18) | A category could appear in several pain points | A category with mapped products appears at most once per card, evidence merged; only `other_unmapped` may repeat. New deterministic check #18 | Splitting evidence would lower confidence (two `medium` instead of one `high`) and change the ranking |
| Prerequisite pain points (FR-012) | Prerequisite addressed the same pain points as the requiring product | Also lists its own pain points; confidence stays that of the requiring product | Defined behaviour when a prerequisite is also a candidate |
| Short-card review count (FR-007) | "Number of reviews analysed" on every card | Short cards show "Reviews not analysed" | Reviews are not analysed for closed or chain restaurants |
| Prerequisites in metrics (SC-004, SC-005) | Undefined | Primary and prerequisite products both count | Gold labels list prerequisites (e.g. R04) |
| Rule-breaking model output (Edge cases) | Undefined | Unknown category or non-verbatim quote produces a card that fails the checks; only unparseable output or a failed call is a generation failure | Problems stay visible in the evaluation report |
| Gold-label validation (FR-028, Story 3 #6) | Three invalid-row types; behaviour after an error undefined | Six invalid-row types; the evaluation lists all invalid rows and stops before running the agent | Metrics are never computed on a partial or contradictory label set |

## 2026-11-26 — 001-visit-card-agent: clarification session

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `74b1c68` ("spec: add restaurant pitch card specification")
- **Source**: `/speckit-clarify` session and owner review of the pain-point mapping, 2026-11-26. Each decision is also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Pain point → product (FR-002, FR-008, FR-013, FR-013a, FR-015a) | The model decided which product addresses a pain point | A fixed category list and category → product table in `data/products/pain-point-product-mapping.json`; the model only classifies reviews and extracts evidence; candidates, support counts, confidence and ranking are computed by rule | Reproducible recommendations that the deterministic checks can verify |
| Closed / chain restaurants (FR-006, FR-007, FR-020a, Story 2) | Full card with no recommendation | Short card produced by rule without calling the model; states that the restaurant is not in the recommendation target list because it is closed and/or a chain; other sections say "Not applicable" | No value in analysing restaurants that will not be pitched; deterministic and testable |
| Verbatim quote check (FR-009, FR-025 #3) | "Verbatim excerpt", matching rule undefined | Exact substring after trimming and collapsing whitespace; case and punctuation must match; at least 3 words | Tolerate formatting noise without allowing rewording; block meaningless one-word quotes |
| Insufficient evidence with no pain points (FR-017a, Story 2) | Undefined | Opening pitch "Not applicable"; general operational questions from the category list, labelled "Not based on reviews" | Rep still has questions to ask without presenting ungrounded claims as evidence |
| Deterministic checks (FR-025) | 15 checks | 17 checks: added category validity (#16) and table consistency (#17); #3, #8 and #12 tightened as above | Cover the new rules |

Decisions taken in the same session before the baseline commit (confidence levels, no `low` level, max 2 primary products, ranking with `product_id` tie-break) are part of the baseline and not repeated here.
