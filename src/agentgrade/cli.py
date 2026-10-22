"""`agentgrade` command line.

uv run agentgrade run suites/shop.yaml
uv run agentgrade run suites/shop.yaml --repeats 5 --variants baseline,clear-search-description
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from agentgrade.evaluate import FATAL_ERRORS, RunSummary, run_suite
from agentgrade.models.ollama import OllamaModel
from agentgrade.report import load_results, reclassify, write_report
from agentgrade.suite import Suite, Task, Variant, load_suite


def _csv(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def _ollama_factory(suite: Suite, variant: Variant, task: Task, repeat: int) -> OllamaModel:
    return OllamaModel(suite.model.name, temperature=suite.model.temperature)


def _print_progress(run: RunSummary) -> None:
    mark = "PASS" if run.passed else f"FAIL ({run.category})"
    print(
        f"  {run.variant:28} {run.task_id:24} r{run.repeat}  {mark:22} "
        f"{run.signals.steps:>2} steps  {run.duration_ms / 1000:5.1f}s",
        flush=True,
    )


async def _run(args: argparse.Namespace) -> int:
    suite = load_suite(args.suite)
    describe_model = OllamaModel(suite.model.name)
    print(f"Suite: {suite.name} - model {suite.model.name}, temperature {suite.model.temperature}")
    try:
        result, out_dir = await run_suite(
            suite,
            _ollama_factory,
            args.runs_dir,
            repeats=args.repeats,
            only_variants=_csv(args.variants),
            only_tasks=_csv(args.tasks),
            on_run=_print_progress,
            describe_model=describe_model.describe,
        )
    except FATAL_ERRORS as exc:
        print(f"\nStopped: {exc}", file=sys.stderr)
        return 1
    finally:
        await describe_model.aclose()

    report = write_report(result, out_dir)
    passed = sum(r.passed for r in result.runs)
    print(f"\n{passed}/{len(result.runs)} runs passed.")
    print(f"Report:  {report}")
    print(f"Results: {out_dir / 'results.json'}")
    return 0


def _report(args: argparse.Namespace) -> int:
    result = reclassify(load_results(args.run_dir))
    path = write_report(result, args.run_dir)
    passed = sum(r.passed for r in result.runs)
    print(f"{passed}/{len(result.runs)} runs passed (categories re-derived with current rules).")
    print(f"Report: {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentgrade", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run an evaluation suite")
    run.add_argument("suite", type=Path)
    run.add_argument("--repeats", type=int, help="override the suite's repeats")
    run.add_argument("--variants", help="comma-separated variant names (default: all)")
    run.add_argument("--tasks", help="comma-separated task ids (default: all)")
    run.add_argument("--runs-dir", type=Path, default=Path("runs"))
    rep = sub.add_parser("report", help="re-render report.md for an existing run folder")
    rep.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            return _report(args)
        return asyncio.run(_run(args))
    except (ValueError, FileNotFoundError) as exc:  # bad suite file / unknown variant
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
