"""Section E: ranking and selection (TC-R01–TC-R08)."""

import pytest

from pitch_agent.rules import ProductCandidate, rank_and_select


def cand(product_id, confidence, support):
    reviews = tuple(f"{product_id}-r{i}" for i in range(support))
    return ProductCandidate(product_id, confidence, ("PP1",), reviews)


CASES = {
    "TC-R01": ([cand("dish-pay", "medium", 1)], ["dish-pay"], []),
    "TC-R02": (
        [cand("dish-pos", "medium", 1), cand("dish-pay", "high", 2)],
        ["dish-pay", "dish-pos"],
        [],
    ),
    "TC-R03": (
        [cand("dish-pay", "high", 2), cand("dish-pos", "medium", 5), cand("dish-starter", "medium", 1)],
        ["dish-pay", "dish-pos"],
        ["dish-starter"],
    ),
    "TC-R04": (
        [cand("dish-pay", "medium", 1), cand("dish-pos", "medium", 3), cand("dish-starter", "medium", 2)],
        ["dish-pos", "dish-starter"],
        ["dish-pay"],
    ),
    "TC-R05": (
        [cand("dish-starter", "high", 2), cand("dish-pay", "high", 2), cand("dish-pos", "medium", 5)],
        ["dish-pay", "dish-starter"],
        ["dish-pos"],
    ),
    "TC-R06": (
        [
            cand("dish-professional-order", "medium", 1),
            cand("dish-pos", "medium", 1),
            cand("dish-pay", "medium", 1),
        ],
        ["dish-pay", "dish-pos"],
        ["dish-professional-order"],
    ),
    "TC-R07": ([], [], []),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_tc_r01_r07_rank_and_select(case):
    candidates, expected_primaries, expected_not_selected = CASES[case]
    primaries, not_selected = rank_and_select(candidates)
    assert [c.product_id for c in primaries] == expected_primaries, case
    assert [c.product_id for c in not_selected] == expected_not_selected, case


def test_tc_r05_tie_broken_by_product_id():
    primaries, _ = rank_and_select(CASES["TC-R05"][0])
    assert [c.product_id for c in primaries] == ["dish-pay", "dish-starter"]


def test_tc_r08_input_order_does_not_matter():
    candidates = list(reversed(CASES["TC-R05"][0]))
    primaries, not_selected = rank_and_select(candidates)
    assert [c.product_id for c in primaries] == ["dish-pay", "dish-starter"]
    assert [c.product_id for c in not_selected] == ["dish-pos"]
