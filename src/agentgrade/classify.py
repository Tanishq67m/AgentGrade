"""Failure classification: turn a run into ONE primary category + supporting signals.

Rule-based and deterministic, derived only from what the trace recorded. Categories are
ordered so each run gets the most specific explanation that applies.

  pass            all checks passed
  harness_error   AgentGrade/model/server crashed mid-run (not the agent's fault)
  loop            hit max_steps while repeating a tool call that kept returning the same result
  step_limit      hit max_steps without such a repetition
  no_answer       stopped with an empty final answer
  wrong_answer    gave an answer, but a check failed
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from agentgrade.checks import CheckOutcome
from agentgrade.runner import RunResult

Category = Literal["pass", "harness_error", "loop", "step_limit", "no_answer", "wrong_answer"]

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
    if checks and all(c.passed for c in checks):
        return "pass", signals
    if result.stop_reason == "max_steps":
        return ("loop" if signals.longest_repeat >= LOOP_MIN_REPEATS else "step_limit"), signals
    if not (result.final_answer or "").strip():
        return "no_answer", signals
    return "wrong_answer", signals
