---

description: "Task list for the Restaurant Visit Card Agent"
---

# Tasks: Restaurant Visit Card Agent

**Input**: Design documents from `specs/001-visit-card-agent/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [test-cases.md](test-cases.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: Required. Constitution Principle VI and plan.md require test-first development for all deterministic logic. Every test task references the case IDs from [test-cases.md](test-cases.md) and comes before its implementation task. Write the test, run it and confirm it fails (red), then implement (green). Test function names carry the case ID, e.g. `test_tc_r05_tie_broken_by_product_id` (research R14).

**Organization**: Phases follow the suggested implementation phases in plan.md. Story phases are labelled with the user story they deliver: US1 = Generate a visit card (P1), US2 = No recommendation (P1), US3 = Evaluation (P2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story the task belongs to (US1, US2, US3)
- Field rules are cited as `data-model.md` `Entity.field`; they are not repeated here

## Path Conventions

Single project, `src/` layout (plan.md "Project Structure"): package `src/pitch_agent/`, tests in `tests/unit/` (L1), `tests/pipeline/` (L2), `tests/regression/` (L3), fixtures in `tests/fixtures/`.

## Checkpoint rule (applies to every phase)

At each **Checkpoint**: run `uv run pytest` (all tests must pass), stop, wait for the owner's review, and propose a commit message that references the task IDs of the phase (e.g. `feat: add loaders and rules (T010-T027)`). Do not start the next phase before the owner approves.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, package skeleton and the synthetic fixtures FX-* from test-cases.md

- [X] T001 Create `pyproject.toml` at the repository root: `uv` project `pitch-agent`, `requires-python = ">=3.12"`, no runtime dependencies (research R2), dev dependency group with `pytest` only, `src/` layout build config, console script `pitch-agent = "pitch_agent.cli:main"`, and `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
- [X] T002 Create the package skeleton with empty modules: `src/pitch_agent/__init__.py`, `src/pitch_agent/{cli,config,models,loaders,rules,analysis,agent,render,checks}.py`, `src/pitch_agent/llm/__init__.py`, `src/pitch_agent/llm/{factory,mock,ollama}.py`, `src/pitch_agent/evaluation/__init__.py`, `src/pitch_agent/evaluation/{labels,metrics,runner,report}.py`, and test folders `tests/unit/`, `tests/pipeline/`, `tests/regression/` (plan.md "Source Code")
- [X] T003 [P] Add `runs/` to `.gitignore` (research R12)
- [X] T004 [P] Create fixture FX-RST in `tests/fixtures/data/processed/restaurants.csv` with the same header as `data/processed/restaurants.csv` (`restaurant_id,name,city,address,status,segment`) and rows F01–F06 exactly as in test-cases.md "FX-RST"
- [X] T005 [P] Create fixture FX-REV in `tests/fixtures/data/processed/reviews.csv` with the same header as `data/processed/reviews.csv` (`review_id,restaurant_id,text,text_source,review_date,date_imputed,rating,rating_imputed,platform,source_url`) and the 9 reviews from test-cases.md "FX-REV"; F01-006 text contains a real line break inside a quoted CSV field
- [X] T006 [P] Create fixture FX-CAT in `tests/fixtures/data/products/`: six files `dish-pay.md`, `dish-pos.md`, `dish-professional-order.md`, `dish-professional-reservation.md`, `dish-ai-phone-assistant.md`, `dish-starter.md`, each with flat frontmatter `product_id`, `name`, `category` and (only for `dish-ai-phone-assistant`) `requires: dish-professional-reservation`, followed by a short markdown body (test-cases.md "FX-CAT")
- [X] T007 [P] Create fixture FX-MAP in `tests/fixtures/data/products/pain-point-product-mapping.json` with the same top-level shape as the real file (`schema_version`, `categories`, `rules`) and the 9 categories of test-cases.md "FX-MAP", each with `category_id`, `definition`, `product_ids`, `example_signals`, `exclusions`
- [X] T008 Create `tests/conftest.py` with fixtures `fixture_data_dir` (`tests/fixtures/data`), `real_data_dir` (`data`), `tmp_data_dir` (a copy of the fixture data in `tmp_path` that tests may modify) and a helper `model_output(...)` that builds a model-output dict in the shape of [contracts/model-output.md](contracts/model-output.md)
- [X] T009 Run `uv sync` (from `pyproject.toml`) and `uv run pytest` and confirm the empty suite runs without errors

**Checkpoint**: Setup complete — run all tests, stop for owner review, propose a commit message (T001–T009).

---

## Phase 2: Foundational (Blocking Prerequisites, L1)

**Purpose**: Data types, loaders (section A), quote check (section H) and the rule functions (sections C–G) that every story depends on. All steps 4–10 of the card derivation pipeline in data-model.md are pure functions developed test-first here.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Data types

- [ ] T010 Define frozen dataclasses for the input entities in `src/pitch_agent/models.py`: `Restaurant` (data-model.md `Restaurant.restaurant_id`, `Restaurant.name`, `Restaurant.city`, `Restaurant.address`, `Restaurant.status`, `Restaurant.segment`, with derived `is_closed`, `is_chain`, `eligible`), `Review` (data-model.md `Review.review_id`, `Review.restaurant_id`, `Review.text`, `Review.text_source`, `Review.review_date`, `Review.date_imputed`, `Review.rating`, `Review.rating_imputed`, `Review.platform`, `Review.source_url`), `Product` (data-model.md `Product.product_id`, `Product.name`, `Product.category`, `Product.requires`), `PainPointCategory` (data-model.md `PainPointCategory.category_id`, `PainPointCategory.definition`, `PainPointCategory.product_ids`, `PainPointCategory.example_signals`, `PainPointCategory.exclusions`, `PainPointCategory.catalog_reference`, with derived `repeatable`), and a `Mapping` container holding the categories and the top-level `rules` object
- [ ] T011 Define the card dataclasses in `src/pitch_agent/models.py` with `to_dict()` / `from_dict()` producing exactly the JSON keys of [contracts/visit-card.md](contracts/visit-card.md): `VisitCard` (data-model.md `VisitCard.schema_version`, `VisitCard.restaurant`, `VisitCard.decision`, `VisitCard.decision_reasons`, `VisitCard.pain_points`, `VisitCard.recommendations`, `VisitCard.candidates_not_selected`, `VisitCard.opening_pitch`, `VisitCard.discovery_questions`), `RestaurantSummary` (data-model.md `RestaurantSummary.restaurant_id`, `RestaurantSummary.name`, `RestaurantSummary.city`, `RestaurantSummary.status`, `RestaurantSummary.segment`, `RestaurantSummary.reviews_analysed`, `RestaurantSummary.description`), `PainPoint` (data-model.md `PainPoint.pain_point_id`, `PainPoint.category_id`, `PainPoint.description`, `PainPoint.confidence`, `PainPoint.evidence`), `Evidence` (data-model.md `Evidence.review_id`, `Evidence.quote`, `Evidence.text_source`), `Recommendation` (data-model.md `Recommendation.product_id`, `Recommendation.name`, `Recommendation.role`, `Recommendation.required_by`, `Recommendation.pain_point_ids`, `Recommendation.supporting_review_ids`, `Recommendation.support_count`, `Recommendation.confidence`), `Candidate` (data-model.md `Candidate.product_id`, `Candidate.confidence`, `Candidate.support_count`, `Candidate.pain_point_ids`), `DiscoveryQuestion` (data-model.md `DiscoveryQuestion.question`, `DiscoveryQuestion.pain_point_id`, `DiscoveryQuestion.category_id`, `DiscoveryQuestion.based_on_reviews`), and `CheckResult` (data-model.md `CheckResult.check_id`, `CheckResult.passed`, `CheckResult.reasons`)

### Data loading (section A)

- [ ] T012 [P] Write tests TC-D01–TC-D12 and TC-D15–TC-D19 in `tests/unit/test_loaders.py` against `fixture_data_dir`; TC-D02 expects `UnknownRestaurantError`; TC-D06 adds a `.DS_Store` file to `tmp_data_dir`; TC-D07, TC-D09, TC-D10, TC-D11 modify files in `tmp_data_dir` and expect `LoadError` naming the offending product or category; TC-D12 checks that extra fields do not change the mapped product IDs; TC-D15–TC-D19 modify `restaurants.csv` / `reviews.csv` in `tmp_data_dir` and expect `LoadError` naming the file, row and reason. Confirm they fail
- [ ] T013 Implement `src/pitch_agent/loaders.py` until T012 passes: `load_restaurants` (FR-002a: validates required data-model.md `Restaurant.restaurant_id`, `Restaurant.name`, `Restaurant.city`, `Restaurant.status`, `Restaurant.segment`, `Restaurant.restaurant_id` uniqueness, allowed `Restaurant.segment` values), `get_restaurant` (raises `UnknownRestaurantError`), `load_reviews` (FR-002a: validates required data-model.md `Review.review_id`, `Review.restaurant_id`, `Review.text`, `Review.text_source`, `Review.platform`, `Review.source_url`, `Review.review_id` uniqueness, allowed `Review.text_source` values, `Review.restaurant_id` in the restaurants; dates and ratings not validated) and `reviews_for(restaurant_id)` (FR-003; keeps only the fields of data-model.md `Review.*`, FR-005), `load_catalog` (flat frontmatter parser, `*.md` only, research R10; validates data-model.md `Product.product_id` uniqueness, required `Product.name` / `Product.category`, and `Product.requires` against the catalog), `load_mapping` (validates data-model.md `PainPointCategory.category_id` uniqueness, required `PainPointCategory.definition` and `PainPointCategory.product_ids`, every product ID in the catalog), and `load_agent_data(data_dir)` that reads only `data_dir/processed/` and `data_dir/products/` (research R13)

### Quote check (section H)

- [ ] T014 [P] Write tests TC-Q01–TC-Q13 in `tests/unit/test_quote_check.py` for a function `quote_is_verbatim(quote, review_text) -> (bool, reason)`. Confirm they fail
- [ ] T015 Implement `quote_is_verbatim` in `src/pitch_agent/checks.py` until T014 passes: whitespace trim and collapse in both strings, exact case- and punctuation-sensitive substring, at least 3 whitespace-separated words (data-model.md `Evidence.quote`; FR-025 check 3)

### Rules (sections C–G)

- [ ] T016 [P] Write tests TC-C01–TC-C07 and TC-C10 in `tests/unit/test_rules_confidence.py` for pain-point confidence and product confidence; TC-C05 expects `confidence` None for a pain point with no evidence (it then fails check 1, see T033); TC-C10 checks that such a pain point does not count toward a product (FR-012). Confirm they fail
- [ ] T017 [P] Write rule-level tests TC-C08 and TC-C09 in `tests/unit/test_rules_merge.py` for `merge_pain_points`: same non-repeatable category merged with evidence concatenated in order and refs remapped; `c_none` kept as separate pain points; IDs `PP1..n` in order of first appearance. Confirm they fail
- [ ] T018 [P] Write tests TC-S01–TC-S05 and TC-S07 in `tests/unit/test_rules_candidates.py` for `build_candidates`. Confirm they fail
- [ ] T019 [P] Write tests TC-R01–TC-R08 in `tests/unit/test_rules_ranking.py` for `rank_and_select` (input: candidates; output: primaries in rank order and candidates not selected). Confirm they fail
- [ ] T020 [P] Write tests TC-P01–TC-P07 in `tests/unit/test_rules_prerequisites.py` for `add_prerequisites`, including TC-P06 (each product at most once across primary and prerequisite entries). Confirm they fail
- [ ] T021 [P] Write rule-level tests TC-DEC01, TC-DEC02 and TC-DEC05 in `tests/unit/test_rules_decision.py` for `decide` (decision and decision reasons from the selected primaries). Confirm they fail
- [ ] T022 Implement `merge_pain_points`, `attach_text_source` and `pain_point_confidence` in `src/pitch_agent/rules.py` until T016 (pain-point part) and T017 pass (data-model.md `PainPoint.pain_point_id`, `PainPoint.description`, `PainPoint.confidence`, `Evidence.text_source`; repeatability from `PainPointCategory.product_ids`, research R11)
- [ ] T023 Implement `build_candidates` and product confidence in `src/pitch_agent/rules.py` until T016 (product part) and T018 pass (data-model.md `Recommendation.pain_point_ids`, `Recommendation.supporting_review_ids`, `Recommendation.support_count`, `Recommendation.confidence`; FR-013a, FR-012; pain points without evidence ignored, FR-012)
- [ ] T024 Implement `rank_and_select` in `src/pitch_agent/rules.py` until T019 passes: sort key (confidence desc, support count desc, `product_id` asc), top 2 primary, rest as data-model.md `Candidate.*` (FR-015a)
- [ ] T025 Implement `add_prerequisites` in `src/pitch_agent/rules.py` until T020 passes: data-model.md `Recommendation.role`, `Recommendation.required_by`, `Recommendation.pain_point_ids` (union for prerequisites), `Recommendation.confidence` (from the requiring product); remove the prerequisite from candidates not selected; order primaries then prerequisites by `product_id` (contracts/visit-card.md)
- [ ] T026 Implement `decide` in `src/pitch_agent/rules.py` until T021 passes (data-model.md `VisitCard.decision`, `VisitCard.decision_reasons`; FR-020, FR-021)

**Checkpoint**: Foundation ready — run all tests, stop for owner review, propose a commit message (T010–T026).

---

## Phase 3: User Story 2 — No recommendation: short cards, plain text and checks (Priority: P1)

**Goal**: Closed and chain restaurants get a short `no_recommendation` card by rule, without a model call. This phase also delivers the plain-text renderer and the 18 deterministic checks, which every later card (US1) and the evaluation (US3) reuse.

**Independent Test**: `generate_card` for F02, F03, F04 (fixtures) and R10, R11 (real data) returns a short card with the correct reason(s), the stub model is never called, the plain text shows "Not applicable" and "Reviews not analysed", and all 18 checks pass.

### Short cards (section B)

- [ ] T027 [P] [US2] Write tests TC-E01–TC-E07 in `tests/unit/test_short_cards.py`, plus TC-D02 at agent level (unknown ID → `UnknownRestaurantError`, no card); TC-E06 passes an inline stub LLM whose `generate` fails the test if called. Confirm they fail
- [ ] T028 [US2] Implement `build_short_card(restaurant)` and `generate_card(restaurant_id, data, llm)` in `src/pitch_agent/agent.py` until T027 passes, covering only the unknown-ID and closed/chain branches; the eligible branch is completed in T046 (data-model.md `RestaurantSummary.reviews_analysed` and `RestaurantSummary.description` null, `VisitCard.decision_reasons` codes, `VisitCard.opening_pitch` null, empty lists; FR-020a)

### Plain-text card (section J)

- [ ] T029 [P] [US2] Write tests TC-T01–TC-T09 in `tests/unit/test_render.py`, building the input card dicts in the tests (a valid F01 `recommend` card with a prerequisite and a candidate not selected, an `insufficient_evidence` card, an F02 short card, a card with general questions). Confirm they fail
- [ ] T030 [US2] Implement `render_text(card)` in `src/pitch_agent/render.py` until T029 passes, following the plain-text layout and fixed wording of [contracts/visit-card.md](contracts/visit-card.md) (labels from data-model.md `DiscoveryQuestion.based_on_reviews` and `Recommendation.required_by`; no review dates or reviewer data)

### Deterministic checks 1–18 (section I)

- [ ] T031 [P] [US2] Create the valid F01 card used by the check tests in `tests/fixtures/cards/valid_f01.json` (decision `recommend`, all 18 checks pass by construction, matches contracts/visit-card.md)
- [ ] T032 [US2] Write tests TC-K00–TC-K19 in `tests/unit/test_checks.py` for `run_checks(card_dict, data) -> list[CheckResult]`, deriving each failing card from `valid_f01.json` (or a short card for TC-K08*); TC-K17d covers a pain point without evidence (FR-025 item 17); TC-K03 reuses section H through check 3. Confirm they fail
- [ ] T033 [US2] Implement check 1 (structure: all keys of contracts/visit-card.md present, valid data-model.md `VisitCard.decision`, `PainPoint.confidence`, `Recommendation.role`, `PainPoint.evidence` non-empty) and the `run_checks` driver in `src/pitch_agent/checks.py`: all 18 checks always run; a check that cannot read a field reports "not evaluated: invalid structure" (data-model.md `CheckResult.check_id`, `CheckResult.reasons`; TC-K19)
- [ ] T034 [US2] Implement checks 2–9 in `src/pitch_agent/checks.py` (evidence against the review dataset, catalog and `requires`, closed/chain and decision rules; FR-025 items 2–9) until their T032 tests pass
- [ ] T035 [US2] Implement checks 10–18 in `src/pitch_agent/checks.py` (confidence, primary/prerequisite limits, question links, support counts, rank order, candidates, category membership, mapping coverage, category repetition; FR-025 items 10–18) until all T032 tests pass

### Real-data short cards (section O, part)

- [ ] T036 [P] [US2] Write tests TC-X04 and TC-X05 in `tests/regression/test_real_short_cards.py`: `generate_card` for R10 and R11 with `real_data_dir` and a stub LLM that fails if called; the card passes all 18 checks. They should pass with T028–T035 in place

**Checkpoint**: Short cards, plain text and checks work — run all tests, stop for owner review, propose a commit message (T027–T036).

---

## Phase 4: User Story 1 — Generate a visit card with the mock model (Priority: P1) 🎯 MVP

**Goal**: For an eligible restaurant, one model call (mock provider) produces a full card: merged pain points with verbatim evidence, rule-derived products, pitch and questions; the `card` command prints it as text or JSON. The insufficient-evidence path of US2 is completed here because it runs through the same pipeline.

**Independent Test**: `uv run pitch-agent card R03 --provider mock --mock-responses tests/fixtures/mock_responses/r03.json` prints a card with all six sections; TC-I01–TC-I09 pass.

### LLM interface and configuration

- [ ] T037 [P] [US1] Write configuration tests in `tests/unit/test_config.py` (plan.md design tests, no case ID): CLI flag > environment variable > default for provider and model (research R6), default model per provider (`qwen3:8b` / `mock`), `create_llm` with an unknown provider raises `ConfigError` listing the available providers. Confirm they fail
- [ ] T038 [US1] Implement `LLMRequest`, `LLMClient` (protocol), `LLMError`, `LLMConfig` and `ConfigError` in `src/pitch_agent/llm/__init__.py` per [contracts/llm-interface.md](contracts/llm-interface.md)
- [ ] T039 [US1] Implement `MockLLM` in `src/pitch_agent/llm/mock.py` per contracts/llm-interface.md "mock": mapping, callable or JSON file input; `{"raw": …}` and `{"error": …}` responses; empty-analysis default; `calls` list; `provider = model = "mock"`
- [ ] T040 [US1] Implement `resolve_llm_config(...)` in `src/pitch_agent/config.py` and the registry plus `create_llm` in `src/pitch_agent/llm/factory.py` (registry `{"mock": MockLLM}`; `ollama` is added in T052) until T037 passes
- [ ] T041 [US1] Add mock helpers to `tests/conftest.py`: a `mock_llm` fixture factory taking `{restaurant_id: response}` and a `failing_llm` stub that fails the test if called

### Model input and output (analysis)

- [ ] T042 [P] [US1] Write tests in `tests/unit/test_analysis.py`: prompt contents (plan.md design test: only the requested restaurant's reviews as `review_id` + `text`; no dates, ratings, platform, URL, product IDs or `catalog_reference`; JSON schema enums for category and review IDs, research R7), and the parsing rules table of [contracts/model-output.md](contracts/model-output.md) including TC-S06 (extra product suggestions ignored) and TC-I05 at parser level (invalid JSON or wrong shape → `GenerationError`). Confirm they fail
- [ ] T043 [US1] Implement `build_request(restaurant, reviews, mapping) -> LLMRequest` and `parse_model_output(text) -> ModelAnalysis` with `GenerationError` in `src/pitch_agent/analysis.py` until T042 passes (data-model.md `ModelAnalysis.restaurant_description`, `ModelAnalysis.pain_points`, `ModelAnalysis.opening_pitch`, `ModelAnalysis.discovery_questions`, `ModelAnalysis.general_questions`; enums not enforced by the parser, research R8)

### Agent pipeline (section K)

- [ ] T044 [P] [US1] Write pipeline tests in `tests/pipeline/test_agent_pipeline.py` with the mock: TC-I01, TC-I02, TC-I03, TC-I04, TC-I05, TC-I06, TC-I07, TC-I09, TC-C08 and TC-C09 (pipeline level), TC-E08, TC-D13 (copy of fixture data without `raw/` and `eval/`) and TC-D14 (structured and plain-text card contain no reviewer fields); TC-I01–TC-I04 and TC-I09 also run `run_checks` on the card. Confirm they fail
- [ ] T045 [P] [US2] Write pipeline tests for the insufficient-evidence path in `tests/pipeline/test_agent_insufficient.py`: TC-DEC02 (pipeline level), TC-DEC03, TC-DEC04 (F05, 0 reviews analysed) and TC-I08 (all checks pass). Confirm they fail
- [ ] T046 [US1] Complete the eligible branch of `generate_card` in `src/pitch_agent/agent.py` until T044 and T045 pass: steps 1–12 of the card derivation pipeline in data-model.md, wrapping `LLMError` in `GenerationError`; set data-model.md `RestaurantSummary.reviews_analysed` and `RestaurantSummary.description`; translate model refs to `PPn` for data-model.md `DiscoveryQuestion.pain_point_id` (unmatched refs kept as given); use general questions (data-model.md `DiscoveryQuestion.category_id`, `DiscoveryQuestion.based_on_reviews` false) and `VisitCard.opening_pitch` null only when there are no pain points (FR-017a)

### `card` command

- [ ] T047 [P] [US1] Create the mock response file `tests/fixtures/mock_responses/r03.json` for the real restaurant R03 (`{"R03": <model output>}`), with quotes copied verbatim from R03 reviews in `data/processed/reviews.csv` (used by quickstart step 3 and T048)
- [ ] T048 [US1] Write CLI tests in `tests/pipeline/test_cli_card.py` for [contracts/cli.md](contracts/cli.md) `card`: exit 0 with text card on stdout; `--format json` output parses and passes `run_checks`; `--output PATH`; unknown ID → `Unknown restaurant: <id>` on stderr, exit 2, nothing on stdout; generation failure → `Generation failed for <id>: <reason>`, exit 1, no partial card; load error → exit 2; unknown provider → usage error. Use `--data-dir` with the fixtures and `--provider mock --mock-responses`. Confirm they fail
- [ ] T049 [US1] Implement `main()` with `argparse` in `src/pitch_agent/cli.py`: common options (`--data-dir`, `--provider`, `--model`, `--mock-responses`) and the `card` subcommand (`--format`, `--output`) with the exit codes of contracts/cli.md, until T048 passes

**Checkpoint**: MVP — full card with the mock works end to end. Run all tests and quickstart steps 1–3 (`card` commands only), stop for owner review, propose a commit message (T037–T049).

---

## Phase 5: User Story 1 — Ollama provider (Priority: P1)

**Goal**: The agent runs against a local model with no API key, selected by configuration only.

**Independent Test**: Tests against a local stub HTTP server pass; no real model is needed for automated tests.

- [ ] T050 [P] [US1] Write tests in `tests/unit/test_ollama.py` (plan.md design test, no case ID) using a stub HTTP server from `http.server` on a free local port: request body (`model`, system + user `messages`, `format` = `json_schema`, `stream: false`, `options` `{temperature: 0, seed: 42, num_ctx: 8192}`); returns `message.content`; connection refused, HTTP ≥ 400, timeout and missing `message.content` raise `LLMError` whose message names the host and model and suggests `ollama serve` / `ollama pull <model>`. Confirm they fail
- [ ] T051 [US1] Implement `OllamaLLM` in `src/pitch_agent/llm/ollama.py` with `urllib.request` per contracts/llm-interface.md "ollama"; host from `OLLAMA_HOST` (default `http://localhost:11434`), timeout from `PITCH_AGENT_LLM_TIMEOUT` (default 900 s), research R4, R6; until T050 passes
- [ ] T052 [US1] Register `ollama` in `src/pitch_agent/llm/factory.py` and extend `tests/unit/test_config.py` so the default provider resolves to `ollama` with model `qwen3:8b`
- [ ] T053 [US1] Manual smoke run (owner, not automated), following `specs/001-visit-card-agent/quickstart.md`: install Ollama and pull `qwen3:8b` (quickstart step 4), then run `uv run pitch-agent card R03` and check that a card is printed; with Ollama stopped, check the error message of quickstart "Troubleshooting"

**Checkpoint**: Ollama provider ready — run all tests, stop for owner review (including the T053 smoke result), propose a commit message (T050–T053).

---

## Phase 6: User Story 3 — Evaluation (Priority: P2)

**Goal**: `pitch-agent eval` validates the gold labels, runs the agent once per labelled restaurant, runs all 18 checks, computes SC-001 – SC-005 and writes a run folder with report.json, report.md and cards.

**Independent Test**: `uv run pitch-agent eval --provider mock --mock-responses tests/fixtures/mock_responses/all.json` writes `runs/<timestamp>/` with all sections of [contracts/evaluation-report.md](contracts/evaluation-report.md), including provider `mock` and model `mock`; TC-V01–TC-V09 pass.

### Gold labels (section L)

- [ ] T054 [P] [US3] Create gold-label fixtures in `tests/fixtures/labels/` for TC-G01–TC-G12 and TC-V01–TC-V09 (header `restaurant_id,decision,must_include,acceptable,rationale`; one file per invalid case, one file with three invalid rows for TC-G11, one valid file over F01, F02, F05 for the evaluation tests)
- [ ] T055 [US3] Write tests TC-G01–TC-G12 in `tests/unit/test_labels.py` for `load_gold_labels(path, restaurants, catalog)`. Confirm they fail
- [ ] T056 [US3] Implement `src/pitch_agent/evaluation/labels.py` until T055 passes: `GoldLabel` (data-model.md `GoldLabel.restaurant_id`, `GoldLabel.decision`, `GoldLabel.must_include`, `GoldLabel.acceptable`, `GoldLabel.rationale`), `;`-separated lists, missing columns reject the file, all invalid rows collected as `LabelError(row_number, restaurant_id, reason)` before raising

### Metrics (section M)

- [ ] T057 [P] [US3] Write tests TC-M01–TC-M10 in `tests/unit/test_metrics.py` for `compute_metrics(case_results, restaurants)` using synthetic `CaseResult` values. Confirm they fail
- [ ] T058 [US3] Implement `CaseResult` and `compute_metrics` in `src/pitch_agent/evaluation/metrics.py` until T057 passes (data-model.md `CaseResult.restaurant_id`, `CaseResult.card`, `CaseResult.error`, `CaseResult.checks`, `CaseResult.expected_decision`, `CaseResult.actual_decision`, `CaseResult.recommended_products`, `CaseResult.missed_must_include`, `CaseResult.outside_expected`; metric definitions and targets in data-model.md "Metrics (SC-001 – SC-005)"; output shape of contracts/evaluation-report.md `metrics`)

### Evaluation run (section N)

- [ ] T059 [US3] Write tests TC-V01–TC-V09 in `tests/pipeline/test_evaluation.py` running the evaluation in-process and through `pitch-agent eval` with `--data-dir` fixtures, `--labels` from T054, `--out-dir` in `tmp_path` and the mock (TC-V08 compares SHA-256 of the label file and `data/raw/duesseldorf_reviews.csv` before and after; TC-V09 asserts the mock has no calls, no run folder and exit code 2). Confirm they fail
- [ ] T060 [US3] Implement `run_evaluation(...)` in `src/pitch_agent/evaluation/runner.py`: validate labels first; one `generate_card` call per labelled restaurant; `run_checks` on every card; generation failure → check 1 failed with the error and checks 2–18 failed with the reason "not evaluated: generation failed" (data-model.md `CaseResult.checks`), `actual_decision` = `error`; progress line per restaurant on stderr; `RunMetadata` (data-model.md "RunMetadata": `run_id`, `git_commit` via `git rev-parse HEAD` or `unknown`, `git_dirty`, `provider`, `model` from the `LLMClient`, `run_date`, `labels_path`, `labels_sha256`, `unlabelled_restaurants`)
- [ ] T061 [US3] Implement `write_report(...)` in `src/pitch_agent/evaluation/report.py`: `runs/<YYYYMMDDTHHMMSSZ>/report.json`, `report.md` (five sections in order) and `cards/<id>.json` + `cards/<id>.txt` per [contracts/evaluation-report.md](contracts/evaluation-report.md); nothing written under `data/`
- [ ] T062 [US3] Add the `eval` subcommand (`--labels`, `--out-dir`) to `src/pitch_agent/cli.py` with the outputs and exit codes of contracts/cli.md, until T059 passes
- [ ] T063 [P] [US3] Create `tests/fixtures/mock_responses/all.json` for quickstart step 3, containing at least the R03 response from T047 (restaurants not in the file get the mock's empty analysis)

### Real-data files (section O, rest)

- [ ] T064 [P] [US3] Write tests TC-X01–TC-X03 in `tests/regression/test_real_data_files.py` against `data/products/` and `data/eval/expected.csv`; they should pass with T013 and T056 in place

**Checkpoint**: Evaluation works with the mock — run all tests and quickstart step 3 (`eval`), stop for owner review, propose a commit message (T054–T064).

---

## Phase 7: Polish & Cross-Cutting Concerns (L4 evaluation run)

**Purpose**: Final validation of the whole feature, including the real local-model evaluation and human review

- [ ] T065 Verify the data-access boundary in `src/pitch_agent/`: no module outside `src/pitch_agent/evaluation/` imports `pitch_agent.evaluation`, and no code opens `data/raw/` (constitution V, research R13); fix any violation
- [ ] T066 Run quickstart steps 1–3 from [quickstart.md](quickstart.md) exactly as written and confirm every expected result
- [ ] T067 Run the real evaluation with Ollama (quickstart step 5: `uv run pitch-agent eval`) and check `runs/<timestamp>/report.md` for SC-001 – SC-005 and the recorded git commit, provider and model
- [ ] T068 Owner human review (SC-006) of `runs/<timestamp>/cards/*.txt`: opening pitches from the guests' perspective without blame, no recommendation breaking a product limit in `data/products/`; any agent behaviour change goes through the spec first and is logged in `docs/spec-changes.md`

**Checkpoint**: Feature complete — run all tests, stop for owner review of the evaluation results, propose a commit message (T065–T068); the run folder is committed only if the owner decides so (research R12).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup — blocks all user stories
- **Phase 3 (US2 short cards, render, checks)**: depends on Phase 2
- **Phase 4 (US1 pipeline + US2 insufficient evidence)**: depends on Phase 3 (uses `generate_card`, `render_text`, `run_checks`)
- **Phase 5 (US1 Ollama)**: depends on Phase 4 (LLM interface and factory)
- **Phase 6 (US3 evaluation)**: depends on Phase 4; independent of Phase 5 (all tests use the mock)
- **Phase 7 (Polish / L4)**: depends on Phases 5 and 6

### User Story Dependencies

- **US2 (P1)**: closed/chain path needs only Phase 2; the insufficient-evidence path (T045) needs the US1 pipeline (T046)
- **US1 (P1)**: needs Phase 2 and the renderer/checks from Phase 3
- **US3 (P2)**: needs US1 and US2 (it runs the agent and the checks)

### Within Each Phase

- Each test task comes before its implementation task and must fail first
- Data types before loaders and rules; rules before the agent; agent before the CLI
- Tasks in the same file are sequential (e.g. T022–T026 in `rules.py`, T033–T035 in `checks.py`)

---

## Parallel Examples

### Phase 1

```text
T003 .gitignore | T004 restaurants.csv | T005 reviews.csv | T006 catalog *.md | T007 mapping JSON
```

### Phase 2 (after T010–T011)

```text
Tests in parallel: T012 test_loaders.py | T014 test_quote_check.py | T016 test_rules_confidence.py
                   T017 test_rules_merge.py | T018 test_rules_candidates.py | T019 test_rules_ranking.py
                   T020 test_rules_prerequisites.py | T021 test_rules_decision.py
Implementation in parallel (different files): T013 loaders.py | T015 checks.py | T022–T026 rules.py (sequential)
```

### Phase 3 (US2)

```text
T027 test_short_cards.py | T029 test_render.py | T031 valid_f01.json | T036 test_real_short_cards.py (test file only)
then: T028 agent.py | T030 render.py | T032 → T033 → T034 → T035 checks.py
```

### Phase 4 (US1)

```text
T037 test_config.py | T042 test_analysis.py | T044 test_agent_pipeline.py | T045 test_agent_insufficient.py | T047 r03.json
```

### Phase 6 (US3)

```text
T054 label fixtures | T057 test_metrics.py | T063 all.json | T064 test_real_data_files.py
```

---

## Implementation Strategy

### MVP first

1. Phase 1 Setup → Phase 2 Foundational (checkpoints after each)
2. Phase 3: short cards, plain text and checks (US2 closed/chain) → checkpoint
3. Phase 4: full card with the mock (US1) → **MVP checkpoint**: a rep-style card can be generated for any eligible restaurant from canned model output

### Incremental delivery

1. Phase 5 adds the real local model (Ollama) without touching business logic
2. Phase 6 adds the evaluation command (US3), tested entirely with the mock
3. Phase 7 runs the real evaluation and human review; results decide whether the spec needs changes

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- No test ever calls a real model; L4 runs only through `pitch-agent eval` (research R14)
- Never read `.env`; never modify `data/raw/duesseldorf_reviews.csv` or `data/eval/expected.csv`
- Do not add behaviour beyond spec.md and these tasks; if behaviour must change, update the spec first and log it in `docs/spec-changes.md`
- Plan deviation (minor): TC-X04/TC-X05 run in Phase 3 instead of Phase 4, because short cards and checks are complete there; TC-D02 is also tested at agent level in T027
