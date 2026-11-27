"""`pitch-agent card` per contracts/cli.md."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pitch_agent.checks import run_checks
from pitch_agent.cli import main
from pitch_agent.loaders import load_agent_data

ENV_KEYS = ("PITCH_AGENT_LLM_PROVIDER", "PITCH_AGENT_LLM_MODEL", "PITCH_AGENT_LLM_TIMEOUT")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def responses(tmp_path, model_output):
    def write(mapping):
        path = tmp_path / "responses.json"
        path.write_text(json.dumps(mapping), encoding="utf-8")
        return str(path)

    return write


@pytest.fixture
def f01_responses(responses, model_output):
    return responses({"F01": model_output([("p1", "c_cash", [("F01-001", "only accept cash payments")])])})


def card(fixture_data_dir, *args):
    return ["card", *args, "--data-dir", str(fixture_data_dir), "--provider", "mock"]


def test_text_card_on_stdout(fixture_data_dir, f01_responses, capsys):
    assert main(card(fixture_data_dir, "F01", "--mock-responses", f01_responses)) == 0
    out, err = capsys.readouterr()
    assert out.startswith("VISIT CARD — Fixture Bistro (F01)\n")
    assert "Primary 1: dish-pay — DISH Pay" in out
    assert err == ""


def test_json_card_passes_checks(fixture_data_dir, f01_responses, capsys):
    assert main(card(fixture_data_dir, "F01", "--mock-responses", f01_responses, "--format", "json")) == 0
    out, _ = capsys.readouterr()
    parsed = json.loads(out)
    assert parsed["decision"] == "recommend"
    assert all(r.passed for r in run_checks(parsed, load_agent_data(fixture_data_dir)))


def test_output_file(fixture_data_dir, f01_responses, tmp_path, capsys):
    target = tmp_path / "out" / "f01.json"
    target.parent.mkdir()
    args = card(fixture_data_dir, "F01", "--mock-responses", f01_responses, "--format", "json",
                "--output", str(target))
    assert main(args) == 0
    out, _ = capsys.readouterr()
    assert out == ""
    assert json.loads(target.read_text(encoding="utf-8"))["restaurant"]["restaurant_id"] == "F01"


def test_short_card_without_mock_responses(fixture_data_dir, capsys):
    assert main(card(fixture_data_dir, "F02")) == 0
    out, _ = capsys.readouterr()
    assert "Not in the recommendation target list because the restaurant is closed." in out


def test_unknown_restaurant(fixture_data_dir, capsys):
    assert main(card(fixture_data_dir, "F99")) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.strip() == "Unknown restaurant: F99"


def test_generation_failure(fixture_data_dir, responses, tmp_path, capsys):
    path = responses({"F01": {"raw": "Sure! Here you go."}})
    target = tmp_path / "f01.txt"
    assert main(card(fixture_data_dir, "F01", "--mock-responses", path, "--output", str(target))) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert err.startswith("Generation failed for F01: ")
    assert "not valid JSON" in err
    assert not target.exists()


def test_failed_call(fixture_data_dir, responses, capsys):
    path = responses({"F01": {"error": "connection refused"}})
    assert main(card(fixture_data_dir, "F01", "--mock-responses", path)) == 1
    _, err = capsys.readouterr()
    assert err.strip() == "Generation failed for F01: connection refused"


def test_load_error(tmp_data_dir, capsys):
    (tmp_data_dir / "products" / "pain-point-product-mapping.json").write_text("{", encoding="utf-8")
    assert main(card(tmp_data_dir, "F01")) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert "pain-point-product-mapping.json" in err


def test_unknown_provider_is_usage_error(fixture_data_dir, capsys):
    with pytest.raises(SystemExit) as e:
        main(["card", "F01", "--data-dir", str(fixture_data_dir), "--provider", "gpt"])
    assert e.value.code == 2
    _, err = capsys.readouterr()
    assert "gpt" in err and "mock" in err


def test_mock_responses_only_with_mock_provider(fixture_data_dir, f01_responses, capsys):
    with pytest.raises(SystemExit) as e:
        main(["card", "F01", "--data-dir", str(fixture_data_dir), "--provider", "ollama",
              "--mock-responses", f01_responses])
    assert e.value.code == 2
    assert "--mock-responses" in capsys.readouterr().err


def test_invalid_timeout_is_usage_error(fixture_data_dir, monkeypatch, capsys):
    monkeypatch.setenv("PITCH_AGENT_LLM_TIMEOUT", "15m")
    with pytest.raises(SystemExit) as e:
        main(["card", "F01", "--data-dir", str(fixture_data_dir), "--provider", "ollama"])
    assert e.value.code == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert "PITCH_AGENT_LLM_TIMEOUT" in err and "15m" in err


def test_provider_from_environment(fixture_data_dir, monkeypatch, capsys):
    monkeypatch.setenv("PITCH_AGENT_LLM_PROVIDER", "mock")
    assert main(["card", "F05", "--data-dir", str(fixture_data_dir)]) == 0
    assert "Reviews analysed: 0" in capsys.readouterr().out


def test_console_script_exit_code(fixture_data_dir):
    script = Path(sys.executable).parent / "pitch-agent"
    result = subprocess.run(
        [str(script), "card", "F99", "--data-dir", str(fixture_data_dir), "--provider", "mock"],
        capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.strip() == "Unknown restaurant: F99"
