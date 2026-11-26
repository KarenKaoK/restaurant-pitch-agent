"""The only boundary between business logic and a language model (contracts/llm-interface.md).

Core modules import ``LLMClient``, ``LLMRequest`` and ``LLMError`` only; they never
import a provider module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    system: str
    prompt: str
    json_schema: dict
    request_id: str


class LLMClient(Protocol):
    provider: str
    model: str

    def generate(self, request: LLMRequest) -> str:
        """Return the raw answer text; raise ``LLMError`` on failure."""
        ...


class LLMError(Exception):
    """The model call failed: connection, HTTP status, timeout or provider error."""


class ConfigError(Exception):
    """Invalid LLM configuration, e.g. an unknown provider."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
