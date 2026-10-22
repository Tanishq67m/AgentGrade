"""A scripted, deterministic model for tests.

Real models can't be made to fail on command. This one returns pre-written
responses in order, so tests can force any scenario (wrong tool, bad args,
infinite loop) for free and with the same result every time.
"""

from __future__ import annotations

import itertools
from typing import Any

from agentgrade.types import Message, ModelResponse, ToolCall, ToolSpec, Usage

_ids = itertools.count(1)


def call_tool(tool_name: str, /, *, usage: Usage | None = None, **arguments: Any) -> ModelResponse:
    """Build a response in which the model requests one tool call.

    `tool_name` is positional-only (the `/`), so a tool argument that is itself called
    `name` - e.g. call_tool("read_note", name="todo") - lands in `arguments`, not here.
    """
    return ModelResponse(
        tool_calls=[ToolCall(id=f"call_{next(_ids)}", name=tool_name, arguments=arguments)],
        usage=usage or Usage(),
    )


def final_answer(text: str, usage: Usage | None = None) -> ModelResponse:
    """Build a response in which the model gives its final text answer."""
    return ModelResponse(content=text, usage=usage or Usage())


class ScriptExhaustedError(RuntimeError):
    """The runner asked for more turns than the test scripted."""


class ScriptedModel:
    def __init__(self, responses: list[ModelResponse], name: str = "fake:scripted") -> None:
        self.name = name
        self._responses = list(responses)
        # Snapshot of what the model was sent on each call - lets tests assert that
        # tool results really were fed back into the conversation.
        self.received: list[list[Message]] = []
        self.received_tools: list[list[ToolSpec]] = []  # what the model was told about tools

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        self.received.append([m.model_copy(deep=True) for m in messages])
        self.received_tools.append(list(tools))
        if not self._responses:
            raise ScriptExhaustedError(f"No scripted response left for call #{len(self.received)}")
        return self._responses.pop(0)
