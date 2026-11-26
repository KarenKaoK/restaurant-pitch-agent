"""Rule-based card derivation, steps 4–10 of the pipeline in data-model.md.

All functions are pure: the model classifies and quotes; products, confidence,
ranking, prerequisites and the decision are decided here by rule.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from pitch_agent.models import (
    Candidate,
    Evidence,
    Mapping,
    PainPoint,
    Product,
    RawPainPoint,
    Recommendation,
    Restaurant,
    Review,
)

MAX_PRIMARIES = 2
_CONFIDENCE_RANK = {"high": 2, "medium": 1}


def _highest(confidences) -> str | None:
    values = [c for c in confidences if c in _CONFIDENCE_RANK]
    return max(values, key=_CONFIDENCE_RANK.__getitem__) if values else None


def _pain_point_order(pain_point_id: str) -> int:
    """``PP2`` sorts before ``PP10``; IDs are always ``PPn`` (assigned by merge)."""
    return int(pain_point_id.removeprefix("PP"))


# ---------------------------------------------------------------------------
# Pain points (steps 4–6)
# ---------------------------------------------------------------------------


def _is_repeatable(category_id: str, mapping: Mapping) -> bool:
    """Listed categories without products and unknown categories are never merged
    (research R11, TC-C11)."""
    category = mapping.category(category_id)
    return category is None or category.repeatable


def merge_pain_points(
    raw_pain_points: list[RawPainPoint], mapping: Mapping
) -> tuple[list[PainPoint], dict[str, str]]:
    """Merge pain points of the same non-repeatable category (FR-008, research R11).

    Evidence is concatenated in order, the first description is kept and IDs
    ``PP1..n`` follow the order of first appearance. Returns the pain points and a
    map from the model's refs (unique, enforced by the parser) to the assigned IDs.
    ``confidence`` and ``text_source`` are left unset.
    """
    merged: list[PainPoint] = []
    by_category: dict[str, PainPoint] = {}
    ref_map: dict[str, str] = {}
    for raw in raw_pain_points:
        evidence = [Evidence(e.review_id, e.quote, None) for e in raw.evidence]
        mergeable = not _is_repeatable(raw.category_id, mapping)
        target = by_category.get(raw.category_id) if mergeable else None
        if target is None:
            target = PainPoint(f"PP{len(merged) + 1}", raw.category_id, raw.description, None, evidence)
            merged.append(target)
            if mergeable:
                by_category[raw.category_id] = target
        else:
            target.evidence.extend(evidence)
        ref_map[raw.ref] = target.pain_point_id
    return merged, ref_map


def attach_text_source(pain_points: list[PainPoint], reviews: list[Review]) -> list[PainPoint]:
    """Set each evidence item's ``text_source`` from the restaurant's review with that
    ID; ``None`` when the ID is not one of the restaurant's reviews."""
    sources = {r.review_id: r.text_source for r in reviews}
    return [
        replace(
            pp,
            evidence=[Evidence(e.review_id, e.quote, sources.get(e.review_id)) for e in pp.evidence],
        )
        for pp in pain_points
    ]


def pain_point_confidence(pain_point: PainPoint) -> str | None:
    """FR-011: more than one distinct cited review → high; exactly one → medium; none → None."""
    distinct = {e.review_id for e in pain_point.evidence}
    if len(distinct) > 1:
        return "high"
    if len(distinct) == 1:
        return "medium"
    return None


# ---------------------------------------------------------------------------
# Candidates (step 7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductCandidate:
    """A product mapped from at least one pain point with evidence."""

    product_id: str
    confidence: str
    pain_point_ids: tuple[str, ...]
    supporting_review_ids: tuple[str, ...]

    @property
    def support_count(self) -> int:
        return len(self.supporting_review_ids)


def build_candidates(pain_points: list[PainPoint], mapping: Mapping) -> list[ProductCandidate]:
    """Products mapped from the pain points' categories (FR-013a). Pain points without
    evidence are ignored (FR-012). Candidates are in order of first mapping."""
    collected: dict[str, list[PainPoint]] = {}
    for pp in pain_points:
        if not pp.evidence:
            continue
        category = mapping.category(pp.category_id)
        if category is None:
            continue
        for product_id in category.product_ids:
            collected.setdefault(product_id, []).append(pp)

    candidates = []
    for product_id, pps in collected.items():
        candidates.append(
            ProductCandidate(
                product_id=product_id,
                confidence=_highest(pain_point_confidence(pp) for pp in pps),
                pain_point_ids=tuple(pp.pain_point_id for pp in pps),
                supporting_review_ids=tuple(sorted({e.review_id for pp in pps for e in pp.evidence})),
            )
        )
    return candidates


# ---------------------------------------------------------------------------
# Ranking (step 8)
# ---------------------------------------------------------------------------


def _rank_key(candidate: ProductCandidate):
    return (-_CONFIDENCE_RANK[candidate.confidence], -candidate.support_count, candidate.product_id)


def rank_and_select(
    candidates: list[ProductCandidate],
) -> tuple[list[ProductCandidate], list[ProductCandidate]]:
    """FR-015a: sort by confidence desc, support count desc, product_id asc; the top
    two are primary, the rest are not selected (both in rank order)."""
    ranked = sorted(candidates, key=_rank_key)
    return ranked[:MAX_PRIMARIES], ranked[MAX_PRIMARIES:]


# ---------------------------------------------------------------------------
# Prerequisites (step 9)
# ---------------------------------------------------------------------------


def add_prerequisites(
    primaries: list[ProductCandidate],
    not_selected: list[ProductCandidate],
    catalog: dict[str, Product],
) -> tuple[list[Recommendation], list[Candidate]]:
    """FR-015, FR-012: add the required product of each primary as a prerequisite
    (unless already primary) and remove it from the candidates not selected.

    Returns recommendations (primaries in rank order, then prerequisites by
    product_id) and the candidates not selected in rank order.
    """
    primary_ids = {c.product_id for c in primaries}
    recommendations = [
        Recommendation(
            product_id=c.product_id,
            name=catalog[c.product_id].name,
            role="primary",
            required_by=[],
            pain_point_ids=list(c.pain_point_ids),
            supporting_review_ids=list(c.supporting_review_ids),
            support_count=c.support_count,
            confidence=c.confidence,
        )
        for c in primaries
    ]

    requiring: dict[str, list[ProductCandidate]] = {}
    for c in primaries:
        required = catalog[c.product_id].requires
        if required is not None and required not in primary_ids:
            requiring.setdefault(required, []).append(c)

    own = {c.product_id: c for c in not_selected}
    for product_id in sorted(requiring):
        sources = requiring[product_id] + ([own[product_id]] if product_id in own else [])
        pain_point_ids = sorted({p for s in sources for p in s.pain_point_ids}, key=_pain_point_order)
        review_ids = sorted({r for s in sources for r in s.supporting_review_ids})
        recommendations.append(
            Recommendation(
                product_id=product_id,
                name=catalog[product_id].name,
                role="prerequisite",
                required_by=[c.product_id for c in requiring[product_id]],
                pain_point_ids=pain_point_ids,
                supporting_review_ids=review_ids,
                support_count=len(review_ids),
                confidence=_highest(c.confidence for c in requiring[product_id]),
            )
        )

    remaining = [
        Candidate(c.product_id, c.confidence, c.support_count, list(c.pain_point_ids))
        for c in not_selected
        if c.product_id not in requiring
    ]
    return recommendations, remaining


# ---------------------------------------------------------------------------
# Decision (step 10)
# ---------------------------------------------------------------------------


def decide(restaurant: Restaurant, primaries: list) -> tuple[str, list[str]]:
    """FR-020, FR-020a: closed/chain takes precedence; otherwise recommend when there
    is at least one primary product, else insufficient evidence."""
    if not restaurant.eligible:
        reasons = (["closed"] if restaurant.is_closed else []) + (["chain"] if restaurant.is_chain else [])
        return "no_recommendation", reasons
    if primaries:
        return "recommend", []
    return "insufficient_evidence", ["insufficient_evidence"]
