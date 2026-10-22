"""Tools the agent can call, and the registry that validates and executes them.

The registry is the safety boundary between "the model asked for X" and
"our code ran X": it rejects unknown tools and schema-invalid arguments
*before* any function runs.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from jsonschema.validators import validator_for
from pydantic import BaseModel

from agentgrade.types import ToolCall, ToolSpec

ToolErrorType = Literal["unknown_tool", "invalid_arguments", "tool_error"]


@dataclass(frozen=True)
class Tool:
    """A callable the agent may use. `func` may be a normal or an async function."""

    name: str
    description: str
    input_schema: dict[str, Any]
    func: Callable[..., Any]

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name, description=self.description, input_schema=self.input_schema
        )


class ToolResult(BaseModel):
    """Outcome of executing one tool call. Errors are data, not exceptions."""

    call_id: str
    tool_name: str
    ok: bool
    content: str  # what the model will see
    error_type: ToolErrorType | None = None
    latency_ms: float | None = None  # filled in by the runner


class ToolRegistry:
    def __init__(self, tools: list[Tool] | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._validators: dict[str, Any] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name!r}")
        # Honour the schema's own "$schema" draft (MCP servers often send draft-07);
        # default to 2020-12 when it doesn't say.
        validator_cls = validator_for(tool.input_schema, default=Draft202012Validator)
        try:
            validator_cls.check_schema(tool.input_schema)
        except SchemaError as exc:  # a broken schema must fail loudly at startup
            raise ValueError(f"Invalid input_schema for tool {tool.name!r}: {exc.message}") from exc
        self._tools[tool.name] = tool
        self._validators[tool.name] = validator_cls(tool.input_schema)

    def specs(self) -> list[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]

    async def execute(self, call: ToolCall) -> ToolResult:
        tool = self._tools.get(call.name)
        if tool is None:
            available = ", ".join(sorted(self._tools)) or "(none)"
            return self._error(
                call, "unknown_tool", f"Unknown tool {call.name!r}. Available tools: {available}"
            )

        errors = sorted(
            self._validators[call.name].iter_errors(call.arguments), key=lambda e: list(e.path)
        )
        if errors:
            details = "; ".join(_describe_validation_error(e) for e in errors)
            return self._error(call, "invalid_arguments", f"Invalid arguments: {details}")

        try:
            value = tool.func(**call.arguments)
            if inspect.isawaitable(value):
                value = await value
        except Exception as exc:  # noqa: BLE001
            # Deliberately broad: a failing tool is an *observation* we record and show
            # to the model (can it recover?), not a crash of the evaluation itself.
            return self._error(call, "tool_error", f"{type(exc).__name__}: {exc}")

        return ToolResult(call_id=call.id, tool_name=call.name, ok=True, content=_to_text(value))

    @staticmethod
    def _error(call: ToolCall, error_type: ToolErrorType, message: str) -> ToolResult:
        return ToolResult(
            call_id=call.id,
            tool_name=call.name,
            ok=False,
            content=f"ERROR ({error_type}): {message}",
            error_type=error_type,
        )


def _describe_validation_error(error: Any) -> str:
    location = ".".join(str(p) for p in error.path) or "(root)"
    return f"{location}: {error.message}"


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, default=str, ensure_ascii=False)
