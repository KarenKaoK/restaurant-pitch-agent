# Feature Specification: Restaurant Visit Card Agent

**Feature Branch**: `001-visit-card-agent`

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "Create the feature specification for the Restaurant Visit Card Agent. DISH sales reps, before visiting independent small/mid-sized restaurants, need to quickly understand the restaurant, know which DISH product to recommend, and how to open the conversation. The agent reads the restaurant's public reviews and generates a visit card for the rep. Stories: generate a visit card (P1), no recommendation (P1), evaluation (P2)."

**References**: `docs/discovery/01-business-research.md`, `docs/discovery/02-user-discovery.md`, `docs/discovery/03-user-stories.md`, `docs/discovery/04-data-collection.md`, `.specify/memory/constitution.md` (v1.0.0)

## Clarifications

### Session 2026-11-26

- Q: How many reviews must support a pain point, and what confidence does it get? → A: One review is enough to recommend. Exactly 1 distinct review → `medium`; more than 1 → `high`.
- Q: Maximum number of products per card? → A: At most 2 primary products; a required prerequisite (`requires`) is added on top and does not count.
- Q: When is a finding `low`? → A: There is no `low` level. Pain points are `high` or `medium`; "insufficient evidence" means no pain point maps to a catalog product. Discovery questions are generated from the pain points on the card.
- Q: When more than 2 products qualify as primary, which ones are selected? → A: Rank by product confidence (`high` > `medium`), then by the number of distinct review IDs supporting the product (merged across all its pain points), highest first. Remaining ties are broken by `product_id` in ascending alphabetical order (initially random; changed the same day so results are reproducible). Select the top 2; prerequisites do not count. No weighted scoring.
- Q: Who decides which product addresses a pain point? → A: A fixed pain-point category list with a category → product mapping table, stored with the product catalog. The model only classifies reviews into categories and extracts evidence; candidate products and their ranking are derived from the table by rule.
- Q: Should cards for closed or chain restaurants still analyse reviews? → A: No. They are short cards produced by rule without calling the model: restaurant summary (without a review-based description), decision `no_recommendation` and the reason that the restaurant is not in the recommendation target list because it is closed and/or a chain. Pain points, opening pitch and discovery questions each state "Not applicable".
- Q: How strict is the verbatim-quote check, and how short may a quote be? → A: After trimming leading/trailing whitespace and collapsing runs of whitespace to one space (in both quote and review text), the quote must be an exact substring of the review `text`, case and punctuation included, and must contain at least 3 words.
- Q: On an `insufficient_evidence` card, what do the opening pitch and discovery questions contain? → A: If the card has pain points (whose categories map to no product), the pitch and questions are written as usual. If it has no pain points at all, the pitch states "Not applicable" and the discovery questions are general operational questions derived from the pain-point category list, each labelled "Not based on reviews".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a visit card (Priority: P1)

A DISH field sales rep is about to visit an independent restaurant. The rep enters the restaurant's ID and receives a visit card that summarises the restaurant, lists the operational pain points that guests mention in reviews (each backed by verbatim quotes), recommends one or more DISH products that address those pain points, suggests a respectful opening line and lists discovery questions for the owner. The rep can export the card as plain text and paste it into their notes.

**Why this priority**: This is the core value of the project (discovery doc 03, US-01 – US-03, US-06, US-07, US-10 – US-12, US-15). Without it there is no product.

**Independent Test**: Run the agent for one independent, non-closed restaurant with clear pain signals in its reviews. Verify that the card contains all five sections, that every quote can be found verbatim in the cited review, and that the plain-text export is readable without any special viewer.

**Acceptance Scenarios**:

1. **Given** a restaurant ID that exists in the restaurant dataset, is not closed and is not a chain, **When** the rep requests a visit card, **Then** the card contains a restaurant summary, a pain-point list, a recommended-products section, an opening pitch and discovery questions.
2. **Given** a generated card, **When** the rep reads a pain point, **Then** it shows a confidence level and at least one piece of evidence, and each piece of evidence shows the review ID, a verbatim excerpt of that review's text and the review's text source (`original`, `translated` or `expanded`).
3. **Given** a generated card with a recommendation, **When** the rep reads it, **Then** the product is identified by its catalog `product_id`, and the card states which pain point(s) it addresses, which evidence supports it and its confidence level.
4. **Given** a generated card, **When** the rep reads the opening pitch, **Then** it is worded from the guests' perspective (e.g. "several guests mention…") and does not accuse or blame the owner.
5. **Given** a pain point on the card, **When** the rep reads the discovery questions, **Then** there is at least one question the rep can ask the owner to confirm or reject that pain point, so the card reads as a hypothesis, not a verdict.
6. **Given** a generated card, **When** the rep exports it, **Then** the full card is available as plain text with all sections and evidence intact.
7. **Given** more than 2 candidate products where one is `high` and the others are `medium`, **When** the card is generated, **Then** the `high` product is selected first and the remaining slot goes to the `medium` product with the most distinct supporting reviews.
8. **Given** two candidate products with the same confidence, **When** the card is generated, **Then** the product supported by more distinct review IDs (counted across all pain points it addresses, without duplicates) ranks higher.
9. **Given** candidate products that tie on both confidence and support count for the last slot, **When** the card is generated, **Then** the product whose `product_id` comes first alphabetically is selected, and the others are listed as candidates not selected.
10. **Given** a selected primary product that has a `requires` prerequisite, **When** the card is generated, **Then** the prerequisite is added as a `prerequisite` recommendation and the second primary slot is still available.
11. **Given** a restaurant ID that does not exist in the dataset, **When** the rep requests a card, **Then** the agent reports that the restaurant is unknown and produces no card.

---

### User Story 2 - No recommendation (Priority: P1)

For some restaurants the right answer is "do not pitch a product". If the restaurant has closed, is a chain, or its reviews do not give enough evidence, the agent still produces a visit card but recommends no product and clearly states why. In the insufficient-evidence case, the agent turns whatever it found into discovery questions so the rep can still learn something on the visit.

**Why this priority**: Recommending a product to a closed restaurant, a chain outside the target group, or on weak evidence damages the rep's credibility (constitution Principle III; discovery doc 03, US-16). This safeguard is as important as the recommendation itself.

**Independent Test**: Run the agent for the closed restaurant, the chain restaurant and a restaurant with very few or non-specific reviews. Verify that each card contains no product recommendation and states the correct reason.

**Acceptance Scenarios**:

1. **Given** a restaurant whose `status` is `closed`, **When** the rep requests a card, **Then** the card recommends no product and states that the restaurant is not in the recommendation target list because it is closed.
2. **Given** a restaurant whose `segment` is `chain`, **When** the rep requests a card, **Then** the card recommends no product and states that the restaurant is not in the recommendation target list because it is a chain.
3. **Given** a restaurant that is both closed and a chain, **When** the rep requests a card, **Then** the card recommends no product and states both reasons.
4. **Given** a closed or chain restaurant, **When** the card is generated, **Then** its reviews are not analysed, the model is not called, and the pain points, opening pitch and discovery questions sections each state "Not applicable".
5. **Given** an independent, non-closed restaurant whose reviews do not meet the evidence threshold for any recommendation, **When** the rep requests a card, **Then** the card states "insufficient evidence", recommends no product, and lists the findings as discovery questions.
6. **Given** an eligible restaurant with no pain points at all, **When** the card is generated, **Then** the decision is `insufficient_evidence`, the opening pitch states "Not applicable", and the discovery questions are general operational questions, each labelled "Not based on reviews" and linked to a pain-point category.
7. **Given** an `insufficient_evidence` card, **When** the rep reads it, **Then** the restaurant summary and any evidence-backed observations remain verifiable (same evidence rules as Story 1).

---

### User Story 3 - Evaluation (Priority: P2)

The project owner runs a single command that generates a visit card for every restaurant listed in the gold-label file, checks every card with the deterministic checks from constitution Principle VI, compares each card's decision and recommended products against the gold labels, and writes an evaluation report. The report records the git commit and model name so runs can be compared over time.

**Why this priority**: LLM output is not developed test-first, so this evaluation is the only way to measure whether the agent is good enough (constitution Principle VI). It depends on Stories 1 and 2 being in place.

**Independent Test**: With a filled-in gold-label file, run the evaluation command once and verify that the report lists every labelled restaurant, the result of each deterministic check per card, the accuracy metrics in the Success Criteria, the git commit and the model name.

**Acceptance Scenarios**:

1. **Given** a gold-label file with one row per restaurant, **When** the owner runs the evaluation command, **Then** the agent runs exactly once for each labelled restaurant and a report is produced.
2. **Given** generated cards, **When** the evaluation runs, **Then** each card is checked against every deterministic check in FR-025 and the report shows pass/fail per check per card, with the failure reason.
3. **Given** gold labels, **When** the evaluation runs, **Then** the report shows, per restaurant, the expected decision, the actual decision, the recommended products, which `must_include` products were missed, and which recommended products were outside `must_include` and `acceptable`.
4. **Given** a completed run, **When** the owner opens the report, **Then** it shows the aggregate metrics SC-001 – SC-005 and whether each target is met.
5. **Given** a completed run, **When** the owner opens the report, **Then** it shows the git commit and the model name used for the run.
6. **Given** a gold-label row that references an unknown restaurant ID, an invalid decision value or an unknown product ID, **When** the evaluation runs, **Then** it reports the invalid row clearly instead of silently scoring it.

---

### Edge Cases

- **Restaurant with very few reviews** (e.g. R12 has one review): the agent may still report a pain point if the evidence threshold is met; otherwise it uses the insufficient-evidence path.
- **Restaurant whose reviews are all positive**: no pain point is found → `insufficient_evidence`; the opening pitch states "Not applicable" and the card lists general discovery questions labelled "Not based on reviews" (FR-017a).
- **Pain point whose category maps to no product** (e.g. food quality, price level): it may appear on the card as a pain point with a discovery question, but it produces no candidate product.
- **Review that fits no category in the list**: it is not reported as a pain point; the model MUST NOT invent a new category.
- **More than 2 candidate products**: only the top 2 by the FR-015a ranking become primary recommendations; the others are listed as candidates not selected, with their confidence and support count.
- **One product addresses several pain points that cite the same review**: the review is counted once in the product's support count.
- **Tie on confidence and support count**: the tie is broken by `product_id` in ascending alphabetical order (e.g. `dish-pay` before `dish-pos`), so the same pain points and evidence always produce the same selection.
- **Prerequisite product that is also a candidate in its own right** (e.g. `dish-professional-reservation` addresses its own pain point): it is ranked as a candidate; if selected, it counts as a primary product, otherwise it is added only as a prerequisite and does not use a slot.
- **Recommended product with a catalog prerequisite** (e.g. `dish-ai-phone-assistant` requires `dish-professional-reservation`): the required product MUST also be recommended, or the dependent product MUST NOT be recommended.
- **Product limits written as text in the catalog** (e.g. a product unsuited to a certain venue type): the agent must respect them; violations are found in human review, not automatically.
- **Quote that spans text not present in the review** (e.g. merged from two reviews, or reworded): fails the deterministic evidence check.
- **Quote that differs only in whitespace** (extra spaces, line breaks): passes after whitespace normalisation. A quote that differs in case, punctuation or quote style (e.g. `"` vs `“`) fails.
- **Quote shorter than 3 words** (e.g. "too slow"): fails the deterministic evidence check.
- **Evidence citing a review from another restaurant**: fails the deterministic check.
- **Reviews with `text_source` = `translated` or `expanded`**: the quote is still taken from the stored `text`, and the card shows the text source so the rep knows it is not the guest's own wording.
- **Review dates**: the agent MUST NOT use review dates to say a problem is recent, ongoing or resolved.
- **Generation failure** (the model returns output that cannot be parsed or a call fails): the agent reports an error for that restaurant instead of producing a partial card; in evaluation, the card counts as failing the format check.
- **Restaurant in the dataset but missing from the gold-label file**: not evaluated; the report lists it as unlabelled.

## Requirements *(mandatory)*

### Functional Requirements

**Input and data access**

- **FR-001**: The agent MUST accept a single restaurant ID as input and produce one visit card for that restaurant.
- **FR-002**: The agent MUST use only the processed restaurant dataset, the processed review dataset and the product catalog (including the pain-point category table, FR-013a) as inputs. It MUST NOT read raw data or anything in the evaluation folder (constitution Principle V).
- **FR-003**: The agent MUST use only the reviews whose restaurant ID matches the requested restaurant.
- **FR-004**: If the restaurant ID does not exist, the agent MUST report this and MUST NOT produce a card.
- **FR-005**: The agent MUST NOT store, display or log reviewer identity data.

**Visit card content**

- **FR-006**: Every card MUST contain these sections: restaurant summary, pain points, recommendation decision, recommended products, opening pitch, discovery questions. A section with no content MUST say so explicitly (e.g. "No products recommended"). On a closed or chain card (FR-020a), the pain points, opening pitch and discovery questions sections MUST state "Not applicable".
- **FR-007**: The restaurant summary MUST include the restaurant's name, city, status, segment and the number of reviews analysed, plus a short description based only on the restaurant data and its reviews. On a closed or chain card the review-based description is omitted.
- **FR-008**: Each pain point MUST have a category from the pain-point category list (FR-013a), a short description, a confidence level (`high` or `medium`) and at least one piece of evidence. There is no `low` level in v1.
- **FR-009**: Each piece of evidence MUST include the review ID, a verbatim excerpt of that review's `text` field, and that review's `text_source`. An excerpt MUST come from a single review, MUST NOT be reworded, and MUST contain at least 3 words (words are separated by whitespace).
- **FR-010**: A finding that cannot be supported by at least one verbatim review excerpt MUST NOT appear on the card, neither as a pain point nor in the opening pitch.
- **FR-011**: The confidence level of a pain point MUST follow this rule, counting distinct reviews of the restaurant cited as evidence: more than 1 review → `high`; exactly 1 review → `medium`. A single review is enough to support a recommendation.
- **FR-012**: Each recommended product MUST be identified by its catalog `product_id`, MUST list the pain point(s) it addresses and the evidence (review IDs) behind them, and MUST carry a confidence level equal to the highest confidence among the pain points it addresses. A required prerequisite product (see FR-015) carries the confidence of the product that requires it.
- **FR-013**: A product MAY be recommended only if it addresses at least one pain point on the card. Exception: a product added only as a required prerequisite (FR-015) addresses the same pain points as the product that requires it. "Insufficient evidence" means the restaurant is eligible but no pain point on the card belongs to a category that maps to a product.
- **FR-013a**: The project MUST keep a fixed pain-point category list and a category → product mapping table in `data/products/pain-point-product-mapping.json`. Each category MUST have a unique `category_id`, a `definition` and a `product_ids` list (zero or more catalog `product_id`s); categories with an empty `product_ids` list (e.g. `other_unmapped` for food quality or price) are allowed. Other fields in the file (example signals, exclusions, classification rules) guide classification only and MUST NOT override this spec. The model MUST only assign reviews to categories in this list and extract evidence; it MUST NOT decide which product addresses a pain point. The products that address a pain point are exactly the products mapped to its category. Candidate products, support counts, confidence and the FR-015a ranking MUST be computed by rule from the pain points and the table, not by the model.
- **FR-014**: The agent MUST recommend only products in the catalog, MUST respect the `requires` prerequisites in the catalog, and MUST keep product descriptions consistent with the catalog's official facts. Project-authored sales notes MUST NOT be presented as official DISH facts.
- **FR-015**: A card MUST recommend at most 2 primary products. A product listed in a primary product's `requires` field is added as a prerequisite and does not count toward this limit, unless it is also recommended in its own right. Each recommendation MUST be marked as `primary` or `prerequisite`.
- **FR-015a**: When more than 2 catalog products qualify as primary (each is mapped by the table to the category of at least one pain point on the card, FR-013a), the agent MUST select primaries in this order, without any weighted scoring:
  1. by product confidence (FR-012), `high` before `medium`;
  2. then by support count, highest first. The support count is the number of distinct review IDs cited as evidence across all pain points the product addresses; a review cited by several of those pain points counts once;
  3. remaining ties are broken by `product_id` in ascending alphabetical order.
  The top 2 become primary recommendations, listed in rank order. Prerequisites added under FR-015 do not take a slot.
- **FR-015b**: Every card with decision `recommend` MUST list each primary recommendation's support count, and MUST list every qualifying product that was not selected ("candidates not selected") with its confidence, support count and addressed pain points, so the rep and the deterministic checks can verify the selection.
- **FR-016**: The opening pitch MUST be worded from the guests' perspective and MUST NOT accuse or blame the owner. It MUST refer only to pain points that appear on the card.
- **FR-017**: Discovery questions MUST be open questions the rep can ask the owner to confirm or reject a finding. Each pain point on the card MUST have at least one discovery question. On an `insufficient_evidence` card, the findings MUST be turned into discovery questions.
- **FR-017a**: When an eligible card has no pain points at all, the opening pitch MUST state "Not applicable", and the discovery questions MUST be general operational questions derived from the pain-point category list. Each such question MUST be labelled "Not based on reviews", MUST be linked to a category in the list, and MUST NOT claim or imply that guests mentioned a problem. General questions MUST NOT appear on a card that has pain points.
- **FR-018**: The card MAY cite prices or pricing models stated in the catalog, but MUST NOT calculate quotes, combine prices into an offer or offer discounts.
- **FR-019**: The card MUST NOT use review dates to claim that a problem is recent, ongoing or resolved.

**Recommendation decision**

- **FR-020**: Every card MUST state exactly one decision: `recommend`, `no_recommendation` or `insufficient_evidence`.
  - `no_recommendation` MUST be used when the restaurant's `status` is `closed` or its `segment` is `chain`, with the reason(s) stated on the card. This check takes precedence over all others.
  - `insufficient_evidence` MUST be used when the restaurant is eligible but no product meets FR-013. The card MUST say "insufficient evidence" and turn the findings into discovery questions.
  - `recommend` MUST be used otherwise, and the card MUST then list at least one product.
- **FR-020a**: For a restaurant whose `status` is `closed` or whose `segment` is `chain`, the card MUST be produced by rule without calling the model and without analysing reviews. It MUST contain the restaurant summary (FR-007, without the review-based description), decision `no_recommendation`, and the reason: the restaurant is not in the recommendation target list because it is closed, because it is a chain, or both.
- **FR-021**: Cards with decision `no_recommendation` or `insufficient_evidence` MUST list no products.

**Output**

- **FR-022**: Every card MUST be exportable as plain text containing all sections and all evidence fields.
- **FR-023**: Every card MUST also be available in a structured, machine-checkable form, so the deterministic checks can run on it.
- **FR-024**: The agent MUST NOT contact restaurants, send messages or take any outward-facing action, and MUST NOT present the card as a final decision.

**Deterministic checks (constitution Principle VI)**

- **FR-025**: A check function MUST verify on every card that:
  1. the card's structure is valid (all required sections and fields present, valid decision and confidence values);
  2. every cited review ID exists in the review dataset;
  3. every quote is a verbatim excerpt of the cited review's `text` field: after trimming leading and trailing whitespace and collapsing every run of whitespace to a single space in both the quote and the review text, the quote is an exact substring of the review text (case and punctuation must match), and it contains at least 3 words;
  4. every cited review belongs to the card's restaurant;
  5. every cited `text_source` matches the review's stored `text_source`;
  6. every recommended `product_id` exists in the catalog;
  7. every recommended product with a `requires` field is recommended together with the required product;
  8. a card for a restaurant with `status` = `closed` or `segment` = `chain` has decision `no_recommendation`, states each applicable reason (closed, chain), and contains no recommendations, candidates, pain points, opening pitch or discovery questions;
  9. a card with decision `insufficient_evidence` or `no_recommendation` contains no recommendations, and a card with decision `recommend` contains at least one;
  10. every pain point's confidence matches FR-011 (more than 1 distinct cited review → `high`, exactly 1 → `medium`);
  11. the card has at most 2 `primary` recommendations, and every `prerequisite` recommendation is required by a `primary` one (FR-015);
  12. every pain point is linked to at least one discovery question; questions labelled "Not based on reviews" appear only when the card has no pain points, and each is linked to a category in the list;
  13. every listed support count (primary and not-selected candidates) equals the number of distinct review IDs cited across the pain points that product addresses;
  14. primary recommendations are listed in FR-015a rank order (confidence, then support count, then `product_id` ascending), and no candidate not selected ranks higher than a selected primary under that full order;
  15. a candidate not selected appears only when 2 primary recommendations are already selected;
  16. every pain point's category exists in the pain-point category list;
  17. every primary recommendation and every candidate not selected is mapped by the table to the category of at least one pain point it lists, and every product mapped from a pain point category on the card appears as a primary recommendation or a candidate not selected (unless it is only present as a prerequisite).

**Evaluation**

- **FR-026**: The evaluation MUST be runnable with a single command.
- **FR-027**: The evaluation MUST read gold labels from `data/eval/expected.csv` with the columns `restaurant_id`, `decision` (`recommend` / `no_recommendation` / `insufficient_evidence`), `must_include` (zero or more product IDs), `acceptable` (zero or more product IDs) and `rationale`. Multiple product IDs in one field are separated by `;`.
- **FR-028**: The evaluation MUST validate the gold-label file before running and report invalid rows (unknown restaurant, invalid decision, unknown product ID).
- **FR-029**: The evaluation MUST run the agent exactly once per labelled restaurant.
- **FR-030**: The evaluation MUST run all FR-025 checks on every card and report pass/fail per check per card.
- **FR-031**: The evaluation MUST compute and report the metrics in SC-001 – SC-005 and whether each target is met.
- **FR-032**: The evaluation report MUST record the git commit, the model name and the run date, and MUST include the generated cards (or a reference to them) so results can be reviewed.
- **FR-033**: The evaluation MUST NOT modify raw data or the gold-label file.

### Key Entities

- **Restaurant**: a restaurant in the processed dataset. Attributes: restaurant ID, name, city, address, status (`unknown`, `closed`, …), segment (`independent`, `chain`).
- **Review**: a public review of one restaurant. Attributes: review ID, restaurant ID, text, text source (`original`, `translated`, `expanded`), review date, rating, platform, source URL. Contains no reviewer identity data.
- **Product**: a DISH product in the catalog. Attributes: product ID, name, category, optional prerequisite (`requires`), official facts, product limits, sales notes.
- **Visit Card**: the agent's output for one restaurant. Contains restaurant summary, decision, decision reason(s), pain points, recommendations, opening pitch, discovery questions.
- **Pain Point Category**: an entry in the fixed category list. Has category ID, short definition and zero or more mapped product IDs.
- **Pain Point**: an operational problem inferred from reviews. Has category, description, confidence level and one or more evidence items.
- **Evidence**: a link from a claim to a review. Has review ID, verbatim excerpt and text source.
- **Recommendation**: a product suggested on a card. Has product ID, role (`primary` or `prerequisite`), addressed pain points, supporting review IDs, support count (distinct review IDs) and confidence level.
- **Candidate Not Selected**: a product that qualifies as primary but ranked below the top 2. Has product ID, confidence, support count and addressed pain points. Not a recommendation.
- **Discovery Question**: a question for the rep to ask the owner, linked to the pain point it tests, or — when the card has no pain points — a general question linked to a pain-point category and labelled "Not based on reviews".
- **Gold Label**: the owner's expected result for one restaurant: decision, `must_include` products, `acceptable` products, rationale.
- **Evaluation Report**: the result of one evaluation run: per-card check results, per-restaurant comparison with gold labels, aggregate metrics, git commit, model name, run date.

## Success Criteria *(mandatory)*

All criteria are measured by one evaluation run over the 15 labelled restaurants.

### Measurable Outcomes

- **SC-001**: 100% of generated visit cards pass all deterministic checks (FR-025).
- **SC-002**: 100% of cards for closed or chain restaurants contain no recommended products.
- **SC-003**: The card's decision matches the gold-label decision for at least 13 of 15 restaurants.
- **SC-004**: At least 80% of all `must_include` products (summed over all labelled restaurants) appear in the corresponding card's recommendations.
- **SC-005**: At most 1 restaurant has a card that recommends a product outside its `must_include` and `acceptable` lists.
- **SC-006**: In the human review at each checkpoint, every opening pitch reviewed is worded from the guests' perspective and does not blame the owner, and no recommendation violates a product limit written in the catalog.

## Assumptions

- The rep selects a restaurant from the predefined offline dataset (15 restaurants in Düsseldorf); no live search.
- All review text in the processed dataset is in English; the agent does not translate.
- A restaurant `status` of `unknown` is treated as open.
- The gold-label file `data/eval/expected.csv` will be created and filled in by the project owner before the evaluation is run; it does not exist yet. The existing `data/eval/labels.csv` (review topic tags) is not used by this feature.
- Multi-value product ID fields in the gold-label file use `;` as the separator, matching the existing `labels.csv` convention.
- "Recommendation accuracy" means the metrics SC-003 – SC-005.
- The pain-point category list and mapping table are authored by the project owner before implementation, starting from the signal → product table in discovery doc 01 §5.2 and limited to the products in `data/products/`. Changing the table is a catalog data change and is committed separately from code (constitution, Scope and Data Constraints).
- Country availability of products is not considered in v1 (constitution Principle II).
- Rule-based parts (data loading, checks, formatting, metric calculation) are developed test-first; the LLM-generated card content is verified by the evaluation.

## Out of Scope

- Live review collection, CRM integration, route planning, batch generation of cards for all restaurants outside the evaluation
- Assessing review recency
- Calculating quotes or discounts
- Any outward-facing action (contacting restaurants, sending messages)
- A web interface
- Detecting which products a restaurant already uses (discovery doc 03, US-W3)
- Rep feedback and visit notes (US-18, US-19)
