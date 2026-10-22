"""Turn a SuiteResult into a markdown report a developer can act on.

Honesty rules: every pass rate is shown with its
run count and a 95% Wilson confidence interval, and small samples are labelled. With 3-5
repeats an interval is wide - the report says so instead of pretending to precision.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from pathlib import Path

from agentgrade.evaluate import RunSummary, SuiteResult

SMALL_SAMPLE = 10


def wilson_interval(passes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a pass rate. Stays sensible at 0/n and n/n (unlike p±1.96σ)."""
    if n == 0:
        return 0.0, 0.0
    p = passes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _rate(runs: list[RunSummary]) -> str:
    n = len(runs)
    k = sum(r.passed for r in runs)
    lo, hi = wilson_interval(k, n)
    return f"{k}/{n} ({k / n:.0%}, 95% CI {lo:.0%}-{hi:.0%})" if n else "-"


def _failures(runs: list[RunSummary]) -> str:
    counts = Counter(r.category for r in runs if not r.passed)
    return ", ".join(f"{cat} x{n}" for cat, n in counts.most_common()) or "-"


def _median_s(runs: list[RunSummary]) -> str:
    return f"{statistics.median(r.duration_ms for r in runs) / 1000:.1f}s" if runs else "-"


def _mean_tokens(runs: list[RunSummary]) -> str:
    if not runs:
        return "-"
    return f"{statistics.mean(r.input_tokens + r.output_tokens for r in runs):,.0f}"


def render_report(result: SuiteResult) -> str:
    variants = list(dict.fromkeys(r.variant for r in result.runs))
    tasks = list(dict.fromkeys(r.task_id for r in result.runs))
    by = {
        (v, t): [r for r in result.runs if r.variant == v and r.task_id == t]
        for v in variants
        for t in tasks
    }
    repeats = max((r.repeat for r in result.runs), default=0)
    env, model, server = result.environment, result.model, result.server
    lines: list[str] = []
    add = lines.append

    add(f"# AgentGrade report - {result.suite}\n")
    add(f"Run `{result.suite_run_id}` - {result.started_at[:19]}Z to {result.finished_at[:19]}Z\n")
    add("| | |\n|---|---|")
    digest = (model.get("digest") or "unknown")[:12]
    add(
        f"| Model | `{model.get('name')}` (digest `{digest}`, temperature {model.get('temperature')}) |"
    )
    add(
        f"| Server | {server.get('server_name')} {server.get('server_version')} (protocol {server.get('protocol_version')}) |"
    )
    add(
        f"| Runs | {len(result.runs)} = {len(variants)} variant(s) x {len(tasks)} task(s) x {repeats} repeat(s) |"
    )
    git = env.get("git") or {}
    add(
        f"| Code | agentgrade {env.get('agentgrade_version')}, commit `{(git.get('commit') or 'n/a')[:7]}`{' (dirty)' if git.get('dirty') else ''} |"
    )
    add(
        f"| Environment | Python {env.get('python')}, Node {env.get('node')}, {env.get('platform')} |\n"
    )

    add("## Summary by variant\n")
    add("| Variant | Pass rate | Failures | Median time | Mean tokens |\n|---|---|---|---|---|")
    for v in variants:
        runs = [r for r in result.runs if r.variant == v]
        add(
            f"| {v} | {_rate(runs)} | {_failures(runs)} | {_median_s(runs)} | {_mean_tokens(runs)} |"
        )
    add("")

    if len(variants) > 1:
        base = variants[0]
        add(f"## Change vs `{base}`\n")
        add("| Task | " + " | ".join(variants) + " |\n|---|" + "---|" * len(variants))
        for t in tasks:
            cells = [f"{sum(r.passed for r in by[(v, t)])}/{len(by[(v, t)])}" for v in variants]
            add(f"| {t} | " + " | ".join(cells) + " |")
        add("")

    add("## Detail by task\n")
    for t in tasks:
        add(f"### {t}\n")
        add(
            "| Variant | Pass rate | Failures | Median steps | Example answer |\n|---|---|---|---|---|"
        )
        for v in variants:
            runs = by[(v, t)]
            steps = statistics.median(r.signals.steps for r in runs) if runs else 0
            answer = next((r.final_answer for r in runs if r.final_answer), None)
            shown = (answer or "-").replace("\n", " ").replace("|", "\\|")[:80]
            add(f"| {v} | {_rate(runs)} | {_failures(runs)} | {steps:g} | {shown} |")
        add("")

    failed = [r for r in result.runs if not r.passed]
    if failed:
        add("## Failed runs\n")
        add("| Variant | Task | # | Category | Why | Trace |\n|---|---|---|---|---|---|")
        for r in failed:
            if r.error:
                why = r.error
            else:
                why = "; ".join(c.detail for c in r.checks if not c.passed) or r.stop_reason or ""
                if r.category == "loop":
                    why = (
                        f"same tool returned an identical result {r.signals.longest_repeat}x in a row; "
                        + why
                    )
            add(
                f"| {r.variant} | {r.task_id} | {r.repeat} | {r.category} | {why[:120]} | `{r.trace}` |"
            )
        add("")

    add("## How to read this\n")
    add(
        "- A run passes only when **every** code-based check passes. No model grades another model."
    )
    add(
        "- Categories: `loop` = step limit hit while one tool kept returning the same result; "
        "`step_limit` = step limit without repetition; `wrong_answer` = answered but a check failed; "
        "`no_answer`; `harness_error` = infrastructure failure, not the agent's fault."
    )
    n_cell = repeats
    if n_cell < SMALL_SAMPLE:
        add(
            f"- **Small sample:** {n_cell} repeat(s) per task. The 95% intervals are wide; treat "
            "differences between variants as indicative unless the intervals clearly separate."
        )
    add("- Every run's full trace (every model call, tool call and result) is in `traces/`.")
    return "\n".join(lines) + "\n"


def write_report(result: SuiteResult, out_dir: Path) -> Path:
    path = out_dir / "report.md"
    path.write_text(render_report(result), encoding="utf-8")
    return path
