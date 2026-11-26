"""Visit card generation (data-model.md "Card derivation")."""

from __future__ import annotations

from pitch_agent.loaders import AgentData
from pitch_agent.models import Restaurant, RestaurantSummary, VisitCard
from pitch_agent.rules import decide

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


def generate_card(restaurant_id: str, data: AgentData, llm) -> VisitCard:
    """Produce the visit card for one restaurant.

    Raises ``UnknownRestaurantError`` for an unknown ID (FR-004). Closed and chain
    restaurants get a short card without a model call (FR-020a).
    """
    restaurant = data.get_restaurant(restaurant_id)
    if not restaurant.eligible:
        return build_short_card(restaurant)
    raise NotImplementedError("eligible restaurants: completed in T046")
