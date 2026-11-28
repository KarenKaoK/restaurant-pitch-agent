# Contract: Command-Line Interface

Entry point: `pitch-agent` (console script from `pyproject.toml`; run as `uv run pitch-agent …`).

## Common options

| Option | Default | Meaning |
|---|---|---|
| `--data-dir PATH` | `data` | Root of the data folder. The agent reads only `processed/` and `products/` below it. |
| `--provider NAME` | env `PITCH_AGENT_LLM_PROVIDER`, else `ollama` | LLM provider: `mock` or `ollama` in v1 |
| `--model NAME` | env `PITCH_AGENT_LLM_MODEL`, else provider default (`granite4.2:8b` / `mock`) | Model name passed to the provider |
| `--mock-responses PATH` | none | Only with `--provider mock`: JSON file `{restaurant_id: response}` (see [llm-interface.md](llm-interface.md)); a missing file, invalid JSON or JSON that is not an object is a usage error naming the file |

An unknown provider name is a usage error that lists the available providers. An invalid provider setting (e.g. a `PITCH_AGENT_LLM_TIMEOUT` that is not a positive number) is a usage error that names the setting. No option or setting is an API key.

## `pitch-agent card RESTAURANT_ID`

Generates one visit card (FR-001).

| Option | Default | Meaning |
|---|---|---|
| `--format text\|json` | `text` | `text`: plain-text card (FR-022). `json`: structured card (FR-023, [visit-card.md](visit-card.md)) |
| `--output PATH` | stdout | Write the card to a file instead |

| Situation | stdout | stderr | Exit code |
|---|---|---|---|
| Card produced | the card | — | 0 |
| Unknown restaurant ID (FR-004) | nothing | `Unknown restaurant: <id>` | 2 |
| Generation failure (call failed, unparseable output) | nothing (no partial card) | `Generation failed for <id>: <reason>` | 1 |
| Data load error (e.g. invalid mapping file) | nothing | the load error | 2 |

The `card` command does not run the deterministic checks; they run in `eval`.

## `pitch-agent eval`

Runs the evaluation (FR-026 – FR-033) as one command.

| Option | Default | Meaning |
|---|---|---|
| `--labels PATH` | `data/eval/expected.csv` | Gold-label file |
| `--out-dir PATH` | `runs` | Parent folder; the run is written to `<out-dir>/<UTC timestamp>/` |

| Situation | Output | Exit code |
|---|---|---|
| Run completed (whether or not targets are met) | Run folder ([evaluation-report.md](evaluation-report.md)); a summary of SC-001 – SC-005 and the run folder path on stdout | 0 |
| Gold-label file invalid (FR-028) | Every invalid row with its reason, or the file-level error, on stderr; agent not run; no run folder | 2 |
| Data load error | The load error on stderr; agent not run; no run folder | 2 |
| `--out-dir` inside the data folder (FR-033) | Usage error; agent not run; nothing written | 2 |
| Run folder cannot be created or already exists | Message on stderr; agent not run | 1 |
| Interrupted (Ctrl+C) | "Run interrupted" and the incomplete run folder, if one was created, on stderr; cards so far kept; no report | 130 |
| Unexpected error | Message and the incomplete run folder on stderr; cards so far kept; no report | 1 |

Progress (one line per restaurant: ID, decision or error, elapsed time) is printed to stderr so a slow local model is visibly working.

## Not provided

No command contacts restaurants or sends anything outward (FR-024). There is no web interface and no batch command for all restaurants outside the evaluation (Out of Scope).
