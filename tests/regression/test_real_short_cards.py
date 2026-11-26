"""Section O (part): real-data short cards (TC-X04, TC-X05)."""

import pytest

from pitch_agent.agent import generate_card
from pitch_agent.checks import run_checks
from pitch_agent.loaders import load_agent_data


class FailIfCalledLLM:
    provider = model = "fail-if-called"

    def generate(self, request):
        pytest.fail("the model must not be called for a closed or chain restaurant")


@pytest.fixture(scope="module")
def real_data():
    from pathlib import Path

    return load_agent_data(Path(__file__).resolve().parents[2] / "data")


@pytest.mark.parametrize(
    "case, restaurant_id, reasons",
    [("TC-X04", "R10", ["chain"]), ("TC-X05", "R11", ["closed"])],
)
def test_tc_x04_x05_real_short_card(real_data, case, restaurant_id, reasons):
    card = generate_card(restaurant_id, real_data, FailIfCalledLLM()).to_dict()
    assert card["decision"] == "no_recommendation", case
    assert card["decision_reasons"] == reasons, case
    assert card["restaurant"]["reviews_analysed"] is None
    failures = {r.check_id: r.reasons for r in run_checks(card, real_data) if not r.passed}
    assert failures == {}, case
