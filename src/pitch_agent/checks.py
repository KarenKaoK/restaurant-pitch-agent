"""Quote check and deterministic card checks (FR-025)."""

from __future__ import annotations

MIN_QUOTE_WORDS = 3


def _collapse(text: str) -> str:
    """Trim and collapse all whitespace (including line breaks) to single spaces."""
    return " ".join(text.split())


def quote_is_verbatim(quote: str, review_text: str) -> tuple[bool, str]:
    """Check 3: the quote is an exact, case- and punctuation-sensitive substring of the
    review text after whitespace normalisation, and has at least 3 words.

    Returns ``(passed, reason)``; ``reason`` is empty when passed.
    """
    normalised = _collapse(quote)
    if not normalised:
        return False, "quote is empty"
    if len(normalised.split(" ")) < MIN_QUOTE_WORDS:
        return False, f"quote has fewer than {MIN_QUOTE_WORDS} words"
    if normalised not in _collapse(review_text):
        return False, "quote is not a verbatim excerpt of the review text"
    return True, ""
