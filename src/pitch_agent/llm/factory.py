"""Provider registry and ``create_llm`` (contracts/llm-interface.md)."""

from __future__ import annotations

from pitch_agent.llm import ConfigError, LLMClient, LLMConfig
from pitch_agent.llm.mock import MockLLM


def _mock(config: LLMConfig) -> LLMClient:
    return MockLLM(config.options.get("responses"), model=config.model or "mock")


PROVIDERS = {"mock": _mock}


def create_llm(config: LLMConfig) -> LLMClient:
    try:
        build = PROVIDERS[config.provider]
    except KeyError:
        available = ", ".join(sorted(PROVIDERS))
        raise ConfigError(f"Unknown LLM provider '{config.provider}' (available: {available})") from None
    return build(config)
