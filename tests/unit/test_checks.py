"""Section I: deterministic checks 1–18 (TC-K00–TC-K19)."""

import copy
import json
from pathlib import Path

import pytest

from pitch_agent.agent import build_short_card
from pitch_agent.checks import run_checks
from pitch_agent.loaders import load_agent_data

VALID_F01 = Path(__file__).resolve().parents[1] / "fixtures" / "cards" / "valid_f01.json"
NOT_EVALUATED = "not evaluated: invalid structure"


@pytest.fixture
def data(fixture_data_dir):
    return load_agent_data(fixture_data_dir)


@pytest.fixture
def valid():
    return json.loads(VALID_F01.read_text(encoding="utf-8"))


def short(data, restaurant_id):
    return build_short_card(data.get_restaurant(restaurant_id)).to_dict()


def results(card, data):
    out = run_checks(card, data)
    assert [r.check_id for r in out] == list(range(1, 19))
    return {r.check_id: r for r in out}


def failed(card, data):
    return {i for i, r in results(card, data).items() if not r.passed}


def assert_fails(card, data, check_id):
    r = results(card, data)[check_id]
    assert not r.passed, f"check {check_id} should fail"
    assert r.reasons and all(reason.strip() for reason in r.reasons)


def assert_passes(card, data, check_id):
    r = results(card, data)[check_id]
    assert r.passed, f"check {check_id} should pass: {r.reasons}"
    assert r.reasons == []


def rec(card, product_id):
    return next(r for r in card["recommendations"] if r["product_id"] == product_id)


def primary(product_id, name, confidence, pain_point_ids, review_ids):
    return {
        "product_id": product_id, "name": name, "role": "primary", "required_by": [],
        "pain_point_ids": pain_point_ids, "supporting_review_ids": review_ids,
        "support_count": len(review_ids), "confidence": confidence,
    }


def general_card(valid):
    card = copy.deepcopy(valid)
    card.update(
        decision="insufficient_evidence", decision_reasons=["insufficient_evidence"], pain_points=[],
        recommendations=[], candidates_not_selected=[], opening_pitch=None,
        discovery_questions=[{"question": "How do guests pay?", "pain_point_id": None,
                              "category_id": "c_cash", "based_on_reviews": False}],
    )
    return card


# --- TC-K00 -------------------------------------------------------------------


def test_tc_k00_valid_card_passes_all_checks(valid, data):
    assert failed(valid, data) == set()


@pytest.mark.parametrize("restaurant_id", ["F02", "F03", "F04"])
def test_tc_k00_short_cards_pass_all_checks(data, restaurant_id):
    assert failed(short(data, restaurant_id), data) == set()


def test_tc_k00_general_questions_card_passes_all_checks(valid, data):
    assert failed(general_card(valid), data) == set()


# --- check 1: structure ---------------------------------------------------------


def test_tc_k01a_missing_opening_pitch(valid, data):
    del valid["opening_pitch"]
    assert_fails(valid, data, 1)


def test_tc_k01b_invalid_decision(valid, data):
    valid["decision"] = "maybe"
    assert_fails(valid, data, 1)


def test_tc_k01c_invalid_pain_point_confidence(valid, data):
    valid["pain_points"][0]["confidence"] = "low"
    assert_fails(valid, data, 1)


def test_tc_k01_pain_point_without_evidence(valid, data):
    valid["pain_points"][3]["evidence"] = []
    assert_fails(valid, data, 1)
    assert "pain point PP4: no evidence" in results(valid, data)[1].reasons


def test_tc_k01_missing_nested_field(valid, data):
    del valid["recommendations"][0]["support_count"]
    assert_fails(valid, data, 1)


def test_tc_k01_invalid_role(valid, data):
    valid["recommendations"][0]["role"] = "secondary"
    assert_fails(valid, data, 1)


# --- checks 2–5: evidence --------------------------------------------------------


def test_tc_k02_unknown_review_id(valid, data):
    valid["pain_points"][0]["evidence"][0]["review_id"] = "F01-099"
    assert_fails(valid, data, 2)


@pytest.mark.parametrize("quote", ["Only accept cash payments", "accept cash", "only accept card"])
def test_tc_k03_non_verbatim_quote(valid, data, quote):
    valid["pain_points"][0]["evidence"][0]["quote"] = quote
    assert_fails(valid, data, 3)
    assert_passes(valid, data, 2)


def test_tc_k04_review_from_another_restaurant(valid, data):
    valid["pain_points"][0]["evidence"][0]["review_id"] = "F06-001"
    assert_fails(valid, data, 4)
    assert_passes(valid, data, 2)
    assert_passes(valid, data, 3)


def test_tc_k05_text_source_mismatch(valid, data):
    evidence = valid["pain_points"][0]["evidence"][1]
    assert evidence["review_id"] == "F01-002"
    evidence["text_source"] = "original"
    assert_fails(valid, data, 5)


# --- checks 6–9: catalog and decision ---------------------------------------------


def test_tc_k06_product_not_in_catalog(valid, data):
    rec(valid, "dish-pos")["product_id"] = "dish-weblisting"
    assert_fails(valid, data, 6)


def test_tc_k07_required_product_missing(valid, data):
    ai = rec(valid, "dish-pos")
    ai.update(product_id="dish-ai-phone-assistant", name="AI Phone Assistant")
    assert_fails(valid, data, 7)


def test_tc_k08a_closed_card_with_recommendation(valid, data):
    card = short(data, "F02")
    card["recommendations"] = [rec(valid, "dish-pay")]
    assert_fails(card, data, 8)


def test_tc_k08b_closed_chain_card_with_one_reason(data):
    card = short(data, "F04")
    card["decision_reasons"] = ["closed"]
    assert_fails(card, data, 8)


def test_tc_k08c_chain_card_with_pain_point(valid, data):
    card = short(data, "F03")
    card["pain_points"] = [valid["pain_points"][0]]
    assert_fails(card, data, 8)


def test_tc_k08c_chain_card_with_opening_pitch(data):
    card = short(data, "F03")
    card["opening_pitch"] = "Guests mention cash."
    assert_fails(card, data, 8)


def test_tc_k08_chain_card_with_wrong_decision(data):
    card = short(data, "F03")
    card["decision"] = "insufficient_evidence"
    assert_fails(card, data, 8)


def test_tc_k09a_insufficient_evidence_with_product(valid, data):
    valid["decision"] = "insufficient_evidence"
    valid["decision_reasons"] = ["insufficient_evidence"]
    assert_fails(valid, data, 9)


def test_tc_k09b_recommend_without_product(valid, data):
    valid["recommendations"] = []
    assert_fails(valid, data, 9)


# --- checks 10–15: rules --------------------------------------------------------


def test_tc_k10a_two_reviews_marked_medium(valid, data):
    valid["pain_points"][0]["confidence"] = "medium"
    assert_fails(valid, data, 10)


def test_tc_k10b_one_review_marked_high(valid, data):
    valid["pain_points"][1]["confidence"] = "high"
    assert_fails(valid, data, 10)


def test_tc_k11a_three_primaries(valid, data):
    valid["recommendations"].append(primary("dish-starter", "DISH Starter", "medium", ["PP4"], ["F01-004"]))
    assert_fails(valid, data, 11)


def test_tc_k11b_prerequisite_without_requiring_primary(valid, data):
    prereq = primary("dish-professional-reservation", "DISH Professional Reservation", "high", ["PP1"],
                     ["F01-001", "F01-002"])
    prereq.update(role="prerequisite", required_by=["dish-ai-phone-assistant"])
    valid["recommendations"].append(prereq)
    assert_fails(valid, data, 11)


def test_tc_k12a_pain_point_without_question(valid, data):
    valid["discovery_questions"] = [q for q in valid["discovery_questions"] if q["pain_point_id"] != "PP4"]
    assert_fails(valid, data, 12)


def test_tc_k12a_question_linked_to_unknown_pain_point(valid, data):
    valid["discovery_questions"].append(
        {"question": "Anything else?", "pain_point_id": "p9", "category_id": None, "based_on_reviews": True}
    )
    assert_fails(valid, data, 12)


def test_tc_k12b_general_question_on_card_with_pain_points(valid, data):
    valid["discovery_questions"].append(
        {"question": "How do guests book?", "pain_point_id": None, "category_id": "c_booking",
         "based_on_reviews": False}
    )
    assert_fails(valid, data, 12)


def test_tc_k12c_general_question_with_unknown_category(valid, data):
    card = general_card(valid)
    card["discovery_questions"][0]["category_id"] = "c_unknown"
    assert_fails(card, data, 12)


def test_tc_k13_support_count_mismatch(valid, data):
    rec(valid, "dish-pos")["support_count"] = 3
    assert_fails(valid, data, 13)


def test_tc_k13_candidate_support_count_mismatch(valid, data):
    pos = rec(valid, "dish-pos")
    valid["recommendations"].remove(pos)
    valid["recommendations"].append(primary("dish-starter", "DISH Starter", "high", ["PP1"], ["F01-001", "F01-002"]))
    valid["candidates_not_selected"] = [
        {"product_id": "dish-pos", "confidence": "medium", "support_count": 5, "pain_point_ids": ["PP2", "PP3"]}
    ]
    assert_fails(valid, data, 13)


def test_tc_k14a_primaries_in_wrong_order(valid, data):
    valid["recommendations"].reverse()
    assert_fails(valid, data, 14)


def test_tc_k14b_candidate_ranks_higher_than_primary(valid, data):
    # Primaries dish-pos and dish-starter (both high, 2) are in order; dish-pay (high, 2)
    # ranks above dish-starter only by product_id.
    rec(valid, "dish-pos")["confidence"] = "high"
    valid["recommendations"] = [
        rec(valid, "dish-pos"),
        primary("dish-starter", "DISH Starter", "high", ["PP1"], ["F01-001", "F01-002"]),
    ]
    valid["candidates_not_selected"] = [
        {"product_id": "dish-pay", "confidence": "high", "support_count": 2, "pain_point_ids": ["PP1"]}
    ]
    assert_fails(valid, data, 14)


def test_tc_k15_candidate_with_one_primary(valid, data):
    valid["recommendations"] = [rec(valid, "dish-pay")]
    valid["candidates_not_selected"] = [
        {"product_id": "dish-pos", "confidence": "medium", "support_count": 2, "pain_point_ids": ["PP2", "PP3"]}
    ]
    assert_fails(valid, data, 15)


# --- checks 16–18: mapping table ---------------------------------------------------


def test_tc_k16_unknown_category(valid, data):
    valid["pain_points"][3]["category_id"] = "c_unknown"
    assert_fails(valid, data, 16)


def test_tc_k17a_primary_not_mapped_to_its_pain_points(valid, data):
    rec(valid, "dish-pay").update(product_id="dish-starter", name="DISH Starter")
    assert_fails(valid, data, 17)
    assert any("dish-starter is not mapped" in reason for reason in results(valid, data)[17].reasons)


def test_tc_k17b_mapped_product_missing(valid, data):
    valid["recommendations"] = [rec(valid, "dish-pay")]
    assert_fails(valid, data, 17)


def test_tc_k17c_product_present_only_as_prerequisite(valid, data):
    # TC-P03: PP1 c_phone high, PP2 c_booking medium, PP3 c_cash high.
    ev = lambda rid: {"review_id": rid, "quote": "x y z", "text_source": "original"}  # noqa: E731
    valid["pain_points"] = [
        {"pain_point_id": "PP1", "category_id": "c_phone", "description": "d", "confidence": "high",
         "evidence": [ev("F01-001"), ev("F01-002")]},
        {"pain_point_id": "PP2", "category_id": "c_booking", "description": "d", "confidence": "medium",
         "evidence": [ev("F01-003")]},
        {"pain_point_id": "PP3", "category_id": "c_cash", "description": "d", "confidence": "high",
         "evidence": [ev("F01-004"), ev("F01-005")]},
    ]
    prereq = primary("dish-professional-reservation", "DISH Professional Reservation", "high",
                     ["PP1", "PP2"], ["F01-001", "F01-002", "F01-003"])
    prereq.update(role="prerequisite", required_by=["dish-ai-phone-assistant"])
    valid["recommendations"] = [
        primary("dish-ai-phone-assistant", "AI Phone Assistant", "high", ["PP1"], ["F01-001", "F01-002"]),
        primary("dish-pay", "DISH Pay", "high", ["PP3"], ["F01-004", "F01-005"]),
        prereq,
    ]
    valid["candidates_not_selected"] = []
    assert_passes(valid, data, 17)


def test_tc_k17d_pain_point_without_evidence_needs_no_product(valid, data):
    valid["pain_points"][0]["evidence"] = []
    valid["pain_points"][0]["confidence"] = None
    valid["recommendations"] = [rec(valid, "dish-pos")]
    assert_passes(valid, data, 17)
    assert_fails(valid, data, 1)


def test_tc_k18a_mapped_category_twice(valid, data):
    valid["pain_points"][1]["category_id"] = "c_cash"
    assert_fails(valid, data, 18)


def test_tc_k18b_unmapped_category_twice(valid, data):
    valid["pain_points"][1]["category_id"] = "c_none"
    assert_passes(valid, data, 18)


# --- TC-K19: all checks always run -------------------------------------------------


def test_tc_k19_all_failures_reported(valid, data):
    valid["pain_points"][0]["evidence"][0]["review_id"] = "F01-099"
    rec(valid, "dish-pos").update(product_id="dish-ai-phone-assistant", name="AI Phone Assistant")
    out = results(valid, data)
    assert not out[2].passed and out[2].reasons
    assert not out[7].passed and out[7].reasons
    assert all(r.passed in (True, False) for r in out.values())


def test_tc_k19_broken_structure_still_runs_every_check(valid, data):
    del valid["pain_points"]
    out = results(valid, data)
    assert not out[1].passed
    not_evaluated = [i for i, r in out.items() if NOT_EVALUATED in r.reasons]
    assert 3 in not_evaluated and 10 in not_evaluated
    assert all(not out[i].passed for i in not_evaluated)


def test_tc_k01_section_not_a_list(valid, data):
    valid["pain_points"] = "none"
    assert "'pain_points' is not a list" in results(valid, data)[1].reasons


def test_tc_k01_restaurant_not_an_object(valid, data):
    valid["restaurant"] = "F01"
    assert "restaurant is not an object" in results(valid, data)[1].reasons


def test_tc_k19_card_not_an_object(data):
    out = results([], data)
    assert out[1].reasons == ["card is not an object"]
    assert all(not r.passed for r in out.values())
