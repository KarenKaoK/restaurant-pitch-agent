# Contract: Visit Card

Two forms of the same card: structured JSON (FR-023), which the deterministic checks read, and plain text (FR-022), which the rep reads. Field rules are in [data-model.md](../data-model.md).

## Structured form (JSON)

Example: an eligible card with one primary product, a prerequisite and a candidate not selected (values are illustrative).

```json
{
  "schema_version": "1",
  "restaurant": {
    "restaurant_id": "R04",
    "name": "Example Bistro",
    "city": "Düsseldorf",
    "status": "unknown",
    "segment": "independent",
    "reviews_analysed": 20,
    "description": "Neighbourhood bistro; guests mention busy evenings and booking by phone."
  },
  "decision": "recommend",
  "decision_reasons": [],
  "pain_points": [
    {
      "pain_point_id": "PP1",
      "category_id": "unanswered_phone_calls",
      "description": "Guests could not reach the restaurant by phone.",
      "confidence": "high",
      "evidence": [
        {"review_id": "R04-003", "quote": "nobody picked up the phone", "text_source": "translated"},
        {"review_id": "R04-011", "quote": "tried to call three times", "text_source": "original"}
      ]
    }
  ],
  "recommendations": [
    {
      "product_id": "dish-ai-phone-assistant",
      "name": "AI Phone Assistant (add-on for DISH Professional Reservation)",
      "role": "primary",
      "required_by": [],
      "pain_point_ids": ["PP1"],
      "supporting_review_ids": ["R04-003", "R04-011"],
      "support_count": 2,
      "confidence": "high"
    },
    {
      "product_id": "dish-professional-reservation",
      "name": "DISH Professional Reservation",
      "role": "prerequisite",
      "required_by": ["dish-ai-phone-assistant"],
      "pain_point_ids": ["PP1"],
      "supporting_review_ids": ["R04-003", "R04-011"],
      "support_count": 2,
      "confidence": "high"
    }
  ],
  "candidates_not_selected": [],
  "opening_pitch": "Several guests mention that it can be hard to get through by phone at busy times…",
  "discovery_questions": [
    {"question": "How do you handle calls during the dinner rush?", "pain_point_id": "PP1", "category_id": null, "based_on_reviews": true}
  ]
}
```

### Variants

| Card | `decision` | `decision_reasons` | `reviews_analysed` / `description` | `pain_points` | `recommendations` / `candidates_not_selected` | `opening_pitch` | `discovery_questions` |
|---|---|---|---|---|---|---|---|
| Closed / chain (short) | `no_recommendation` | `["closed"]`, `["chain"]` or `["closed","chain"]` | `null` / `null` | `[]` | `[]` / `[]` | `null` | `[]` |
| Eligible, pain points, no mapped product | `insufficient_evidence` | `["insufficient_evidence"]` | int / str | non-empty | `[]` / `[]` | str | linked to pain points |
| Eligible, no pain points | `insufficient_evidence` | `["insufficient_evidence"]` | int / str | `[]` | `[]` / `[]` | `null` | general: `pain_point_id` null, `category_id` set, `based_on_reviews` false |
| Eligible, ≥ 1 mapped product | `recommend` | `[]` | int / str | non-empty | ≥ 1 primary / only when 2 primaries | str | linked to pain points |

All keys are always present (check 1). Order of `recommendations`: primaries in rank order, then prerequisites in order of `product_id`.

## Plain-text form

Fixed section order and fixed wording; rendering the same card twice gives identical text (TC-T08). Layout:

```text
VISIT CARD — <name> (<restaurant_id>)
Prepared for the sales rep. Hypotheses from public reviews; not a final decision.

1. RESTAURANT SUMMARY
   City: <city> | Status: <status> | Segment: <segment>
   Reviews analysed: <n>            ← "Reviews not analysed" on short cards
   <description>                    ← omitted on short cards

2. RECOMMENDATION DECISION
   Decision: recommend | no_recommendation | insufficient_evidence
   Reason: Not in the recommendation target list because the restaurant is closed.
           Not in the recommendation target list because the restaurant is a chain.
           Insufficient evidence: no pain point on this card maps to a catalog product.

3. PAIN POINTS                      ← "Not applicable" on short cards; "No pain points found in the reviews" if empty
   [PP1] <category_id> — confidence: high
         <description>
         - <review_id> (<text_source>): "<quote>"

4. RECOMMENDED PRODUCTS             ← "No products recommended" when empty
   Primary 1: <product_id> — <name>
         Confidence: high | Support: 2 reviews (R04-003, R04-011) | Addresses: PP1
   Prerequisite: <product_id> — <name>
         Required by: <product_id> | Confidence: … | Support: … | Addresses: …
   Candidates not selected:
   - <product_id> — confidence: medium | support: 1 | addresses: PP2

5. OPENING PITCH                    ← "Not applicable" on short cards and when there are no pain points
   <opening_pitch>

6. DISCOVERY QUESTIONS              ← "Not applicable" on short cards
   - [PP1] <question>
   - [Not based on reviews | <category_id>] <question>
```

The plain text contains no reviewer identity data and no review dates (FR-005, FR-019).
