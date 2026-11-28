"""Command-line interface (contracts/cli.md)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pitch_agent.agent import generate_card
from pitch_agent.analysis import GenerationError
from pitch_agent.config import resolve_llm_config
from pitch_agent.evaluation.labels import GoldLabelError
from pitch_agent.evaluation.runner import (
    OutputInsideDataError,
    RunAborted,
    RunFolderError,
    RunInterrupted,
    run_evaluation,
)
from pitch_agent.llm import ConfigError, LLMClient
from pitch_agent.llm.factory import create_llm
from pitch_agent.loaders import LoadError, UnknownRestaurantError, load_agent_data
from pitch_agent.render import render_text

EXIT_OK, EXIT_FAILURE, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 130


def _common_options() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-dir", default="data", help="root of the data folder (default: data)")
    common.add_argument("--provider", help="LLM provider (env PITCH_AGENT_LLM_PROVIDER, default ollama)")
    common.add_argument("--model", help="model name (env PITCH_AGENT_LLM_MODEL, default per provider)")
    common.add_argument("--mock-responses", help="only with --provider mock: JSON file {restaurant_id: response}")
    return common


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pitch-agent", description="Restaurant visit card agent")
    commands = parser.add_subparsers(dest="command", required=True)
    card = commands.add_parser("card", parents=[_common_options()], help="generate one visit card")
    card.set_defaults(subparser=card)
    card.add_argument("restaurant_id")
    card.add_argument("--format", choices=("text", "json"), default="text")
    card.add_argument("--output", help="write the card to this file instead of stdout")
    evaluate = commands.add_parser("eval", parents=[_common_options()], help="run the evaluation")
    evaluate.set_defaults(subparser=evaluate)
    evaluate.add_argument("--labels", default="data/eval/expected.csv", help="gold-label file")
    evaluate.add_argument("--out-dir", default="runs", help="parent folder of the run folder (default: runs)")
    return parser


def _llm(parser: argparse.ArgumentParser, args: argparse.Namespace) -> LLMClient:
    options = {"responses": args.mock_responses} if args.mock_responses else {}
    config = resolve_llm_config(provider=args.provider, model=args.model, options=options)
    if args.mock_responses and config.provider != "mock":
        parser.error("--mock-responses can only be used with --provider mock")
    try:
        return create_llm(config)
    except ConfigError as e:
        parser.error(str(e))


def _run_card(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    llm = _llm(parser, args)
    try:
        data = load_agent_data(Path(args.data_dir))
        visit_card = generate_card(args.restaurant_id, data, llm).to_dict()
    except (UnknownRestaurantError, LoadError) as e:
        print(str(e), file=sys.stderr)
        return EXIT_USAGE
    except GenerationError as e:
        print(f"Generation failed for {args.restaurant_id}: {e}", file=sys.stderr)
        return EXIT_FAILURE

    if args.format == "json":
        text = json.dumps(visit_card, indent=2, ensure_ascii=False) + "\n"
    else:
        text = render_text(visit_card)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return EXIT_OK


def _summary(run) -> str:
    lines = []
    for name, metric in run.metrics.items():
        status = "n/a" if metric["met"] is None else "met" if metric["met"] else "not met"
        lines.append(f"{name}  {metric['value']}  target {metric['target']}  {status}")
    lines.append(f"Run folder: {run.run_dir}")
    return "\n".join(lines) + "\n"


def _run_eval(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    try:
        return _evaluate(parser, args)
    except KeyboardInterrupt:  # before the run folder exists (afterwards: RunInterrupted)
        print("Run interrupted; no run folder was created", file=sys.stderr)
        return EXIT_INTERRUPTED


def _evaluate(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    llm = _llm(parser, args)
    try:
        run = run_evaluation(Path(args.data_dir), Path(args.labels), Path(args.out_dir), llm)
    except OutputInsideDataError as e:
        parser.error(str(e))
    except (GoldLabelError, LoadError) as e:
        print(str(e), file=sys.stderr)
        return EXIT_USAGE
    except (RunFolderError, RunAborted) as e:
        print(str(e), file=sys.stderr)
        return EXIT_FAILURE
    except RunInterrupted as e:
        print(str(e), file=sys.stderr)
        return EXIT_INTERRUPTED
    sys.stdout.write(_summary(run))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "eval":
        return _run_eval(args.subparser, args)
    return _run_card(args.subparser, args)
