"""Section K: pipeline with a stubbed model (TC-I01–TC-I07, TC-I09), plus TC-C08, TC-C09
(pipeline level), TC-E08, TC-D13 and TC-D14."""

import pytest

from pitch_agent.agent import generate_card
from pitch_agent.analysis import GenerationError
from pitch_agent.checks import run_checks
from pitch_agent.loaders import load_agent_data
from pitch_agent.render import render_text

CASH_1 = ("F01-001", "only accept cash payments")
CASH_2 = ("F01-002", "Cash only, so we had to find an ATM.")
WAIT = ("F01-003", "waited two hours for our food")
SOUP = ("F01-004", "soup was cold and bland")
STAFF = ("F01-005", "Lovely staff and great coffee.")


@pytest.fixture
def data(fixture_data_dir):
    return load_agent_data(fixture_data_dir)


def failed_checks(card, data):
    return {r.check_id: r.reasons for r in run_checks(card, data) if not r.passed}


def run(data, mock_llm, output, restaurant_id="F01"):
    llm = mock_llm({restaurant_id: output})
    return generate_card(restaurant_id, data, llm).to_dict(), llm


def test_tc_i01_full_card(data, mock_llm, model_output):
    output = model_output([("p1", "c_cash", [CASH_1, CASH_2]), ("p2", "c_kitchen", [WAIT])],
                          restaurant_description="Bistro with cash-only payment.")
    card, llm = run(data, mock_llm, output)
    assert card["decision"] == "recommend"
    assert card["decision_reasons"] == []
    primaries = [(r["product_id"], r["confidence"], r["support_count"]) for r in card["recommendations"]]
    assert primaries == [("dish-pay", "high", 2), ("dish-pos", "medium", 1)]
    assert [r["role"] for r in card["recommendations"]] == ["primary", "primary"]
    assert card["restaurant"]["reviews_analysed"] == 6
    assert card["restaurant"]["description"] == "Bistro with cash-only payment."
    assert card["opening_pitch"] == output["opening_pitch"]
    assert [e["text_source"] for e in card["pain_points"][0]["evidence"]] == ["original", "translated"]
    assert len(llm.calls) == 1
    assert failed_checks(card, data) == {}


def test_tc_i02_prerequisite_added(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_phone", [WAIT])]))
    roles = [(r["product_id"], r["role"], r["required_by"]) for r in card["recommendations"]]
    assert roles == [
        ("dish-ai-phone-assistant", "primary", []),
        ("dish-professional-reservation", "prerequisite", ["dish-ai-phone-assistant"]),
    ]
    assert failed_checks(card, data) == {}


def test_tc_i03_non_verbatim_quote_kept_and_reported(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_kitchen", [("F01-003", "they never answered")])]))
    assert card["pain_points"][0]["evidence"][0]["quote"] == "they never answered"
    assert set(failed_checks(card, data)) == {3}


def test_tc_i04_unknown_category_reported(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_unknown", [SOUP])]))
    assert card["pain_points"][0]["category_id"] == "c_unknown"
    assert 16 in failed_checks(card, data)


def test_tc_i09_review_of_another_restaurant_reported(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_cash", [("F06-001", "only accept cash payments")])]))
    evidence = card["pain_points"][0]["evidence"][0]
    assert evidence["review_id"] == "F06-001"
    assert evidence["text_source"] is None
    assert 4 in failed_checks(card, data)


def test_tc_i05_unparseable_output(data, mock_llm):
    with pytest.raises(GenerationError, match="not valid JSON"):
        generate_card("F01", data, mock_llm({"F01": {"raw": "Sure! Here is the card:"}}))


def test_tc_i06_failed_call(data, mock_llm):
    with pytest.raises(GenerationError, match="connection refused"):
        generate_card("F01", data, mock_llm({"F01": {"error": "connection refused"}}))


@pytest.mark.parametrize("restaurant_id", ["F02", "F03", "F04"])
def test_tc_i07_model_not_called_for_closed_or_chain(data, mock_llm, model_output, restaurant_id):
    llm = mock_llm({restaurant_id: model_output([("p1", "c_kitchen", [WAIT])])})
    card = generate_card(restaurant_id, data, llm)
    assert card.decision == "no_recommendation"
    assert llm.calls == []


def test_tc_c08_same_category_merged(data, mock_llm, model_output):
    output = model_output([("p1", "c_cash", [CASH_1]), ("p2", "c_cash", [CASH_2])])
    card, _ = run(data, mock_llm, output)
    assert len(card["pain_points"]) == 1
    pp = card["pain_points"][0]
    assert (pp["pain_point_id"], pp["confidence"]) == ("PP1", "high")
    assert [e["review_id"] for e in pp["evidence"]] == ["F01-001", "F01-002"]
    assert [q["pain_point_id"] for q in card["discovery_questions"]] == ["PP1", "PP1"]
    assert failed_checks(card, data) == {}


def test_tc_c09_unmapped_category_kept_separate(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_none", [SOUP]), ("p2", "c_none", [STAFF])]))
    assert [(p["pain_point_id"], p["category_id"]) for p in card["pain_points"]] == [
        ("PP1", "c_none"), ("PP2", "c_none")]
    assert 18 not in failed_checks(card, data)


def test_tc_e08_unknown_status_treated_as_open(data, mock_llm, model_output):
    assert data.get_restaurant("F01").status == "unknown"
    card, llm = run(data, mock_llm, model_output([("p1", "c_cash", [CASH_1])]))
    assert [c.request_id for c in llm.calls] == ["F01"]
    assert card["decision"] == "recommend"


def test_tc_d13_no_raw_or_eval_folder_needed(tmp_data_dir, mock_llm, model_output):
    assert not (tmp_data_dir / "raw").exists() and not (tmp_data_dir / "eval").exists()
    data = load_agent_data(tmp_data_dir)
    card, _ = run(data, mock_llm, model_output([("p1", "c_cash", [CASH_1])]))
    assert card["decision"] == "recommend"


FORBIDDEN = ("reviewer", "author", "profile", "user_id", "photo", "review_date", "rating", "platform",
             "source_url", "tripadvisor", "google", "example.com", "2026-")


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_tc_d14_no_reviewer_fields(data, mock_llm, model_output):
    card, _ = run(data, mock_llm, model_output([("p1", "c_cash", [CASH_1, CASH_2]), ("p2", "c_kitchen", [WAIT])]))
    text = render_text(card).lower()
    for key in _keys(card):
        assert not any(f in key.lower() for f in FORBIDDEN), key
    for forbidden in FORBIDDEN:
        assert forbidden not in text, forbidden


def test_question_refs_translated_and_unmatched_kept(data, mock_llm, model_output):
    """Design test (T046): model refs → PPn; an unmatched ref is kept and fails check 12."""
    output = model_output(
        [("p1", "c_cash", [CASH_1]), ("p2", "c_kitchen", [WAIT])],
        discovery_questions=[
            {"pain_point_ref": "p2", "question": "How long do orders take?"},
            {"pain_point_ref": "p1", "question": "How do guests pay?"},
            {"pain_point_ref": "p9", "question": "Anything else?"},
        ],
    )
    card, _ = run(data, mock_llm, output)
    assert card["discovery_questions"] == [
        {"question": "How long do orders take?", "pain_point_id": "PP2", "category_id": None, "based_on_reviews": True},
        {"question": "How do guests pay?", "pain_point_id": "PP1", "category_id": None, "based_on_reviews": True},
        {"question": "Anything else?", "pain_point_id": "p9", "category_id": None, "based_on_reviews": True},
    ]
    assert set(failed_checks(card, data)) == {12}


def test_pain_point_without_evidence_kept(data, mock_llm, model_output):
    """TC-C05 at pipeline level: kept with null confidence, fails check 1, no product."""
    card, _ = run(data, mock_llm, model_output([("p1", "c_cash", [])]))
    assert card["pain_points"][0]["confidence"] is None
    assert card["recommendations"] == []
    assert card["decision"] == "insufficient_evidence"
    assert 1 in failed_checks(card, data)
