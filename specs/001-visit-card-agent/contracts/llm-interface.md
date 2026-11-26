# Contract: LLM Interface

The only boundary between business logic and a language model (research R3). Core modules import `LLMClient`, `LLMRequest` and `LLMError` only; they never import a provider module.

## Types

```text
LLMRequest
  system: str          # system prompt
  prompt: str          # user prompt
  json_schema: dict    # expected output shape (contracts/model-output.md)
  request_id: str      # restaurant ID; used for tracing and by the mock

LLMClient (protocol)
  provider: str        # e.g. "mock", "ollama" — recorded in the evaluation report
  model: str           # e.g. "granite4.2:8b" — recorded in the evaluation report
  generate(request: LLMRequest) -> str     # raw answer text; raises LLMError on failure

LLMError(Exception)    # call failed: connection, HTTP status, timeout, provider error

LLMConfig
  provider: str
  model: str | None
  options: dict        # provider-specific (e.g. host, timeout, mock responses)

create_llm(config: LLMConfig) -> LLMClient   # raises ConfigError for an unknown provider
```

## Providers in v1

### `mock`

- Built with: a mapping `{request_id: response}`, a callable `(LLMRequest) -> response`, or a JSON file (`--mock-responses`).
- `response` is one of:
  - a dict in the model-output shape → returned as JSON text;
  - `{"raw": "<text>"}` → that text returned as is (simulates unparseable output);
  - `{"error": "<message>"}` → raises `LLMError`.
- A `request_id` with no configured response → `{"restaurant_description": "", "pain_points": [], "opening_pitch": "", "discovery_questions": [], "general_questions": []}`.
- Records every `LLMRequest` it receives (`calls`), so tests can assert call counts and prompt content.
- `provider = "mock"`, `model = "mock"` unless set.

### `ollama`

- `POST {OLLAMA_HOST}/api/chat`, body:
  - `model`;
  - `messages`: system + user;
  - `format`: `json_schema`;
  - `stream`: `false`;
  - `think`: `false` (no reasoning phase before the answer; thinking-capable models such as `granite4.2:8b` think by default and are too slow on CPU);
  - `options`: `{temperature: 0, seed: 42, num_ctx: 8192}`.
- Returns `message.content`.
- Connection refused, HTTP ≥ 400, timeout or a missing `message.content` → `LLMError`. The message names the host and model and gives a hint that fits the error:
  - cannot connect → start Ollama (`ollama serve` or the Ollama app);
  - HTTP ≥ 400 → check that the model is pulled (`ollama pull <model>`);
  - timeout → raise `PITCH_AGENT_LLM_TIMEOUT` (seconds) or use a smaller model;
  - missing `message.content` → the Ollama response is unexpected (no fixed hint).
- No API key; nothing secret is sent or logged.

## Adding a provider later (not in v1)

1. New module `pitch_agent/llm/<provider>.py` implementing `LLMClient`.
2. One registry entry in `pitch_agent/llm/factory.py`.
3. Its SDK as an optional dependency group in `pyproject.toml`, so the default install stays dependency-free.
4. Its API key read from an environment variable when the client is created; never written to files, logs, cards or reports (constitution V).

No business-logic module changes when a provider is added.
