"""LLM settings: CLI flag > environment variable > default (research R6)."""

from __future__ import annotations

import os
from collections.abc import Mapping

from pitch_agent.llm import LLMConfig

DEFAULT_PROVIDER = "ollama"
DEFAULT_MODELS = {"ollama": "qwen3:8b", "mock": "mock"}
PROVIDER_ENV = "PITCH_AGENT_LLM_PROVIDER"
MODEL_ENV = "PITCH_AGENT_LLM_MODEL"


def resolve_llm_config(
    provider: str | None = None,
    model: str | None = None,
    options: dict | None = None,
    env: Mapping[str, str] | None = None,
) -> LLMConfig:
    env = os.environ if env is None else env
    provider = provider or env.get(PROVIDER_ENV) or DEFAULT_PROVIDER
    model = model or env.get(MODEL_ENV) or DEFAULT_MODELS.get(provider)
    return LLMConfig(provider=provider, model=model, options=dict(options or {}))
