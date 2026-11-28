"""Per-case results and the metrics SC-001 – SC-005 (data-model.md "Metrics")."""

from __future__ import annotations

from dataclasses import dataclass

from pitch_agent.evaluation.labels import GoldLabel
from pitch_agent.models import CheckResult


@dataclass(frozen=True)
class CaseResult:
    restaurant_id: str
    card: dict | None
    error: str | None
    checks: list[CheckResult]
    expected_decision: str
    actual_decision: str
    must_include: list[str]
    recommended_products: list[str]
    missed_must_include: list[str]
    outside_expected: list[str]


def case_result(label: GoldLabel, card: dict | None, error: str | None, checks: list[CheckResult]) -> CaseResult:
    """Compare one card with its gold label; ``card`` is None on generation failure."""
    recommended = [r["product_id"] for r in card["recommendations"]] if card else []
    expected = set(label.must_include) | set(label.acceptable)
    return CaseResult(
        restaurant_id=label.restaurant_id,
        card=card,
        error=error,
        checks=checks,
        expected_decision=label.decision,
        actual_decision=card["decision"] if card else "error",
        must_include=list(label.must_include),
        recommended_products=recommended,
        missed_must_include=[p for p in label.must_include if p not in recommended],
        outside_expected=[p for p in recommended if p not in expected],
    )


def _ratio(count: int, total: int, target: str, met) -> dict:
    """A count/total metric; with total 0 there is nothing to measure ("n/a")."""
    if total == 0:
        return {"value": "0/0", "percent": None, "target": target, "met": None}
    return {"value": f"{count}/{total}", "percent": round(100 * count / total, 1), "target": target,
            "met": met(count, total)}


def _passes_all_checks(case: CaseResult) -> bool:
    return case.error is None and all(c.passed for c in case.checks)


def compute_metrics(case_results: list[CaseResult], restaurants: dict) -> dict:
    """SC-001 – SC-005 for one run (data-model.md "Metrics (SC-001 – SC-005)")."""
    cases = list(case_results)
    total = len(cases)
    not_eligible = [c for c in cases if not restaurants[c.restaurant_id].eligible]
    must_total = sum(len(c.must_include) for c in cases)
    must_hits = must_total - sum(len(c.missed_must_include) for c in cases)
    outside = sum(1 for c in cases if c.outside_expected)
    return {
        "SC-001": _ratio(sum(map(_passes_all_checks, cases)), total, "100%", lambda n, t: n == t),
        "SC-002": _ratio(sum(1 for c in not_eligible if not c.recommended_products), len(not_eligible), "100%",
                         lambda n, t: n == t),
        "SC-003": _ratio(sum(1 for c in cases if c.actual_decision == c.expected_decision), total, ">= 13/15",
                         lambda n, t: n * 15 >= 13 * t),
        "SC-004": _ratio(must_hits, must_total, ">= 80%", lambda n, t: n * 5 >= 4 * t),
        "SC-005": {"value": outside, "target": "<= 1", "met": outside <= 1},
    }
