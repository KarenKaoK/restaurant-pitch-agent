"""Insufficient-evidence path: TC-DEC02 (pipeline level), TC-DEC03, TC-DEC04, TC-I08."""

import pytest

from pitch_agent.agent import generate_card
from pitch_agent.checks import run_checks
from pitch_agent.loaders import load_agent_data
from pitch_agent.render import render_text

GENERAL = [
    {"category_id": "c_cash", "question": "Which payment methods do you offer?"},
    {"category_id": "c_booking", "question": "How do guests book a table?"},
]


@pytest.fixture
def data(fixture_data_dir):
    return load_agent_data(fixture_data_dir)


def failed_checks(card, data):
    return {r.check_id: r.reasons for r in run_checks(card, data) if not r.passed}


def no_pain_points(model_output):
    return model_output([], opening_pitch="Guests love the coffee.", general_questions=GENERAL)


def test_tc_dec02_only_unmapped_pain_point(data, mock_llm, model_output):
    output = model_output([("p1", "c_none", [("F01-004", "soup was cold and bland")])],
                          opening_pitch="A guest mentions a cold soup.")
    card = generate_card("F01", data, mock_llm({"F01": output})).to_dict()
    assert card["decision"] == "insufficient_evidence"
    assert card["decision_reasons"] == ["insufficient_evidence"]
    assert card["recommendations"] == [] and card["candidates_not_selected"] == []
    assert card["opening_pitch"] == "A guest mentions a cold soup."
    assert [q["pain_point_id"] for q in card["discovery_questions"]] == ["PP1"]
    assert "insufficient evidence" in render_text(card).lower()
    assert failed_checks(card, data) == {}


def _assert_general_card(card):
    assert card["decision"] == "insufficient_evidence"
    assert card["pain_points"] == []
    assert card["opening_pitch"] is None
    assert card["discovery_questions"] == [
        {"question": q["question"], "pain_point_id": None, "category_id": q["category_id"], "based_on_reviews": False}
        for q in GENERAL
    ]
    text = render_text(card)
    assert "5. OPENING PITCH\n   Not applicable\n" in text
    assert "- [Not based on reviews | c_cash] Which payment methods do you offer?" in text


def test_tc_dec03_no_pain_points(data, mock_llm, model_output):
    card = generate_card("F01", data, mock_llm({"F01": no_pain_points(model_output)})).to_dict()
    _assert_general_card(card)
    assert card["restaurant"]["reviews_analysed"] == 6


def test_tc_dec04_restaurant_without_reviews(data, mock_llm, model_output):
    llm = mock_llm({"F05": no_pain_points(model_output)})
    card = generate_card("F05", data, llm).to_dict()
    _assert_general_card(card)
    assert card["restaurant"]["reviews_analysed"] == 0
    assert "Reviews analysed: 0" in render_text(card)
    assert [c.request_id for c in llm.calls] == ["F05"]


@pytest.mark.parametrize("restaurant_id", ["F01", "F05"])
def test_tc_i08_no_pain_points_card_passes_all_checks(data, mock_llm, model_output, restaurant_id):
    card = generate_card(restaurant_id, data, mock_llm({restaurant_id: no_pain_points(model_output)})).to_dict()
    assert failed_checks(card, data) == {}
