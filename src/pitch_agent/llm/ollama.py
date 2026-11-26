"""Ollama provider (contracts/llm-interface.md "ollama", research R4, R6).

Local model, no API key; uses only the standard library.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping

from pitch_agent.llm import LLMError, LLMRequest

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_TIMEOUT = 900.0
HOST_ENV = "OLLAMA_HOST"
TIMEOUT_ENV = "PITCH_AGENT_LLM_TIMEOUT"
OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 8192}


class OllamaLLM:
    provider = "ollama"

    def __init__(
        self,
        model: str,
        host: str | None = None,
        timeout: float | None = None,
        env: Mapping[str, str] | None = None,
    ):
        env = os.environ if env is None else env
        self.model = model
        self.host = host or env.get(HOST_ENV) or DEFAULT_HOST
        self.timeout = float(timeout if timeout is not None else env.get(TIMEOUT_ENV) or DEFAULT_TIMEOUT)

    def _error(self, problem: str, hint: str = "") -> LLMError:
        """An error naming the host and model, with a hint that fits the error."""
        message = f"Ollama at {self.host} (model {self.model}): {problem}."
        return LLMError(f"{message} {hint}" if hint else message)

    def generate(self, request: LLMRequest) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
            "format": request.json_schema,
            "stream": False,
            "think": False,
            "options": OPTIONS,
        }
        http_request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace").strip()
            raise self._error(f"HTTP {e.code} {detail}", f"Is the model pulled (`ollama pull {self.model}`)?") from e
        except TimeoutError as e:
            raise self._error(
                f"request timed out after {self.timeout:g} s",
                f"Raise {TIMEOUT_ENV} (seconds) or use a smaller model.",
            ) from e
        except urllib.error.URLError as e:
            raise self._error(
                f"cannot connect ({e.reason})", "Is Ollama running (`ollama serve` or the Ollama app)?"
            ) from e

        try:
            content = json.loads(raw)["message"]["content"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            raise self._error("response has no message.content") from e
        if not isinstance(content, str):
            raise self._error("response has no message.content")
        return content
