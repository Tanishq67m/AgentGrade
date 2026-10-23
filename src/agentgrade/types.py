"""Core data types shared by every part of AgentGrade.

These are provider-neutral: the runner, tools and reports only ever see these
shapes. Each model adapter translates them to/from its provider's wire format.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]


class ToolSpec(BaseModel):
    """What the model is told about a tool: name, description and argument schema."""

    name: str
    description: str
    input_schema: dict[str, Any]


class ToolCall(BaseModel):
    """A request from the model to run one tool. The model never runs it itself."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    # Set when the model's arguments couldn't be parsed (e.g. malformed JSON). That's the
    # MODEL's mistake, so it's reported back as invalid_arguments - not a harness crash.
    parse_error: str | None = None


class Message(BaseModel):
    """One entry in the conversation history sent to the model on every turn."""

    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)  # only on assistant messages
    tool_call_id: str | None = None  # only on tool messages: which call this answers
    tool_name: str | None = None  # only on tool messages


class Usage(BaseModel):
    """Token counts reported by the provider for one model call."""

    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


class ModelResponse(BaseModel):
    """What a model returns for one call: either tool calls, a final answer, or both."""

    content: str = ""  # the answer / visible text - never contains reasoning
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    # Reasoning from "thinking" models. Kept for traces (explains *why* an agent failed),
    # never sent back as part of the conversation and never treated as the answer.
    thinking: str = ""
    # Time spent waiting on provider rate limits (free tiers). Excluded from latency metrics.
    rate_limit_wait_ms: float = 0.0
    # What the provider reports about itself (served model id, fingerprint) - for reproducibility.
    provider_meta: dict[str, Any] = Field(default_factory=dict)
