"""Section D: candidates and support count (TC-S01–TC-S05, TC-S07)."""

from pitch_agent.models import Evidence, PainPoint
from pitch_agent.rules import build_candidates


def pp(pid, category, review_ids):
    evidence = [Evidence(rid, f"quote from {rid}", "original") for rid in review_ids]
    return PainPoint(pid, category, f"desc {pid}", None, evidence)


def by_id(candidates):
    return {c.product_id: c for c in candidates}


def test_tc_s01_single_mapped_product(fixture_mapping):
    candidates = build_candidates([pp("PP1", "c_cash", ["F01-001"])], fixture_mapping)
    assert [c.product_id for c in candidates] == ["dish-pay"]


def test_tc_s02_unmapped_category_gives_no_candidates(fixture_mapping):
    assert build_candidates([pp("PP1", "c_none", ["F01-004"])], fixture_mapping) == []


def test_tc_s03_category_mapped_to_two_products(fixture_mapping):
    candidates = by_id(build_candidates([pp("PP1", "c_multi", ["F01-006"])], fixture_mapping))
    assert set(candidates) == {"dish-pos", "dish-pay"}
    assert list(candidates["dish-pos"].pain_point_ids) == ["PP1"]
    assert list(candidates["dish-pay"].pain_point_ids) == ["PP1"]


def test_tc_s04_support_counts_reviews_across_pain_points(fixture_mapping):
    candidates = by_id(
        build_candidates(
            [pp("PP1", "c_kitchen", ["F01-003"]), pp("PP2", "c_order", ["F01-006"])], fixture_mapping
        )
    )
    pos = candidates["dish-pos"]
    assert pos.support_count == 2
    assert list(pos.pain_point_ids) == ["PP1", "PP2"]
    assert list(pos.supporting_review_ids) == ["F01-003", "F01-006"]


def test_tc_s05_review_counted_once(fixture_mapping):
    candidates = by_id(
        build_candidates(
            [pp("PP1", "c_kitchen", ["F01-006", "F01-003"]), pp("PP2", "c_order", ["F01-006"])],
            fixture_mapping,
        )
    )
    pos = candidates["dish-pos"]
    assert pos.support_count == 2
    assert list(pos.supporting_review_ids) == ["F01-003", "F01-006"]


def test_tc_s07_pain_point_without_evidence_gives_no_candidates(fixture_mapping):
    assert build_candidates([pp("PP1", "c_cash", [])], fixture_mapping) == []
