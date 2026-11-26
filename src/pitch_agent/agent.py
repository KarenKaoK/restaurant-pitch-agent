"""Visit card generation (data-model.md "Card derivation")."""

from __future__ import annotations

from dataclasses import replace

from pitch_agent.analysis import GenerationError, ModelAnalysis, build_request, parse_model_output
from pitch_agent.llm import LLMClient, LLMError
from pitch_agent.loaders import AgentData
from pitch_agent.models import DiscoveryQuestion, Restaurant, RestaurantSummary, VisitCard
from pitch_agent.rules import (
    add_prerequisites,
    attach_text_source,
    build_candidates,
    decide,
    merge_pain_points,
    pain_point_confidence,
    rank_and_select,
)

SCHEMA_VERSION = "1"


def _summary(restaurant: Restaurant, reviews_analysed: int | None, description: str | None) -> RestaurantSummary:
    return RestaurantSummary(
        restaurant_id=restaurant.restaurant_id,
        name=restaurant.name,
        city=restaurant.city,
        status=restaurant.status,
        segment=restaurant.segment,
        reviews_analysed=reviews_analysed,
        description=description,
    )


def build_short_card(restaurant: Restaurant) -> VisitCard:
    """FR-020a: card for a closed and/or chain restaurant, produced by rule."""
    decision, reasons = decide(restaurant, [])
    return VisitCard(
        schema_version=SCHEMA_VERSION,
        restaurant=_summary(restaurant, reviews_analysed=None, description=None),
        decision=decision,
        decision_reasons=reasons,
        pain_points=[],
        recommendations=[],
        candidates_not_selected=[],
        opening_pitch=None,
        discovery_questions=[],
    )


def _questions(analysis: ModelAnalysis, ref_map: dict[str, str]) -> list[DiscoveryQuestion]:
    """FR-017, FR-017a: questions linked to pain points (model refs translated to PPn,
    unmatched refs kept as given); general questions only without pain points."""
    if analysis.pain_points:
        return [DiscoveryQuestion(q, ref_map.get(ref, ref), None, True) for ref, q in analysis.discovery_questions]
    return [DiscoveryQuestion(q, None, category_id, False) for category_id, q in analysis.general_questions]


def _eligible_card(restaurant: Restaurant, data: AgentData, llm: LLMClient) -> VisitCard:
    """Steps 1–12 of the card derivation pipeline (data-model.md)."""
    reviews = data.reviews_for(restaurant.restaurant_id)
    request = build_request(restaurant, reviews, data.mapping)
    try:
        text = llm.generate(request)
    except LLMError as e:
        raise GenerationError(str(e)) from e
    analysis = parse_model_output(text)

    pain_points, ref_map = merge_pain_points(list(analysis.pain_points), data.mapping)
    pain_points = attach_text_source(pain_points, reviews)
    pain_points = [replace(pp, confidence=pain_point_confidence(pp)) for pp in pain_points]

    primaries, not_selected = rank_and_select(build_candidates(pain_points, data.mapping))
    recommendations, candidates = add_prerequisites(primaries, not_selected, data.catalog)
    decision, reasons = decide(restaurant, primaries)

    return VisitCard(
        schema_version=SCHEMA_VERSION,
        restaurant=_summary(restaurant, reviews_analysed=len(reviews), description=analysis.restaurant_description),
        decision=decision,
        decision_reasons=reasons,
        pain_points=pain_points,
        recommendations=recommendations,
        candidates_not_selected=candidates,
        opening_pitch=analysis.opening_pitch,
        discovery_questions=_questions(analysis, ref_map),
    )


def generate_card(restaurant_id: str, data: AgentData, llm: LLMClient) -> VisitCard:
    """Produce the visit card for one restaurant.

    Raises ``UnknownRestaurantError`` for an unknown ID (FR-004) and ``GenerationError``
    when the model call fails or its output cannot be parsed; no partial card is
    returned. Closed and chain restaurants get a short card without a model call
    (FR-020a).
    """
    restaurant = data.get_restaurant(restaurant_id)
    if not restaurant.eligible:
        return build_short_card(restaurant)
    return _eligible_card(restaurant, data, llm)
