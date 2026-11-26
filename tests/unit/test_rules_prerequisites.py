"""Section F: prerequisites (TC-P01–TC-P07)."""

import pytest

from pitch_agent.rules import ProductCandidate, add_prerequisites, rank_and_select

AI = "dish-ai-phone-assistant"
RES = "dish-professional-reservation"


def cand(product_id, confidence, support, pain_point_ids=("PP1",)):
    reviews = tuple(f"{product_id}-r{i}" for i in range(support))
    return ProductCandidate(product_id, confidence, tuple(pain_point_ids), reviews)


def run(candidates, catalog):
    primaries, not_selected = rank_and_select(candidates)
    return add_prerequisites(primaries, not_selected, catalog)


def roles(recommendations):
    return [(r.product_id, r.role) for r in recommendations]


P01 = [cand(AI, "medium", 1, ["PP1"]), cand("dish-pos", "medium", 1, ["PP2"])]
P02 = [cand(RES, "high", 2), cand(AI, "medium", 1), cand("dish-pos", "medium", 1)]
P03 = [cand(AI, "high", 2, ["PP1"]), cand("dish-pay", "high", 2, ["PP3"]), cand(RES, "medium", 1, ["PP2"])]
P05 = [cand("dish-pay", "high", 2), cand("dish-pos", "high", 2), cand(AI, "medium", 1)]


def test_tc_p01_prerequisite_does_not_use_a_slot(fixture_catalog):
    recommendations, not_selected = run(P01, fixture_catalog)
    assert roles(recommendations) == [(AI, "primary"), ("dish-pos", "primary"), (RES, "prerequisite")]
    prereq = recommendations[2]
    assert prereq.required_by == [AI]
    assert prereq.name == fixture_catalog[RES].name
    assert recommendations[0].required_by == []
    assert not_selected == []


def test_tc_p02_prerequisite_already_primary(fixture_catalog):
    recommendations, not_selected = run(P02, fixture_catalog)
    assert roles(recommendations) == [(RES, "primary"), (AI, "primary")]
    assert [c.product_id for c in not_selected] == ["dish-pos"]


def test_tc_p03_prerequisite_removed_from_not_selected(fixture_catalog):
    recommendations, not_selected = run(P03, fixture_catalog)
    assert roles(recommendations) == [(AI, "primary"), ("dish-pay", "primary"), (RES, "prerequisite")]
    assert not_selected == []


def test_tc_p04_prerequisite_takes_requiring_product_values(fixture_catalog):
    recommendations, _ = run(P01, fixture_catalog)
    ai, prereq = recommendations[0], recommendations[2]
    assert prereq.confidence == ai.confidence == "medium"
    assert prereq.pain_point_ids == ai.pain_point_ids == ["PP1"]
    assert prereq.supporting_review_ids == ai.supporting_review_ids
    assert prereq.support_count == len(prereq.supporting_review_ids)


def test_tc_p07_prerequisite_unions_pain_points(fixture_catalog):
    recommendations, _ = run(P03, fixture_catalog)
    prereq = recommendations[2]
    assert prereq.product_id == RES
    assert prereq.pain_point_ids == ["PP1", "PP2"]
    assert prereq.confidence == "high"
    assert prereq.supporting_review_ids == sorted(
        [f"{AI}-r0", f"{AI}-r1", f"{RES}-r0"]
    )
    assert prereq.support_count == 3


def test_tc_p05_no_prerequisite_when_requiring_product_not_selected(fixture_catalog):
    recommendations, not_selected = run(P05, fixture_catalog)
    assert roles(recommendations) == [("dish-pay", "primary"), ("dish-pos", "primary")]
    assert [c.product_id for c in not_selected] == [AI]
    assert not_selected[0].confidence == "medium"
    assert not_selected[0].support_count == 1


@pytest.mark.parametrize("candidates", [P01, P02, P03, P05], ids=["P01", "P02", "P03", "P05"])
def test_tc_p06_each_product_at_most_once(fixture_catalog, candidates):
    recommendations, not_selected = run(candidates, fixture_catalog)
    ids = [r.product_id for r in recommendations]
    assert len(ids) == len(set(ids))
    assert not set(ids) & {c.product_id for c in not_selected}


def test_prerequisite_pain_point_ids_in_numeric_order(fixture_catalog):
    """Design test (no case ID): PP2 sorts before PP10."""
    candidates = [cand(AI, "high", 2, ["PP10"]), cand("dish-pay", "high", 2, ["PP1"]), cand(RES, "medium", 1, ["PP2"])]
    recommendations, _ = run(candidates, fixture_catalog)
    assert recommendations[2].pain_point_ids == ["PP2", "PP10"]
