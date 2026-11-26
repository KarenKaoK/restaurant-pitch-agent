# Implementation Plan: Restaurant Visit Card Agent

**Branch**: `001-visit-card-agent` (work happens on `main`, by owner practice) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-visit-card-agent/spec.md`; test cases from [test-cases.md](test-cases.md)

## Summary

A command-line agent takes a restaurant ID and produces a visit card for a DISH sales rep. Closed and chain restaurants get a short card by rule, without a model call. For eligible restaurants, one language-model call:
- classifies the restaurant's reviews into the fixed pain-point categories;
- extracts verbatim evidence;
- writes the description, opening pitch and discovery questions.

Everything else is deterministic Python developed test-first: confidence, merging, candidate products from the mapping table, support counts, ranking, prerequisites, decision, plain-text rendering and the 18 deterministic checks. A second command runs the evaluation against `data/eval/expected.csv` and writes a report with SC-001 – SC-005, the git commit, the LLM provider and the model.

The model sits behind a small provider-independent interface. v1 ships a **mock** provider (tests and pipeline development) and an **Ollama** provider (local model, no API key). No paid API is needed to develop, test or run anything.

## Technical Context

**Language/Version**: Python ≥ 3.12 (managed with `uv`; 3.14 available locally) — research R1

**Primary Dependencies**: none at runtime (standard library only, including `urllib` for the Ollama HTTP API); `pytest` for development — research R2

**Storage**: Files only:
- inputs: CSV in `data/processed/`, Markdown frontmatter and JSON in `data/products/`;
- gold labels: `data/eval/expected.csv` (evaluation only);
- outputs: JSON/Markdown/text in `runs/<timestamp>/` (git-ignored).

**Testing**: `pytest`; layers L1 unit (fixtures), L2 pipeline (mock LLM), L3 real-data regression (no model calls); L4 quality via `pitch-agent eval` and human review — research R14

**Target Platform**: macOS developer machine (Intel i5, 16 GB RAM, no GPU acceleration); any OS with Python 3.12+ and optionally Ollama

**Project Type**: CLI application (single project, `src/` layout)

**LLM access**: provider and model are configuration (`--provider/--model`, env `PITCH_AGENT_LLM_PROVIDER/PITCH_AGENT_LLM_MODEL`). v1 providers: `mock` and `ollama` (default model `qwen3:8b`). The interface allows OpenAI, Anthropic or Gemini to be added later without touching business logic — research R3–R6, [contracts/llm-interface.md](contracts/llm-interface.md)

**Performance Goals**: none beyond usability:
- rule-only cards and all tests run in seconds;
- a local-model card takes minutes on CPU;
- one full evaluation fits in roughly an hour (research R5).

**Constraints**:
- no API key or paid service needed;
- the agent reads only `data/processed/` and `data/products/`;
- deterministic logic is developed test-first;
- no reviewer data, review dates or ratings reach the model;
- `temperature: 0` and a fixed seed;
- each evaluation case runs once.

**Scale/Scope**: 15 restaurants (R01–R16 without R14), 250 reviews (max 37 per restaurant), 6 products, 21 categories, 15 gold-label rows

All Technical Context items are resolved; no NEEDS CLARIFICATION remains.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design (below).*

| Principle | How the design complies | Status |
|---|---|---|
| **I. Evidence-Grounded Output** | Every pain point has ≥ 1 evidence item with `review_id`, unchanged `quote` and rule-attached `text_source`. Check 3 verifies quotes verbatim (whitespace-normalised substring, ≥ 3 words); checks 2, 4, 5 verify the cited review. Output that breaks the rules is not repaired: it is reported by the checks. The pitch is instructed to use the guests' perspective; reviewed by a human (SC-006). | ✅ |
| **II. Catalog Fidelity** | Products come only from the mapping table + catalog, computed by rule. The model never sees product IDs. Cards show the catalog `name`, never model-written product descriptions. `requires` is enforced by rule and by check 7. Text limits are checked in human review. No country logic. | ✅ |
| **III. Honest Uncertainty** | Confidence by rule (FR-011). `insufficient_evidence` when no pain point maps to a product. Questions are generated for every pain point. The model never receives review dates. Closed and chain restaurants get a short card by rule (`no_recommendation` + reasons; checks 8, 9). | ✅ |
| **IV. Human in the Loop** | CLI only; no network calls except to the configured local model host; no outward action. The plain-text card states it is a hypothesis, not a decision. Prices are not computed (no price fields used). | ✅ |
| **V. Data Integrity and Privacy** | The agent reads only `processed/` and `products/` (FR-002; TC-D13). Evaluation code lives in a separate package the agent never imports. `data/raw/` is never opened; `eval` writes only under `runs/`. No reviewer data is loaded. No API keys exist in v1; future providers read keys from environment variables only, never logged. The application does not load `.env`. | ✅ |
| **VI. Tested and Reproducible** | TDD for every deterministic module, with tests named after [test-cases.md](test-cases.md) IDs; `tasks.md` will order each test task before its implementation. LLM output is verified by `pitch-agent eval` (one command, one run per case). All 18 FR-025 checks are implemented (a superset of the six in Principle VI). The report records the git commit, the dirty flag, provider, model and date. | ✅ |
| **Scope and Data Constraints** | Runtime uses the standard library only. No features beyond the spec: no extra commands, no live data. A catalog or mapping change stays a separate data commit. | ✅ |
| **Development Workflow** | The spec was updated before this plan for the provider-in-report change and logged in `docs/spec-changes.md`. Implementation will proceed phase by phase with checkpoints. | ✅ |

**Gate result (pre-research)**: PASS — no violations.

**Gate result (post-design)**: PASS. Design choices that touch principles:
- The model's JSON schema restricts category and review IDs. This only guides decoding: values outside the lists are still passed through and caught by the checks, so Principle I/VI visibility is preserved.
- The LLM interface is one protocol with two small implementations, required by the owner for provider switching. It is not an unnecessary abstraction.

## Project Structure

### Documentation (this feature)

```text
specs/001-visit-card-agent/
├── spec.md              # Feature specification
├── test-cases.md        # Behaviour test cases (written before this plan)
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R14
├── data-model.md        # Phase 1: entities, rules, card derivation pipeline
├── quickstart.md        # Phase 1: validation guide
├── contracts/
│   ├── cli.md               # pitch-agent card / eval
│   ├── visit-card.md        # structured JSON + plain-text layout
│   ├── model-output.md      # model input/output contract and parsing rules
│   ├── llm-interface.md     # LLMClient protocol, mock and ollama providers
│   └── evaluation-report.md # run folder, report.json, report.md
├── checklists/requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
pyproject.toml                 # uv project; console script pitch-agent; dev dependency pytest
src/pitch_agent/
├── __init__.py
├── cli.py                     # argparse: card, eval; exit codes (contracts/cli.md)
├── config.py                  # LLM settings: flag > env > default
├── models.py                  # dataclasses: Restaurant, Review, Product, Category, VisitCard, …
├── loaders.py                 # restaurants, reviews, catalog frontmatter, mapping table + validation
├── rules.py                   # merge, confidence, candidates, support, ranking, prerequisites, decision
├── analysis.py                # prompt + JSON schema building; model-output parsing → ModelAnalysis
├── agent.py                   # generate_card(): short card or eligible pipeline
├── render.py                  # plain-text card
├── checks.py                  # quote check + deterministic checks 1–18 on card dicts
├── llm/
│   ├── __init__.py            # LLMClient, LLMRequest, LLMError, LLMConfig
│   ├── factory.py             # registry {mock, ollama}; create_llm()
│   ├── mock.py
│   └── ollama.py
└── evaluation/                # imports the agent; never imported by it
    ├── __init__.py
    ├── labels.py              # gold-label loading + FR-028 validation
    ├── metrics.py             # SC-001 – SC-005
    ├── runner.py              # one agent run per labelled restaurant, checks, run metadata
    └── report.py              # report.json, report.md, card files

tests/
├── conftest.py                # fixture paths, mock LLM helpers
├── fixtures/
│   ├── data/processed/        # FX-RST, FX-REV (restaurants.csv, reviews.csv)
│   ├── data/products/         # FX-CAT (*.md) and FX-MAP (pain-point-product-mapping.json)
│   ├── labels/                # gold-label files for TC-G*, TC-V*
│   └── mock_responses/        # canned model outputs (fixtures and real restaurants)
├── unit/                      # L1: TC-D, E, C, S, R, P, DEC, Q, K, T, G, M
├── pipeline/                  # L2: TC-I (agent + mock), TC-V (evaluation + mock)
└── regression/                # L3: TC-X (real data/, no model)

runs/                          # evaluation output, git-ignored (added to .gitignore in tasks)
```

**Structure Decision**: Single Python project in `src/` layout with one package, `pitch_agent`. The modules follow the derivation pipeline in [data-model.md](data-model.md), so each test-case section maps to one module:
- `loaders.py`: A, L (via `evaluation/labels.py`)
- `agent.py`: B
- `rules.py`: C, D, E, F, G
- `checks.py`: H, I
- `render.py`: J
- `evaluation/metrics.py`: M

The provider code is isolated in `llm/`, and evaluation in `evaluation/`. `scripts/build_processed_data.py` stays outside the package and is not part of this feature.

## Test-case traceability

| Section | Cases | Module(s) | Layer |
|---|---|---|---|
| A Data loading | TC-D01–D19 | `loaders.py`, `agent.py` (D13, D14) | L1 |
| B Eligibility / short cards | TC-E01–E08 | `agent.py` | L1 (mock asserting no call) |
| C Confidence | TC-C01–C10 | `rules.py` (C08, C09 via `agent.py` + mock) | L1 |
| D Candidates / support | TC-S01–S07 | `rules.py`, `analysis.py` (S06) | L1 |
| E Ranking | TC-R01–R08 | `rules.py` | L1 |
| F Prerequisites | TC-P01–P07 | `rules.py` | L1 |
| G Decision | TC-DEC01–05 | `rules.py`, `agent.py` | L1 |
| H Quote check | TC-Q01–Q13 | `checks.py` | L1 |
| I Checks 1–18 | TC-K00–K19 | `checks.py` | L1 |
| J Plain text | TC-T01–T09 | `render.py` | L1 |
| K Pipeline | TC-I01–I09 | `agent.py`, `analysis.py`, `llm/mock.py` | L2 |
| L Gold labels | TC-G01–G12 | `evaluation/labels.py` | L1 |
| M Metrics | TC-M01–M10 | `evaluation/metrics.py` | L1 |
| N Evaluation run | TC-V01–V09 | `evaluation/runner.py`, `report.py`, `cli.py` | L2 |
| O Real data | TC-X01–X05 | all loaders, `agent.py`, `checks.py` | L3 |

The design also adds a few small tests that are not case IDs in test-cases.md. They verify design rules of this plan, and `/speckit-tasks` lists them next to the related cases:
- configuration precedence and unknown providers (`config.py`, `llm/factory.py`);
- the Ollama request body and error mapping, using a local stub HTTP server (no real model);
- the prompt contains only the restaurant's reviews, and no dates, ratings or product IDs (research R7).

## Suggested implementation phases (input for `/speckit-tasks`)

Each phase ends with a checkpoint: all tests pass, then stop for owner review and propose a commit message with task IDs.

1. **Setup**: `pyproject.toml`, package skeleton, pytest config, fixtures FX-*, `runs/` in `.gitignore`.
2. **Foundations (L1)**: models, loaders (A), quote check (H), rules (C, D, E, F, G). Tests first in each case.
3. **Story 2 + card output (L1)**: short cards (B), plain-text rendering (J), deterministic checks (I).
4. **Story 1 pipeline (L2)**: LLM interface, mock provider, analysis parsing, agent orchestration (K); `card` command; L3 short-card regression (TC-X04, X05).
5. **Ollama provider**: request/response mapping tested against a local stub server; a manual smoke run on one restaurant (not part of the automated tests).
6. **Story 3 evaluation (L1/L2)**: gold-label validation (L), metrics (M), runner and report (N), `eval` command; L3 data regression (TC-X01–X03).
7. **Evaluation run (L4)**: real run with Ollama, human review (SC-006), record results. Any agent behaviour change goes through the spec first.

## Owner decisions on open items (2026-11-26)

1. **Run output location**: approved — `runs/<timestamp>/`, git-ignored; a run is committed only on purpose (research R12).
2. **Default local model**: approved — start with `qwen3:8b` on Ollama (research R5). Ollama is not installed on the development machine yet (quickstart step 4). If local runs turn out too slow, the owner will consider adding a cloud API provider; that would be a later spec change, and the LLM interface already allows it without business-logic changes.
3. **Local model quality risk**: accepted — an 8B model on CPU may miss SC-003 – SC-005 or reword quotes (check 3); the evaluation will show this.
4. **Interpretations**: approved —
   - categories with no mapped products may repeat (research R11);
   - a pain point with no evidence is kept and fails check 1 (research R8);
   - general questions are written by the model and labelled by rule (research R7);
   - ratings are not sent to the model (research R7).

## Complexity Tracking

No constitution violations; nothing to justify.
