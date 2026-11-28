"""Section M: metrics SC-001 – SC-005 from synthetic case results."""

import pytest

from pitch_agent.evaluation.labels import GoldLabel
from pitch_agent.evaluation.metrics import case_result, compute_metrics
from pitch_agent.loaders import load_agent_data
from pitch_agent.models import CheckResult


@pytest.fixture
def restaurants(fixture_data_dir):
    return load_agent_data(fixture_data_dir).restaurants


def checks(failing=()):
    return [CheckResult(i, i not in failing, ["failed"] if i in failing else []) for i in range(1, 19)]


def case(rid="F01", expected="recommend", actual="recommend", recommended=(), must=(), acceptable=(),
         failing=(), error=None):
    label = GoldLabel(rid, expected, tuple(must), tuple(acceptable), "")
    card = None if error else {"decision": actual, "recommendations": [{"product_id": p} for p in recommended]}
    return case_result(label, card, error, checks(failing))


def metric(cases, restaurants, sc):
    return compute_metrics(cases, restaurants)[sc]


def test_tc_m01_all_cards_pass(restaurants):
    cases = [case("F01"), case("F05"), case("F06")]
    assert metric(cases, restaurants, "SC-001") == {"value": "3/3", "percent": 100.0, "target": "100%", "met": True}


def test_tc_m02_one_card_fails_one_check(restaurants):
    cases = [case("F01"), case("F05", failing=(3,)), case("F06")]
    assert metric(cases, restaurants, "SC-001") == {"value": "2/3", "percent": 66.7, "target": "100%", "met": False}


def test_tc_m03_closed_card_with_a_product(restaurants):
    cases = [case("F02", "no_recommendation", "recommend", recommended=["dish-pay"]),
             case("F03", "no_recommendation", "no_recommendation")]
    assert metric(cases, restaurants, "SC-002") == {"value": "1/2", "percent": 50.0, "target": "100%", "met": False}


def test_tc_m03_independent_restaurants_not_counted(restaurants):
    cases = [case("F01", recommended=["dish-pay"]), case("F02", "no_recommendation", "no_recommendation")]
    assert metric(cases, restaurants, "SC-002")["value"] == "1/1"


def test_tc_m04_decision_match(restaurants):
    cases = [case("F01"), case("F05", "insufficient_evidence", "insufficient_evidence"),
             case("F06", "insufficient_evidence", "recommend")]
    assert metric(cases, restaurants, "SC-003") == {"value": "2/3", "percent": 66.7, "target": ">= 13/15",
                                                    "met": False}


@pytest.mark.parametrize("matches, met", [(13, True), (12, False)])
def test_tc_m04_target_is_13_of_15(restaurants, matches, met):
    cases = [case("F01") if i < matches else case("F01", actual="insufficient_evidence") for i in range(15)]
    assert metric(cases, restaurants, "SC-003")["met"] is met


def test_tc_m05_must_include_hit_rate(restaurants):
    cases = [case("F01", recommended=["dish-pay"], must=["dish-pay", "dish-pos"]),
             case("F05", recommended=["dish-starter"], must=["dish-starter"]),
             case("F06", recommended=["dish-pos"])]
    assert metric(cases, restaurants, "SC-004") == {"value": "2/3", "percent": 66.7, "target": ">= 80%",
                                                    "met": False}


@pytest.mark.parametrize("hits, met", [(4, True), (3, False)])
def test_tc_m05_target_is_80_percent(restaurants, hits, met):
    cases = [case("F01", recommended=["dish-pay"] if i < hits else [], must=["dish-pay"]) for i in range(5)]
    assert metric(cases, restaurants, "SC-004")["met"] is met


def test_tc_m06_wrong_decision_counts_must_include_as_missed(restaurants):
    result = case("F01", actual="insufficient_evidence", must=["dish-pay", "dish-pos"])
    assert result.missed_must_include == ["dish-pay", "dish-pos"]
    assert metric([result], restaurants, "SC-004")["value"] == "0/2"


def test_tc_m07_one_restaurant_outside_expected(restaurants):
    cases = [case("F01", recommended=["dish-pay", "dish-starter"], must=["dish-pay"]),
             case("F05", recommended=["dish-pos"], acceptable=["dish-pos"])]
    assert cases[0].outside_expected == ["dish-starter"] and cases[1].outside_expected == []
    assert metric(cases, restaurants, "SC-005") == {"value": 1, "target": "<= 1", "met": True}


def test_tc_m08_two_restaurants_outside_expected(restaurants):
    cases = [case("F01", recommended=["dish-starter"]), case("F05", recommended=["dish-pos"])]
    assert metric(cases, restaurants, "SC-005") == {"value": 2, "target": "<= 1", "met": False}


def test_tc_m09a_prerequisite_counts_as_hit(restaurants):
    result = case("F01", recommended=["dish-ai-phone-assistant", "dish-professional-reservation"],
                  must=["dish-ai-phone-assistant", "dish-professional-reservation"])
    assert result.recommended_products == ["dish-ai-phone-assistant", "dish-professional-reservation"]
    assert metric([result], restaurants, "SC-004")["value"] == "2/2"


def test_tc_m09b_prerequisite_outside_lists_counts(restaurants):
    result = case("F01", recommended=["dish-ai-phone-assistant", "dish-professional-reservation"],
                  must=["dish-ai-phone-assistant"])
    assert result.outside_expected == ["dish-professional-reservation"]
    assert metric([result], restaurants, "SC-005")["value"] == 1


def test_tc_m10_generation_failure(restaurants):
    result = case("F01", must=["dish-pay"], error="Ollama timed out")
    assert (result.actual_decision, result.recommended_products) == ("error", [])
    assert result.missed_must_include == ["dish-pay"]
    metrics = compute_metrics([result, case("F05", "insufficient_evidence", "insufficient_evidence")], restaurants)
    assert metrics["SC-001"]["value"] == "1/2"
    assert metrics["SC-003"]["value"] == "1/2"


def test_tc_m10_error_fails_sc001_even_if_checks_passed(restaurants):
    label = GoldLabel("F01", "recommend", (), (), "")
    result = case_result(label, None, "boom", checks())
    assert metric([result], restaurants, "SC-001")["value"] == "0/1"


def test_tc_m11_zero_denominators(restaurants):
    metrics = compute_metrics([case("F01", recommended=["dish-pay"])], restaurants)
    na = {"value": "0/0", "percent": None, "met": None}
    assert metrics["SC-002"] == {**na, "target": "100%"}
    assert metrics["SC-004"] == {**na, "target": ">= 80%"}


def test_metrics_keys_in_order(restaurants):
    assert list(compute_metrics([case()], restaurants)) == ["SC-001", "SC-002", "SC-003", "SC-004", "SC-005"]
