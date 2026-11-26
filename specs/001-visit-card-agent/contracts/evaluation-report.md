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

`runs/` is git-ignored. The command never writes to `data/` (FR-033).

## `report.json`

```json
{
  "run": {
    "run_id": "20261126T101500Z",
    "run_date": "2026-11-26T10:15:00Z",
    "git_commit": "1b2650d…",
    "git_dirty": false,
    "provider": "ollama",
    "model": "qwen3:8b",
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
2. **Summary**: a table with SC-001 – SC-005 — value, target, met / not met. SC-006 is shown as "human review".
3. **Per restaurant**: one row per labelled restaurant — expected decision, actual decision, match, recommended products, missed `must_include`, products outside `must_include` ∪ `acceptable`, number of failed checks, links to the card files.
4. **Check failures**: for each card with a failed check, the check number and reason(s).
5. **Unlabelled restaurants**: restaurants in the dataset but not in the gold labels (not evaluated).

## Invalid gold labels

No run folder is created. stderr lists every invalid row: `row <n> (<restaurant_id>): <reason>`, or one file-level error for missing columns. Exit code 2.
