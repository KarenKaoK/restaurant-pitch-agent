"""Section H: quote check, deterministic check 3 (TC-Q01–TC-Q13)."""

import pytest

from pitch_agent.checks import quote_is_verbatim

F01_001 = "They only accept cash payments here."
F01_006 = "The bill was wrong and\nthey forgot our drinks."


@pytest.mark.parametrize(
    "case, quote",
    [
        ("TC-Q01", "only accept cash"),
        ("TC-Q02", "only  accept   cash"),
        ("TC-Q03", "  only accept cash  "),
        ("TC-Q04", "They only accept cash payments here."),
        ("TC-Q05", "only accept cash payments"),
        ("TC-Q05", "accept cash payments"),
    ],
)
def test_tc_q01_q05_verbatim_quotes_pass(case, quote):
    ok, reason = quote_is_verbatim(quote, F01_001)
    assert ok, f"{case}: {reason}"
    assert reason == ""


@pytest.mark.parametrize(
    "case, quote",
    [
        ("TC-Q06", "Only accept cash"),
        ("TC-Q07", "accept cash"),
        ("TC-Q08", "only accept card"),
        ("TC-Q09", "cash payments here!"),
        ("TC-Q10", "“only accept cash”"),
        ("TC-Q11", ""),
        ("TC-Q13", "here. Cash only, so"),
    ],
)
def test_tc_q06_q11_q13_non_verbatim_quotes_fail(case, quote):
    ok, reason = quote_is_verbatim(quote, F01_001)
    assert not ok, case
    assert reason


def test_tc_q07_reason_names_word_minimum():
    ok, reason = quote_is_verbatim("accept cash", F01_001)
    assert not ok
    assert "3 words" in reason


def test_tc_q12_line_break_in_review_matches_space_in_quote():
    ok, reason = quote_is_verbatim("wrong and they forgot", F01_006)
    assert ok, reason
