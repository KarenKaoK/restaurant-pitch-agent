"""Provider registry and ``create_llm`` (contracts/llm-interface.md)."""

from __future__ import annotations

from pitch_agent.llm import ConfigError, LLMClient, LLMConfig
from pitch_agent.llm.mock import MockLLM
from pitch_agent.llm.ollama import OllamaLLM


def _mock(config: LLMConfig) -> LLMClient:
    return MockLLM(config.options.get("responses"), model=config.model or "mock")


def _ollama(config: LLMConfig) -> LLMClient:
    return OllamaLLM(config.model)


PROVIDERS = {"mock": _mock, "ollama": _ollama}


def create_llm(config: LLMConfig) -> LLMClient:
    try:
        build = PROVIDERS[config.provider]
    except KeyError:
        available = ", ".join(sorted(PROVIDERS))
        raise ConfigError(f"Unknown LLM provider '{config.provider}' (available: {available})") from None
    return build(config)
