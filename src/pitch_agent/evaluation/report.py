"""Run folder files: cards, report.json and report.md (contracts/evaluation-report.md)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from urllib.parse import quote

from pitch_agent.render import render_text

METRIC_NAMES = ("SC-001", "SC-002", "SC-003", "SC-004", "SC-005")


def _card_files(restaurant_id: str) -> dict:
    return {"json": f"cards/{restaurant_id}.json", "text": f"cards/{restaurant_id}.txt"}


def write_card(run_dir, restaurant_id: str, card: dict) -> None:
    """Write one card as soon as it is generated, so an interrupted run keeps it."""
    files = _card_files(restaurant_id)
    run_dir = Path(run_dir)
    (run_dir / files["json"]).write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / files["text"]).write_text(render_text(card), encoding="utf-8")


def _case_json(case) -> dict:
    return {
        "restaurant_id": case.restaurant_id,
        "card_files": _card_files(case.restaurant_id) if case.card is not None else None,
        "error": case.error,
        "expected_decision": case.expected_decision,
        "actual_decision": case.actual_decision,
        "decision_match": case.actual_decision == case.expected_decision,
        "recommended_products": case.recommended_products,
        "missed_must_include": case.missed_must_include,
        "outside_expected": case.outside_expected,
        "checks": [c.to_dict() for c in case.checks],
    }


def _report_json(metadata, cases, metrics) -> dict:
    run = asdict(metadata)
    unlabelled = run.pop("unlabelled_restaurants")
    return {"run": run, "metrics": metrics, "cases": [_case_json(c) for c in cases],
            "unlabelled_restaurants": unlabelled}


def _status(met) -> str:
    return "n/a" if met is None else "met" if met else "not met"


def _value(metric: dict) -> str:
    percent = metric.get("percent")
    return f"{metric['value']} ({percent}%)" if percent is not None else str(metric["value"])


def _list(items) -> str:
    return ", ".join(items) if items else "—"


def _cell(value) -> str:
    """A Markdown table cell: an unescaped ``|`` would split the row."""
    return str(value).replace("|", "\\|")


def _commit(metadata) -> str:
    if metadata.git_dirty is None:
        return f"{metadata.git_commit} (changes unknown)"
    return f"{metadata.git_commit} (uncommitted changes)" if metadata.git_dirty else metadata.git_commit


def _report_md(metadata, cases, metrics) -> str:
    lines = [
        f"# Evaluation run {metadata.run_id}",
        "",
        "## Run",
        "",
        f"- Run ID: {metadata.run_id}",
        f"- Date: {metadata.run_date}",
        f"- Git commit: {_commit(metadata)}",
        f"- Provider: {metadata.provider}",
        f"- Model: {metadata.model}",
        f"- Gold labels: {metadata.labels_path} (sha256 {metadata.labels_sha256})",
        "",
        "## Summary",
        "",
        "| Metric | Value | Target | Status |",
        "|---|---|---|---|",
    ]
    lines += [f"| {name} | {_value(metrics[name])} | {metrics[name]['target']} | {_status(metrics[name]['met'])} |"
              for name in METRIC_NAMES]
    lines += [
        "| SC-006 | — | — | human review |",
        "",
        "## Per restaurant",
        "",
        "| Restaurant | Expected | Actual | Match | Recommended | Missed must_include | Outside expected "
        "| Failed checks | Card |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for case in cases:
        failed = sum(1 for c in case.checks if not c.passed)
        files = _card_files(case.restaurant_id)
        card = (f"[json]({quote(files['json'])}) · [text]({quote(files['text'])})" if case.card is not None
                else "—")
        match = "yes" if case.actual_decision == case.expected_decision else "no"
        cells = [case.restaurant_id, case.expected_decision, case.actual_decision, match,
                 _list(case.recommended_products), _list(case.missed_must_include), _list(case.outside_expected),
                 failed]
        lines.append("| " + " | ".join(map(_cell, cells)) + f" | {card} |")
    lines += ["", "## Check failures", ""]
    failing = [c for c in cases if any(not check.passed for check in c.checks)]
    if not failing:
        lines.append("No check failures.")
    for case in failing:
        lines += [f"### {case.restaurant_id}", ""]
        lines += [f"- Check {c.check_id}: {'; '.join(c.reasons)}" for c in case.checks if not c.passed]
        lines.append("")
    lines += ["", "## Unlabelled restaurants", "", _list(metadata.unlabelled_restaurants)
              if metadata.unlabelled_restaurants else "None.", ""]
    return "\n".join(lines)


def write_report(run_dir, metadata, cases, metrics) -> None:
    """Write report.json and report.md, both or neither (an incomplete run has no report)."""
    run_dir = Path(run_dir)
    texts = {
        "report.json": json.dumps(_report_json(metadata, cases, metrics), indent=2, ensure_ascii=False) + "\n",
        "report.md": _report_md(metadata, cases, metrics),
    }
    temporary = {name: run_dir / f".{name}.tmp" for name in texts}
    try:
        for name, text in texts.items():
            temporary[name].write_text(text, encoding="utf-8")
        for name, path in temporary.items():
            path.replace(run_dir / name)
    except BaseException:  # also Ctrl+C between or right after a rename; the run folder is new,
        for name in texts:  # so any report file in it was written by this call
            (run_dir / name).unlink(missing_ok=True)
        raise
    finally:
        for path in temporary.values():
            path.unlink(missing_ok=True)
