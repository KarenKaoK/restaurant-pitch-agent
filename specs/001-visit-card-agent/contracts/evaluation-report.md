# Contract: Evaluation Run Output

`pitch-agent eval` writes one folder per run (research R12):

```text
runs/<YYYYMMDDTHHMMSSZ>/
├── report.md          # for people
├── report.json        # for comparing runs
└── cards/
    ├── R01.json       # structured card (contracts/visit-card.md), absent on generation failure
    ├── R01.txt        # plain-text card, absent on generation failure
    └── …
```

`runs/` is git-ignored. The command never writes to `data/` (FR-033): an `--out-dir` inside the data folder is a usage error.

### Run folder lifecycle

1. The gold labels and the data are validated; nothing is created if they are invalid.
2. `--out-dir` is created if missing, then the run folder. If the run folder (with its `cards/` folder) cannot be created or already exists, the run stops before the first model call (exit 1); an existing folder is never touched, and a folder this run created is removed again. The gold-label file is read once; its hash is taken from the bytes that were validated.
3. Each card's `cards/<id>.json` and `cards/<id>.txt` are written as soon as the card is generated.
4. `report.json` and `report.md` are written last, both or neither. A run interrupted by Ctrl+C (exit 130) or stopped by an unexpected error (exit 1) has no report; the cards written so far are kept and stderr names the incomplete run folder.

## `report.json`

```json
{
  "run": {
    "run_id": "20261126T101500Z",
    "run_date": "2026-11-26T10:15:00Z",
    "git_commit": "1b2650d…",
    "git_dirty": false,          // tracked files only; null without git
    "provider": "ollama",
    "model": "granite4.2:8b",
    "labels_path": "data/eval/expected.csv",
    "labels_sha256": "…"
  },
  "metrics": {
    "SC-001": {"value": "15/15", "percent": 100.0, "target": "100%", "met": true},
    "SC-002": {"value": "2/2", "percent": 100.0, "target": "100%", "met": true},
    "SC-003": {"value": "13/15", "percent": 86.7, "target": ">= 13/15", "met": true},
    "SC-004": {"value": "9/10", "percent": 90.0, "target": ">= 80%", "met": true},
    "SC-005": {"value": 1, "target": "<= 1", "met": true}
  },
  // a ratio with denominator 0: {"value": "0/0", "percent": null, "target": "100%", "met": null}
  "cases": [
    {
      "restaurant_id": "R04",
      "card_files": {"json": "cards/R04.json", "text": "cards/R04.txt"},
      "error": null,
      "expected_decision": "recommend",
      "actual_decision": "recommend",
      "decision_match": true,
      "recommended_products": ["dish-ai-phone-assistant", "dish-professional-reservation"],
      "missed_must_include": [],
      "outside_expected": [],
      "checks": [
        {"check_id": 1, "passed": true, "reasons": []},
        {"check_id": 3, "passed": false, "reasons": ["R04-011: quote not found in review text"]}
      ]
    }
  ],
  "unlabelled_restaurants": ["…"]
}
```

`checks` always lists all 18 checks for every case (FR-030).

## `report.md`

Sections, in order:

1. **Run**: run ID, date, git commit (+ "uncommitted changes" if dirty), provider, model, gold-label file and hash.
2. **Summary**: a table with SC-001 – SC-005 — value, target, met / not met / n/a. SC-006 is shown as "human review".
3. **Per restaurant**: one row per labelled restaurant — expected decision, actual decision, match, recommended products, missed `must_include`, products outside `must_include` ∪ `acceptable`, number of failed checks, links to the card files.
4. **Check failures**: for each card with a failed check, the check number and reason(s).
5. **Unlabelled restaurants**: restaurants in the dataset but not in the gold labels (not evaluated).

## Invalid gold labels

No run folder is created. stderr lists every invalid row: `row <n> (<restaurant_id>): <reason>`, or one file-level error for missing columns. Exit code 2.
