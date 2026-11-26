"""Quote check and deterministic card checks (FR-025).

Checks read the card's JSON form (contracts/visit-card.md) and the agent data.
"""

from __future__ import annotations

from pitch_agent.models import CheckResult

MIN_QUOTE_WORDS = 3
NOT_EVALUATED = "not evaluated: invalid structure"

DECISIONS = ("recommend", "no_recommendation", "insufficient_evidence")
CONFIDENCES = ("high", "medium")
ROLES = ("primary", "prerequisite")

CARD_KEYS = (
    "schema_version", "restaurant", "decision", "decision_reasons", "pain_points",
    "recommendations", "candidates_not_selected", "opening_pitch", "discovery_questions",
)
RESTAURANT_KEYS = ("restaurant_id", "name", "city", "status", "segment", "reviews_analysed", "description")
PAIN_POINT_KEYS = ("pain_point_id", "category_id", "description", "confidence", "evidence")
EVIDENCE_KEYS = ("review_id", "quote", "text_source")
RECOMMENDATION_KEYS = (
    "product_id", "name", "role", "required_by", "pain_point_ids",
    "supporting_review_ids", "support_count", "confidence",
)
CANDIDATE_KEYS = ("product_id", "confidence", "support_count", "pain_point_ids")
QUESTION_KEYS = ("question", "pain_point_id", "category_id", "based_on_reviews")
LIST_KEYS = ("decision_reasons", "pain_points", "recommendations", "candidates_not_selected", "discovery_questions")


def _collapse(text: str) -> str:
    """Trim and collapse all whitespace (including line breaks) to single spaces."""
    return " ".join(text.split())


def quote_is_verbatim(quote: str, review_text: str) -> tuple[bool, str]:
    """Check 3: the quote is an exact, case- and punctuation-sensitive substring of the
    review text after whitespace normalisation, and has at least 3 words.

    Returns ``(passed, reason)``; ``reason`` is empty when passed.
    """
    normalised = _collapse(quote)
    if not normalised:
        return False, "quote is empty"
    if len(normalised.split(" ")) < MIN_QUOTE_WORDS:
        return False, f"quote has fewer than {MIN_QUOTE_WORDS} words"
    if normalised not in _collapse(review_text):
        return False, "quote is not a verbatim excerpt of the review text"
    return True, ""


# ---------------------------------------------------------------------------
# Check 1: structure
# ---------------------------------------------------------------------------


def _missing(obj, keys, where: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{where} is not an object"]
    return [f"{where}: missing field '{k}'" for k in keys if k not in obj]


def _items(items_in: list, keys: tuple[str, ...], label: str) -> tuple[list[str], list[dict]]:
    """Reasons for malformed items, and the well-formed items."""
    reasons, items = [], []
    for i, item in enumerate(items_in):
        problems = _missing(item, keys, f"{label} #{i + 1}")
        reasons += problems
        if not problems:
            items.append(item)
    return reasons, items


def check_structure(card: dict, data) -> list[str]:
    """Check 1: all sections and fields present, valid decision, confidence and role
    values, every pain point with at least one evidence item."""
    reasons = _missing(card, CARD_KEYS, "card")
    if not isinstance(card, dict):
        return reasons
    if "restaurant" in card:
        reasons += _missing(card["restaurant"], RESTAURANT_KEYS, "restaurant")
    lists = {}
    for key in LIST_KEYS:
        value = card.get(key, [])
        if not isinstance(value, list):
            reasons.append(f"'{key}' is not a list")
            value = []
        lists[key] = value
    if "decision" in card and card["decision"] not in DECISIONS:
        reasons.append(f"invalid decision '{card['decision']}'")

    problems, pain_points = _items(lists["pain_points"], PAIN_POINT_KEYS, "pain point")
    reasons += problems
    for pp in pain_points:
        pid = pp["pain_point_id"]
        if pp["confidence"] not in CONFIDENCES:
            reasons.append(f"pain point {pid}: invalid confidence {pp['confidence']!r}")
        if not isinstance(pp["evidence"], list) or not pp["evidence"]:
            reasons.append(f"pain point {pid}: no evidence")
            continue
        for j, e in enumerate(pp["evidence"]):
            reasons += _missing(e, EVIDENCE_KEYS, f"pain point {pid} evidence #{j + 1}")

    problems, recommendations = _items(lists["recommendations"], RECOMMENDATION_KEYS, "recommendation")
    reasons += problems
    for r in recommendations:
        if r["role"] not in ROLES:
            reasons.append(f"recommendation {r['product_id']}: invalid role {r['role']!r}")
        if r["confidence"] not in CONFIDENCES:
            reasons.append(f"recommendation {r['product_id']}: invalid confidence {r['confidence']!r}")

    problems, candidates = _items(lists["candidates_not_selected"], CANDIDATE_KEYS, "candidate")
    reasons += problems
    for c in candidates:
        if c["confidence"] not in CONFIDENCES:
            reasons.append(f"candidate {c['product_id']}: invalid confidence {c['confidence']!r}")

    problems, _ = _items(lists["discovery_questions"], QUESTION_KEYS, "discovery question")
    return reasons + problems


# ---------------------------------------------------------------------------
# Checks 2–5: evidence against the review dataset
# ---------------------------------------------------------------------------


def _evidence(card: dict):
    for pp in card["pain_points"]:
        for e in pp["evidence"]:
            yield pp["pain_point_id"], e


def _reviews_by_id(data) -> dict:
    return {r.review_id: r for r in data.reviews}


def check_review_ids_exist(card: dict, data) -> list[str]:
    """Check 2: every cited review ID exists in the review dataset."""
    reviews = _reviews_by_id(data)
    return [f"{pid}: review {e['review_id']} does not exist" for pid, e in _evidence(card)
            if e["review_id"] not in reviews]


def check_quotes_verbatim(card: dict, data) -> list[str]:
    """Check 3: every quote is a verbatim excerpt of the cited review (section H)."""
    reviews = _reviews_by_id(data)
    reasons = []
    for pid, e in _evidence(card):
        review = reviews.get(e["review_id"])
        if review is None:
            continue  # reported by check 2
        ok, reason = quote_is_verbatim(e["quote"], review.text)
        if not ok:
            reasons.append(f"{pid}: {e['review_id']}: {reason}")
    return reasons


def check_reviews_belong_to_restaurant(card: dict, data) -> list[str]:
    """Check 4: every cited review belongs to the card's restaurant."""
    reviews = _reviews_by_id(data)
    restaurant_id = card["restaurant"]["restaurant_id"]
    reasons = []
    for pid, e in _evidence(card):
        review = reviews.get(e["review_id"])
        if review is not None and review.restaurant_id != restaurant_id:
            reasons.append(f"{pid}: review {e['review_id']} belongs to {review.restaurant_id}, not {restaurant_id}")
    return reasons


def check_text_sources(card: dict, data) -> list[str]:
    """Check 5: every cited text_source matches the stored one."""
    reviews = _reviews_by_id(data)
    reasons = []
    for pid, e in _evidence(card):
        review = reviews.get(e["review_id"])
        if review is not None and e["text_source"] != review.text_source:
            reasons.append(
                f"{pid}: review {e['review_id']} text_source is {review.text_source!r}, card shows {e['text_source']!r}"
            )
    return reasons


# ---------------------------------------------------------------------------
# Checks 6–9: catalog and decision
# ---------------------------------------------------------------------------


def check_products_in_catalog(card: dict, data) -> list[str]:
    """Check 6: every recommended product_id exists in the catalog."""
    return [f"product {r['product_id']} is not in the catalog" for r in card["recommendations"]
            if r["product_id"] not in data.catalog]


def check_requirements_met(card: dict, data) -> list[str]:
    """Check 7: every recommended product with ``requires`` comes with the required product."""
    recommended = {r["product_id"] for r in card["recommendations"]}
    reasons = []
    for product_id in sorted(recommended):
        product = data.catalog.get(product_id)
        if product is not None and product.requires and product.requires not in recommended:
            reasons.append(f"product {product_id} requires {product.requires}, which is not recommended")
    return reasons


def check_closed_or_chain(card: dict, data) -> list[str]:
    """Check 8: a closed or chain restaurant gets a short no_recommendation card that
    states each applicable reason."""
    restaurant_id = card["restaurant"]["restaurant_id"]
    restaurant = data.restaurants.get(restaurant_id)
    if restaurant is None:
        return [f"restaurant {restaurant_id} is not in the dataset"]
    if restaurant.eligible:
        return []
    expected = (["closed"] if restaurant.is_closed else []) + (["chain"] if restaurant.is_chain else [])
    reasons = []
    if card["decision"] != "no_recommendation":
        reasons.append(f"decision is {card['decision']!r}, expected 'no_recommendation'")
    if sorted(card["decision_reasons"]) != sorted(expected):
        reasons.append(f"decision reasons are {card['decision_reasons']}, expected {expected}")
    for key in ("recommendations", "candidates_not_selected", "pain_points", "discovery_questions"):
        if card[key]:
            reasons.append(f"'{key}' must be empty on a closed or chain card")
    if card["opening_pitch"] is not None:
        reasons.append("opening pitch must be empty on a closed or chain card")
    return reasons


def check_decision_matches_products(card: dict, data) -> list[str]:
    """Check 9: no products unless the decision is recommend; at least one if it is."""
    decision, count = card["decision"], len(card["recommendations"])
    if decision in ("insufficient_evidence", "no_recommendation") and count:
        return [f"decision {decision!r} with {count} recommended product(s)"]
    if decision == "recommend" and not count:
        return ["decision 'recommend' without a recommended product"]
    return []


# ---------------------------------------------------------------------------
# Checks 10–15: confidence, limits, questions, support, ranking
# ---------------------------------------------------------------------------

_CONFIDENCE_RANK = {"high": 2, "medium": 1}


def _primaries(card: dict) -> list[dict]:
    return [r for r in card["recommendations"] if r["role"] == "primary"]


def _distinct_reviews(pain_points: list[dict]) -> set[str]:
    return {e["review_id"] for pp in pain_points for e in pp["evidence"]}


def check_pain_point_confidence(card: dict, data) -> list[str]:
    """Check 10: >1 distinct cited review → high; exactly 1 → medium (FR-011)."""
    reasons = []
    for pp in card["pain_points"]:
        count = len(_distinct_reviews([pp]))
        expected = "high" if count > 1 else "medium" if count == 1 else None
        if pp["confidence"] != expected:
            reasons.append(
                f"{pp['pain_point_id']}: confidence {pp['confidence']!r} with {count} distinct review(s), "
                f"expected {expected!r}"
            )
    return reasons


def check_primary_limits(card: dict, data) -> list[str]:
    """Check 11: at most 2 primaries; every prerequisite is required by a primary."""
    primaries = _primaries(card)
    reasons = []
    if len(primaries) > 2:
        reasons.append(f"{len(primaries)} primary recommendations, at most 2 allowed")
    required = {data.catalog[p["product_id"]].requires for p in primaries if p["product_id"] in data.catalog}
    for r in card["recommendations"]:
        if r["role"] == "prerequisite" and r["product_id"] not in required:
            reasons.append(f"prerequisite {r['product_id']} is not required by a primary recommendation")
    return reasons


def check_question_links(card: dict, data) -> list[str]:
    """Check 12: every pain point has a question; general questions only on cards
    without pain points, each linked to a listed category."""
    pain_point_ids = [pp["pain_point_id"] for pp in card["pain_points"]]
    questions = card["discovery_questions"]
    linked = {q["pain_point_id"] for q in questions if q["based_on_reviews"]}
    reasons = [f"{pid}: no linked discovery question" for pid in pain_point_ids if pid not in linked]
    for q in questions:
        if q["based_on_reviews"]:
            if q["pain_point_id"] not in pain_point_ids:
                reasons.append(f"question linked to unknown pain point {q['pain_point_id']!r}")
            continue
        if pain_point_ids:
            reasons.append("question not based on reviews on a card with pain points")
        if data.mapping.category(q["category_id"]) is None:
            reasons.append(f"general question linked to unknown category {q['category_id']!r}")
    return reasons


def check_support_counts(card: dict, data) -> list[str]:
    """Check 13: support count = distinct review IDs across the product's pain points
    (primaries and candidates not selected)."""
    by_id = {pp["pain_point_id"]: pp for pp in card["pain_points"]}
    reasons = []
    for item in _primaries(card) + card["candidates_not_selected"]:
        unknown = [pid for pid in item["pain_point_ids"] if pid not in by_id]
        if unknown:
            reasons.append(f"{item['product_id']}: lists unknown pain point(s) {unknown}")
            continue
        expected = len(_distinct_reviews([by_id[pid] for pid in item["pain_point_ids"]]))
        if item["support_count"] != expected:
            reasons.append(f"{item['product_id']}: support count {item['support_count']}, expected {expected}")
    return reasons


def _rank_key(item: dict):
    return (-_CONFIDENCE_RANK[item["confidence"]], -item["support_count"], item["product_id"])


def check_rank_order(card: dict, data) -> list[str]:
    """Check 14: primaries in FR-015a rank order; no candidate ranks above a primary."""
    primaries = _primaries(card)
    reasons = []
    if primaries != sorted(primaries, key=_rank_key):
        reasons.append("primary recommendations are not in rank order")
    if primaries:
        lowest = max(_rank_key(p) for p in primaries)
        for c in card["candidates_not_selected"]:
            if _rank_key(c) < lowest:
                reasons.append(f"candidate {c['product_id']} ranks higher than a selected primary")
    return reasons


def check_candidates_need_two_primaries(card: dict, data) -> list[str]:
    """Check 15: candidates not selected appear only when 2 primaries are selected."""
    count = len(_primaries(card))
    if card["candidates_not_selected"] and count != 2:
        return [f"candidates not selected with {count} primary recommendation(s)"]
    return []


# ---------------------------------------------------------------------------
# Checks 16–18: mapping table
# ---------------------------------------------------------------------------


def check_categories_known(card: dict, data) -> list[str]:
    """Check 16: every pain point's category exists in the category list."""
    return [f"{pp['pain_point_id']}: unknown category {pp['category_id']!r}" for pp in card["pain_points"]
            if data.mapping.category(pp["category_id"]) is None]


def _mapped_products(category_id: str, data) -> tuple[str, ...]:
    category = data.mapping.category(category_id)
    return category.product_ids if category else ()


def check_mapping_coverage(card: dict, data) -> list[str]:
    """Check 17: listed products are mapped from their pain points' categories, and
    every product mapped from a pain point with evidence is primary or not selected
    (unless it is only present as a prerequisite)."""
    by_id = {pp["pain_point_id"]: pp for pp in card["pain_points"]}
    listed = _primaries(card) + card["candidates_not_selected"]
    reasons = []
    for item in listed:
        categories = [by_id[pid]["category_id"] for pid in item["pain_point_ids"] if pid in by_id]
        if not any(item["product_id"] in _mapped_products(c, data) for c in categories):
            reasons.append(f"{item['product_id']} is not mapped from the category of any pain point it lists")
    present = {i["product_id"] for i in listed} | {
        r["product_id"] for r in card["recommendations"] if r["role"] == "prerequisite"
    }
    for pp in card["pain_points"]:
        if not pp["evidence"]:
            continue
        for product_id in _mapped_products(pp["category_id"], data):
            if product_id not in present:
                reasons.append(
                    f"{product_id} is mapped from {pp['pain_point_id']} ({pp['category_id']}) but is not on the card"
                )
    return reasons


def check_category_repetition(card: dict, data) -> list[str]:
    """Check 18: only categories without mapped products may appear more than once."""
    counts: dict[str, int] = {}
    for pp in card["pain_points"]:
        counts[pp["category_id"]] = counts.get(pp["category_id"], 0) + 1
    reasons = []
    for category_id, count in counts.items():
        category = data.mapping.category(category_id)
        if count > 1 and not (category is not None and category.repeatable):
            reasons.append(f"category {category_id!r} appears in {count} pain points")
    return reasons


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


CHECKS = {
    1: check_structure,
    2: check_review_ids_exist,
    3: check_quotes_verbatim,
    4: check_reviews_belong_to_restaurant,
    5: check_text_sources,
    6: check_products_in_catalog,
    7: check_requirements_met,
    8: check_closed_or_chain,
    9: check_decision_matches_products,
    10: check_pain_point_confidence,
    11: check_primary_limits,
    12: check_question_links,
    13: check_support_counts,
    14: check_rank_order,
    15: check_candidates_need_two_primaries,
    16: check_categories_known,
    17: check_mapping_coverage,
    18: check_category_repetition,
}


def run_checks(card: dict, data) -> list[CheckResult]:
    """Run all 18 checks; a failure in one never stops the others (TC-K19). A check
    that cannot read a field reports "not evaluated: invalid structure"."""
    results = []
    for check_id, check in CHECKS.items():
        try:
            reasons = check(card, data)
        except (KeyError, TypeError, AttributeError, IndexError, ValueError):
            reasons = [NOT_EVALUATED]
        results.append(CheckResult(check_id, passed=not reasons, reasons=list(reasons)))
    return results
