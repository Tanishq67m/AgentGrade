"""Run a whole suite: every variant x task x repeat, each in a fresh sandbox, fully traced.

Isolation per run: a fresh copy of the fixture and a fresh server process, so no state
leaks from one run into the next and every run is independently reproducible.
"""

from __future__ import annotations

import shutil
import tempfile
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agentgrade.checks import CheckOutcome, evaluate_check
from agentgrade.classify import Category, Signals, classify
from agentgrade.environment import collect_environment
from agentgrade.mcp_client import McpServerConfig, McpServerStartError, connect
from agentgrade.models.base import ModelAdapter
from agentgrade.models.ollama import OllamaModelNotFoundError, OllamaUnavailableError
from agentgrade.models.openai_compat import (
    MissingApiKeyError,
    ProviderAuthError,
    ProviderModelNotFoundError,
    ProviderRateLimitError,
)
from agentgrade.runner import DEFAULT_SYSTEM_PROMPT, RunLimits, run_agent
from agentgrade.suite import ROOT_PLACEHOLDER, Suite, Task, Variant
from agentgrade.tools import ToolRegistry
from agentgrade.trace import TraceWriter, new_run_id

# Errors that mean "the setup is broken" - retrying 50 more runs would just fail 50 more times.
FATAL_ERRORS = (
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    McpServerStartError,
    MissingApiKeyError,
    ProviderAuthError,
    ProviderModelNotFoundError,
    ProviderRateLimitError,  # retries exhausted = quota gone; the next run would fail the same way
)

# Called once per run. It may return the same instance every time (and should, for
# rate-limited providers); whoever created the instance closes it.
ModelFactory = Callable[[Suite, Variant, Task, int], ModelAdapter]


def system_prompt_for(variant: Variant) -> str:
    if variant.system_prompt_suffix:
        return f"{DEFAULT_SYSTEM_PROMPT}\n\n{variant.system_prompt_suffix.strip()}"
    return DEFAULT_SYSTEM_PROMPT


def root_cause(exc: BaseException) -> BaseException:
    """Unwrap (nested) exception groups to the first real exception."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return exc


ProgressFn = Callable[["RunSummary"], None]


class RunSummary(BaseModel):
    variant: str
    task_id: str
    repeat: int
    category: Category
    passed: bool
    checks: list[CheckOutcome]
    signals: Signals
    stop_reason: str | None
    final_answer: str | None
    input_tokens: int
    output_tokens: int
    duration_ms: float
    trace: str  # path relative to the suite run directory
    error: str | None = None


class SuiteResult(BaseModel):
    suite: str
    suite_run_id: str
    started_at: str
    finished_at: str
    model: dict[str, Any]
    server: dict[str, Any]
    environment: dict[str, Any]
    config: dict[str, Any]  # the full suite as run (variants, tasks, checks)
    runs: list[RunSummary]


async def run_suite(
    suite: Suite,
    model_factory: ModelFactory,
    runs_dir: Path,
    *,
    repeats: int | None = None,
    only_variants: list[str] | None = None,
    only_tasks: list[str] | None = None,
    on_run: ProgressFn | None = None,
    describe_model: Callable[[], Awaitable[dict[str, Any]]] | None = None,
) -> tuple[SuiteResult, Path]:
    repeats = repeats or suite.repeats
    variants = _select(suite.variants, only_variants, lambda v: v.name, "variant")
    tasks = _select(suite.tasks, only_tasks, lambda t: t.id, "task")

    suite_run_id = new_run_id()
    out_dir = runs_dir / suite_run_id
    out_dir.mkdir(parents=True)
    started = datetime.now(UTC).isoformat()
    environment = collect_environment()
    model_info = await describe_model() if describe_model else {}
    model_info = {**suite.model.model_dump(), **model_info}
    server_info: dict[str, Any] = {}

    runs: list[RunSummary] = []
    for variant in variants:
        for task in tasks:
            for repeat in range(1, repeats + 1):
                summary, info = await _run_one(
                    suite, variant, task, repeat, model_factory, out_dir, environment, model_info
                )
                server_info = server_info or info
                runs.append(summary)
                if on_run:
                    on_run(summary)

    result = SuiteResult(
        suite=suite.name,
        suite_run_id=suite_run_id,
        started_at=started,
        finished_at=datetime.now(UTC).isoformat(),
        model=model_info,
        server=server_info,
        environment=environment,
        config=suite.model_dump(mode="json"),
        runs=runs,
    )
    (out_dir / "results.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return result, out_dir


async def _run_one(
    suite: Suite,
    variant: Variant,
    task: Task,
    repeat: int,
    model_factory: ModelFactory,
    out_dir: Path,
    environment: dict[str, Any],
    model_info: dict[str, Any],
) -> tuple[RunSummary, dict[str, Any]]:
    trace_rel = Path("traces") / f"{variant.name}__{task.id}__r{repeat}.jsonl"
    model = model_factory(suite, variant, task, repeat)
    start = time.perf_counter()
    server_info: dict[str, Any] = {}
    result, error = None, None

    with tempfile.TemporaryDirectory(prefix="agentgrade-") as tmp:
        root = Path(tmp).resolve() / "sandbox"  # resolve(): macOS /var -> /private/var
        if suite.server.fixture is not None:
            shutil.copytree(suite.server.fixture, root)
        else:
            root.mkdir()
        server = McpServerConfig(
            name=suite.name,
            command=suite.server.command,
            args=[a.replace(ROOT_PLACEHOLDER, str(root)) for a in suite.server.args],
            timeout_s=suite.server.timeout_s,
        )
        with TraceWriter(out_dir / trace_rel) as trace:
            try:
                async with connect(server) as conn:
                    server_info = conn.describe()
                    registry = ToolRegistry(
                        conn.agent_tools(
                            suite.tools_for(variant),
                            description_overrides=variant.description_overrides,
                        )
                    )
                    result = await run_agent(
                        model,
                        registry,
                        task.prompt,
                        system_prompt=system_prompt_for(variant),
                        limits=RunLimits(max_steps=suite.max_steps_for(task)),
                        trace=trace,
                        metadata={
                            "suite": suite.name,
                            "variant": variant.model_dump(),
                            "task_id": task.id,
                            "repeat": repeat,
                            "model_info": model_info,
                            "server": server_info,
                            "environment": environment,
                            "sandbox_root": str(root),
                        },
                    )
            except Exception as exc:  # noqa: BLE001 - one broken run must not stop the suite
                # Errors raised inside the MCP client arrive wrapped in an ExceptionGroup
                # (anyio task groups). Unwrap first, or "Ollama is down" would look like an
                # ordinary failed run and the suite would grind through every remaining run.
                cause = root_cause(exc)
                if isinstance(cause, FATAL_ERRORS):
                    raise cause from exc
                error = f"{type(cause).__name__}: {cause}"
            # The factory owns the model's lifecycle (one shared instance can pace requests
            # across runs for rate-limited providers), so it is not closed here.

            checks = [evaluate_check(c, result) for c in task.checks] if result else []
            category, signals = classify(result, checks, crashed=error is not None)
            for outcome in checks:
                trace.event(
                    "check", check=outcome.type, passed=outcome.passed, detail=outcome.detail
                )
            trace.event("classified", category=category, signals=signals.model_dump())

    return (
        RunSummary(
            variant=variant.name,
            task_id=task.id,
            repeat=repeat,
            category=category,
            passed=category == "pass",
            checks=checks,
            signals=signals,
            stop_reason=result.stop_reason if result else None,
            final_answer=result.final_answer if result else None,
            input_tokens=result.usage.input_tokens if result else 0,
            output_tokens=result.usage.output_tokens if result else 0,
            duration_ms=(time.perf_counter() - start) * 1000,
            trace=str(trace_rel),
            error=error,
        ),
        server_info,
    )


def _select(items: list, names: list[str] | None, key: Callable, what: str) -> list:
    if not names:
        return list(items)
    known = {key(i) for i in items}
    unknown = sorted(set(names) - known)
    if unknown:
        raise ValueError(f"Unknown {what}(s): {unknown}. Known: {sorted(known)}")
    return [i for i in items if key(i) in names]
