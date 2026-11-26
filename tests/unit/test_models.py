"""Design tests (no case ID): card JSON form matches contracts/visit-card.md."""

import json

from pitch_agent.models import (
    Candidate,
    DiscoveryQuestion,
    Evidence,
    PainPoint,
    Recommendation,
    RestaurantSummary,
    VisitCard,
)

CARD_KEYS = [
    "schema_version",
    "restaurant",
    "decision",
    "decision_reasons",
    "pain_points",
    "recommendations",
    "candidates_not_selected",
    "opening_pitch",
    "discovery_questions",
]


def _card():
    return VisitCard(
        schema_version="1",
        restaurant=RestaurantSummary("F01", "Fixture Bistro", "Testcity", "unknown", "independent", 6, "Desc."),
        decision="recommend",
        decision_reasons=[],
        pain_points=[
            PainPoint("PP1", "c_cash", "Cash only.", "high", [
                Evidence("F01-001", "only accept cash", "original"),
                Evidence("F01-002", "Cash only, so", "translated"),
            ])
        ],
        recommendations=[
            Recommendation("dish-pay", "DISH Pay", "primary", [], ["PP1"], ["F01-001", "F01-002"], 2, "high")
        ],
        candidates_not_selected=[Candidate("dish-pos", "medium", 1, ["PP2"])],
        opening_pitch="Guests mention paying in cash.",
        discovery_questions=[DiscoveryQuestion("How do guests pay?", "PP1", None, True)],
    )


def test_card_to_dict_has_contract_keys():
    d = _card().to_dict()
    assert list(d) == CARD_KEYS
    assert list(d["restaurant"]) == [
        "restaurant_id", "name", "city", "status", "segment", "reviews_analysed", "description"
    ]
    assert list(d["pain_points"][0]) == ["pain_point_id", "category_id", "description", "confidence", "evidence"]
    assert list(d["pain_points"][0]["evidence"][0]) == ["review_id", "quote", "text_source"]
    assert list(d["recommendations"][0]) == [
        "product_id", "name", "role", "required_by", "pain_point_ids",
        "supporting_review_ids", "support_count", "confidence",
    ]
    assert list(d["candidates_not_selected"][0]) == ["product_id", "confidence", "support_count", "pain_point_ids"]
    assert list(d["discovery_questions"][0]) == ["question", "pain_point_id", "category_id", "based_on_reviews"]


def test_card_round_trip_through_json():
    card = _card()
    assert VisitCard.from_dict(json.loads(json.dumps(card.to_dict()))) == card
