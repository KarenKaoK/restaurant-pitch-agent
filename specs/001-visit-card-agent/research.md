# Research: Restaurant Visit Card Agent

**Feature**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Date**: 2026-11-26

Each entry records a decision, why it was taken and what else was considered. All "NEEDS CLARIFICATION" items from the Technical Context are resolved here.

## R1. Language and runtime

- **Decision**: Python ≥ 3.12, managed with `uv` (project defined in `pyproject.toml`, `src/` layout, console script `pitch-agent`).
- **Rationale**: The existing data-preparation script is Python; Python 3.12 and 3.14 and `uv` are installed on the development machine. `uv` gives a reproducible environment from one lock file.
- **Alternatives**: plain `venv` + `requirements.txt` (no lock file, more manual steps); Node/TypeScript (no benefit for CSV/JSON work and splits the project across two languages).

## R2. Dependencies

- **Decision**: No third-party runtime dependencies. Use the standard library (`csv`, `json`, `dataclasses`, `argparse`, `urllib.request`, `subprocess`). Development dependency: `pytest` only.
- **Rationale**: Constitution "Scope and Data Constraints": prefer the simplest design and add no dependencies the spec does not need. The Ollama HTTP API is plain JSON over HTTP, so `urllib` is enough; catalog frontmatter is flat `key: value` lines (see R10).
- **Alternatives**: `pydantic` for schema validation (convenient, but the card and model-output shapes are small and validated by our own deterministic checks anyway); `ollama` Python client (adds a dependency for two HTTP calls); `PyYAML` for frontmatter (not needed for flat frontmatter).

## R3. LLM interface (provider-independent)

- **Decision**: A small interface in `pitch_agent/llm/`:
  - `LLMRequest`: `system` prompt, `prompt`, `json_schema` (the expected output shape), `request_id` (the restaurant ID, for tracing and for the mock).
  - `LLMClient` protocol: attributes `provider` and `model`; one method `generate(request) -> str` that returns the raw text of the model's answer, or raises `LLMError`.
  - A registry `{"mock": MockLLM, "ollama": OllamaLLM}` and a factory `create_llm(config)`.
  - Parsing and validating the raw text is done in core code (`analysis.py`), not in the providers, so every provider is treated the same way.
- **Rationale**: The owner requires that the business logic does not depend on a provider, that providers and models are switched by configuration, and that a mock is available for TDD. With one method that returns text, a new provider is one module plus one registry entry. The core code sees only `LLMClient`.
- **Alternatives**: a provider abstraction library such as LiteLLM or LangChain (large dependencies, hides request details, harder to test offline); calling Ollama directly from the agent (couples business logic to one provider).
- **Future providers** (OpenAI, Anthropic, Gemini): not implemented in v1. Each would be one module in `pitch_agent/llm/`, an optional dependency group in `pyproject.toml`, and a registry entry. Its API key is read only from an environment variable at call time, never printed or logged (constitution V). No code or configuration for them is added now.

## R4. v1 providers

- **Decision**:
  - **`mock`**: returns fixed responses. In tests, responses are given in code (per restaurant ID, or a function, or an exception to raise). From the CLI, `--mock-responses FILE` loads a JSON file `{restaurant_id: response}`. A response can be a model-output object, `{"raw": "<text>"}` (to simulate unparseable output) or `{"error": "<message>"}` (to simulate a failed call). A restaurant not in the file gets an empty analysis (no pain points). The mock records every request, so tests can assert that it was or was not called (TC-E06, TC-I07, TC-V02, TC-V09).
  - **`ollama`**: `POST {host}/api/chat` with `stream: false`, `format: <json_schema>` (Ollama's structured output), `options: {temperature: 0, seed: 42, num_ctx: 8192}`. Default host `http://localhost:11434`. A connection error, HTTP error or timeout raises `LLMError` with a hint to start Ollama or pull the model.
- **Rationale**: The owner wants no paid API to be a precondition. `mock` covers L1–L2 tests and pipeline development; Ollama runs a local model with no API key. `temperature: 0` and a fixed seed reduce run-to-run variation (v1 runs each case once, constitution VI). The largest prompt (R06: 37 reviews, about 14 words each, plus 21 categories with definitions, signals and exclusions) is roughly 4–5k tokens, so `num_ctx: 8192` is enough; Ollama's smaller default context would silently truncate the prompt.
- **Alternatives**: Ollama's OpenAI-compatible endpoint (also works, but the native endpoint has first-class JSON-schema `format`); llama.cpp server directly (more setup for the owner).

## R5. Default local model

- **Decision**: Default model `qwen3:8b`, overridable by configuration. The final default is confirmed by the owner after the first real evaluation run (see Open items in the plan).
- **Rationale**: An 8B instruction model with good JSON-schema adherence fits the development machine (16 GB RAM, Intel CPU, no GPU acceleration). Smaller models (≤ 3B) are faster but weaker at fine-grained classification with exclusions.
- **Expected speed**: CPU-only inference of an 8B model is slow — roughly a few minutes per restaurant, so a full evaluation of 13 eligible restaurants may take about an hour. Closed and chain restaurants (R10, R11) never call the model. This is acceptable for v1 (one run per checkpoint) and is stated in the quickstart.
- **Alternatives**: `llama3.1:8b` (widely used, similar size; can be selected with `--model`); a smaller model for faster development runs (selectable the same way; quality is measured by the evaluation).

## R6. Configuration

- **Decision**: Resolution order: CLI flag > environment variable > default.

  | Setting | CLI flag | Environment variable | Default |
  |---|---|---|---|
  | Provider | `--provider` | `PITCH_AGENT_LLM_PROVIDER` | `ollama` |
  | Model | `--model` | `PITCH_AGENT_LLM_MODEL` | `qwen3:8b` for `ollama`, `mock` for `mock` |
  | Ollama host | — | `OLLAMA_HOST` | `http://localhost:11434` |
  | Request timeout (s) | — | `PITCH_AGENT_LLM_TIMEOUT` | `900` |

  No `.env` loading by the application; no setting is a secret in v1.
- **Rationale**: Switching provider or model must not require code changes. Environment variables let the owner set a model once per shell. No API key exists in v1, so nothing secret needs handling.
- **Alternatives**: a config file (`pitch-agent.toml`) — more machinery than four settings need; reading `.env` — not needed and the project forbids tools from reading it.

## R7. What the model does and does not do

- **Decision**: One model call per eligible restaurant. The model receives:
  - the restaurant's name and city;
  - its reviews as `review_id` + `text` only (no dates, ratings, platform, URL or reviewer data);
  - the category list with `category_id`, `definition`, `example_signals`, `exclusions` and the `rules` text from the mapping file — but **not** `product_ids` or `catalog_reference`.

  It returns: a short restaurant description, pain points (category, description, evidence as `review_id` + `quote`), an opening pitch, discovery questions linked to pain points, and general questions linked to categories (used only when there are no pain points).

  Everything else is computed by rule: `text_source` (looked up from the review), confidence (FR-011), merging of same-category pain points (FR-008), candidates, support counts, ranking, prerequisites, decision, decision reasons.
- **Rationale**: FR-013a says the model classifies and extracts evidence but never decides products, so it is not shown the mapping. Leaving out dates enforces FR-019 by construction. Leaving out ratings avoids classifying by star score instead of text (some ratings are imputed). Leaving out reviewer data enforces FR-005.
- **Constrained output**: the JSON schema sent to the provider lists the restaurant's review IDs and the category IDs as `enum`s, which steers Ollama toward valid values. The core parser does **not** enforce those enums: a value outside them (e.g. from the mock or another provider) passes through and fails deterministic checks 2, 4 or 16, as the spec requires (Edge cases; TC-I03, TC-I04, TC-I09).
- **Alternatives**: two calls (classify, then write pitch and questions) — better separation, but doubles CPU time on the local model; can be revisited if the evaluation shows the single call is weak.

## R8. Generation failure vs. rule-breaking output

- **Decision**: `GenerationError` is raised only when the provider raises `LLMError`, the text is not valid JSON, or the JSON does not have the required shape (required keys present, correct types). Anything that parses with the right shape becomes a card "as returned": unknown categories, unknown or foreign review IDs, non-verbatim quotes, pain points with no evidence, questions linked to an unknown pain point. The agent does not drop or repair them; the deterministic checks report them.
- **Rationale**: Clarification Q6 / Edge cases: only unparseable output or a failed call is a generation failure; other problems must stay visible in the evaluation.
- **Consequences**:
  - A cited review that does not belong to the restaurant gets `text_source: null` (the agent only loads the restaurant's own reviews, FR-003), so checks 4 and 5 fail; a non-existent review also fails check 2.
  - A pain point with no evidence gets `confidence: null` and fails check 1 (TC-C05: "not allowed on a card").
  - Unknown categories produce no candidate products (they are not in the table).
- **Model suggestions for products** (TC-S06): any extra keys in the model output, such as product suggestions, are ignored by the parser.

## R9. Card format

- **Decision**: The structured card (FR-023) is a JSON object with a `schema_version`; its shape is in [contracts/visit-card.md](contracts/visit-card.md). In memory it is a set of dataclasses with `to_dict()` / `from_dict()`. The deterministic checks take the **dict** form, so check 1 can report structural problems in any card file, not only in cards the agent built.
- Sections that do not apply are represented by empty lists or `null`; the wording ("Not applicable", "No products recommended", "insufficient evidence", "Reviews not analysed", "Not based on reviews") is produced by the plain-text renderer from fixed strings, so it is identical on every card.
- Product names on the card come from the catalog `name` field. The card contains no model-written product descriptions, so FR-014 (consistency with official facts) holds by construction for the product section; the opening pitch is still reviewed by a human (SC-006).
- **Alternatives**: rendering text first and parsing it for checks (fragile); a JSON Schema validator library (dependency; check 1 is simple enough to write test-first).

## R10. Catalog frontmatter

- **Decision**: Parse the block between the first two `---` lines as flat `key: value` pairs; ignore the markdown body. Only `*.md` files in `data/products/` are products (TC-D06). Required keys: `product_id`, `name`, `category`; optional `requires`. Unknown `requires` targets are a load error (TC-D07).
- **Rationale**: All six catalog files use flat frontmatter; a 15-line parser is simpler than a YAML dependency and is tested first.
- **Alternatives**: `PyYAML` (dependency for a trivial format).

## R11. Repeatable category

- **Decision**: A category whose `product_ids` list is empty may appear in several pain points; any other category may appear once (merge rule and check 18). In the real table the only such category is `other_unmapped`; in fixtures it is `c_none` (TC-K18b). A category that is not in the table is never merged either: the card keeps the model output as returned and check 16 reports it (TC-C11).
- **Rationale**: FR-008 is phrased as "a category with mapped products appears at most once". Deriving the rule from the table avoids hard-coding a category name and makes fixtures work unchanged.

## R12. Evaluation output and run metadata

- **Decision**: `pitch-agent eval` writes one directory per run, `runs/<UTC timestamp>/`, containing:
  - `report.md` (for people);
  - `report.json` (for comparing runs);
  - `cards/<restaurant_id>.json` and `cards/<restaurant_id>.txt`.

  `runs/` is git-ignored; the owner commits a run deliberately when needed.

  The run metadata records:
  - the git commit (`git rev-parse HEAD`);
  - a `dirty` flag (`git status --porcelain` is not empty);
  - `provider` and `model` taken from the `LLMClient` actually used;
  - the run date (UTC);
  - the gold-label file path and its SHA-256.

  If `git` is unavailable, the commit is recorded as `unknown`.
- **Rationale**: FR-032 (commit, provider, model, date, cards included). The dirty flag and label hash make runs comparable when uncommitted changes exist. Keeping runs out of git by default avoids large commits on every run.
- **Alternatives**: committing every report (history noise); a single overwritten report file (loses comparisons).

## R13. Data access boundaries

- **Decision**: The agent package receives a `data_dir` and reads only `data_dir/processed/restaurants.csv`, `data_dir/processed/reviews.csv` and `data_dir/products/`. Gold-label reading lives in `pitch_agent/evaluation/`, which imports the agent; the agent never imports the evaluation package. Reviewer identity columns are not present in processed data; the loader keeps only the documented review fields (FR-005).
- **Rationale**: Constitution V and FR-002; TC-D13 runs the agent on a copy of `data/` without `raw/` and `eval/`.

## R14. Test organisation

- **Decision**: `pytest` with three folders matching the test layers:
  - `tests/unit/` (L1);
  - `tests/pipeline/` (L2, agent and evaluation with the mock);
  - `tests/regression/` (L3, real files in `data/`, no model calls).

  The fixtures FX-CAT, FX-MAP, FX-RST and FX-REV are files under `tests/fixtures/data/`, laid out like the real `data/` folder. Each test function's name or docstring carries its case ID (e.g. `test_tc_r05_tie_broken_by_product_id`). The tests never call a real model; L4 runs only through `pitch-agent eval`.
- **Rationale**: Case IDs from [test-cases.md](test-cases.md) map one-to-one to tests, so `/speckit-tasks` can reference them and the owner can trace coverage.
