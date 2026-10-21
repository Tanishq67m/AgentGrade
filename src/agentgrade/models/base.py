"""The one interface every model provider must implement.

The runner depends only on this Protocol, never on a specific provider, so
adding a paid provider later means writing one new adapter - nothing else changes.
"""

from __future__ import annotations

from typing import Protocol

from agentgrade.types import Message, ModelResponse, ToolSpec


class ModelAdapter(Protocol):
    name: str  # e.g. "ollama:qwen3:4b" - recorded in every result

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        """Send the full conversation + available tools; return the model's next move."""
        ...
