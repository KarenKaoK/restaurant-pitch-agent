"""One evaluation run (FR-026 – FR-033, contracts/evaluation-report.md)."""

from __future__ import annotations

import contextlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pitch_agent.agent import generate_card
from pitch_agent.analysis import GenerationError
from pitch_agent.checks import CHECKS, run_checks
from pitch_agent.evaluation.labels import read_gold_labels
from pitch_agent.evaluation.metrics import case_result, compute_metrics
from pitch_agent.evaluation.report import write_card, write_report
from pitch_agent.loaders import load_agent_data
from pitch_agent.models import CheckResult

NOT_EVALUATED = "not evaluated: generation failed"
PACKAGE_DIR = Path(__file__).resolve().parent  # git is asked about the code that runs


class OutputInsideDataError(ValueError):
    """The output folder is inside the data folder (FR-033)."""


class RunFolderError(Exception):
    """The run folder cannot be created or already exists."""


class IncompleteRunError(Exception):
    """The run stopped after the run folder was created; no report was written."""

    def __init__(self, run_dir: Path, message: str):
        super().__init__(message)
        self.run_dir = run_dir


class RunInterrupted(IncompleteRunError):
    """Ctrl+C during the run."""


class RunAborted(IncompleteRunError):
    """An unexpected (non-generation) error during the run."""


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    run_date: str
    git_commit: str
    git_dirty: bool | None
    provider: str
    model: str
    labels_path: str
    labels_sha256: str
    unlabelled_restaurants: list[str]


@dataclass(frozen=True)
class EvaluationRun:
    run_dir: Path
    metadata: RunMetadata
    cases: list
    metrics: dict


def git_info(cwd=None, git: str = "git") -> tuple[str, bool | None]:
    """HEAD commit and whether tracked files have uncommitted changes (untracked files
    do not count); ``("unknown", None)`` without git or outside a repository."""
    try:
        commit = subprocess.run([git, "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True)
        status = subprocess.run([git, "status", "--porcelain", "--untracked-files=no"], cwd=cwd,
                                capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown", None
    return commit.stdout.strip(), bool(status.stdout.strip())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _failed_checks(error: str) -> list[CheckResult]:
    """data-model.md CaseResult.checks on generation failure."""
    return [CheckResult(1, False, [error])] + [CheckResult(i, False, [NOT_EVALUATED]) for i in sorted(CHECKS) if i != 1]


def _inside(path: Path, folder: Path) -> bool:
    """True if ``path`` is ``folder`` or below it, also on a case-insensitive file system."""
    folder = folder.resolve()
    if not folder.exists():
        return path.resolve().is_relative_to(folder)
    resolved = path.resolve()
    return any(candidate == folder or (candidate.exists() and os.path.samefile(candidate, folder))
               for candidate in (resolved, *resolved.parents))


def _create_run_dir(out_dir: Path, run_id: str) -> Path:
    run_dir = out_dir / run_id
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir()
    except FileExistsError as e:
        problem = "already exists" if run_dir.exists() else "is not a folder"
        raise RunFolderError(f"Cannot create run folder {run_dir}: {e.filename} {problem}") from e
    except OSError as e:
        raise RunFolderError(f"Cannot create run folder {run_dir}: {e}") from e
    try:
        (run_dir / "cards").mkdir()
    except BaseException as e:  # also Ctrl+C: leave no half-created run folder behind
        with contextlib.suppress(OSError):
            run_dir.rmdir()
        if isinstance(e, OSError):
            raise RunFolderError(f"Cannot create run folder {run_dir}: {e}") from e
        raise
    return run_dir


def _run_case(label, data, llm, run_dir: Path, progress) -> object:
    started = time.monotonic()
    try:
        card, error = generate_card(label.restaurant_id, data, llm).to_dict(), None
    except GenerationError as e:
        card, error = None, str(e)
    if card is not None:
        write_card(run_dir, label.restaurant_id, card)
        checks = run_checks(card, data)
    else:
        checks = _failed_checks(error)
    outcome = card["decision"] if card else f"error: {error}"
    print(f"{label.restaurant_id}: {outcome} ({time.monotonic() - started:.1f} s)", file=progress, flush=True)
    return case_result(label, card, error, checks)


def run_evaluation(data_dir, labels_path, out_dir, llm, now=None, progress=None) -> EvaluationRun:
    """Validate, run the agent once per labelled restaurant, check and score every card,
    and write the run folder (contracts/evaluation-report.md "Run folder lifecycle")."""
    data_dir, labels_path, out_dir = Path(data_dir), Path(labels_path), Path(out_dir)
    progress = progress if progress is not None else sys.stderr
    if _inside(out_dir, data_dir):
        raise OutputInsideDataError(f"--out-dir {out_dir} is inside the data folder {data_dir}")
    data = load_agent_data(data_dir)
    labels, labels_sha256 = read_gold_labels(labels_path, data.restaurants, data.catalog)
    commit, dirty = git_info(cwd=PACKAGE_DIR)

    started = now or _utcnow()
    run_id = started.strftime("%Y%m%dT%H%M%SZ")
    run_dir = _create_run_dir(out_dir, run_id)
    try:
        cases = [_run_case(label, data, llm, run_dir, progress) for label in labels]
        metrics = compute_metrics(cases, data.restaurants)
        labelled = {label.restaurant_id for label in labels}
        metadata = RunMetadata(
            run_id=run_id,
            run_date=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            git_commit=commit,
            git_dirty=dirty,
            provider=llm.provider,
            model=llm.model,
            labels_path=str(labels_path),
            labels_sha256=labels_sha256,
            unlabelled_restaurants=[rid for rid in data.restaurants if rid not in labelled],
        )
        write_report(run_dir, metadata, cases, metrics)
    except KeyboardInterrupt as e:
        raise RunInterrupted(run_dir, f"Run interrupted; incomplete run folder: {run_dir}") from e
    except Exception as e:
        raise RunAborted(run_dir, f"Run aborted ({type(e).__name__}: {e}); incomplete run folder: {run_dir}") from e
    return EvaluationRun(run_dir, metadata, cases, metrics)
