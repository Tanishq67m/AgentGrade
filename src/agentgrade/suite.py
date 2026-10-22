"""Evaluation suites: tasks, checks, variants and run settings, loaded from YAML.

A suite answers: "on THIS server, with THIS model, how reliably are THESE tasks solved,
and does a change (a variant) make it better or worse?"

Variants are the before/after mechanism. Each one changes exactly one thing relative to
the baseline - the tool set, or a tool's description - so a difference in pass rate can be
attributed to that change. Description overrides let a server author test a better tool
description WITHOUT redeploying the server.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT_PLACEHOLDER = "{root}"


class _Strict(BaseModel):
    # Typos in a suite file ("expeced:") must fail loudly, not be silently ignored.
    model_config = ConfigDict(extra="forbid")


class ModelConfig(_Strict):
    provider: Literal["ollama"] = "ollama"
    name: str
    temperature: float | None = None  # None = model default; recorded in every result either way


class ServerConfig(_Strict):
    """How to start the MCP server. `{root}` in args is replaced by the per-run sandbox path."""

    command: str
    args: list[str] = Field(default_factory=list)
    fixture: Path | None = None  # copied fresh for EVERY run; the server only sees the copy
    timeout_s: float = 60.0


class AnswerNumberCheck(_Strict):
    type: Literal["answer_number"]
    expected: float
    tolerance: float = 1e-9


class AnswerContainsCheck(_Strict):
    type: Literal["answer_contains"]
    expected: str
    case_sensitive: bool = False


class AnswerRegexCheck(_Strict):
    type: Literal["answer_regex"]
    pattern: str


class ToolCalledCheck(_Strict):
    type: Literal["tool_called"]
    tool: str


Check = Annotated[
    AnswerNumberCheck | AnswerContainsCheck | AnswerRegexCheck | ToolCalledCheck,
    Field(discriminator="type"),
]


class Task(_Strict):
    id: str
    prompt: str
    checks: list[Check] = Field(min_length=1)  # every task needs at least one code-based check
    max_steps: int | None = None


class Variant(_Strict):
    name: str
    description: str = ""
    tools: list[str] | None = None  # None = suite allowlist; otherwise must be a SUBSET of it
    description_overrides: dict[str, str] = Field(default_factory=dict)


class Suite(_Strict):
    name: str
    description: str = ""
    model: ModelConfig
    server: ServerConfig
    tools: list[str] = Field(min_length=1)  # the read-only allowlist for the whole suite
    max_steps: int = Field(default=10, ge=1)
    repeats: int = Field(default=3, ge=1)
    variants: list[Variant] = Field(default_factory=lambda: [Variant(name="baseline")])
    tasks: list[Task] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate(self) -> Suite:
        _unique("task id", [t.id for t in self.tasks])
        _unique("variant name", [v.name for v in self.variants])
        allow = set(self.tools)
        for variant in self.variants:
            extra = set(variant.tools or []) - allow
            if extra:
                raise ValueError(
                    f"Variant {variant.name!r} uses tools outside the suite allowlist: "
                    f"{sorted(extra)}"
                )
            active = set(variant.tools) if variant.tools is not None else allow
            stray = set(variant.description_overrides) - active
            if stray:
                raise ValueError(
                    f"Variant {variant.name!r} overrides descriptions of tools it doesn't use: "
                    f"{sorted(stray)}"
                )
        for task in self.tasks:
            for check in task.checks:
                if isinstance(check, ToolCalledCheck) and check.tool not in allow:
                    raise ValueError(
                        f"Task {task.id!r} checks for tool {check.tool!r} not in allowlist"
                    )
        return self

    def tools_for(self, variant: Variant) -> list[str]:
        return list(variant.tools) if variant.tools is not None else list(self.tools)

    def max_steps_for(self, task: Task) -> int:
        return task.max_steps or self.max_steps


def load_suite(path: Path) -> Suite:
    """Load and validate a suite. Relative fixture paths resolve against the suite file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    suite = Suite.model_validate(data)
    fixture = suite.server.fixture
    if fixture is not None and not fixture.is_absolute():
        suite.server.fixture = (path.parent / fixture).resolve()
    if suite.server.fixture is not None and not suite.server.fixture.is_dir():
        raise ValueError(f"Fixture directory not found: {suite.server.fixture}")
    return suite


def _unique(what: str, values: list[str]) -> None:
    seen: set[str] = set()
    dupes = sorted({v for v in values if v in seen or seen.add(v)})
    if dupes:
        raise ValueError(f"Duplicate {what}: {dupes}")
