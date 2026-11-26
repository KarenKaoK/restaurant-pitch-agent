"""Section C: merging pain points (TC-C08, TC-C09, rule level)."""

from pitch_agent.models import RawEvidence, RawPainPoint
from pitch_agent.rules import build_candidates, merge_pain_points, pain_point_confidence


def raw(ref, category, review_ids, description=None):
    evidence = tuple(RawEvidence(rid, f"quote from {rid}") for rid in review_ids)
    return RawPainPoint(ref, category, description or f"desc {ref}", evidence)


def test_tc_c08_same_category_merged_with_evidence_in_order(fixture_mapping):
    merged, ref_map = merge_pain_points(
        [raw("p1", "c_cash", ["F01-001"], "First"), raw("p2", "c_cash", ["F01-002"], "Second")],
        fixture_mapping,
    )
    assert len(merged) == 1
    pp = merged[0]
    assert pp.pain_point_id == "PP1"
    assert pp.category_id == "c_cash"
    assert pp.description == "First"
    assert [e.review_id for e in pp.evidence] == ["F01-001", "F01-002"]
    assert [e.quote for e in pp.evidence] == ["quote from F01-001", "quote from F01-002"]
    assert pain_point_confidence(pp) == "high"
    assert ref_map == {"p1": "PP1", "p2": "PP1"}


def test_tc_c09_repeatable_category_kept_separate(fixture_mapping):
    merged, ref_map = merge_pain_points(
        [raw("p1", "c_none", ["F01-004"]), raw("p2", "c_none", ["F01-005"])],
        fixture_mapping,
    )
    assert [(p.pain_point_id, p.category_id) for p in merged] == [("PP1", "c_none"), ("PP2", "c_none")]
    assert [[e.review_id for e in p.evidence] for p in merged] == [["F01-004"], ["F01-005"]]
    assert ref_map == {"p1": "PP1", "p2": "PP2"}


def test_tc_c08_ids_follow_order_of_first_appearance(fixture_mapping):
    merged, ref_map = merge_pain_points(
        [
            raw("p1", "c_kitchen", ["F01-003"]),
            raw("p2", "c_cash", ["F01-001"]),
            raw("p3", "c_kitchen", ["F01-004"]),
            raw("p4", "c_none", ["F01-005"]),
        ],
        fixture_mapping,
    )
    assert [(p.pain_point_id, p.category_id) for p in merged] == [
        ("PP1", "c_kitchen"),
        ("PP2", "c_cash"),
        ("PP3", "c_none"),
    ]
    assert [e.review_id for e in merged[0].evidence] == ["F01-003", "F01-004"]
    assert ref_map == {"p1": "PP1", "p2": "PP2", "p3": "PP1", "p4": "PP3"}


def test_tc_c11_unknown_category_kept_separate(fixture_mapping):
    merged, ref_map = merge_pain_points(
        [raw("p1", "c_unknown", ["F01-001"]), raw("p2", "c_unknown", ["F01-002"])],
        fixture_mapping,
    )
    assert [(p.pain_point_id, p.category_id) for p in merged] == [("PP1", "c_unknown"), ("PP2", "c_unknown")]
    assert [[e.review_id for e in p.evidence] for p in merged] == [["F01-001"], ["F01-002"]]
    assert ref_map == {"p1": "PP1", "p2": "PP2"}


def test_tc_c11_unknown_category_gives_no_candidates(fixture_mapping):
    merged, _ = merge_pain_points(
        [raw("p1", "c_unknown", ["F01-001"]), raw("p2", "c_unknown", ["F01-002"])],
        fixture_mapping,
    )
    assert build_candidates(merged, fixture_mapping) == []
