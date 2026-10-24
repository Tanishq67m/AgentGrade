"""End to end: suite -> variants x tasks x repeats -> real stdio MCP server -> results + report."""

import json
import sys
from pathlib import Path

from agentgrade.evaluate import run_suite
from agentgrade.models.fake import ScriptedModel, call_tool, final_answer
from agentgrade.report import render_report, wilson_interval, write_report
from agentgrade.suite import Suite
from agentgrade.trace import read_trace

NOTES_SERVER = str(Path(__file__).parent / "fixtures" / "notes_server.py")

SUITE = Suite.model_validate(
    {
        "name": "notes",
        "model": {"name": "fake", "temperature": 0.7},
        "server": {"command": sys.executable, "args": [NOTES_SERVER]},
        "tools": ["list_notes", "read_note"],
        "repeats": 2,
        "max_steps": 4,
        "variants": [
            {"name": "baseline"},
            {
                "name": "better-description",
                "description_overrides": {"read_note": "Read a note. Use list_notes first."},
            },
        ],
        "tasks": [
            {
                "id": "todo",
                "prompt": "What is on my todo note?",
                "checks": [
                    {"type": "answer_contains", "expected": "AgentGrade"},
                    {"type": "tool_called", "tool": "read_note"},
                ],
            }
        ],
    }
)

created: list[ScriptedModel] = []


def factory(suite, variant, task, repeat):
    if variant.name == "baseline":  # baseline agent gets stuck guessing note names
        script = [call_tool("read_note", name="to-do") for _ in range(4)]
    else:
        script = [call_tool("list_notes"), call_tool("read_note", name="todo"),
                  final_answer("finish AgentGrade M2")]  # fmt: skip
    model = ScriptedModel(script)
    created.append(model)
    return model


async def test_suite_run_produces_results_traces_and_report(tmp_path: Path):
    created.clear()
    result, out_dir = await run_suite(SUITE, factory, tmp_path)

    assert len(result.runs) == 4  # 2 variants x 1 task x 2 repeats
    baseline = [r for r in result.runs if r.variant == "baseline"]
    better = [r for r in result.runs if r.variant == "better-description"]
    assert all(r.category == "loop" and not r.passed for r in baseline)
    assert all(r.passed for r in better)
    assert result.server["server_name"] == "agentgrade-test-notes"
    assert result.environment["python"]

    # results.json is complete, plain JSON
    saved = json.loads((out_dir / "results.json").read_text())
    assert len(saved["runs"]) == 4 and saved["config"]["name"] == "notes"

    # each run has its own trace, ending with checks + classification
    trace = read_trace(out_dir / better[0].trace)
    assert trace[0]["metadata"]["variant"]["name"] == "better-description"
    assert [e["type"] for e in trace][-3:] == ["check", "check", "classified"]

    report = write_report(result, out_dir).read_text()
    assert "| baseline | 0/2" in report
    assert "| better-description | 2/2" in report
    assert "Small sample" in report
    assert "loop" in report


async def test_description_override_reaches_the_model_but_not_the_server(tmp_path: Path):
    created.clear()
    await run_suite(SUITE, factory, tmp_path, only_variants=["better-description"], repeats=1)
    shown = {t.name: t.description for t in created[0].received_tools[0]}
    assert shown["read_note"] == "Read a note. Use list_notes first."
    assert shown["list_notes"] == "List the names of all notes."  # untouched


async def test_crashing_run_is_recorded_and_suite_continues(tmp_path: Path):
    def crashing_factory(suite, variant, task, repeat):
        return ScriptedModel([])  # raises on first call

    result, _ = await run_suite(SUITE, crashing_factory, tmp_path, only_variants=["baseline"])
    assert [r.category for r in result.runs] == ["harness_error", "harness_error"]
    assert "ScriptExhaustedError" in result.runs[0].error
    assert "harness_error" in render_report(result)


def test_wilson_interval_is_honest_about_small_samples():
    lo, hi = wilson_interval(3, 3)
    assert hi == 1.0 and lo < 0.5  # 3/3 is NOT proof of 100% reliability
    lo, hi = wilson_interval(0, 5)
    assert lo == 0.0 and hi > 0.4
    assert wilson_interval(0, 0) == (0.0, 0.0)


async def test_regression_fatal_error_inside_mcp_context_stops_the_suite(tmp_path: Path):
    # Bug found in M4: errors raised inside `async with connect(...)` arrive wrapped in an
    # ExceptionGroup, so "Ollama is down" was recorded as a normal failed run and the suite
    # kept going. It must stop immediately instead.
    import pytest

    from agentgrade.models.ollama import OllamaUnavailableError

    class DownModel:
        name = "ollama:down"

        async def complete(self, messages, tools):
            raise OllamaUnavailableError("Could not connect to Ollama")

    calls = []

    def factory(suite, variant, task, repeat):
        calls.append(repeat)
        return DownModel()

    with pytest.raises(OllamaUnavailableError):
        await run_suite(SUITE, factory, tmp_path)
    assert calls == [1]  # stopped after the first run, not after all 4


async def test_system_prompt_suffix_reaches_the_model(tmp_path: Path):
    suite = SUITE.model_copy(
        update={
            "variants": [
                SUITE.variants[0].model_copy(
                    update={"name": "agent-context", "system_prompt_suffix": "Explore first."}
                )
            ]
        }
    )
    created.clear()

    def solver(suite, variant, task, repeat):
        model = ScriptedModel([call_tool("read_note", name="todo"), final_answer("AgentGrade")])
        created.append(model)
        return model

    await run_suite(suite, solver, tmp_path, repeats=1)
    system = created[0].received[0][0]
    assert system.role == "system" and system.content.endswith("Explore first.")


async def test_report_command_reclassifies_stored_results(tmp_path: Path):
    from agentgrade.cli import main
    from agentgrade.report import load_results

    def refuser(suite, variant, task, repeat):
        return ScriptedModel([final_answer("I don't have access to that.")])

    _, out_dir = await run_suite(SUITE, refuser, tmp_path, only_variants=["baseline"], repeats=1)
    # simulate a results.json written by an older classifier
    stored = load_results(out_dir)
    stale = stored.model_copy(
        update={"runs": [r.model_copy(update={"category": "wrong_answer"}) for r in stored.runs]}
    )
    (out_dir / "results.json").write_text(stale.model_dump_json())

    assert main(["report", str(out_dir)]) == 0
    assert "gave_up" in (out_dir / "report.md").read_text()


async def test_one_shared_model_instance_serves_every_run(tmp_path: Path):
    # Rate-limit pacing lives in the model instance, so the CLI passes ONE instance for the
    # whole suite. The suite must not close it between runs.
    class Shared(ScriptedModel):
        closed = False

        async def aclose(self):
            self.closed = True

    shared = Shared([call_tool("read_note", name="todo"), final_answer("AgentGrade")] * 4)
    result, _ = await run_suite(SUITE, lambda *_: shared, tmp_path, only_variants=["baseline"])
    assert [r.passed for r in result.runs] == [True, True]
    assert shared.closed is False


async def test_report_times_exclude_rate_limit_waits(tmp_path: Path):
    from agentgrade.types import ModelResponse

    def queued(suite, variant, task, repeat):
        return ScriptedModel([
            ModelResponse(tool_calls=call_tool("read_note", name="todo").tool_calls,
                          rate_limit_wait_ms=60_000),
            ModelResponse(content="AgentGrade", rate_limit_wait_ms=30_000),
        ])  # fmt: skip

    result, _ = await run_suite(SUITE, queued, tmp_path, only_variants=["baseline"], repeats=1)
    assert result.runs[0].rate_limit_wait_ms == 90_000
    report = render_report(result)
    assert "| Rate-limit waits | 90s" in report
    assert (
        "| baseline | 1/1" in report
        and "-" not in report.split("| baseline | 1/1")[1].split("|")[2]
    )
