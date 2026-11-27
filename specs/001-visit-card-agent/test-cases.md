# Test Cases: Restaurant Visit Card Agent

**Feature**: [spec.md](spec.md)
**Created**: 2026-11-26
**Status**: Reviewed by owner (2026-11-26)

## Purpose and use

This document defines the expected behaviour of the feature as concrete test cases, before any design or code exists. It follows constitution Principle VI: deterministic logic is developed test-first; LLM output is verified by the evaluation.

- **Now**: the owner reviews these cases. Open questions found while writing them are listed in [Open questions](#open-questions).
- **`/speckit-plan`**: the plan designs interfaces and data formats so that every automated case below can be written as a test.
- **`/speckit-tasks`**: every test task comes before its implementation task and references the case IDs (e.g. "T010 Write tests TC-R01–TC-R08").
- **Implement**: write the test (red), confirm it fails, implement (green), refactor.

Case IDs are stable. Each case names the spec requirement it covers. The cases describe behaviour, not function names or file formats.

## Test layers

| Layer | What | Method | Data |
|---|---|---|---|
| L1 Deterministic logic | Loading, validation, confidence, support count, ranking, prerequisites, decision, short cards, quote check, the 18 deterministic checks, plain-text output, gold-label validation, metrics | TDD | Synthetic fixtures (below) |
| L2 Pipeline with a stubbed model | The full path from model output to card, with the model replaced by a stub that returns fixed output | TDD | Synthetic fixtures + stub |
| L3 Real-data regression | Real catalog, mapping, gold labels; rule-only cards (closed, chain) | TDD | Real files in `data/` |
| L4 Model quality | Classification accuracy, pitch tone, product descriptions | Evaluation (Story 3) and human review (SC-006) | `data/eval/expected.csv` |

L1–L3 are automated tests and must all pass at every checkpoint. L4 is not a unit test.

## Fixtures

Fixtures are small, fixed files used only by tests, so tests do not change when real data changes. Product IDs reuse the real catalog IDs for readability.

### FX-CAT: fixture catalog

| product_id | requires |
|---|---|
| dish-pay | — |
| dish-pos | — |
| dish-professional-order | — |
| dish-professional-reservation | — |
| dish-ai-phone-assistant | dish-professional-reservation |
| dish-starter | — |

### FX-MAP: fixture category table

| category_id | product_ids |
|---|---|
| c_cash | dish-pay |
| c_kitchen | dish-pos |
| c_order | dish-pos |
| c_booking | dish-professional-reservation |
| c_phone | dish-ai-phone-assistant |
| c_web | dish-starter |
| c_takeaway | dish-professional-order |
| c_multi | dish-pos; dish-pay |
| c_none | (empty) |

`c_multi` exists only to test a category mapped to two products; the real table has none.

### FX-RST: fixture restaurants

| restaurant_id | status | segment | Notes |
|---|---|---|---|
| F01 | unknown | independent | Main eligible restaurant |
| F02 | closed | independent | |
| F03 | unknown | chain | |
| F04 | closed | chain | |
| F05 | unknown | independent | No reviews |
| F06 | unknown | independent | Owns a review with the same text as F01-001 |

### FX-REV: fixture reviews

| review_id | restaurant | text | text_source |
|---|---|---|---|
| F01-001 | F01 | `They only accept cash payments here.` | original |
| F01-002 | F01 | `Cash only, so we had to find an ATM.` | translated |
| F01-003 | F01 | `We waited two hours for our food.` | original |
| F01-004 | F01 | `The soup was cold and bland.` | expanded |
| F01-005 | F01 | `Lovely staff and great coffee.` | original |
| F01-006 | F01 | `The bill was wrong and\nthey forgot our drinks.` (contains a line break) | original |
| F02-001 | F02 | `We waited two hours for our food.` | original |
| F03-001 | F03 | `They only accept cash payments here.` | original |
| F06-001 | F06 | `They only accept cash payments here.` | original |

Notation used below: `PP(category, [review IDs])` is a pain point; `cand(product, confidence, support)` is a candidate product.

---

## A. Data loading and validation (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-D01 | FR-001 | Restaurant F01 | Restaurant loaded with name, city, status, segment |
| TC-D02 | FR-004 | Restaurant ID `F99` (not in data) | Error "unknown restaurant"; no card produced |
| TC-D03 | FR-003 | Restaurant F01 | Only F01-* reviews returned; F06-001 not included |
| TC-D04 | FR-003 | Restaurant F05 | Empty review list; no error |
| TC-D05 | FR-014 | FX-CAT | 6 products loaded; `product_id` read from frontmatter; `dish-ai-phone-assistant` requires `dish-professional-reservation` |
| TC-D06 | FR-014 | Catalog folder also contains the mapping file and a `.DS_Store` file | Only `.md` product files are loaded as products |
| TC-D07 | FR-014 | A product whose `requires` names a product not in the catalog | Load error naming the product |
| TC-D08 | FR-013a | FX-MAP | 9 categories loaded; `c_none` has an empty product list |
| TC-D09 | FR-013a | Mapping with a duplicate `category_id` | Load error |
| TC-D10 | FR-013a | Mapping with a `product_id` not in the catalog | Load error |
| TC-D11 | FR-013a | Mapping category missing `definition` or `product_ids` | Load error |
| TC-D12 | FR-013a | Mapping with extra fields (`example_signals`, `exclusions`, `rules`) | Loads; extra fields do not change candidate products |
| TC-D13 | FR-002 | Agent run for F01 with `data/raw/` and `data/eval/` absent | Card produced normally (agent does not depend on them) |
| TC-D14 | FR-005 | Any card (structured and plain text) | Contains no reviewer name, profile URL, reviewer ID, photo or reviewer statistics fields |
| TC-D15 | FR-002a | Restaurants file with two rows for F01 | Load error naming `restaurants.csv`, the row and "duplicate restaurant_id" |
| TC-D16 | FR-002a | Reviews file with two rows for F01-001 | Load error naming `reviews.csv`, the row and "duplicate review_id" |
| TC-D17 | FR-002a | Review `F99-001` with `restaurant_id` = `F99` (not in restaurants) | Load error naming `reviews.csv`, the row and "unknown restaurant_id" |
| TC-D18 | FR-002a | (a) Review with `text_source` = `machine`; (b) restaurant with `segment` = `franchise` | Each: load error naming the file, the row and the invalid value |
| TC-D19 | FR-002a | (a) Reviews file without the `text_source` column; (b) restaurant with an empty `name`; (c) review with an empty `source_url`; (d) review with an empty `review_date` and `rating` | (a)–(c): load error naming the file, the row (if any) and the missing column or value; (d): loads (dates and ratings not validated) |

## B. Eligibility and short cards (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-E01 | FR-020a | F02 (closed) | Decision `no_recommendation`; reason: not in the recommendation target list because it is closed |
| TC-E02 | FR-020a | F03 (chain) | Decision `no_recommendation`; reason: not in the recommendation target list because it is a chain |
| TC-E03 | FR-020a | F04 (closed and chain) | Both reasons stated |
| TC-E04 | FR-006, FR-020a | F02 | Pain points, opening pitch and discovery questions each state "Not applicable"; no recommendations; no candidates |
| TC-E05 | FR-007, FR-020a | F02 | Summary has name, city, status, segment and "Reviews not analysed"; no review-based description |
| TC-E06 | FR-020a | F02, F03, F04 with a model stub that fails the test if called | Model is never called |
| TC-E07 | FR-020 | F02 even though F02-001 would be a strong pain point | Still `no_recommendation` (closed/chain takes precedence) |
| TC-E08 | Assumption | F01 (`status` = `unknown`) | Treated as open; goes through normal analysis |

## C. Confidence (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-C01 | FR-011 | PP(c_cash, [F01-001]) | `medium` |
| TC-C02 | FR-011 | PP(c_cash, [F01-001, F01-002]) | `high` |
| TC-C03 | FR-011 | PP(c_cash) with two evidence items both citing F01-001 | `medium` (distinct reviews counted) |
| TC-C04 | FR-011 | PP(c_kitchen, [F01-003, F01-004, F01-005]) | `high` |
| TC-C05 | FR-008 | Pain point with no evidence | Confidence is null; the pain point stays on the card and fails check 1; it does not count toward any product (FR-012) |
| TC-C06 | FR-012 | dish-pos addresses PP(c_kitchen, [F01-003, F01-004]) `high` and PP(c_order, [F01-006]) `medium` | Product confidence `high` |
| TC-C07 | FR-012 | dish-pos addresses only `medium` pain points | Product confidence `medium` |
| TC-C08 | FR-008 | Model stub returns c_cash twice: [F01-001] and [F01-002] | Card has one PP(c_cash, [F01-001, F01-002]) with confidence `high` |
| TC-C09 | FR-008 | Model stub returns c_none twice for two distinct issues: [F01-004] and [F01-005] | Two separate `c_none` pain points are allowed |
| TC-C10 | FR-012 | dish-pos addresses PP(c_kitchen, [F01-003]) `medium` and PP(c_order) with no evidence | Product confidence `medium`; support = 1; `pain_point_ids` lists only the c_kitchen pain point |
| TC-C11 | FR-008 | Model stub returns `c_unknown` (not in FX-MAP) twice: [F01-001] and [F01-002] | Two separate pain points (not merged); no candidates |

## D. Candidates and support count (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-S01 | FR-013a | PP(c_cash, [F01-001]) | Candidates: dish-pay only |
| TC-S02 | FR-013a | PP(c_none, [F01-004]) only | No candidates |
| TC-S03 | FR-013a | PP(c_multi, [F01-006]) | Candidates: dish-pos and dish-pay, each addressing that pain point |
| TC-S04 | FR-015a | PP(c_kitchen, [F01-003]) and PP(c_order, [F01-006]) | dish-pos support = 2 |
| TC-S05 | FR-015a | PP(c_kitchen, [F01-003, F01-006]) and PP(c_order, [F01-006]) | dish-pos support = 2 (F01-006 counted once) |
| TC-S06 | FR-013a | Model stub also returns its own product suggestions | Suggestions ignored; candidates come only from the table |
| TC-S07 | FR-012 | PP(c_cash) with no evidence only | No candidates (dish-pay is not a candidate) |

## E. Ranking and selection (L1)

Input is the candidate list; output is primaries in rank order and candidates not selected.

| ID | Spec | Candidates | Expected primaries | Not selected |
|---|---|---|---|---|
| TC-R01 | FR-015a | cand(dish-pay, medium, 1) | dish-pay | — |
| TC-R02 | FR-015a | cand(dish-pos, medium, 1), cand(dish-pay, high, 2) | dish-pay, dish-pos | — |
| TC-R03 | FR-015a | cand(dish-pay, high, 2), cand(dish-pos, medium, 5), cand(dish-starter, medium, 1) | dish-pay, dish-pos | dish-starter |
| TC-R04 | FR-015a | cand(dish-pay, medium, 1), cand(dish-pos, medium, 3), cand(dish-starter, medium, 2) | dish-pos, dish-starter | dish-pay |
| TC-R05 | FR-015a | cand(dish-starter, high, 2), cand(dish-pay, high, 2), cand(dish-pos, medium, 5) | dish-pay, dish-starter | dish-pos |
| TC-R06 | FR-015a | cand(dish-professional-order, medium, 1), cand(dish-pos, medium, 1), cand(dish-pay, medium, 1) | dish-pay, dish-pos | dish-professional-order |
| TC-R07 | FR-015a | (none) | (none) | — |
| TC-R08 | FR-015a | Same as TC-R05 in a different input order | Same result as TC-R05 |

## F. Prerequisites (L1)

| ID | Spec | Candidates | Expected recommendations |
|---|---|---|---|
| TC-P01 | FR-015 | cand(dish-ai-phone-assistant, medium, 1), cand(dish-pos, medium, 1) | Primary: dish-ai-phone-assistant, dish-pos. Prerequisite: dish-professional-reservation (does not use a slot) |
| TC-P02 | FR-015, Edge case | cand(dish-professional-reservation, high, 2), cand(dish-ai-phone-assistant, medium, 1), cand(dish-pos, medium, 1) | Primary: dish-professional-reservation, dish-ai-phone-assistant. No separate prerequisite entry. Not selected: dish-pos |
| TC-P03 | FR-015, Edge case | cand(dish-ai-phone-assistant, high, 2), cand(dish-pay, high, 2), cand(dish-professional-reservation, medium, 1) | Primary: dish-ai-phone-assistant, dish-pay. Prerequisite: dish-professional-reservation. dish-professional-reservation is not listed as "not selected" |
| TC-P04 | FR-012 | As TC-P01 | Prerequisite confidence = confidence of dish-ai-phone-assistant; it addresses the same pain points |
| TC-P07 | FR-012 | As TC-P03, with PP(c_phone) `high` and PP(c_booking) `medium` | Prerequisite dish-professional-reservation lists PP(c_phone) and PP(c_booking); confidence `high` (from dish-ai-phone-assistant) |
| TC-P05 | FR-015 | cand(dish-pay, high, 2), cand(dish-pos, high, 2), cand(dish-ai-phone-assistant, medium, 1) | Primary: dish-pay, dish-pos. No prerequisite added (dish-ai-phone-assistant not selected) |
| TC-P06 | FR-015 | Any result | Each product appears at most once across primary and prerequisite entries |

## G. Decision (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-DEC01 | FR-020 | F01 with PP(c_cash, [F01-001]) | `recommend`, at least one product |
| TC-DEC02 | FR-013, FR-020 | F01 with only PP(c_none, [F01-004]) | `insufficient_evidence`; card says "insufficient evidence"; no products |
| TC-DEC03 | FR-017a, FR-020 | F01 with no pain points | `insufficient_evidence`; opening pitch "Not applicable"; general questions labelled "Not based on reviews" |
| TC-DEC04 | FR-017a | F05 (no reviews) | Same as TC-DEC03; summary shows 0 reviews analysed |
| TC-DEC05 | FR-021 | Any `insufficient_evidence` or `no_recommendation` card | No recommendations and no candidates |

## H. Quote check — deterministic check 3 (L1)

Review text for all cases: F01-001 `They only accept cash payments here.` unless stated.

| ID | Quote | Expect |
|---|---|---|
| TC-Q01 | `only accept cash` | Pass |
| TC-Q02 | `only  accept   cash` (extra spaces) | Pass |
| TC-Q03 | `  only accept cash  ` (leading/trailing spaces) | Pass |
| TC-Q04 | `They only accept cash payments here.` (whole review) | Pass |
| TC-Q05 | `only accept cash payments` (exactly 4 words) / `accept cash payments` (exactly 3 words) | Pass |
| TC-Q06 | `Only accept cash` (case differs) | Fail |
| TC-Q07 | `accept cash` (2 words) | Fail |
| TC-Q08 | `only accept card` (not in text) | Fail |
| TC-Q09 | `cash payments here!` (punctuation differs) | Fail |
| TC-Q10 | `“only accept cash”` (curly quotes added) | Fail |
| TC-Q11 | `` (empty) | Fail |
| TC-Q12 | Review F01-006; quote `wrong and they forgot` (line break in review, space in quote) | Pass |
| TC-Q13 | `here. Cash only, so` (spans F01-001 and F01-002) | Fail |

## I. Deterministic checks 1–18 (L1)

Each check gets one passing card and at least one failing card. "Valid card" means a card built from F01 that passes all checks.

| ID | Check | Failing input | Expect |
|---|---|---|---|
| TC-K00 | All | Valid card | All 18 checks pass |
| TC-K01a | 1 | Card missing the opening pitch section | Check 1 fails |
| TC-K01b | 1 | Decision `maybe` | Check 1 fails |
| TC-K01c | 1 | Pain point confidence `low` | Check 1 fails |
| TC-K02 | 2 | Evidence cites `F01-099` | Check 2 fails |
| TC-K03 | 3 | See section H | — |
| TC-K04 | 4 | F01 card cites F06-001 (same text as F01-001) | Check 4 fails |
| TC-K05 | 5 | Evidence for F01-002 shows `original` (stored: `translated`) | Check 5 fails |
| TC-K06 | 6 | Recommendation `dish-weblisting` | Check 6 fails |
| TC-K07 | 7 | dish-ai-phone-assistant recommended without dish-professional-reservation | Check 7 fails |
| TC-K08a | 8 | F02 card with a recommendation | Check 8 fails |
| TC-K08b | 8 | F04 card stating only "closed" | Check 8 fails (both reasons required) |
| TC-K08c | 8 | F03 card with a pain point or opening pitch content | Check 8 fails |
| TC-K09a | 9 | `insufficient_evidence` card with a product | Check 9 fails |
| TC-K09b | 9 | `recommend` card with no product | Check 9 fails |
| TC-K10a | 10 | PP with 2 distinct reviews marked `medium` | Check 10 fails |
| TC-K10b | 10 | PP with 1 review marked `high` | Check 10 fails |
| TC-K11a | 11 | 3 primary recommendations | Check 11 fails |
| TC-K11b | 11 | Prerequisite dish-professional-reservation with no primary requiring it | Check 11 fails |
| TC-K12a | 12 | A pain point with no linked discovery question | Check 12 fails |
| TC-K12b | 12 | "Not based on reviews" question on a card that has pain points | Check 12 fails |
| TC-K12c | 12 | General question linked to an unknown category | Check 12 fails |
| TC-K13 | 13 | dish-pos support shown as 3 when its pain points cite 2 distinct reviews | Check 13 fails |
| TC-K14a | 14 | Primaries listed as dish-pos (medium), dish-pay (high) | Check 14 fails (wrong order) |
| TC-K14b | 14 | Primary cand(dish-starter, high, 2), not selected cand(dish-pay, high, 2) | Check 14 fails (dish-pay ranks higher by product_id) |
| TC-K15 | 15 | One primary and one candidate not selected | Check 15 fails |
| TC-K16 | 16 | Pain point with category `c_unknown` | Check 16 fails |
| TC-K17a | 17 | Primary dish-starter addressing only PP(c_cash) | Check 17 fails (not mapped) |
| TC-K17b | 17 | PP(c_kitchen) on the card but dish-pos neither primary nor not selected | Check 17 fails (missing candidate) |
| TC-K17c | 17 | dish-professional-reservation present only as prerequisite while PP(c_booking) is on the card (TC-P03) | Check 17 passes |
| TC-K17d | 17 | PP(c_cash) with no evidence on the card; dish-pay neither primary nor not selected | Check 17 passes (check 1 fails) |
| TC-K18a | 18 | Two pain points with category c_cash | Check 18 fails |
| TC-K18b | 18 | Two pain points with category `other_unmapped` (c_none in fixtures) | Check 18 passes |
| TC-K19 | All | Run all checks on a card failing checks 2 and 7 | Both failures reported, each with a reason; other checks still run |

## J. Plain-text output (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-T01 | FR-006, FR-022 | Valid `recommend` card | Text contains all six sections in a fixed order |
| TC-T02 | FR-009, FR-022 | Valid card | Every evidence item shows review ID, quote and text source |
| TC-T03 | FR-015b | Card with candidates not selected | Each shows product ID, confidence, support count and addressed pain points; primaries show support count |
| TC-T04 | FR-006 | `insufficient_evidence` card | Recommended-products section says "No products recommended"; card says "insufficient evidence" |
| TC-T05 | FR-006, FR-020a | F02 short card | Three sections say "Not applicable"; reason stated |
| TC-T06 | FR-017a | Card with general questions | Each shows the label "Not based on reviews" |
| TC-T07 | FR-012 | Card with a prerequisite | Prerequisite is marked as prerequisite and names the product that requires it |
| TC-T08 | FR-022 | Same structured card rendered twice | Identical text |
| TC-T09 | FR-024 | Any card (`recommend`, `insufficient_evidence` and short card) | Text contains the fixed line "Prepared for the sales rep. Hypotheses from public reviews; not a final decision." |

## K. Pipeline with a stubbed model (L2)

| ID | Spec | Stub returns | Expect |
|---|---|---|---|
| TC-I01 | FR-001 | F01: c_cash [F01-001, F01-002], c_kitchen [F01-003], valid quotes | `recommend`; primaries dish-pay (high, 2), dish-pos (medium, 1); all checks pass |
| TC-I02 | FR-013a | F01: c_phone [F01-003] | dish-ai-phone-assistant primary + dish-professional-reservation prerequisite |
| TC-I03 | FR-025, Edge case | A quote not in the review | Card produced (not a generation failure); check 3 fails; agent does not silently fix the quote |
| TC-I04 | FR-025, Edge case | A category not in the table | Card produced (not a generation failure); check 16 fails |
| TC-I09 | FR-025, Edge case | Evidence citing F06-001 for F01 | Card produced; check 4 fails |
| TC-I05 | Edge case | Output that cannot be parsed | Error reported for the restaurant; no partial card |
| TC-I06 | Edge case | Stub raises an error (call failed) | Error reported; no partial card |
| TC-I07 | FR-020a | Any, for F02/F03/F04 | Stub not called (same as TC-E06) |
| TC-I08 | FR-017a | No pain points | `insufficient_evidence`; general questions; all checks pass |

## L. Gold-label validation (L1)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-G01 | FR-027 | Valid file | All rows loaded |
| TC-G02 | FR-027 | `must_include` = `dish-pay;dish-pos` | Parsed as two product IDs |
| TC-G03 | FR-027 | Blank `must_include` and `acceptable` | Empty lists |
| TC-G04 | FR-028 | Row with restaurant `F99` | Invalid row: unknown restaurant |
| TC-G05 | FR-028 | Decision `yes` | Invalid row: invalid decision |
| TC-G06 | FR-028 | Product `dish-weblisting` | Invalid row: unknown product |
| TC-G07 | FR-028 | Missing column `acceptable` | File rejected with a clear error |
| TC-G08 | FR-028 | Two rows for F01 | Invalid row: duplicate restaurant |
| TC-G09 | FR-028 | `must_include` = dish-pay, `acceptable` = dish-pay;dish-pos | Invalid row: product in both lists |
| TC-G10 | FR-028 | Decision `insufficient_evidence` with `must_include` = dish-pos | Invalid row: must_include without `recommend` |
| TC-G11 | FR-028 | File with three different invalid rows | All three listed, each with its reason (validation does not stop at the first error) |
| TC-G12 | FR-028 | `no_recommendation` or `insufficient_evidence` with blank product lists; `recommend` with blank `must_include` | Valid |

## M. Metrics (L1)

Synthetic results for three restaurants unless stated.

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-M01 | SC-001 | 3 cards, all checks pass | 100%, target met |
| TC-M02 | SC-001 | 1 of 3 cards fails one check | 66.7%, target not met |
| TC-M03 | SC-002 | Closed card with a product | Target not met |
| TC-M04 | SC-003 | Decisions match for 2 of 3 | Reports 2/3; target compares against "at least 13 of 15" on the real run |
| TC-M05 | SC-004 | must_include {pay, pos}, {starter}, {}; recommended {pay}, {starter}, {pos} | 2/3 = 66.7%, target not met |
| TC-M06 | SC-004 | Restaurant with wrong decision and no products | Its must_include products count as missed |
| TC-M07 | SC-005 | Restaurant A recommends a product outside must_include ∪ acceptable; B does not | Count = 1, target met |
| TC-M08 | SC-005 | Two such restaurants | Count = 2, target not met |
| TC-M09a | SC-004 | must_include {ai-phone, reservation}; card: primary ai-phone, prerequisite reservation | 2/2 hit (prerequisites count) |
| TC-M09b | SC-005 | must_include {ai-phone}, acceptable {}; card: primary ai-phone, prerequisite reservation | Restaurant counted (reservation is outside the lists) |
| TC-M10 | Edge case | Agent failed for one restaurant | Counts as failing check 1 (SC-001) and as a decision mismatch (SC-003) |

## N. Evaluation run (L2)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-V01 | FR-026 | Gold labels + stub | One command produces a report |
| TC-V02 | FR-029 | 3 labelled restaurants | Agent runs exactly 3 times, once each |
| TC-V03 | Edge case | A restaurant in the data but not in the gold labels | Not evaluated; listed as unlabelled |
| TC-V04 | FR-032 | Any run | Report shows git commit, LLM provider, model name, run date |
| TC-V05 | FR-030 | Any run | Pass/fail per check per card, with failure reason |
| TC-V06 | Story 3 #3 | Any run | Per restaurant: expected and actual decision, recommended products, missed must_include, products outside must_include ∪ acceptable |
| TC-V07 | FR-032 | Any run | Generated cards included or referenced |
| TC-V08 | FR-033 | Any run | Gold-label file and raw data unchanged (content identical before and after) |
| TC-V09 | FR-028 | Gold labels with one invalid row | Invalid row listed; evaluation stops; agent (stub) never called; no metrics or report of results produced |

## O. Real-data regression (L3)

| ID | Spec | Given | Expect |
|---|---|---|---|
| TC-X01 | FR-014 | `data/products/` | 6 products load; dish-ai-phone-assistant requires dish-professional-reservation |
| TC-X02 | FR-013a | `data/products/pain-point-product-mapping.json` | Valid: 21 categories, unique IDs, all product IDs in the catalog |
| TC-X03 | FR-027, FR-028 | `data/eval/expected.csv` | Valid: 15 rows, no invalid rows, every restaurant exists |
| TC-X04 | FR-020a | R10 | Short card: `no_recommendation`, reason "chain", passes all checks |
| TC-X05 | FR-020a | R11 | Short card: `no_recommendation`, reason "closed", passes all checks |

## Not covered by automated tests (L4)

| Requirement | How it is verified |
|---|---|
| Classification of reviews into categories | Evaluation against `expected.csv` (SC-003 – SC-005) |
| FR-016 opening pitch reports in the third person what guests say, no blame | Human review at each checkpoint (SC-006) |
| FR-014 product descriptions consistent with official facts; sales notes not presented as facts | Human review |
| Product limits written as text in the catalog | Human review (constitution Principle II) |
| FR-018 no quotes, offers or discounts | Human review |
| FR-019 no claims about recency from review dates | Human review |
| FR-024 no outward-facing action | Design review in the plan (the agent has no capability to send anything); the "not a final decision" line is tested by TC-T09 |

---

## Open questions

Found while writing the cases. All were resolved by the owner on 2026-11-26 and written into the spec and `docs/spec-changes.md`.

| ID | Question | Affects | Suggested answer |
|---|---|---|---|
| Q1 | May the same mapped category appear as two pain points on one card? | FR-008, check 18 | **Resolved 2026-11-26**: no; only `other_unmapped` may repeat. |
| Q2 | Which pain points does a prerequisite list when it has its own pain point? | FR-012 | **Resolved 2026-11-26**: requiring product's pain points plus its own; confidence of the requiring product. |
| Q3 | What does a short card show for reviews analysed? | FR-007 | **Resolved 2026-11-26**: "Reviews not analysed". |
| Q4 | Do prerequisites count in SC-004 and SC-005? | SC-004, SC-005 | **Resolved 2026-11-26**: yes. |
| Q5 | Which gold-label rows are invalid, and does the evaluation stop? | FR-028 | **Resolved 2026-11-26**: duplicate restaurant, product in both lists and must_include without `recommend` are invalid; the evaluation lists all invalid rows and stops before running the agent. |
| Q6 | Is an unknown category or non-verbatim quote a generation failure? | Edge cases | **Resolved 2026-11-26**: no; the card is produced and fails checks. |
