"""Design tests (plan.md, no case ID): LLM configuration and provider factory (research R6)."""

import pytest

from pitch_agent.config import resolve_llm_config
from pitch_agent.llm import ConfigError, LLMConfig
from pitch_agent.llm.factory import create_llm
from pitch_agent.llm.mock import MockLLM

ENV = {"PITCH_AGENT_LLM_PROVIDER": "env-provider", "PITCH_AGENT_LLM_MODEL": "env-model"}


def test_flag_wins_over_environment():
    config = resolve_llm_config(provider="mock", model="flag-model", env=ENV)
    assert (config.provider, config.model) == ("mock", "flag-model")


def test_environment_wins_over_default():
    config = resolve_llm_config(env=ENV)
    assert (config.provider, config.model) == ("env-provider", "env-model")


def test_default_provider_is_ollama():
    assert resolve_llm_config(env={}).provider == "ollama"


@pytest.mark.parametrize("provider, model", [("ollama", "granite4.2:8b"), ("mock", "mock")])
def test_default_model_per_provider(provider, model):
    assert resolve_llm_config(provider=provider, env={}).model == model


def test_environment_model_used_with_flag_provider():
    config = resolve_llm_config(provider="mock", env={"PITCH_AGENT_LLM_MODEL": "env-model"})
    assert config.model == "env-model"


def test_options_passed_through():
    config = resolve_llm_config(provider="mock", options={"responses": {"F01": {}}}, env={})
    assert config.options == {"responses": {"F01": {}}}


def test_create_mock_llm():
    llm = create_llm(LLMConfig("mock", "mock", {"responses": {}}))
    assert isinstance(llm, MockLLM)
    assert (llm.provider, llm.model) == ("mock", "mock")


def test_unknown_provider_lists_available_providers():
    with pytest.raises(ConfigError) as e:
        create_llm(LLMConfig("gpt", None))
    assert "gpt" in str(e.value) and "mock" in str(e.value)


def test_default_config_creates_ollama_llm():
    from pitch_agent.llm.ollama import OllamaLLM

    llm = create_llm(resolve_llm_config(env={}))
    assert isinstance(llm, OllamaLLM)
    assert (llm.provider, llm.model) == ("ollama", "granite4.2:8b")


def test_ollama_model_from_flag():
    llm = create_llm(resolve_llm_config(provider="ollama", model="qwen3:8b", env={}))
    assert llm.model == "qwen3:8b"


def test_unknown_provider_lists_ollama():
    with pytest.raises(ConfigError, match="mock, ollama"):
        create_llm(LLMConfig("gpt", None))
