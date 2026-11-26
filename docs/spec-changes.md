# Spec Changes

Behaviour changes to a committed spec are logged here, newest first. Each entry names the spec, the baseline commit, what changed and why.

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
