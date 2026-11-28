"""Provider registry and ``create_llm`` (contracts/llm-interface.md)."""

from __future__ import annotations

import json
from pathlib import Path

from pitch_agent.config import DEFAULT_MODELS
from pitch_agent.llm import ConfigError, LLMClient, LLMConfig
from pitch_agent.llm.mock import MockLLM
from pitch_agent.llm.ollama import OllamaLLM


def _mock_responses(path) -> dict:
    """The ``--mock-responses`` file: a JSON object ``{restaurant_id: response}``."""
    try:
        responses = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as e:
        raise ConfigError(f"Mock responses file {path}: cannot read ({e.strerror})") from e
    except ValueError as e:
        raise ConfigError(f"Mock responses file {path}: not valid JSON ({e})") from e
    if not isinstance(responses, dict):
        raise ConfigError(f"Mock responses file {path}: must be a JSON object {{restaurant_id: response}}")
    return responses


def _mock(config: LLMConfig) -> LLMClient:
    responses = config.options.get("responses")
    if isinstance(responses, (str, Path)):
        responses = _mock_responses(responses)
    return MockLLM(responses, model=config.model or "mock")


def _ollama(config: LLMConfig) -> LLMClient:
    return OllamaLLM(config.model or DEFAULT_MODELS["ollama"])


PROVIDERS = {"mock": _mock, "ollama": _ollama}


def create_llm(config: LLMConfig) -> LLMClient:
    try:
        build = PROVIDERS[config.provider]
    except KeyError:
        available = ", ".join(sorted(PROVIDERS))
        raise ConfigError(f"Unknown LLM provider '{config.provider}' (available: {available})") from None
    return build(config)
