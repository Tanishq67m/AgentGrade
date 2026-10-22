"""Failure classification: turn a run into ONE primary category + supporting signals.

Rule-based and deterministic, derived only from what the trace recorded. Categories are
ordered so each run gets the most specific explanation that applies.

  pass            all checks passed
  harness_error   AgentGrade/model/server crashed mid-run (not the agent's fault)
  loop            hit max_steps while repeating a tool call that kept returning the same result
  step_limit      hit max_steps without such a repetition
  gave_up         answered WITHOUT CALLING ANY TOOL, and failed (e.g. "I don't have access")
  no_answer       stopped with an empty final answer
  wrong_answer    used tools and gave an answer, but a check failed

`gave_up` was added after the first full suite run (2026-10-22): 23 of 25 failures were the
model declining on step 1 without exploring, which `wrong_answer` hid.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agentgrade.checks import CheckOutcome
from agentgrade.runner import RunResult

Category = Literal[
    "pass", "harness_error", "loop", "step_limit", "gave_up", "no_answer", "wrong_answer"
]

LOOP_MIN_REPEATS = 3  # identical result from the same tool this many times in a row


class Signals(BaseModel):
    """Countable evidence, reported alongside the category."""

    steps: int = 0
    tool_calls: int = 0
    unknown_tool: int = 0
    invalid_arguments: int = 0
    tool_error: int = 0
    longest_repeat: int = 0  # longest run of same-tool + identical-result calls
    tools_used: list[str] = []


def collect_signals(result: RunResult) -> Signals:
    signals = Signals(steps=len(result.steps))
    used: list[str] = []
    streak, previous = 0, None
    for step in result.steps:
        for outcome in step.tool_results:
            signals.tool_calls += 1
            if outcome.tool_name not in used:
                used.append(outcome.tool_name)
            if outcome.error_type == "unknown_tool":
                signals.unknown_tool += 1
            elif outcome.error_type == "invalid_arguments":
                signals.invalid_arguments += 1
            elif outcome.error_type == "tool_error":
                signals.tool_error += 1
            key = (outcome.tool_name, outcome.content)
            streak = streak + 1 if key == previous else 1
            previous = key
            signals.longest_repeat = max(signals.longest_repeat, streak)
    signals.tools_used = used
    return signals


def classify(
    result: RunResult | None, checks: list[CheckOutcome], *, crashed: bool = False
) -> tuple[Category, Signals]:
    if crashed or result is None:
        return "harness_error", collect_signals(result) if result else Signals()
    signals = collect_signals(result)
    category = categorize(
        stop_reason=result.stop_reason,
        final_answer=result.final_answer,
        checks_passed=[c.passed for c in checks],
        signals=signals,
    )
    return category, signals


def categorize(
    *,
    stop_reason: str | None,
    final_answer: str | None,
    checks_passed: list[bool],
    signals: Signals,
    crashed: bool = False,
) -> Category:
    """The rules, on plain recorded data - so stored results can be re-classified later."""
    if crashed:
        return "harness_error"
    if checks_passed and all(checks_passed):
        return "pass"
    if stop_reason == "max_steps":
        return "loop" if signals.longest_repeat >= LOOP_MIN_REPEATS else "step_limit"
    if signals.tool_calls == 0 and (final_answer or "").strip():
        return "gave_up"
    if not (final_answer or "").strip():
        return "no_answer"
    return "wrong_answer"
