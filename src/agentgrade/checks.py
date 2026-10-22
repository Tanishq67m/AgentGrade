"""Deterministic answer checks (first version - M4 turns these into suite validators).

Lesson from ADR 0008: `"12.5" in answer` is too weak ("112.5" and a reasoning dump both
pass). Here we extract the actual numbers from the clean answer and compare them.
"""

from __future__ import annotations

import math
import re

# optional sign, digits with optional thousands commas, optional decimals
_NUMBER = re.compile(r"(?<![\w.])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])[-+]?\d+(?:\.\d+)?")


def numbers_in(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in _NUMBER.findall(text)]


def answer_has_number(answer: str | None, expected: float, *, tolerance: float = 1e-9) -> bool:
    """True if any number in the answer equals `expected` (12.50 == 12.5; 112.5 != 12.5)."""
    if not answer:
        return False
    return any(math.isclose(n, expected, abs_tol=tolerance) for n in numbers_in(answer))
