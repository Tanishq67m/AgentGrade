"""`agentgrade` command line.

uv run agentgrade run suites/shop.yaml
uv run agentgrade run suites/shop.yaml --repeats 5 --variants baseline,clear-search-description
uv run agentgrade static-score suites/shop.yaml --judge model_configs/judge-groq-gpt-oss-120b.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from agentgrade.evaluate import FATAL_ERRORS, RunSummary, run_suite
from agentgrade.mcp_client import McpError
from agentgrade.models.factory import build_model
from agentgrade.report import load_results, reclassify, write_report
from agentgrade.static_score import (
    TDQS_COMMIT,
    StaticScore,
    TdqsSpecError,
    load_measured,
    load_tdqs_prompt,
    new_static_run_dir,
    render_static_report,
    score_suite,
    summarize,
)
from agentgrade.suite import load_model_config, load_suite


def _csv(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def load_dotenv(path: Path) -> None:
    """Minimal .env support (KEY=VALUE lines) so API keys stay out of the shell and the repo.

    Existing environment variables win. `.env` is git-ignored.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.removeprefix("export ").strip()
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def _print_progress(run: RunSummary) -> None:
    mark = "PASS" if run.passed else f"FAIL ({run.category})"
    print(
        f"  {run.variant:28} {run.task_id:24} r{run.repeat}  {mark:22} "
        f"{run.signals.steps:>2} steps  {run.duration_ms / 1000:5.1f}s",
        flush=True,
    )


async def _run(args: argparse.Namespace) -> int:
    suite = load_suite(args.suite)
    if args.model:
        suite = suite.model_copy(update={"model": load_model_config(args.model)})
    cfg = suite.model
    print(f"Suite: {suite.name} - {cfg.provider} model {cfg.name}, temperature {cfg.temperature}")
    try:
        model = build_model(cfg)  # ONE instance for the whole suite: shared rate-limit pacing
    except FATAL_ERRORS as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 1
    try:
        result, out_dir = await run_suite(
            suite,
            lambda *_: model,
            args.runs_dir,
            repeats=args.repeats,
            only_variants=_csv(args.variants),
            only_tasks=_csv(args.tasks),
            on_run=_print_progress,
            describe_model=model.describe,
        )
    except FATAL_ERRORS as exc:
        print(f"\nStopped: {exc}", file=sys.stderr)
        return 1
    finally:
        await model.aclose()

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


def _print_static(score: StaticScore, reused: bool) -> None:
    if reused:
        what = "same definition as an earlier variant"
    elif score.error:
        what = f"FAILED ({score.error[:60]})"
    else:
        what = f"TDQS {score.tdqs}  tier {score.tier}"
    print(f"  {score.variant:28} {score.tool:18} r{score.repeat}  {what}", flush=True)


async def _static(args: argparse.Namespace) -> int:
    suite = load_suite(args.suite)
    names = _csv(args.variants)
    known = [v.name for v in suite.variants]
    unknown = sorted(set(names or []) - set(known))
    if unknown:
        raise ValueError(f"Unknown variant(s): {unknown}. Known: {known}")
    variants = [v for v in suite.variants if not names or v.name in names]
    if args.reference and args.reference not in [v.name for v in variants]:
        raise ValueError(f"--reference {args.reference!r} is not among the selected variants")
    measured = load_measured(args.compare, suite.name) if args.compare else {}
    judge_cfg = load_model_config(args.judge)
    print(f"Suite: {suite.name} - TDQS judge {judge_cfg.name}, {args.repeats} scoring(s) each")
    try:
        prompt = await load_tdqs_prompt(args.runs_dir / ".cache", args.tdqs_commit)
        judge = build_model(judge_cfg)
    except (*FATAL_ERRORS, TdqsSpecError) as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 1
    out_dir = new_static_run_dir(args.runs_dir)
    try:
        scores, server_info = await score_suite(
            suite,
            judge,
            prompt,
            out_dir,
            variants=variants,
            only_tools=_csv(args.tools),
            repeats=args.repeats,
            on_score=_print_static,
        )
    except (*FATAL_ERRORS, McpError) as exc:
        print(f"\nStopped: {exc}", file=sys.stderr)
        return 1
    finally:
        await judge.aclose()

    rows = summarize(scores, [v.name for v in variants], measured)
    report = render_static_report(
        rows,
        suite=suite,
        server_info=server_info,
        judge=judge_cfg.name,
        prompt=prompt,
        repeats=args.repeats,
        reference=args.reference,
        scores=scores,
    )
    path = out_dir / "static_report.md"
    path.write_text(report, encoding="utf-8")
    failed = sum(s.error is not None for s in scores)
    print(f"\n{len(scores)} scorings, {failed} failed.")
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
    run.add_argument("--model", type=Path, help="model config file overriding the suite's model")
    rep = sub.add_parser("report", help="re-render report.md for an existing run folder")
    rep.add_argument("run_dir", type=Path)
    st = sub.add_parser(
        "static-score",
        help="score tool descriptions with Glama's TDQS and compare with measured pass rates",
    )
    st.add_argument("suite", type=Path)
    st.add_argument("--judge", type=Path, required=True, help="model config file for the judge")
    st.add_argument("--tools", help="comma-separated tools to score (default: the suite's tools)")
    st.add_argument("--variants", help="comma-separated variant names (default: all)")
    st.add_argument("--repeats", type=int, default=5, help="scorings per definition (default 5)")
    st.add_argument(
        "--compare", type=Path, nargs="+", help="suite run folders with measured pass rates"
    )
    st.add_argument("--reference", help="variant to compare the others against")
    st.add_argument("--tdqs-commit", default=TDQS_COMMIT, help="TDQS spec commit to use")
    st.add_argument("--runs-dir", type=Path, default=Path("runs"))
    args = parser.parse_args(argv)
    load_dotenv(Path(".env"))
    try:
        if args.command == "report":
            return _report(args)
        if args.command == "static-score":
            return asyncio.run(_static(args))
        return asyncio.run(_run(args))
    except (ValueError, FileNotFoundError) as exc:  # bad suite file / unknown variant
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
