"""Section B: eligibility and short cards (TC-E01–TC-E07), plus TC-D02 at agent level."""

import pytest

from pitch_agent.agent import build_short_card, generate_card
from pitch_agent.loaders import UnknownRestaurantError, load_agent_data


class FailIfCalledLLM:
    """Inline stub: any model call fails the test (TC-E06)."""

    provider = model = "fail-if-called"

    def generate(self, request):
        pytest.fail("the model must not be called for a closed or chain restaurant")


@pytest.fixture
def data(fixture_data_dir):
    return load_agent_data(fixture_data_dir)


def card_for(restaurant_id, data):
    return generate_card(restaurant_id, data, FailIfCalledLLM()).to_dict()


def test_tc_d02_unknown_restaurant_gives_no_card(data):
    with pytest.raises(UnknownRestaurantError, match="F99"):
        generate_card("F99", data, FailIfCalledLLM())


def test_tc_e01_closed_restaurant(data):
    card = card_for("F02", data)
    assert card["decision"] == "no_recommendation"
    assert card["decision_reasons"] == ["closed"]


def test_tc_e02_chain_restaurant(data):
    card = card_for("F03", data)
    assert card["decision"] == "no_recommendation"
    assert card["decision_reasons"] == ["chain"]


def test_tc_e03_closed_and_chain_restaurant(data):
    card = card_for("F04", data)
    assert card["decision"] == "no_recommendation"
    assert card["decision_reasons"] == ["closed", "chain"]


def test_tc_e04_short_card_sections_not_applicable(data):
    card = card_for("F02", data)
    assert card["pain_points"] == []
    assert card["opening_pitch"] is None
    assert card["discovery_questions"] == []
    assert card["recommendations"] == []
    assert card["candidates_not_selected"] == []
    assert card["schema_version"] == "1"


def test_tc_e05_short_card_summary(data):
    card = card_for("F02", data)
    assert card["restaurant"] == {
        "restaurant_id": "F02",
        "name": "Fixture Closed",
        "city": "Testcity",
        "status": "closed",
        "segment": "independent",
        "reviews_analysed": None,
        "description": None,
    }


@pytest.mark.parametrize("restaurant_id", ["F02", "F03", "F04"])
def test_tc_e06_model_never_called(data, restaurant_id):
    card = card_for(restaurant_id, data)
    assert card["decision"] == "no_recommendation"


def test_tc_e07_closed_takes_precedence_over_strong_pain_point(data):
    # F02-001 ("We waited two hours for our food.") would be a strong pain point.
    assert [r.review_id for r in data.reviews_for("F02")] == ["F02-001"]
    card = card_for("F02", data)
    assert card["decision"] == "no_recommendation"
    assert card["recommendations"] == []


def test_build_short_card_matches_generate_card(data):
    restaurant = data.get_restaurant("F04")
    assert build_short_card(restaurant) == generate_card("F04", data, FailIfCalledLLM())
