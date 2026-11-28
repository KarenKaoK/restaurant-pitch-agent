"""Section N: the evaluation run, in-process and through `pitch-agent eval` (contracts/cli.md,
contracts/evaluation-report.md)."""

import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import REAL_DATA_DIR, REPO_ROOT
from pitch_agent import cli
from pitch_agent.evaluation import runner
from pitch_agent.evaluation.labels import GoldLabelError
from pitch_agent.evaluation.runner import (
    OutputInsideDataError,
    RunAborted,
    RunFolderError,
    RunInterrupted,
    git_info,
    run_evaluation,
)
from pitch_agent.llm.mock import MockLLM

LABELS = REPO_ROOT / "tests" / "fixtures" / "labels"
NOW = datetime(2026, 11, 28, 10, 15, 0, tzinfo=timezone.utc)
RUN_ID = "20261128T101500Z"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("PITCH_AGENT_LLM_PROVIDER", "PITCH_AGENT_LLM_MODEL", "PITCH_AGENT_LLM_TIMEOUT"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def f01_output(model_output):
    return model_output([("p1", "c_cash", [("F01-001", "only accept cash payments")])])


@pytest.fixture
def llm(f01_output):
    return MockLLM({"F01": f01_output})


@pytest.fixture
def evaluate(fixture_data_dir, tmp_path):
    def run(llm, labels="valid.csv", out_dir=None, data_dir=None, progress=None):
        return run_evaluation(data_dir or fixture_data_dir, LABELS / labels, out_dir or tmp_path / "runs", llm,
                              now=NOW, progress=progress or io.StringIO())

    return run


def report_json(run):
    return json.loads((run.run_dir / "report.json").read_text(encoding="utf-8"))


def report_md(run):
    return (run.run_dir / "report.md").read_text(encoding="utf-8")


def case_of(report, restaurant_id):
    return next(c for c in report["cases"] if c["restaurant_id"] == restaurant_id)


def eval_args(fixture_data_dir, tmp_path, *extra, labels="valid.csv"):
    return ["eval", "--data-dir", str(fixture_data_dir), "--labels", str(LABELS / labels),
            "--out-dir", str(tmp_path / "runs"), "--provider", "mock", *extra]


@pytest.fixture
def use_llm(monkeypatch):
    """Make the CLI use a given client (for behaviour a responses file cannot express)."""
    return lambda client: monkeypatch.setattr(cli, "create_llm", lambda config: client)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --- TC-V01 – TC-V08: a completed run --------------------------------------------------


def test_tc_v01_one_command_produces_a_report(evaluate, llm, tmp_path):
    run = evaluate(llm)
    assert run.run_dir == tmp_path / "runs" / RUN_ID
    assert {p.name for p in run.run_dir.iterdir()} == {"report.json", "report.md", "cards"}


def test_tc_v01_cli(fixture_data_dir, tmp_path, f01_output, capsys):
    responses = tmp_path / "responses.json"
    responses.write_text(json.dumps({"F01": f01_output}), encoding="utf-8")
    assert cli.main(eval_args(fixture_data_dir, tmp_path, "--mock-responses", str(responses))) == 0
    out, err = capsys.readouterr()
    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1 and (run_dirs[0] / "report.json").exists()
    assert f"Run folder: {run_dirs[0]}" in out
    for sc in ("SC-001", "SC-002", "SC-003", "SC-004", "SC-005"):
        assert sc in out
    assert [line.split(":")[0] for line in err.splitlines()] == ["F01", "F02", "F05"]


def test_tc_v02_agent_runs_once_per_labelled_restaurant(evaluate, llm, monkeypatch):
    calls = []
    real = runner.generate_card
    monkeypatch.setattr(runner, "generate_card", lambda rid, data, client: calls.append(rid) or real(rid, data, client))
    run = evaluate(llm)
    assert calls == ["F01", "F02", "F05"]
    assert [r.request_id for r in llm.calls] == ["F01", "F05"]  # F02 is closed: short card without the model
    assert [c.restaurant_id for c in run.cases] == ["F01", "F02", "F05"]


def test_tc_v03_unlabelled_restaurants_listed(evaluate, llm):
    run = evaluate(llm)
    assert report_json(run)["unlabelled_restaurants"] == ["F03", "F04", "F06"]
    section = report_md(run).split("## Unlabelled restaurants", 1)[1]
    assert "F03" in section and "F04" in section and "F06" in section


def test_tc_v04_run_metadata(evaluate, llm):
    run = evaluate(llm)
    meta = report_json(run)["run"]
    assert meta["run_id"] == RUN_ID and meta["run_date"] == "2026-11-28T10:15:00Z"
    assert (meta["provider"], meta["model"]) == ("mock", "mock")
    assert meta["git_commit"] and isinstance(meta["git_commit"], str)
    assert meta["labels_path"] == str(LABELS / "valid.csv")
    assert meta["labels_sha256"] == sha256(LABELS / "valid.csv")
    run_section = report_md(run).split("## Run", 1)[1].split("## Summary", 1)[0]
    for value in (RUN_ID, meta["git_commit"], "mock", meta["labels_sha256"]):
        assert value in run_section


def test_tc_v05_all_checks_per_card(evaluate, model_output):
    bad_quote = model_output([("p1", "c_cash", [("F01-001", "cash only, never cards")])])
    run = evaluate(MockLLM({"F01": bad_quote}))
    report = report_json(run)
    for case in report["cases"]:
        assert [c["check_id"] for c in case["checks"]] == list(range(1, 19))
    check3 = case_of(report, "F01")["checks"][2]
    assert check3["passed"] is False and check3["reasons"]
    failures = report_md(run).split("## Check failures", 1)[1].split("## Unlabelled", 1)[0]
    assert "F01" in failures and "Check 3" in failures and check3["reasons"][0] in failures


def test_tc_v06_per_restaurant_comparison(evaluate, llm):
    run = evaluate(llm)
    f01 = case_of(report_json(run), "F01")
    assert (f01["expected_decision"], f01["actual_decision"], f01["decision_match"]) == ("recommend", "recommend", True)
    assert f01["recommended_products"] == ["dish-pay"]
    assert f01["missed_must_include"] == ["dish-pos"]
    assert f01["outside_expected"] == []
    rows = report_md(run).split("## Per restaurant", 1)[1].split("## Check failures", 1)[0]
    f01_row = next(line for line in rows.splitlines() if line.startswith("| F01 "))
    assert "recommend" in f01_row and "dish-pay" in f01_row and "dish-pos" in f01_row


def test_tc_v07_cards_written_and_referenced(evaluate, llm):
    run = evaluate(llm)
    f01 = case_of(report_json(run), "F01")
    assert f01["card_files"] == {"json": "cards/F01.json", "text": "cards/F01.txt"}
    card = json.loads((run.run_dir / "cards" / "F01.json").read_text(encoding="utf-8"))
    assert card == run.cases[0].card
    assert "Fixture Bistro" in (run.run_dir / "cards" / "F01.txt").read_text(encoding="utf-8")
    assert "(cards/F01.json)" in report_md(run)


def test_tc_v07_generation_failure_case(evaluate):
    run = evaluate(MockLLM({"F01": {"raw": "not json"}}))
    f01 = case_of(report_json(run), "F01")
    assert f01["card_files"] is None and f01["error"]
    assert f01["actual_decision"] == "error" and f01["decision_match"] is False
    assert f01["checks"][0] == {"check_id": 1, "passed": False, "reasons": [f01["error"]]}
    assert all(c == {"check_id": c["check_id"], "passed": False, "reasons": ["not evaluated: generation failed"]}
               for c in f01["checks"][1:])
    assert not (run.run_dir / "cards" / "F01.json").exists()
    assert not (run.run_dir / "cards" / "F01.txt").exists()


def test_tc_v08_inputs_unchanged(evaluate, llm):
    files = [LABELS / "valid.csv", REAL_DATA_DIR / "raw" / "duesseldorf_reviews.csv"]
    before = [sha256(f) for f in files]
    evaluate(llm)
    assert [sha256(f) for f in files] == before


def test_progress_line_per_restaurant(evaluate, llm):
    progress = io.StringIO()
    evaluate(llm, progress=progress)
    lines = progress.getvalue().splitlines()
    assert [line.split(":")[0] for line in lines] == ["F01", "F02", "F05"]
    assert "recommend" in lines[0] and "no_recommendation" in lines[1] and " s)" in lines[0]


def test_summary_and_metrics_in_report(evaluate, llm):
    run = evaluate(llm)
    assert report_json(run)["metrics"] == run.metrics
    summary = report_md(run).split("## Summary", 1)[1].split("## Per restaurant", 1)[0]
    for sc in ("SC-001", "SC-002", "SC-003", "SC-004", "SC-005", "SC-006"):
        assert sc in summary
    assert "human review" in summary


def test_report_md_sections_in_order(evaluate, llm):
    text = report_md(evaluate(llm))
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == ["## Run", "## Summary", "## Per restaurant", "## Check failures", "## Unlabelled restaurants"]


# --- TC-V09 – TC-V18: unhappy inputs ---------------------------------------------------


def test_tc_v09_invalid_labels_stop_before_the_agent(evaluate, llm, tmp_path):
    with pytest.raises(GoldLabelError):
        evaluate(llm, labels="tc_g04_unknown_restaurant.csv")
    assert llm.calls == []
    assert not (tmp_path / "runs").exists()


def test_tc_v09_cli(fixture_data_dir, tmp_path, capsys):
    assert cli.main(eval_args(fixture_data_dir, tmp_path, labels="tc_g11_three_invalid_rows.csv")) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.splitlines() == [
        "row 2 (F99): unknown restaurant_id",
        "row 4 (F01): invalid decision 'yes'",
        "row 5 (F05): must_include must be empty unless decision is recommend",
    ]
    assert not (tmp_path / "runs").exists()


def test_tc_v09_cli_file_level_error(fixture_data_dir, tmp_path, capsys):
    assert cli.main(eval_args(fixture_data_dir, tmp_path, labels="tc_g07_missing_column.csv")) == 2
    assert "acceptable" in capsys.readouterr().err


def test_tc_v10_data_load_error(tmp_data_dir, tmp_path, use_llm, llm, capsys):
    (tmp_data_dir / "products" / "pain-point-product-mapping.json").write_text("{", encoding="utf-8")
    use_llm(llm)
    assert cli.main(eval_args(tmp_data_dir, tmp_path)) == 2
    assert "pain-point-product-mapping.json" in capsys.readouterr().err
    assert llm.calls == [] and not (tmp_path / "runs").exists()


def test_tc_v11_missing_out_dir_is_created(evaluate, llm, tmp_path):
    run = evaluate(llm, out_dir=tmp_path / "a" / "b")
    assert (tmp_path / "a" / "b" / RUN_ID / "report.json").exists() and run.metrics


def test_tc_v12_out_dir_is_a_file(evaluate, llm, tmp_path):
    blocker = tmp_path / "runs"
    blocker.write_text("not a folder", encoding="utf-8")
    with pytest.raises(RunFolderError) as e:
        evaluate(llm, out_dir=blocker)
    assert str(blocker) in str(e.value)
    assert llm.calls == []


def test_tc_v12_cli(fixture_data_dir, tmp_path, use_llm, llm, capsys):
    (tmp_path / "runs").write_text("not a folder", encoding="utf-8")
    use_llm(llm)
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 1
    assert str(tmp_path / "runs") in capsys.readouterr().err
    assert llm.calls == []


def test_tc_v13_out_dir_inside_data_folder(tmp_data_dir, evaluate, llm):
    before = sorted(p.relative_to(tmp_data_dir) for p in tmp_data_dir.rglob("*"))
    with pytest.raises(OutputInsideDataError):
        # only inside the data folder once ".." is resolved
        evaluate(llm, data_dir=tmp_data_dir.parent / "x" / ".." / "data", out_dir=tmp_data_dir / "runs")
    assert llm.calls == []
    assert sorted(p.relative_to(tmp_data_dir) for p in tmp_data_dir.rglob("*")) == before


def test_tc_v13_cli(tmp_data_dir, use_llm, llm, capsys):
    use_llm(llm)
    args = ["eval", "--data-dir", str(tmp_data_dir), "--labels", str(LABELS / "valid.csv"),
            "--out-dir", str(tmp_data_dir / "runs"), "--provider", "mock"]
    with pytest.raises(SystemExit) as e:
        cli.main(args)
    assert e.value.code == 2
    assert "data folder" in capsys.readouterr().err
    assert llm.calls == [] and not (tmp_data_dir / "runs").exists()


def test_tc_v14_existing_run_folder_untouched(evaluate, llm, tmp_path):
    existing = tmp_path / "runs" / RUN_ID
    existing.mkdir(parents=True)
    (existing / "marker.txt").write_text("earlier run", encoding="utf-8")
    with pytest.raises(RunFolderError) as e:
        evaluate(llm)
    assert "already exists" in str(e.value)
    assert [p.name for p in existing.iterdir()] == ["marker.txt"]
    assert (existing / "marker.txt").read_text(encoding="utf-8") == "earlier run"
    assert llm.calls == []


def interrupt_at(restaurant_id, error, f01_output):
    def respond(request):
        if request.request_id == restaurant_id:
            raise error
        return f01_output if request.request_id == "F01" else {"raw": "unused"}

    return MockLLM(respond)


def test_tc_v15_interrupted_run_keeps_cards(evaluate, f01_output, tmp_path):
    with pytest.raises(RunInterrupted) as e:
        evaluate(interrupt_at("F05", KeyboardInterrupt(), f01_output))
    run_dir = tmp_path / "runs" / RUN_ID
    assert e.value.run_dir == run_dir
    assert sorted(p.name for p in (run_dir / "cards").iterdir()) == ["F01.json", "F01.txt", "F02.json", "F02.txt"]
    assert not (run_dir / "report.json").exists() and not (run_dir / "report.md").exists()


def test_tc_v15_cli(fixture_data_dir, tmp_path, use_llm, f01_output, capsys):
    use_llm(interrupt_at("F05", KeyboardInterrupt(), f01_output))
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 130
    out, err = capsys.readouterr()
    run_dir = next((tmp_path / "runs").iterdir())
    assert "Run interrupted" in err and str(run_dir) in err
    assert out == ""


def test_tc_v16_unexpected_error_stops_the_run(evaluate, f01_output, tmp_path):
    with pytest.raises(RunAborted) as e:
        evaluate(interrupt_at("F05", RuntimeError("boom"), f01_output))
    assert "boom" in str(e.value)
    assert (e.value.run_dir / "cards" / "F01.json").exists()
    assert not (e.value.run_dir / "report.json").exists()


def test_tc_v16_cli(fixture_data_dir, tmp_path, use_llm, f01_output, capsys):
    use_llm(interrupt_at("F01", RuntimeError("boom"), f01_output))
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 1
    err = capsys.readouterr().err
    assert "boom" in err and str(next((tmp_path / "runs").iterdir())) in err


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_tc_v17_untracked_files_are_not_dirty(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "tracked.txt").write_text("v1", encoding="utf-8")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    (tmp_path / "untracked.txt").write_text("new", encoding="utf-8")
    commit, dirty = git_info(cwd=tmp_path)
    assert len(commit) == 40 and dirty is False
    (tmp_path / "tracked.txt").write_text("v2", encoding="utf-8")
    assert git_info(cwd=tmp_path)[1] is True


def test_tc_v17_without_git(tmp_path):
    assert git_info(cwd=tmp_path, git="no-such-git-binary") == ("unknown", None)


def test_tc_v17_not_a_repository(tmp_path):
    assert git_info(cwd=tmp_path) == ("unknown", None)


@pytest.mark.parametrize("command", ["card", "eval"])
@pytest.mark.parametrize("content", [None, "{not json"])
def test_tc_v18_bad_mock_responses_file(fixture_data_dir, tmp_path, capsys, command, content):
    responses = tmp_path / "responses.json"
    if content is not None:
        responses.write_text(content, encoding="utf-8")
    args = (["card", "F01", "--data-dir", str(fixture_data_dir), "--provider", "mock"] if command == "card"
            else eval_args(fixture_data_dir, tmp_path))
    with pytest.raises(SystemExit) as e:
        cli.main([*args, "--mock-responses", str(responses)])
    assert e.value.code == 2
    assert str(responses) in capsys.readouterr().err


# --- /code-review findings on Phase 6 ----------------------------------------------------


def test_labels_hash_is_of_the_file_that_was_scored(fixture_data_dir, tmp_path):
    labels = tmp_path / "labels.csv"
    labels.write_bytes((LABELS / "valid.csv").read_bytes())
    original = sha256(labels)

    def edit_during_run(request):
        labels.write_text("edited during the run\n", encoding="utf-8")
        return {"raw": "x"}

    run = run_evaluation(fixture_data_dir, labels, tmp_path / "runs", MockLLM(edit_during_run), now=NOW,
                         progress=io.StringIO())
    assert run.metadata.labels_sha256 == original


def test_git_read_before_the_first_model_call(evaluate, monkeypatch):
    order, real = [], runner.git_info
    monkeypatch.setattr(runner, "git_info", lambda *a, **k: order.append(("git", k.get("cwd"))) or real(*a, **k))
    evaluate(MockLLM(lambda request: order.append("model") or {"raw": "x"}))
    assert order[0][0] == "git" and order.count("model") == 2
    assert Path(order[0][1]) == Path(runner.__file__).resolve().parent


def test_out_dir_in_data_folder_with_other_letter_case(tmp_data_dir, evaluate, llm):
    other_case = tmp_data_dir.parent / "DATA"
    if not other_case.exists():
        pytest.skip("case-sensitive file system")
    with pytest.raises(OutputInsideDataError):
        evaluate(llm, data_dir=tmp_data_dir, out_dir=other_case / "runs")
    assert not (tmp_data_dir / "runs").exists()


def test_no_report_left_when_writing_the_report_fails(evaluate, llm, monkeypatch):
    from pitch_agent.evaluation import report

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr(report, "_report_md", fail)
    with pytest.raises(RunAborted) as e:
        evaluate(llm)
    assert not (e.value.run_dir / "report.json").exists() and not (e.value.run_dir / "report.md").exists()


def test_ctrl_c_before_the_run_folder_exists(fixture_data_dir, tmp_path, use_llm, llm, monkeypatch, capsys):
    from pitch_agent.evaluation import runner as runner_module

    def interrupted(*args):
        raise KeyboardInterrupt

    use_llm(llm)
    monkeypatch.setattr(runner_module, "load_agent_data", interrupted)
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 130
    assert "Run interrupted" in capsys.readouterr().err
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("command", ["card", "eval"])
def test_mock_responses_not_an_object(fixture_data_dir, tmp_path, capsys, command):
    responses = tmp_path / "responses.json"
    responses.write_text("[]", encoding="utf-8")
    args = (["card", "F01", "--data-dir", str(fixture_data_dir), "--provider", "mock"] if command == "card"
            else eval_args(fixture_data_dir, tmp_path))
    with pytest.raises(SystemExit) as e:
        cli.main([*args, "--mock-responses", str(responses)])
    assert e.value.code == 2
    assert str(responses) in capsys.readouterr().err
    assert not (tmp_path / "runs").exists()


def test_out_dir_usage_error_names_the_eval_command(tmp_data_dir, capsys):
    args = ["eval", "--data-dir", str(tmp_data_dir), "--out-dir", str(tmp_data_dir / "runs"), "--provider", "mock"]
    with pytest.raises(SystemExit):
        cli.main(args)
    assert capsys.readouterr().err.startswith("usage: pitch-agent eval")


# --- second /code-review on Phase 6 -------------------------------------------------------


def fail_cards_mkdir(monkeypatch, error):
    real = Path.mkdir

    def mkdir(self, *args, **kwargs):
        if self.name == "cards":
            raise error
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)


def test_tc_v19_cards_folder_os_error(fixture_data_dir, tmp_path, use_llm, monkeypatch, capsys):
    stub = MockLLM({})
    use_llm(stub)
    fail_cards_mkdir(monkeypatch, OSError(28, "No space left on device"))
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 1
    assert "Cannot create run folder" in capsys.readouterr().err
    assert list((tmp_path / "runs").iterdir()) == [] and stub.calls == []


def test_tc_v19_cards_folder_ctrl_c(fixture_data_dir, tmp_path, use_llm, monkeypatch, capsys):
    stub = MockLLM({})
    use_llm(stub)
    fail_cards_mkdir(monkeypatch, KeyboardInterrupt())
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 130
    assert "no run folder was created" in capsys.readouterr().err
    assert list((tmp_path / "runs").iterdir()) == [] and stub.calls == []


def test_tc_v20_report_stops_between_the_two_files(fixture_data_dir, tmp_path, use_llm, llm, monkeypatch, capsys):
    real, renamed = Path.replace, []

    def replace(self, target):
        if renamed:
            raise OSError("disk full")
        renamed.append(target)
        return real(self, target)

    use_llm(llm)
    monkeypatch.setattr(Path, "replace", replace)
    assert cli.main(eval_args(fixture_data_dir, tmp_path)) == 1
    run_dir = tmp_path / "runs" / next((tmp_path / "runs").iterdir()).name
    assert sorted(p.name for p in run_dir.iterdir()) == ["cards"]
    assert "incomplete run folder" in capsys.readouterr().err


@pytest.mark.parametrize("change", ["edit", "delete"])
def test_tc_v21_labels_changed_after_validation(fixture_data_dir, tmp_path, llm, monkeypatch, change):
    from pitch_agent.evaluation import labels as labels_module

    path = tmp_path / "labels.csv"
    path.write_bytes((LABELS / "valid.csv").read_bytes())
    original, real = sha256(path), labels_module._row_reasons

    def change_file(*args):
        if path.exists():
            path.write_text("edited\n", encoding="utf-8") if change == "edit" else path.unlink()
        return real(*args)

    monkeypatch.setattr(labels_module, "_row_reasons", change_file)
    run = run_evaluation(fixture_data_dir, path, tmp_path / "runs", llm, now=NOW, progress=io.StringIO())
    assert run.metadata.labels_sha256 == original


def test_tc_v21_labels_validated_from_the_hashed_bytes(fixture_data_dir, tmp_path, llm, monkeypatch):
    from pitch_agent.evaluation import labels as labels_module

    path = tmp_path / "labels.csv"
    path.write_bytes((LABELS / "valid.csv").read_bytes())
    original, real = sha256(path), labels_module.read_bytes

    def read_then_edit(*args):
        content = real(*args)
        path.write_text("edited\n", encoding="utf-8")
        return content

    monkeypatch.setattr(labels_module, "read_bytes", read_then_edit)
    run = run_evaluation(fixture_data_dir, path, tmp_path / "runs", llm, now=NOW, progress=io.StringIO())
    assert run.metadata.labels_sha256 == original and len(run.cases) == 3
