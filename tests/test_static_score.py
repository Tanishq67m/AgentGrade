"""TDQS static scoring (ADR 0016): spec parsing, deterministic stages, judge retries, end to end.

The real TDQS spec is not vendored (its repo has no license), so these tests use a minimal spec with
the same structure. The pinned real spec is exercised on the Mac, where the experiment runs.
"""

import json
import sys
from pathlib import Path

import pytest

from agentgrade.evaluate import run_suite
from agentgrade.mcp_client import McpToolInfo
from agentgrade.models.fake import ScriptedModel, call_tool, final_answer
from agentgrade.static_score import (
    TEMPLATE_PLACEHOLDERS,
    WEIGHTS,
    TdqsSpecError,
    compute_tdqs,
    context_signals,
    load_measured,
    parse_judge_output,
    parse_spec,
    render_static_report,
    render_user_message,
    round1,
    score_suite,
    score_tool,
    spearman,
    summarize,
    tier,
    variant_definitions,
)
from agentgrade.suite import Suite
from agentgrade.types import ModelResponse, Usage

USER_TEMPLATE = """TOOL NAME: {name}
TITLE: {title | "null"}

DESCRIPTION:
"{description}"

<input-schema>
{inputSchema JSON | "{}"}
</input-schema>

<output-schema>
{outputSchema JSON | "None provided"}
</output-schema>

<annotations>
{annotations JSON | "None provided"}
</annotations>

CONTEXT SIGNALS:
- Parameter count: {paramCount}
- Required parameters: {requiredParamCount}
- Schema description coverage: {schemaDescriptionCoverage}%
- Parameters with enums: {paramsWithEnums}
- Has nested objects: {hasNestedObjects}

<sibling-tools>
{sibling tool names, one per line | "None"}
</sibling-tools>

Respond with JSON only."""

SPEC = f"""# TDQS

## Appendix A: Tool scoring prompt

The system prompt, verbatim:

```text
You evaluate MCP tool definitions.

{{
  "scores": {{}}
}}
```

The user message template:

```text
{USER_TEMPLATE}
```

## Appendix B: Server coherence prompt

```text
not this one
```
"""


def judge_json(scores: dict[str, int], contradiction: bool = False) -> str:
    return json.dumps(
        {
            "scores": {d: {"score": s, "justification": f"{d} reason"} for d, s in scores.items()},
            "annotation_contradiction": contradiction,
            "summary": "ok",
        }
    )


ALL_FOUR = dict.fromkeys(WEIGHTS, 4)  # TDQS 4.0, tier A


def reply(text: str) -> ModelResponse:
    return ModelResponse(content=text, usage=Usage(input_tokens=10, output_tokens=5))


def tool(**overrides) -> McpToolInfo:
    base = {
        "name": "search_files",
        "description": "Find files by glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Where to search"},
                "pattern": {"type": "string"},
            },
            "required": ["path", "pattern"],
        },
        "read_only_hint": True,
        "annotations": {"readOnlyHint": True},
    }
    return McpToolInfo(**{**base, **overrides})


# --- spec ---------------------------------------------------------------------------------


def test_parse_spec_takes_both_appendix_a_blocks_only():
    prompt = parse_spec(SPEC, "abc123")
    assert prompt.system.startswith("You evaluate MCP tool definitions.")
    assert '"scores": {}' in prompt.system  # JSON inside the block is kept
    assert prompt.user_template == USER_TEMPLATE
    assert "not this one" not in prompt.system + prompt.user_template
    assert prompt.commit == "abc123" and len(prompt.sha256) == 64


def test_parse_spec_rejects_a_changed_template():
    changed = SPEC.replace("{paramCount}", "{parameterCount}")
    with pytest.raises(TdqsSpecError, match="parameterCount"):
        parse_spec(changed, "x")


def test_parse_spec_without_appendix_a():
    with pytest.raises(TdqsSpecError, match="Appendix A"):
        parse_spec("# nothing here", "x")


# --- stage 1 ------------------------------------------------------------------------------


def test_context_signals():
    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "string", "description": "x"},
            "b": {"type": "string", "enum": ["x", "y"]},
            "c": {"type": ["object", "null"]},
        },
        "required": ["a"],
    }
    assert context_signals(schema) == {
        "paramCount": 3,
        "requiredParamCount": 1,
        "schemaDescriptionCoverage": 33,
        "paramsWithEnums": 1,
        "hasNestedObjects": True,
    }


@pytest.mark.parametrize(
    ("described", "total", "expected"),
    [(1, 2, 50), (2, 3, 67), (1, 8, 13), (5, 8, 63)],  # 12.5 -> 13 and 62.5 -> 63: half UP
)
def test_coverage_rounds_half_up_like_the_reference(described, total, expected):
    props = {f"p{i}": ({"description": "d"} if i < described else {}) for i in range(total)}
    assert context_signals({"properties": props})["schemaDescriptionCoverage"] == expected


def test_zero_parameters_count_as_full_coverage():
    assert context_signals({"type": "object"})["schemaDescriptionCoverage"] == 100
    assert context_signals(None)["paramCount"] == 0


def test_user_message_fills_every_placeholder_once():
    prompt = parse_spec(SPEC, "x")
    text = render_user_message(
        prompt, tool(description="Use {name} and {paramCount} literally"), ["read_text_file", "x"]
    )
    assert "TOOL NAME: search_files" in text
    assert "TITLE: null" in text
    assert '"Use {name} and {paramCount} literally"' in text  # never re-substituted
    assert '"readOnlyHint": true' in text
    assert "<output-schema>\nNone provided" in text
    assert "Schema description coverage: 50%" in text
    assert "Has nested objects: false" in text
    assert "<sibling-tools>\nread_text_file\nx\n</sibling-tools>" in text
    for placeholder in TEMPLATE_PLACEHOLDERS - {"{name}", "{paramCount}"}:
        assert placeholder not in text


# --- stage 4 ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ((4, 2, 2, 3, 4, 2), 2.9),  # the spec's worked example (285 hundredths, a .X5 tie)
        ((5, 5, 3, 3, 5, 5), 4.3),  # calibration HIGH
        ((1, 1, 1, 1, 2, 1), 1.1),  # calibration LOW
        ((4, 2, 3, 4, 2, 2), 3.0),
    ],
)
def test_compute_tdqs_matches_the_spec(scores, expected):
    assert compute_tdqs(dict(zip(WEIGHTS, scores, strict=True))) == expected


def test_round1_is_half_up_in_integer_arithmetic():
    assert round1(285, 100) == 2.9
    assert round1(284, 100) == 2.8
    assert round1(1, 3) == 0.3


@pytest.mark.parametrize(
    ("score", "expected"), [(3.5, "A"), (3.4, "B"), (3.0, "B"), (2.9, "C"), (2.0, "C"), (1.0, "D")]
)
def test_tiers(score, expected):
    assert tier(score) == expected


def test_parse_judge_output_tolerates_a_code_fence():
    out = parse_judge_output("```json\n" + judge_json(ALL_FOUR) + "\n```")
    assert out.scores["purpose_clarity"].score == 4


@pytest.mark.parametrize(
    "bad",
    [
        judge_json({**ALL_FOUR, "purpose_clarity": 6}),  # out of range
        judge_json({d: 3 for d in list(WEIGHTS)[:5]}),  # a dimension missing
        "I think it is fine.",  # no JSON
    ],
)
def test_parse_judge_output_rejects_invalid(bad):
    with pytest.raises(ValueError):  # pydantic's ValidationError is a ValueError
        parse_judge_output(bad)


# --- stage 2 + 3: score_tool ------------------------------------------------------------------


async def test_invalid_output_is_retried_then_scored():
    judge = ScriptedModel([reply("not json"), reply(judge_json(ALL_FOUR))])
    s = await score_tool(judge, parse_spec(SPEC, "c"), tool(), ["a"], variant="v", repeat=1)
    assert (s.tdqs, s.tier, s.attempts, s.error) == (4.0, "A", 2, None)
    assert s.input_tokens == 20 and s.smells == []
    system, user = judge.received[0]
    assert system.role == "system" and user.content.startswith("TOOL NAME: search_files")
    assert judge.received_tools == [[], []]  # the judge is never offered tools


async def test_all_attempts_failing_records_an_error_not_a_score():
    judge = ScriptedModel([reply("nope")] * 3)
    s = await score_tool(judge, parse_spec(SPEC, "c"), tool(), [], variant="v", repeat=1)
    assert s.tdqs is None and s.attempts == 3 and "invalid judge output" in s.error


async def test_missing_description_is_scored_without_a_judge_call():
    judge = ScriptedModel([])
    s = await score_tool(
        judge, parse_spec(SPEC, "c"), tool(description="  "), [], variant="v", repeat=1
    )
    assert (s.tdqs, s.tier, s.flags) == (1.0, "D", ["No Description"])
    assert judge.received == []


async def test_tautology_caps_purpose_and_contradiction_is_flagged():
    scores = {**ALL_FOUR, "purpose_clarity": 5, "usage_guidelines": 2}
    judge = ScriptedModel([reply(judge_json(scores, contradiction=True))])
    s = await score_tool(
        judge, parse_spec(SPEC, "c"), tool(description="Search_Files "), [], variant="v", repeat=1
    )
    assert s.scores["purpose_clarity"] == 2
    assert s.flags == ["Tautological Description", "Annotation Contradiction"]
    assert s.smells == ["purpose_clarity", "usage_guidelines"]


# --- variants -----------------------------------------------------------------------------

NOTES_SERVER = str(Path(__file__).parent / "fixtures" / "notes_server.py")
SUITE = Suite.model_validate(
    {
        "name": "notes",
        "model": {"name": "fake"},
        "server": {"command": sys.executable, "args": [NOTES_SERVER]},
        "tools": ["list_notes", "read_note"],
        "repeats": 1,
        "variants": [
            {"name": "baseline"},
            {"name": "prompt-only", "system_prompt_suffix": "Be careful."},
            {
                "name": "better-description",
                "description_overrides": {"read_note": "Read a note. Use list_notes first."},
            },
            {"name": "no-list", "tools": ["read_note"]},
        ],
        "tasks": [
            {
                "id": "todo",
                "prompt": "What is on my todo note?",
                "checks": [{"type": "answer_contains", "expected": "AgentGrade"}],
            }
        ],
    }
)


def test_variant_definitions_apply_overrides_and_skip_removed_tools():
    server = [tool(name="list_notes"), tool(name="read_note"), tool(name="delete_note")]
    by_variant = {v.name: v for v in SUITE.variants}

    better = variant_definitions(server, SUITE, by_variant["better-description"], ["read_note"])
    assert [(t.description, sib) for t, sib in better] == [
        ("Read a note. Use list_notes first.", ["list_notes", "delete_note"])
    ]
    assert variant_definitions(server, SUITE, by_variant["no-list"], ["list_notes"]) == []
    with pytest.raises(ValueError, match="not offered"):
        variant_definitions(server, SUITE, by_variant["baseline"], ["nope"])


async def test_end_to_end_against_a_real_server_with_measured_runs(tmp_path: Path):
    # Measured side: a real suite run (scripted agent) -> results.json
    def agent(suite, variant, task, repeat):
        if variant.description_overrides:
            return ScriptedModel(
                [
                    call_tool("list_notes"),
                    call_tool("read_note", name="todo"),
                    final_answer("finish AgentGrade M2"),
                ]  # fmt: skip
            )
        return ScriptedModel([final_answer("I can't access notes.")])

    _, run_dir = await run_suite(SUITE, agent, tmp_path / "runs")
    measured = load_measured([run_dir], "notes")
    assert (measured["better-description"].passed, measured["baseline"].passed) == (1, 0)

    # Static side: baseline and prompt-only share read_note's definition -> scored once
    judge = ScriptedModel(
        [reply(judge_json(ALL_FOUR)), reply(judge_json(ALL_FOUR)),  # baseline r1, r2
         reply(judge_json({**ALL_FOUR, "usage_guidelines": 5})),     # better r1
         reply(judge_json({**ALL_FOUR, "usage_guidelines": 5}))]     # better r2
    )  # fmt: skip
    out = tmp_path / "static"
    out.mkdir()
    variants = SUITE.variants[:3]
    scores, server_info = await score_suite(
        SUITE, judge, parse_spec(SPEC, "c"), out,
        variants=variants, only_tools=["read_note"], repeats=2,
    )  # fmt: skip
    assert len(judge.received) == 4  # 2 distinct definitions x 2 repeats; prompt-only reused
    assert [s.variant for s in scores] == ["baseline"] * 2 + ["prompt-only"] * 2 + [
        "better-description"
    ] * 2
    assert server_info["server_name"] == "agentgrade-test-notes"
    snapshot = json.loads((out / "tool_definitions.json").read_text())
    read_note = next(t for t in snapshot if t["name"] == "read_note")
    assert read_note["annotations"] == {"readOnlyHint": True}  # annotations now captured
    assert len((out / "static_scores.jsonl").read_text().splitlines()) == 6

    rows = summarize(scores, [v.name for v in variants], measured)
    report = render_static_report(
        rows, suite=SUITE, server_info=server_info, judge="fake", prompt=parse_spec(SPEC, "c"),
        repeats=2, reference="baseline", scores=scores,
    )  # fmt: skip
    assert "| better-description | read_note | 4.20 (4.2-4.2) | A |" in report
    assert "1/1 (100%" in report
    assert "| better-description | +0.20 | +100 points |" in report
    assert "### read_note - baseline, prompt-only (TDQS 4.0, tier A)" in report


def test_load_measured_refuses_mixed_models_and_suites(tmp_path: Path):
    def write(name: str, suite: str, model: str) -> Path:
        d = tmp_path / name
        d.mkdir()
        runs = [{"variant": "baseline", "passed": True}]
        (d / "results.json").write_text(
            json.dumps({"suite": suite, "model": {"name": model}, "runs": runs})
        )
        return d

    a, b = write("a", "s", "m1"), write("b", "s", "m2")
    assert load_measured([a, a], "s")["baseline"].total == 2
    with pytest.raises(ValueError, match="different models"):
        load_measured([a, b], "s")
    with pytest.raises(ValueError, match="not 'other'"):
        load_measured([a], "other")


@pytest.mark.parametrize(
    ("xs", "ys", "expected"),
    [
        ([1, 2, 3, 4], [10, 20, 30, 40], 1.0),
        ([1, 2, 3, 4], [4, 3, 2, 1], -1.0),
        ([1, 1, 2, 3], [1, 2, 3, 4], 0.9487),  # ties get average ranks
        ([1, 2, 3, 4], [5, 5, 5, 5], None),
    ],
)
def test_spearman(xs, ys, expected):
    rho = spearman(xs, ys)
    assert rho == expected if expected is None else rho == pytest.approx(expected, abs=1e-4)
