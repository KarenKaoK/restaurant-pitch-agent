# Spec Changes

Behaviour changes to a committed spec are logged here, newest first. Each entry names the spec, the baseline commit, what changed and why.

## 2026-11-28 — 001-visit-card-agent: evaluation unhappy inputs (before Phase 6)

- **Spec**: `specs/001-visit-card-agent/spec.md`, `data-model.md`, `contracts/cli.md`, `contracts/evaluation-report.md`, `test-cases.md`, `tasks.md`
- **Baseline**: commit `4832590`
- **Source**: unhappy inputs listed at every boundary of the evaluation before implementing Phase 6 (CLAUDE.md workflow); decided by the owner on 2026-11-28. Also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Gold-label file read (FR-028) | Only missing columns rejected the file | Also missing/unreadable, not UTF-8, or no data rows; a UTF-8 byte order mark is accepted. New TC-G13–G15, TC-G18 | Excel adds a byte order mark; clear errors instead of a traceback |
| Product lists (FR-027, FR-028) | `;`-separated, nothing about spacing | Spaces and empty items ignored; a product twice in one list is an invalid row. TC-G16, TC-G17 | Hand-edited files |
| Dataset encoding (FR-002a) | A non-UTF-8 file raised a traceback | Load error; byte order mark accepted. TC-D20 | Same reader as the gold labels |
| Metric with denominator 0 | Undefined (division by zero) | `0/0`, percent and met null ("n/a"). TC-M11 | Small fixture sets |
| Output folder (FR-033, evaluation report contract) | Undefined | Inside the data folder refused (exit 2); created before the first model call, so an unwritable location fails at once (exit 1); an existing run folder is never overwritten. TC-V11–V14 | A real run takes hours on the CPU-only machine |
| Interruption and unexpected errors | Undefined | Cards written as generated and kept; no report; exit 130 (Ctrl+C) or 1. TC-V15, TC-V16 | Partial metrics mislead; finished cards are worth keeping |
| `git_dirty` (FR-032) | Undefined | Tracked files only; null without git; commit and dirty flag read at run start for the repository of the running code; the gold-label hash taken before the first model call. TC-V17 | The untracked `scripts/` folder would mark every run dirty; a commit or label edit during a multi-hour run must not change what the report records (found by `/code-review`) |
| `--mock-responses` file missing, invalid or not a JSON object | Traceback, exit 1 | Usage error naming the file, exit 2. TC-V18 | Open question from Phase 4 |
| Data load error in `eval` | Not listed | Exit 2, as for `card`. TC-V10 | Consistency |
| `restaurant_id` characters (FR-002a) | Any non-empty value | `/`, `\`, `.` and `..` rejected (load error). TC-D21, T064b | The ID names the card files; `../x` made `eval` write outside the run folder (found by `/code-review`, reproduced) |
| CSV the reader cannot parse (FR-002a, FR-028) | Traceback | Load error "invalid CSV" (counts as an unreadable file). TC-G19, TC-D20 (c), T064c | Second `/code-review`, reproduced |
| `cards/` folder cannot be created (evaluation report contract) | Traceback; empty run folder left | Exit 1 (Ctrl+C: 130, "no run folder was created"); the run folder this run created is removed. TC-V19, T064c | Second `/code-review`, reproduced |
| Report stops between `report.json` and `report.md` | `report.json` alone left | Neither file left ("both or neither"). TC-V20, T064c | Second `/code-review`, reproduced |
| Gold-label hash (FR-032) | File read again for the hash | Read once; hash of the validated bytes. TC-V21, T064c | Second `/code-review`, reproduced |
| Report cleanup on Ctrl+C (evaluation report contract) | A file renamed just before Ctrl+C could be left | Both final report paths removed on any failure. TC-V20 (b), T064d | Codex review of PR #3, reproduced |
| `report.md` table cells and card links (evaluation report contract) | Values inserted as is; `\|` split the row, spaces and `#` broke links | `\|` escaped, link targets percent-encoded. TC-V22, T064d | Codex review of PR #3, reproduced |

## 2026-11-27 — 001-visit-card-agent: PR #1 review (Ollama errors)

- **Spec**: `specs/001-visit-card-agent/contracts/llm-interface.md`, `specs/001-visit-card-agent/contracts/cli.md`
- **Baseline**: commit `fc519ac`
- **Source**: Codex review and `/code-review` of PR #1; each finding reproduced before the fix. `spec.md` is unchanged by these rows (see the FR-016 note in the entry below).

| Area | Before | After | Reason |
|---|---|---|---|
| Invalid `PITCH_AGENT_LLM_TIMEOUT` | Undefined; `15m` crashed the CLI with a traceback, `0`, negative, `inf` and `nan` were accepted | Must be a positive, finite number; otherwise `ConfigError` naming the variable, shown by the CLI as a usage error (exit 2) | Actionable message instead of a traceback or a misleading failure |
| Connection lost mid-response | Undefined; `RemoteDisconnected` / `IncompleteRead` escaped as a traceback | `LLMError` with the hint to check that Ollama is still running; the CLI reports a generation failure (exit 1) | Ollama can be killed while generating (out of memory on a 16 GB machine) |
| Timeout while connecting | Reported as "cannot connect … Is Ollama running?" | Reported as a timeout with the `PITCH_AGENT_LLM_TIMEOUT` hint | The contract already required the timeout hint; urllib wraps a connect timeout in `URLError` |
| `OLLAMA_HOST` format | Undefined; `0.0.0.0:11434` (Ollama's own format, no scheme) crashed the CLI with `ValueError` | A missing scheme gets `http://`; a trailing `/` is ignored | Users set `OLLAMA_HOST` for `ollama serve` in Ollama's format |
| `LLMConfig.model` is `None` for `ollama` | `"model": null` sent to Ollama | The provider default (`granite4.2:8b`) is used, as for `mock` | Callers that skip `resolve_llm_config` |

## 2026-11-26 — 001-visit-card-agent: first local-model run (T053)

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `2c8a83b`
- **Source**: the first real card with `granite4.2:8b` (R03) wrote the opening pitch in a guest's own voice ("We reserved online but no table was available…") and asked the discovery questions to guests ("How long did you wait…?"); decided by the owner on 2026-11-26. Also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Opening pitch voice (FR-016) | "Worded from the guests' perspective"; speaker undefined | Spoken by the rep to the owner or manager, reporting in the third person what guests say; never in a guest's own voice | The phrase was read as "write as a guest"; Story 1 #4 already gives the intended example "several guests mention…" |
| Default model (plan.md owner decision 2, research R5, contracts/cli.md) | `qwen3:8b` | `granite4.2:8b` | Owner decision before Phase 5; final default decided by the real evaluation (T067) |
| Ollama request (contracts/llm-interface.md, research R4) | No `think` field; one generic error message | `think: false`; each error gives a hint that fits it (start Ollama, pull the model, raise the timeout) | Granite thinks by default and is too slow on CPU; actionable errors |
| Pain-point refs (contracts/model-output.md) | `ref` unique, format free | `p1`, `p2`, … (schema pattern `^p[0-9]+$`) | The model used category IDs as refs, which collided |

Not a spec change, done in the same step: the model prompt now states that discovery questions are asked to the owner or manager (already required by FR-017).

Completed on 2026-11-27 (PR #1 review): FR-016, Story 1 #4, SC-006 and the documents that quote them still said "worded from the guests' perspective" next to the new wording, and the prompt repeated it; the phrase is removed everywhere so only the "After" wording above remains.

## 2026-11-26 — 001-visit-card-agent: Phase 2 review

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `195bb08`
- **Source**: gaps found while implementing Phase 2 (T022, merge rule) and reviewing it for strict TDD; decided by the owner on 2026-11-26. Each decision is also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Unknown category in the merge rule (FR-008, data-model step 4, research R11) | Undefined whether pain points with the same category that is not in the list are merged | Not merged; each stays as returned by the model and fails check 16 (and check 18 when repeated). New test case TC-C11 | The card shows the model output without silent correction |
| Duplicate pain-point `ref` in model output (Edge cases, contracts/model-output.md parsing rules) | Undefined; the contract only says `ref` is unique | Generation failure (`GenerationError`, wrong shape) | Questions cannot be linked to a pain point unambiguously |

## 2026-11-26 — 001-visit-card-agent: analyze findings

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `90580c6`
- **Source**: `/speckit-analyze` findings U1, U2 and I2; decided by the owner on 2026-11-26. Each decision is also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Pain points without evidence (FR-012, FR-025 #17) | Undefined how a pain point with `null` confidence affects products | Kept on the card and fails check 1, but ignored for candidate products, product confidence, support counts and ranking; a product whose mapped pain points all lack evidence is not a candidate; check 17 considers only pain points with evidence | Unsupported findings must not drive a recommendation, while staying visible for debugging in the evaluation |
| Dataset validation (new FR-002a) | Only the catalog and mapping table were validated | The restaurant and review datasets are validated for required columns and values, unique IDs, allowed `segment` / `text_source` values and reviews of known restaurants; dates and ratings are not validated | Broken input data fails loudly instead of producing wrong cards |
| Gold-label file (Assumptions) | `data/eval/expected.csv` "does not exist yet" | The file is created and maintained by the owner | The file now exists; the assumption was outdated |

## 2026-11-26 — 001-visit-card-agent: LLM provider as configuration

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `1b2650d`
- **Source**: owner decision at the start of `/speckit-plan`, 2026-11-26.

| Area | Before | After | Reason |
|---|---|---|---|
| Run metadata (FR-032, Story 3 #5, Evaluation Report entity) | Report records git commit, model name and run date | Also records the LLM provider | The provider is chosen by configuration, so the model name alone does not identify the run |
| Model access (Assumptions, Clarifications) | Undefined | The provider and model are configuration; v1 runs with a local model or a test stand-in; no paid API key is required to develop, test or run the agent | Development and testing must not depend on a paid cloud API |

## 2026-11-26 — 001-visit-card-agent: test-case review

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `a8a6526`
- **Source**: open questions Q1–Q6 found while writing `specs/001-visit-card-agent/test-cases.md`; decided by the owner on 2026-11-26.

| Area | Before | After | Reason |
|---|---|---|---|
| One pain point per category (FR-008, FR-025 #18) | A category could appear in several pain points | A category with mapped products appears at most once per card, evidence merged; only `other_unmapped` may repeat. New deterministic check #18 | Splitting evidence would lower confidence (two `medium` instead of one `high`) and change the ranking |
| Prerequisite pain points (FR-012) | Prerequisite addressed the same pain points as the requiring product | Also lists its own pain points; confidence stays that of the requiring product | Defined behaviour when a prerequisite is also a candidate |
| Short-card review count (FR-007) | "Number of reviews analysed" on every card | Short cards show "Reviews not analysed" | Reviews are not analysed for closed or chain restaurants |
| Prerequisites in metrics (SC-004, SC-005) | Undefined | Primary and prerequisite products both count | Gold labels list prerequisites (e.g. R04) |
| Rule-breaking model output (Edge cases) | Undefined | Unknown category or non-verbatim quote produces a card that fails the checks; only unparseable output or a failed call is a generation failure | Problems stay visible in the evaluation report |
| Gold-label validation (FR-028, Story 3 #6) | Three invalid-row types; behaviour after an error undefined | Six invalid-row types; the evaluation lists all invalid rows and stops before running the agent | Metrics are never computed on a partial or contradictory label set |

## 2026-11-26 — 001-visit-card-agent: clarification session

- **Spec**: `specs/001-visit-card-agent/spec.md`
- **Baseline**: commit `74b1c68` ("spec: add restaurant pitch card specification")
- **Source**: `/speckit-clarify` session and owner review of the pain-point mapping, 2026-11-26. Each decision is also recorded under "Clarifications" in the spec.

| Area | Before | After | Reason |
|---|---|---|---|
| Pain point → product (FR-002, FR-008, FR-013, FR-013a, FR-015a) | The model decided which product addresses a pain point | A fixed category list and category → product table in `data/products/pain-point-product-mapping.json`; the model only classifies reviews and extracts evidence; candidates, support counts, confidence and ranking are computed by rule | Reproducible recommendations that the deterministic checks can verify |
| Closed / chain restaurants (FR-006, FR-007, FR-020a, Story 2) | Full card with no recommendation | Short card produced by rule without calling the model; states that the restaurant is not in the recommendation target list because it is closed and/or a chain; other sections say "Not applicable" | No value in analysing restaurants that will not be pitched; deterministic and testable |
| Verbatim quote check (FR-009, FR-025 #3) | "Verbatim excerpt", matching rule undefined | Exact substring after trimming and collapsing whitespace; case and punctuation must match; at least 3 words | Tolerate formatting noise without allowing rewording; block meaningless one-word quotes |
| Insufficient evidence with no pain points (FR-017a, Story 2) | Undefined | Opening pitch "Not applicable"; general operational questions from the category list, labelled "Not based on reviews" | Rep still has questions to ask without presenting ungrounded claims as evidence |
| Deterministic checks (FR-025) | 15 checks | 17 checks: added category validity (#16) and table consistency (#17); #3, #8 and #12 tightened as above | Cover the new rules |

Decisions taken in the same session before the baseline commit (confidence levels, no `low` level, max 2 primary products, ranking with `product_id` tie-break) are part of the baseline and not repeated here.
