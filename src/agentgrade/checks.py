"""Deterministic answer checks (first version - M4 turns these into suite validators).

Lesson from ADR 0008: `"12.5" in answer` is too weak ("112.5" and a reasoning dump both
pass). Here we extract the actual numbers from the clean answer and compare them.
"""

from __future__ import annotations

import math
import re

from pydantic import BaseModel

from agentgrade.runner import RunResult
from agentgrade.suite import (
    AnswerContainsCheck,
    AnswerNumberCheck,
    AnswerRegexCheck,
    Check,
    ToolCalledCheck,
)

# optional sign, digits with optional thousands commas, optional decimals
_NUMBER = re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])[-+]?\d+(?:\.\d+)?")


def numbers_in(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in _NUMBER.findall(text)]


def answer_has_number(answer: str | None, expected: float, *, tolerance: float = 1e-9) -> bool:
    """True if any number in the answer equals `expected` (12.50 == 12.5; 112.5 != 12.5)."""
    if not answer:
        return False
    return any(math.isclose(n, expected, abs_tol=tolerance) for n in numbers_in(answer))


# --- Suite checks ------------------------------------------------------------------------


class CheckOutcome(BaseModel):
    type: str
    passed: bool
    detail: str


def evaluate_check(check: Check, result: RunResult) -> CheckOutcome:
    """Every check is plain code over the clean final answer or the recorded steps."""
    answer = result.final_answer or ""
    match check:
        case AnswerNumberCheck(expected=expected, tolerance=tolerance):
            passed = answer_has_number(answer, expected, tolerance=tolerance)
            detail = f"expected number {expected}; found {numbers_in(answer) or 'none'}"
        case AnswerContainsCheck(expected=expected, case_sensitive=case_sensitive):
            haystack, needle = (
                (answer, expected) if case_sensitive else (answer.lower(), expected.lower())
            )
            passed = bool(answer) and needle in haystack
            detail = f"expected text {expected!r}"
        case AnswerRegexCheck(pattern=pattern):
            passed = re.search(pattern, answer) is not None
            detail = f"expected match for /{pattern}/"
        case ToolCalledCheck(tool=tool):
            called = [c.name for s in result.steps for c in s.response.tool_calls]
            passed = tool in called
            detail = f"expected a call to {tool!r}; called {sorted(set(called)) or 'nothing'}"
    return CheckOutcome(type=check.type, passed=passed, detail=detail)
