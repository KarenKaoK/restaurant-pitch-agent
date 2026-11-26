"""Data types for input entities and the visit card (data-model.md)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Input entities (read-only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Restaurant:
    restaurant_id: str
    name: str
    city: str
    address: str
    status: str
    segment: str

    @property
    def is_closed(self) -> bool:
        return self.status == "closed"

    @property
    def is_chain(self) -> bool:
        return self.segment == "chain"

    @property
    def eligible(self) -> bool:
        return not (self.is_closed or self.is_chain)


@dataclass(frozen=True)
class Review:
    review_id: str
    restaurant_id: str
    text: str
    text_source: str
    review_date: str
    date_imputed: str
    rating: str
    rating_imputed: str
    platform: str
    source_url: str


@dataclass(frozen=True)
class Product:
    product_id: str
    name: str
    category: str
    requires: str | None = None


@dataclass(frozen=True)
class PainPointCategory:
    category_id: str
    definition: str
    product_ids: tuple[str, ...]
    example_signals: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    catalog_reference: str | None = None

    @property
    def repeatable(self) -> bool:
        """A category without mapped products may appear in several pain points (R11)."""
        return len(self.product_ids) == 0


@dataclass(frozen=True)
class Mapping:
    """The pain-point category table and its top-level ``rules`` object."""

    categories: tuple[PainPointCategory, ...]
    rules: dict[str, Any] = field(default_factory=dict)

    def category(self, category_id: str) -> PainPointCategory | None:
        for category in self.categories:
            if category.category_id == category_id:
                return category
        return None

    @property
    def category_ids(self) -> list[str]:
        return [c.category_id for c in self.categories]


# ---------------------------------------------------------------------------
# Parsed model output (pain point part, used by the merge rule)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawEvidence:
    review_id: str
    quote: str


@dataclass(frozen=True)
class RawPainPoint:
    ref: str
    category_id: str
    description: str
    evidence: tuple[RawEvidence, ...]


# ---------------------------------------------------------------------------
# Output entities (the visit card, contracts/visit-card.md)
# ---------------------------------------------------------------------------


class _JsonMixin:
    """``to_dict`` / ``from_dict`` with exactly the JSON keys of the contract."""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)


@dataclass
class RestaurantSummary(_JsonMixin):
    restaurant_id: str
    name: str
    city: str
    status: str
    segment: str
    reviews_analysed: int | None
    description: str | None


@dataclass
class Evidence(_JsonMixin):
    review_id: str
    quote: str
    text_source: str | None


@dataclass
class PainPoint(_JsonMixin):
    pain_point_id: str
    category_id: str
    description: str
    confidence: str | None
    evidence: list[Evidence]

    @classmethod
    def from_dict(cls, d: dict) -> PainPoint:
        return cls(**{**d, "evidence": [Evidence.from_dict(e) for e in d["evidence"]]})


@dataclass
class Recommendation(_JsonMixin):
    product_id: str
    name: str
    role: str
    required_by: list[str]
    pain_point_ids: list[str]
    supporting_review_ids: list[str]
    support_count: int
    confidence: str


@dataclass
class Candidate(_JsonMixin):
    product_id: str
    confidence: str
    support_count: int
    pain_point_ids: list[str]


@dataclass
class DiscoveryQuestion(_JsonMixin):
    question: str
    pain_point_id: str | None
    category_id: str | None
    based_on_reviews: bool


@dataclass
class VisitCard(_JsonMixin):
    schema_version: str
    restaurant: RestaurantSummary
    decision: str
    decision_reasons: list[str]
    pain_points: list[PainPoint]
    recommendations: list[Recommendation]
    candidates_not_selected: list[Candidate]
    opening_pitch: str | None
    discovery_questions: list[DiscoveryQuestion]

    @classmethod
    def from_dict(cls, d: dict) -> VisitCard:
        return cls(
            schema_version=d["schema_version"],
            restaurant=RestaurantSummary.from_dict(d["restaurant"]),
            decision=d["decision"],
            decision_reasons=list(d["decision_reasons"]),
            pain_points=[PainPoint.from_dict(p) for p in d["pain_points"]],
            recommendations=[Recommendation.from_dict(r) for r in d["recommendations"]],
            candidates_not_selected=[Candidate.from_dict(c) for c in d["candidates_not_selected"]],
            opening_pitch=d["opening_pitch"],
            discovery_questions=[DiscoveryQuestion.from_dict(q) for q in d["discovery_questions"]],
        )


@dataclass
class CheckResult(_JsonMixin):
    check_id: int
    passed: bool
    reasons: list[str] = field(default_factory=list)

