"""Section C: pain-point and product confidence (TC-C01–TC-C07, TC-C10)."""

import pytest

from pitch_agent.models import Evidence, PainPoint
from pitch_agent.rules import build_candidates, pain_point_confidence


def pp(pid, category, review_ids):
    evidence = [Evidence(rid, f"quote from {rid}", "original") for rid in review_ids]
    return PainPoint(pid, category, f"desc {pid}", None, evidence)


@pytest.mark.parametrize(
    "case, review_ids, expected",
    [
        ("TC-C01", ["F01-001"], "medium"),
        ("TC-C02", ["F01-001", "F01-002"], "high"),
        ("TC-C03", ["F01-001", "F01-001"], "medium"),
        ("TC-C04", ["F01-003", "F01-004", "F01-005"], "high"),
    ],
)
def test_tc_c01_c04_pain_point_confidence(case, review_ids, expected):
    assert pain_point_confidence(pp("PP1", "c_cash", review_ids)) == expected, case


def test_tc_c05_pain_point_without_evidence_has_no_confidence():
    assert pain_point_confidence(pp("PP1", "c_cash", [])) is None


def _dish_pos(candidates):
    return next(c for c in candidates if c.product_id == "dish-pos")


def test_tc_c06_product_confidence_is_highest_of_its_pain_points(fixture_mapping):
    pain_points = [pp("PP1", "c_kitchen", ["F01-003", "F01-004"]), pp("PP2", "c_order", ["F01-006"])]
    assert _dish_pos(build_candidates(pain_points, fixture_mapping)).confidence == "high"


def test_tc_c07_product_with_only_medium_pain_points(fixture_mapping):
    pain_points = [pp("PP1", "c_kitchen", ["F01-003"]), pp("PP2", "c_order", ["F01-006"])]
    assert _dish_pos(build_candidates(pain_points, fixture_mapping)).confidence == "medium"


def test_tc_c10_pain_point_without_evidence_does_not_count(fixture_mapping):
    pain_points = [pp("PP1", "c_kitchen", ["F01-003"]), pp("PP2", "c_order", [])]
    pos = _dish_pos(build_candidates(pain_points, fixture_mapping))
    assert pos.confidence == "medium"
    assert pos.support_count == 1
    assert list(pos.pain_point_ids) == ["PP1"]
