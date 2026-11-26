"""Section G: decision (TC-DEC01, TC-DEC02, TC-DEC05, rule level)."""

from pitch_agent.models import Evidence, PainPoint, Restaurant
from pitch_agent.rules import add_prerequisites, build_candidates, decide, rank_and_select

F01 = Restaurant("F01", "Fixture Bistro", "Testcity", "", "unknown", "independent")
F02 = Restaurant("F02", "Fixture Closed", "Testcity", "", "closed", "independent")
F03 = Restaurant("F03", "Fixture Chain", "Testcity", "", "unknown", "chain")
F04 = Restaurant("F04", "Fixture Closed Chain", "Testcity", "", "closed", "chain")


def pp(pid, category, review_ids):
    evidence = [Evidence(rid, f"quote from {rid}", "original") for rid in review_ids]
    return PainPoint(pid, category, f"desc {pid}", None, evidence)


def derive(restaurant, pain_points, mapping, catalog):
    primaries, not_selected = rank_and_select(build_candidates(pain_points, mapping))
    recommendations, candidates = add_prerequisites(primaries, not_selected, catalog)
    decision, reasons = decide(restaurant, primaries)
    return decision, reasons, recommendations, candidates


def test_tc_dec01_mapped_pain_point_gives_recommend(fixture_mapping, fixture_catalog):
    decision, reasons, recommendations, _ = derive(
        F01, [pp("PP1", "c_cash", ["F01-001"])], fixture_mapping, fixture_catalog
    )
    assert decision == "recommend"
    assert reasons == []
    assert [r.product_id for r in recommendations] == ["dish-pay"]


def test_tc_dec02_only_unmapped_pain_point_gives_insufficient_evidence(fixture_mapping, fixture_catalog):
    decision, reasons, recommendations, candidates = derive(
        F01, [pp("PP1", "c_none", ["F01-004"])], fixture_mapping, fixture_catalog
    )
    assert decision == "insufficient_evidence"
    assert reasons == ["insufficient_evidence"]
    assert recommendations == [] and candidates == []


def test_tc_dec05_insufficient_evidence_has_no_products(fixture_mapping, fixture_catalog):
    decision, _, recommendations, candidates = derive(F01, [], fixture_mapping, fixture_catalog)
    assert decision == "insufficient_evidence"
    assert recommendations == [] and candidates == []


def test_tc_dec05_closed_or_chain_gives_no_recommendation(fixture_mapping, fixture_catalog):
    primaries, _ = rank_and_select(build_candidates([pp("PP1", "c_cash", ["F01-001"])], fixture_mapping))
    assert decide(F02, primaries) == ("no_recommendation", ["closed"])
    assert decide(F03, primaries) == ("no_recommendation", ["chain"])
    assert decide(F04, primaries) == ("no_recommendation", ["closed", "chain"])
    assert decide(F04, []) == ("no_recommendation", ["closed", "chain"])
