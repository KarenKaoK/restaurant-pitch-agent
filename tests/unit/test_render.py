"""Section J: plain-text output (TC-T01–TC-T09)."""

import re

import pytest

from pitch_agent.render import render_text

DISCLAIMER = "Prepared for the sales rep. Hypotheses from public reviews; not a final decision."
SECTIONS = [
    "1. RESTAURANT SUMMARY",
    "2. RECOMMENDATION DECISION",
    "3. PAIN POINTS",
    "4. RECOMMENDED PRODUCTS",
    "5. OPENING PITCH",
    "6. DISCOVERY QUESTIONS",
]


def _restaurant(**overrides):
    base = {
        "restaurant_id": "F01",
        "name": "Fixture Bistro",
        "city": "Testcity",
        "status": "unknown",
        "segment": "independent",
        "reviews_analysed": 6,
        "description": "Small bistro; guests mention cash payments and the phone.",
    }
    return {**base, **overrides}


def recommend_card():
    """F01 recommend card with a prerequisite and a candidate not selected."""
    return {
        "schema_version": "1",
        "restaurant": _restaurant(),
        "decision": "recommend",
        "decision_reasons": [],
        "pain_points": [
            {
                "pain_point_id": "PP1",
                "category_id": "c_phone",
                "description": "Guests could not reach the restaurant by phone.",
                "confidence": "high",
                "evidence": [
                    {"review_id": "F01-001", "quote": "only accept cash", "text_source": "original"},
                    {"review_id": "F01-002", "quote": "had to find", "text_source": "translated"},
                ],
            },
            {
                "pain_point_id": "PP2",
                "category_id": "c_cash",
                "description": "Cash only.",
                "confidence": "medium",
                "evidence": [
                    {"review_id": "F01-004", "quote": "soup was cold", "text_source": "expanded"},
                ],
            },
            {
                "pain_point_id": "PP3",
                "category_id": "c_kitchen",
                "description": "Long wait for food.",
                "confidence": "medium",
                "evidence": [
                    {"review_id": "F01-003", "quote": "waited two hours", "text_source": "original"},
                ],
            },
        ],
        "recommendations": [
            {
                "product_id": "dish-ai-phone-assistant",
                "name": "AI Phone Assistant",
                "role": "primary",
                "required_by": [],
                "pain_point_ids": ["PP1"],
                "supporting_review_ids": ["F01-001", "F01-002"],
                "support_count": 2,
                "confidence": "high",
            },
            {
                "product_id": "dish-pay",
                "name": "DISH Pay",
                "role": "primary",
                "required_by": [],
                "pain_point_ids": ["PP2"],
                "supporting_review_ids": ["F01-004"],
                "support_count": 1,
                "confidence": "medium",
            },
            {
                "product_id": "dish-professional-reservation",
                "name": "DISH Professional Reservation",
                "role": "prerequisite",
                "required_by": ["dish-ai-phone-assistant"],
                "pain_point_ids": ["PP1"],
                "supporting_review_ids": ["F01-001", "F01-002"],
                "support_count": 2,
                "confidence": "high",
            },
        ],
        "candidates_not_selected": [
            {"product_id": "dish-pos", "confidence": "medium", "support_count": 1, "pain_point_ids": ["PP3"]},
        ],
        "opening_pitch": "Several guests mention that it can be hard to get through by phone.",
        "discovery_questions": [
            {"question": "How do you handle calls at peak times?", "pain_point_id": "PP1",
             "category_id": None, "based_on_reviews": True},
            {"question": "Which payment methods do you offer?", "pain_point_id": "PP2",
             "category_id": None, "based_on_reviews": True},
            {"question": "How long does a busy evening order take?", "pain_point_id": "PP3",
             "category_id": None, "based_on_reviews": True},
        ],
    }


def insufficient_card():
    """Eligible card with a pain point that maps to no product."""
    card = recommend_card()
    card.update(
        decision="insufficient_evidence",
        decision_reasons=["insufficient_evidence"],
        pain_points=[
            {"pain_point_id": "PP1", "category_id": "c_none", "description": "Cold soup.",
             "confidence": "medium",
             "evidence": [{"review_id": "F01-004", "quote": "soup was cold", "text_source": "expanded"}]},
        ],
        recommendations=[],
        candidates_not_selected=[],
        opening_pitch="A guest mentions a cold soup.",
        discovery_questions=[
            {"question": "How do you keep dishes warm?", "pain_point_id": "PP1",
             "category_id": None, "based_on_reviews": True},
        ],
    )
    return card


def general_questions_card():
    """Eligible card with no pain points (FR-017a)."""
    card = insufficient_card()
    card.update(
        pain_points=[],
        opening_pitch=None,
        discovery_questions=[
            {"question": "Which payment methods do you offer?", "pain_point_id": None,
             "category_id": "c_cash", "based_on_reviews": False},
            {"question": "How do guests book a table?", "pain_point_id": None,
             "category_id": "c_booking", "based_on_reviews": False},
        ],
    )
    return card


def short_card():
    """F02 closed short card."""
    return {
        "schema_version": "1",
        "restaurant": _restaurant(restaurant_id="F02", name="Fixture Closed", status="closed",
                                  reviews_analysed=None, description=None),
        "decision": "no_recommendation",
        "decision_reasons": ["closed"],
        "pain_points": [],
        "recommendations": [],
        "candidates_not_selected": [],
        "opening_pitch": None,
        "discovery_questions": [],
    }


def section(text, number):
    """Body of section ``number`` (1-6), without its heading."""
    start = text.index(SECTIONS[number - 1]) + len(SECTIONS[number - 1])
    end = text.index(SECTIONS[number]) if number < 6 else len(text)
    return text[start:end]


def test_tc_t01_six_sections_in_fixed_order():
    text = render_text(recommend_card())
    assert text.startswith("VISIT CARD — Fixture Bistro (F01)\n")
    positions = [text.index(s) for s in SECTIONS]
    assert positions == sorted(positions)
    summary = section(text, 1)
    assert "City: Testcity | Status: unknown | Segment: independent" in summary
    assert "Reviews analysed: 6" in summary
    assert "Small bistro; guests mention cash payments and the phone." in summary
    assert "Decision: recommend" in section(text, 2)
    assert "Several guests mention that it can be hard to get through by phone." in section(text, 5)


def test_tc_t02_every_evidence_item_shows_id_quote_and_source():
    text = render_text(recommend_card())
    pains = section(text, 3)
    assert "[PP1] c_phone — confidence: high" in pains
    assert "Guests could not reach the restaurant by phone." in pains
    for line in [
        '- F01-001 (original): "only accept cash"',
        '- F01-002 (translated): "had to find"',
        '- F01-004 (expanded): "soup was cold"',
        '- F01-003 (original): "waited two hours"',
    ]:
        assert line in pains


def test_tc_t03_candidates_and_primary_support_shown():
    products = section(render_text(recommend_card()), 4)
    assert "Primary 1: dish-ai-phone-assistant — AI Phone Assistant" in products
    assert "Confidence: high | Support: 2 reviews (F01-001, F01-002) | Addresses: PP1" in products
    assert "Primary 2: dish-pay — DISH Pay" in products
    assert "Confidence: medium | Support: 1 review (F01-004) | Addresses: PP2" in products
    assert "Candidates not selected:" in products
    assert "- dish-pos — confidence: medium | support: 1 | addresses: PP3" in products


def test_tc_t04_insufficient_evidence_card():
    text = render_text(insufficient_card())
    assert "No products recommended" in section(text, 4)
    decision = section(text, 2)
    assert "Decision: insufficient_evidence" in decision
    assert "Insufficient evidence: no pain point on this card maps to a catalog product." in decision


def test_tc_t05_short_card():
    text = render_text(short_card())
    for number in (3, 5, 6):
        assert section(text, number).strip() == "Not applicable", number
    assert "Reviews not analysed" in section(text, 1)
    assert "Reviews analysed:" not in text
    decision = section(text, 2)
    assert "Decision: no_recommendation" in decision
    assert "Not in the recommendation target list because the restaurant is closed." in decision
    assert "No products recommended" in section(text, 4)


def test_tc_t05_closed_and_chain_reasons():
    card = short_card()
    card["restaurant"]["segment"] = "chain"
    card["decision_reasons"] = ["closed", "chain"]
    decision = section(render_text(card), 2)
    assert "Not in the recommendation target list because the restaurant is closed." in decision
    assert "Not in the recommendation target list because the restaurant is a chain." in decision


def test_tc_t06_general_questions_labelled():
    text = render_text(general_questions_card())
    questions = section(text, 6)
    assert "- [Not based on reviews | c_cash] Which payment methods do you offer?" in questions
    assert "- [Not based on reviews | c_booking] How do guests book a table?" in questions
    assert section(text, 5).strip() == "Not applicable"
    assert section(text, 3).strip() == "No pain points found in the reviews"


def test_tc_t06_review_based_questions_linked():
    questions = section(render_text(recommend_card()), 6)
    assert "- [PP1] How do you handle calls at peak times?" in questions
    assert "Not based on reviews" not in questions


def test_tc_t07_prerequisite_marked_and_names_requiring_product():
    products = section(render_text(recommend_card()), 4)
    assert "Prerequisite: dish-professional-reservation — DISH Professional Reservation" in products
    assert (
        "Required by: dish-ai-phone-assistant | Confidence: high | "
        "Support: 2 reviews (F01-001, F01-002) | Addresses: PP1"
    ) in products


def test_tc_t08_rendering_is_deterministic():
    assert render_text(recommend_card()) == render_text(recommend_card())


@pytest.mark.parametrize("build", [recommend_card, insufficient_card, short_card, general_questions_card])
def test_tc_t09_disclaimer_on_every_card(build):
    lines = render_text(build()).splitlines()
    assert lines[1] == DISCLAIMER


def test_no_review_dates_in_text():
    text = render_text(recommend_card())
    assert not re.search(r"\d{4}-\d{2}-\d{2}", text)


def test_empty_questions_section_says_so():
    """Design test (no case ID): FR-006, a section with no content says so."""
    card = insufficient_card()
    card["discovery_questions"] = []
    assert section(render_text(card), 6).strip() == "No discovery questions"
