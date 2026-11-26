"""Mock provider (contracts/llm-interface.md "mock", research R4).

Responses come from a mapping ``{request_id: response}``, a callable
``(LLMRequest) -> response`` or a JSON file with such a mapping. A response is a
model-output dict (returned as JSON text), ``{"raw": text}`` (returned as is) or
``{"error": message}`` (raises ``LLMError``).
"""

from __future__ import annotations

import json
from pathlib import Path

from pitch_agent.llm import LLMError, LLMRequest

EMPTY_ANALYSIS = {
    "restaurant_description": "",
    "pain_points": [],
    "opening_pitch": "",
    "discovery_questions": [],
    "general_questions": [],
}


class MockLLM:
    provider = "mock"

    def __init__(self, responses=None, model: str = "mock"):
        if isinstance(responses, (str, Path)):
            responses = json.loads(Path(responses).read_text(encoding="utf-8"))
        self._responses = responses if responses is not None else {}
        self.model = model
        self.calls: list[LLMRequest] = []

    def generate(self, request: LLMRequest) -> str:
        self.calls.append(request)
        if callable(self._responses):
            response = self._responses(request)
        else:
            response = self._responses.get(request.request_id, EMPTY_ANALYSIS)
        if isinstance(response, dict) and set(response) == {"error"}:
            raise LLMError(response["error"])
        if isinstance(response, dict) and set(response) == {"raw"}:
            return response["raw"]
        return json.dumps(response, ensure_ascii=False)
