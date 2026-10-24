"""Suite checks and failure classification, on hand-built run results."""

import pytest

from agentgrade.checks import evaluate_check
from agentgrade.classify import classify
from agentgrade.runner import RunResult, StepRecord
from agentgrade.suite import (
    AnswerContainsCheck,
    AnswerNumberCheck,
    AnswerRegexCheck,
    ToolCalledCheck,
)
from agentgrade.tools import ToolResult
from agentgrade.types import ModelResponse, ToolCall, Usage


def step(i, tool=None, content="ok", error=None, answer=""):
    calls = [ToolCall(id=f"c{i}", name=tool, arguments={})] if tool else []
    results = (
        [
            ToolResult(
                call_id=f"c{i}", tool_name=tool, ok=error is None, content=content, error_type=error
            )
        ]
        if tool
        else []
    )
    return StepRecord(
        index=i, response=ModelResponse(content=answer, tool_calls=calls), tool_results=results,
        model_latency_ms=1,
    )  # fmt: skip


def run(steps, stop="final_answer", answer=None):
    return RunResult(
        model="m", task="t", stop_reason=stop, final_answer=answer, steps=steps, messages=[],
        usage=Usage(), duration_ms=1,
    )  # fmt: skip


ANSWERED = run(
    [step(1, "read_text_file"), step(2, answer="It costs $12.50")], answer="It costs $12.50"
)


@pytest.mark.parametrize(
    "check, passed",
    [
        (AnswerNumberCheck(type="answer_number", expected=12.5), True),
        (AnswerNumberCheck(type="answer_number", expected=112.5), False),
        (AnswerContainsCheck(type="answer_contains", expected="COSTS"), True),
        (AnswerContainsCheck(type="answer_contains", expected="COSTS", case_sensitive=True), False),
        (AnswerRegexCheck(type="answer_regex", pattern=r"\$\d+\.\d{2}"), True),
        (ToolCalledCheck(type="tool_called", tool="read_text_file"), True),
        (ToolCalledCheck(type="tool_called", tool="list_directory"), False),
    ],
)
def test_checks(check, passed):
    assert evaluate_check(check, ANSWERED).passed is passed


def test_checks_on_empty_answer_fail():
    empty = run([], answer=None)
    assert not evaluate_check(
        AnswerContainsCheck(type="answer_contains", expected=""), empty
    ).passed


def outcome(passed):
    return [
        evaluate_check(
            AnswerNumberCheck(type="answer_number", expected=12.5 if passed else 1), ANSWERED
        )
    ]


def test_pass():
    category, signals = classify(ANSWERED, outcome(True))
    assert category == "pass" and signals.tools_used == ["read_text_file"]


def test_wrong_answer():
    assert classify(ANSWERED, outcome(False))[0] == "wrong_answer"


def test_no_answer():
    assert classify(run([step(1, answer="")], answer=""), outcome(False))[0] == "no_answer"


def test_loop_regression_from_first_real_run():
    # Run 1 (2026-10-22): search_files returned "No matches found" 9 times in a row.
    steps = [step(1, "list_allowed_directories", "Allowed directories: /x")] + [
        step(i, "search_files", "No matches found") for i in range(2, 11)
    ]
    category, signals = classify(run(steps, stop="max_steps"), outcome(False))
    assert category == "loop"
    assert signals.longest_repeat == 9


def test_step_limit_without_repetition():
    steps = [step(i, "read_text_file", f"file {i}") for i in range(1, 11)]
    assert classify(run(steps, stop="max_steps"), outcome(False))[0] == "step_limit"


def test_error_signals_are_counted():
    steps = [
        step(1, "nope", "ERROR", "unknown_tool"),
        step(2, "read_text_file", "ERROR", "invalid_arguments"),
        step(3, "read_text_file", "ERROR", "tool_error"),
    ]
    _, signals = classify(run(steps, answer="x"), outcome(False))
    assert (signals.unknown_tool, signals.invalid_arguments, signals.tool_error) == (1, 1, 1)


def test_crash_is_harness_error_not_agent_failure():
    assert classify(None, [], crashed=True)[0] == "harness_error"


def test_regression_gave_up_from_first_suite_run():
    # Suite run 1 (2026-10-22): 23 of 25 failures were refusals on step 1 with no tool call,
    # e.g. "I don't have access to any system or database that tracks orders...". They were
    # labelled wrong_answer, which hid the real failure.
    refusal = "I don't have access to any system or database that tracks orders."
    category, signals = classify(run([step(1, answer=refusal)], answer=refusal), outcome(False))
    assert category == "gave_up"
    assert signals.tool_calls == 0


def test_wrong_answer_still_means_tools_were_used():
    explored = run([step(1, "read_text_file"), step(2, answer="not stated")], answer="not stated")
    assert classify(explored, outcome(False))[0] == "wrong_answer"


def test_regression_stopped_after_error_from_first_git_run():
    # Git suite run 1 (2026-10-24): the agent called git_log with repo_path=".", got
    # "Repository path '.' is outside the allowed repository '<path>'" - the fix was in the
    # error - and answered "please check the path" instead of retrying.
    error = "ERROR (tool_error): Repository path '.' is outside the allowed repository '/x'"
    answer = "The repository path provided is not within the allowed repository directory."
    steps = [step(1, "git_log", error, "tool_error"), step(2, answer=answer)]
    assert classify(run(steps, answer=answer), outcome(False))[0] == "stopped_after_error"


def test_one_successful_call_means_it_is_not_stopped_after_error():
    steps = [
        step(1, "git_log", "ERROR", "tool_error"),
        step(2, "git_log", "Commit history: "),  # succeeded (but empty) - a different failure
        step(3, answer="no commits"),
    ]
    assert classify(run(steps, answer="no commits"), outcome(False))[0] == "wrong_answer"
