# Quickstart: Restaurant Visit Card Agent

How to check that the feature works, from tests to a real local-model evaluation. No API key is needed at any step. Commands, options and outputs are defined in [contracts/](contracts/); this guide only lists what to run and what to expect.

## Prerequisites

| Need | For | Check |
|---|---|---|
| Python ≥ 3.12 and `uv` | everything | `uv --version` |
| Ollama + a local model | steps 4–5 only | `ollama --version`, `ollama list` |

Steps 1–3 need no model at all.

## 1. Install and run the automated tests (L1–L3)

```bash
uv sync
uv run pytest
```

Expected: all tests pass. The tests use the fixtures in `tests/fixtures/` and the mock provider; they never call Ollama. Test names carry the case IDs from [test-cases.md](test-cases.md), e.g. `uv run pytest -k tc_r05`.

## 2. Rule-only cards (no model involved)

```bash
uv run pitch-agent card R10 --provider mock     # chain
uv run pitch-agent card R11 --provider mock     # closed
uv run pitch-agent card R99 --provider mock     # unknown
```

Expected:
- R10 and R11: short cards with decision `no_recommendation`, reason "not in the recommendation target list because the restaurant is a chain" / "… closed", "Reviews not analysed", and "Not applicable" in pain points, opening pitch and discovery questions (Story 2 #1, #2, #4).
- R99: `Unknown restaurant: R99` on stderr, exit code 2, no card (FR-004).

## 3. Full pipeline with the mock

```bash
uv run pitch-agent card R03 --provider mock --mock-responses tests/fixtures/mock_responses/r03.json
uv run pitch-agent card R03 --provider mock --mock-responses tests/fixtures/mock_responses/r03.json --format json
uv run pitch-agent eval --provider mock --mock-responses tests/fixtures/mock_responses/all.json
```

Expected:
- The text card shows all six sections; every evidence line has review ID, quote and text source; the JSON card matches [contracts/visit-card.md](contracts/visit-card.md).
- `eval` prints the SC-001 – SC-005 summary and the path of a new `runs/<timestamp>/` folder with `report.md`, `report.json` and `cards/`. The report shows provider `mock` and model `mock`. The metric values only reflect the canned responses; this step proves the command works, not the agent's quality.

## 4. Set up the local model

```bash
brew install ollama          # or the installer from ollama.com
ollama serve                 # keep running in a separate terminal
ollama pull granite4.2:8b    # default model (research R5); several GB download
```

Optional: choose another model once per shell.

```bash
export PITCH_AGENT_LLM_MODEL=llama3.1:8b
```

## 5. Real cards and the evaluation (L4)

```bash
uv run pitch-agent card R03          # provider defaults to ollama
uv run pitch-agent eval
```

Expected:
- **Speed**: on the development machine (CPU only), a card takes a few minutes. The full evaluation takes roughly an hour. Progress is printed per restaurant; R10 and R11 finish instantly.
- **Run folder**: the report records the git commit, `provider: ollama` and the model name (FR-032).
- **Acceptance**: the run meets SC-001 – SC-005 ([spec.md](spec.md#measurable-outcomes)).
- **Human review (SC-006)**: read the opening pitches and recommendations in `runs/<timestamp>/cards/*.txt`. Every pitch should report in the third person what guests say, without blaming the owner, and no recommendation should break a product limit in `data/products/`.

If Ollama is not running, the command fails with a message naming the host and model and suggesting `ollama serve` / `ollama pull`; no partial card is written.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Unknown provider` | Typo in `--provider` or `PITCH_AGENT_LLM_PROVIDER` (v1: `mock`, `ollama`) |
| Connection refused | `ollama serve` not running, or `OLLAMA_HOST` wrong |
| `model not found` | Model not pulled: `ollama pull <model>` |
| Timeouts on large restaurants | Raise `PITCH_AGENT_LLM_TIMEOUT` (seconds) |
| Many check 3 failures | The model rewords quotes; try another model — the evaluation records which model was used |
