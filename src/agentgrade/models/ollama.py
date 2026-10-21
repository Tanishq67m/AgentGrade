"""Adapter for a local Ollama server (free, runs on your own machine).

Talks to Ollama's HTTP API directly with httpx so the exact JSON sent and
received is visible. API reference: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import httpx

from agentgrade.types import Message, ModelResponse, ToolCall, ToolSpec, Usage

DEFAULT_BASE_URL = "http://localhost:11434"
THINK_CLOSE_TAG = "</think>"
THINK_OPEN_TAG = "<think>"


class OllamaError(RuntimeError):
    """Base class for Ollama adapter failures."""


class OllamaUnavailableError(OllamaError):
    """Ollama is not running / not reachable."""


class OllamaModelNotFoundError(OllamaError):
    """The requested model has not been pulled."""


class OllamaResponseError(OllamaError):
    """Ollama returned something we couldn't interpret."""


class OllamaModel:
    def __init__(
        self,
        model: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        think: bool | None = None,
        temperature: float | None = None,
        timeout_s: float = 300.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self.name = f"ollama:{model}"
        # None = don't send the option (model default). True/False is only honoured by
        # models that support toggling; always-thinking models (e.g. *-thinking-2507) ignore it.
        self._think = think
        self._temperature = temperature
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout_s)

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        payload = self.build_payload(messages, tools)
        try:
            response = await self._client.post("/api/chat", json=payload)
        except httpx.ConnectError as exc:
            raise OllamaUnavailableError(
                "Could not connect to Ollama. Is it running? Open the Ollama app or run "
                "`ollama serve`."
            ) from exc

        if response.status_code == 404:
            raise OllamaModelNotFoundError(
                f"Model {self.model!r} not found. Run: ollama pull {self.model}"
            )
        if response.status_code >= 400:
            raise OllamaResponseError(
                f"Ollama returned HTTP {response.status_code}: {response.text}"
            )

        return self.parse_response(response.json())

    def build_payload(self, messages: list[Message], tools: list[ToolSpec]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_ollama_message(m) for m in messages],
            "tools": [_to_ollama_tool(t) for t in tools],
            "stream": False,
        }
        if self._think is not None:
            payload["think"] = self._think
        if self._temperature is not None:
            payload["options"] = {"temperature": self._temperature}
        return payload

    @staticmethod
    def parse_response(data: dict[str, Any]) -> ModelResponse:
        message = data.get("message")
        if not isinstance(message, dict):
            raise OllamaResponseError(f"Response has no 'message' object: {data!r}")

        tool_calls = [_parse_tool_call(raw) for raw in message.get("tool_calls") or []]
        thinking, content = split_thinking(
            message.get("thinking") or "", message.get("content") or ""
        )
        return ModelResponse(
            content=content,
            thinking=thinking,
            tool_calls=tool_calls,
            usage=Usage(
                input_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            ),
        )

    async def aclose(self) -> None:
        await self._client.aclose()


def split_thinking(thinking: str, content: str) -> tuple[str, str]:
    """Separate reasoning from the answer.

    Normally Ollama puts reasoning in `message.thinking`. But some models leak it into
    `content`: Qwen3 *-thinking-2507 templates insert the opening <think> themselves, so the
    output holds the reasoning, then only a closing </think>, then the real answer.
    Everything before the LAST </think> is reasoning; everything after it is the answer.
    """
    if THINK_CLOSE_TAG in content:
        leaked, _, content = content.rpartition(THINK_CLOSE_TAG)
        leaked = leaked.replace(THINK_OPEN_TAG, "").strip()
        thinking = "\n\n".join(part for part in (thinking.strip(), leaked) if part)
    return thinking.strip(), content.strip()


def _to_ollama_message(message: Message) -> dict[str, Any]:
    out: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        out["tool_calls"] = [
            {"function": {"name": c.name, "arguments": c.arguments}} for c in message.tool_calls
        ]
    if message.role == "tool" and message.tool_name:
        out["tool_name"] = message.tool_name
    return out


def _to_ollama_tool(tool: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }


def _parse_tool_call(raw: dict[str, Any]) -> ToolCall:
    function = raw.get("function") or {}
    name = function.get("name")
    if not name:
        raise OllamaResponseError(f"Tool call without a function name: {raw!r}")

    arguments = function.get("arguments") or {}
    if isinstance(arguments, str):  # documented as an object, but be defensive
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as exc:
            raise OllamaResponseError(f"Tool arguments are not valid JSON: {arguments!r}") from exc
    if not isinstance(arguments, dict):
        raise OllamaResponseError(f"Tool arguments must be an object, got: {arguments!r}")

    # Ollama does not document call IDs, so we generate one to link calls and results.
    call_id = raw.get("id") or f"call_{uuid.uuid4().hex[:8]}"
    return ToolCall(id=call_id, name=name, arguments=arguments)
