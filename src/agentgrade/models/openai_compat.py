"""Adapter for any OpenAI-compatible Chat Completions API.

One adapter covers Groq, Cerebras, OpenRouter, Ollama's /v1 endpoint and OpenAI itself -
switching provider is a config change (base_url + model + API key env var), not new code.

Free tiers have tight rate limits, so HTTP 429 is handled by waiting for `Retry-After` and
retrying (bounded). That wait is reported separately and excluded from latency metrics.
Other errors are NOT retried: they surface, so problems aren't hidden.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from typing import Any

import httpx

from agentgrade.models.ollama import split_thinking
from agentgrade.types import Message, ModelResponse, ToolCall, ToolSpec, Usage


class ProviderError(RuntimeError):
    """Base class for provider failures."""


class MissingApiKeyError(ProviderError):
    """The API key environment variable is not set."""


class ProviderAuthError(ProviderError):
    """401/403: the key is wrong, expired or lacks access."""


class ProviderModelNotFoundError(ProviderError):
    """404: the model id doesn't exist on this provider."""


class ProviderRateLimitError(ProviderError):
    """Still rate-limited after all retries (e.g. the daily quota is used up)."""


class ProviderResponseError(ProviderError):
    """Any other HTTP error or an unreadable response."""


class OpenAICompatModel:
    def __init__(
        self,
        model: str,
        *,
        base_url: str,
        api_key: str | None,
        temperature: float | None = None,
        requests_per_minute: float | None = None,
        max_rate_limit_retries: int = 8,
        max_wait_s: float = 120.0,
        timeout_s: float = 120.0,
        client: httpx.AsyncClient | None = None,
        sleep=asyncio.sleep,  # injectable so tests don't actually wait
    ) -> None:
        self.model = model
        self.name = f"openai_compat:{model}"
        self._temperature = temperature
        self._min_interval_s = 60.0 / requests_per_minute if requests_per_minute else 0.0
        self._max_retries = max_rate_limit_retries
        self._max_wait_s = max_wait_s
        self._sleep = sleep
        self._last_request = 0.0
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"), headers=headers, timeout=timeout_s
        )

    @classmethod
    def from_env(cls, model: str, *, base_url: str, api_key_env: str | None, **kwargs: Any):
        api_key = None
        if api_key_env:
            api_key = os.environ.get(api_key_env)
            if not api_key:
                raise MissingApiKeyError(
                    f"Environment variable {api_key_env} is not set. Put it in a .env file in "
                    f"the project folder ({api_key_env}=...) or export it in your shell."
                )
        return cls(model, base_url=base_url, api_key=api_key, **kwargs)

    async def complete(self, messages: list[Message], tools: list[ToolSpec]) -> ModelResponse:
        payload = self.build_payload(messages, tools)
        waited = 0.0
        for attempt in range(self._max_retries + 1):
            waited += await self._pace()
            response = await self._post(payload)
            if response.status_code != 429:
                break
            if attempt == self._max_retries:
                raise ProviderRateLimitError(
                    f"Still rate-limited after {self._max_retries} retries "
                    f"(daily quota used up?): {response.text[:300]}"
                )
            delay = min(_retry_after_s(response, attempt), self._max_wait_s)
            await self._sleep(delay)
            waited += delay
        self._raise_for_status(response)
        parsed = self.parse_response(_json(response))
        return parsed.model_copy(update={"rate_limit_wait_ms": waited * 1000})

    def build_payload(self, messages: list[Message], tools: list[ToolSpec]) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_openai_message(m) for m in messages],
        }
        if tools:
            payload["tools"] = [_to_openai_tool(t) for t in tools]
        if self._temperature is not None:
            payload["temperature"] = self._temperature
        return payload

    @staticmethod
    def parse_response(data: dict[str, Any]) -> ModelResponse:
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError(
                f"No choices[0].message in response: {data!r:.300}"
            ) from exc

        tool_calls = [_parse_tool_call(raw) for raw in message.get("tool_calls") or []]
        reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
        thinking, content = split_thinking(reasoning, message.get("content") or "")
        usage = data.get("usage") or {}
        return ModelResponse(
            content=content,
            thinking=thinking,
            tool_calls=tool_calls,
            usage=Usage(
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            ),
            provider_meta={
                k: data[k] for k in ("model", "system_fingerprint") if data.get(k) is not None
            },
        )

    async def describe(self) -> dict[str, Any]:
        """Config identity. The provider's own model id is recorded per call (provider_meta)."""
        return {
            "provider": "openai_compatible",
            "model": self.model,
            "base_url": str(self._client.base_url),
        }

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _pace(self) -> float:
        """Space requests to stay under a requests-per-minute limit instead of hitting 429s."""
        if not self._min_interval_s:
            return 0.0
        wait = self._last_request + self._min_interval_s - time.monotonic()
        if wait > 0:
            await self._sleep(wait)
        self._last_request = time.monotonic()
        return max(wait, 0.0)

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        try:
            return await self._client.post("/chat/completions", json=payload)
        except httpx.ConnectError as exc:
            raise ProviderResponseError(f"Could not connect to {self._client.base_url}") from exc

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise ProviderAuthError(
                f"HTTP {response.status_code} from provider - check the API key: "
                f"{response.text[:200]}"
            )
        if response.status_code == 404:
            raise ProviderModelNotFoundError(
                f"Model {self.model!r} not found on this provider: {response.text[:200]}"
            )
        if response.status_code >= 400:
            raise ProviderResponseError(f"HTTP {response.status_code}: {response.text[:300]}")


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError as exc:
        raise ProviderResponseError(f"Response is not JSON: {response.text[:200]}") from exc


def _retry_after_s(response: httpx.Response, attempt: int) -> float:
    header = response.headers.get("retry-after")
    if header:
        try:
            return max(float(header), 0.5)
        except ValueError:
            pass
    return min(2.0 * 2**attempt, 60.0)  # exponential backoff when the header is missing


def _to_openai_message(message: Message) -> dict[str, Any]:
    if message.role == "tool":
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": message.content}
    out: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        out["content"] = message.content or None
        out["tool_calls"] = [
            {
                "id": c.id,
                "type": "function",
                "function": {"name": c.name, "arguments": json.dumps(c.arguments)},
            }
            for c in message.tool_calls
        ]
    return out


def _to_openai_tool(tool: ToolSpec) -> dict[str, Any]:
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
        raise ProviderResponseError(f"Tool call without a function name: {raw!r}")
    call_id = raw.get("id") or f"call_{uuid.uuid4().hex[:8]}"
    arguments = function.get("arguments")
    if arguments in (None, ""):
        return ToolCall(id=call_id, name=name, arguments={})
    if isinstance(arguments, dict):
        return ToolCall(id=call_id, name=name, arguments=arguments)
    try:
        parsed = json.loads(arguments)
    except (json.JSONDecodeError, TypeError) as exc:
        return ToolCall(id=call_id, name=name, parse_error=f"{exc}: {str(arguments)[:200]!r}")
    if not isinstance(parsed, dict):
        return ToolCall(
            id=call_id, name=name, parse_error=f"expected an object, got {parsed!r:.100}"
        )
    return ToolCall(id=call_id, name=name, arguments=parsed)
