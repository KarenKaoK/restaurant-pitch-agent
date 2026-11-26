"""Plain-text visit card (contracts/visit-card.md "Plain-text form").

Fixed section order and wording; no reviewer data and no review dates.
"""

from __future__ import annotations

DISCLAIMER = "Prepared for the sales rep. Hypotheses from public reviews; not a final decision."
NOT_APPLICABLE = "Not applicable"
REASON_TEXT = {
    "closed": "Not in the recommendation target list because the restaurant is closed.",
    "chain": "Not in the recommendation target list because the restaurant is a chain.",
    "insufficient_evidence": "Insufficient evidence: no pain point on this card maps to a catalog product.",
}
INDENT = "   "
DETAIL = "         "


def _support(count: int, review_ids: list[str]) -> str:
    noun = "review" if count == 1 else "reviews"
    return f"Support: {count} {noun} ({', '.join(review_ids)})"


def _summary(card: dict) -> list[str]:
    r = card["restaurant"]
    lines = [f"{INDENT}City: {r['city']} | Status: {r['status']} | Segment: {r['segment']}"]
    if r["reviews_analysed"] is None:
        lines.append(f"{INDENT}Reviews not analysed")
    else:
        lines.append(f"{INDENT}Reviews analysed: {r['reviews_analysed']}")
    if r["description"] is not None:
        lines.append(f"{INDENT}{r['description']}")
    return lines


def _decision(card: dict) -> list[str]:
    lines = [f"{INDENT}Decision: {card['decision']}"]
    for i, code in enumerate(card["decision_reasons"]):
        label = "Reason: " if i == 0 else " " * len("Reason: ")
        lines.append(f"{INDENT}{label}{REASON_TEXT[code]}")
    return lines


def _pain_points(card: dict, short: bool) -> list[str]:
    if short:
        return [f"{INDENT}{NOT_APPLICABLE}"]
    if not card["pain_points"]:
        return [f"{INDENT}No pain points found in the reviews"]
    lines = []
    for pp in card["pain_points"]:
        lines.append(f"{INDENT}[{pp['pain_point_id']}] {pp['category_id']} — confidence: {pp['confidence']}")
        lines.append(f"{DETAIL}{pp['description']}")
        for e in pp["evidence"]:
            lines.append(f'{DETAIL}- {e["review_id"]} ({e["text_source"]}): "{e["quote"]}"')
    return lines


def _products(card: dict) -> list[str]:
    recommendations = card["recommendations"]
    if not recommendations:
        return [f"{INDENT}No products recommended"]
    lines = []
    primaries = [r for r in recommendations if r["role"] == "primary"]
    for i, r in enumerate(primaries, start=1):
        lines.append(f"{INDENT}Primary {i}: {r['product_id']} — {r['name']}")
        lines.append(
            f"{DETAIL}Confidence: {r['confidence']} | {_support(r['support_count'], r['supporting_review_ids'])}"
            f" | Addresses: {', '.join(r['pain_point_ids'])}"
        )
    for r in recommendations:
        if r["role"] != "prerequisite":
            continue
        lines.append(f"{INDENT}Prerequisite: {r['product_id']} — {r['name']}")
        lines.append(
            f"{DETAIL}Required by: {', '.join(r['required_by'])} | Confidence: {r['confidence']}"
            f" | {_support(r['support_count'], r['supporting_review_ids'])}"
            f" | Addresses: {', '.join(r['pain_point_ids'])}"
        )
    if card["candidates_not_selected"]:
        lines.append(f"{INDENT}Candidates not selected:")
        for c in card["candidates_not_selected"]:
            lines.append(
                f"{INDENT}- {c['product_id']} — confidence: {c['confidence']} | support: {c['support_count']}"
                f" | addresses: {', '.join(c['pain_point_ids'])}"
            )
    return lines


def _pitch(card: dict) -> list[str]:
    pitch = card["opening_pitch"]
    return [f"{INDENT}{NOT_APPLICABLE if pitch is None else pitch}"]


def _questions(card: dict, short: bool) -> list[str]:
    if short:
        return [f"{INDENT}{NOT_APPLICABLE}"]
    if not card["discovery_questions"]:
        return [f"{INDENT}No discovery questions"]
    lines = []
    for q in card["discovery_questions"]:
        label = q["pain_point_id"] if q["based_on_reviews"] else f"Not based on reviews | {q['category_id']}"
        lines.append(f"{INDENT}- [{label}] {q['question']}")
    return lines


def render_text(card: dict) -> str:
    """Render a card dict (contracts/visit-card.md JSON form) as plain text."""
    short = card["decision"] == "no_recommendation"
    r = card["restaurant"]
    sections = [
        ("1. RESTAURANT SUMMARY", _summary(card)),
        ("2. RECOMMENDATION DECISION", _decision(card)),
        ("3. PAIN POINTS", _pain_points(card, short)),
        ("4. RECOMMENDED PRODUCTS", _products(card)),
        ("5. OPENING PITCH", _pitch(card)),
        ("6. DISCOVERY QUESTIONS", _questions(card, short)),
    ]
    lines = [f"VISIT CARD — {r['name']} ({r['restaurant_id']})", DISCLAIMER]
    for heading, body in sections:
        lines += ["", heading, *body]
    return "\n".join(lines) + "\n"
