"""OpenAI-compatible adapter against a fake HTTP server: wire format, errors, rate limits."""

import json

import httpx
import pytest

from agentgrade.models.openai_compat import (
    MissingApiKeyError,
    OpenAICompatModel,
    ProviderAuthError,
    ProviderModelNotFoundError,
    ProviderRateLimitError,
)
from agentgrade.tools import Tool, ToolRegistry
from agentgrade.types import Message, ToolCall, ToolSpec

TOOLS = [ToolSpec(name="read", description="Read a file.", input_schema={"type": "object"})]
USER = [Message(role="user", content="hi")]


def completion(message, **extra):
    return {"model": "openai/gpt-oss-120b", "choices": [{"message": message}], **extra}


class FakeSleep:
    def __init__(self):
        self.calls: list[float] = []

    async def __call__(self, seconds):
        self.calls.append(seconds)


def make(handler, **kwargs):
    client = httpx.AsyncClient(
        base_url="https://llm.test/v1", transport=httpx.MockTransport(handler)
    )
    sleep = kwargs.pop("sleep", FakeSleep())
    return OpenAICompatModel("openai/gpt-oss-120b", base_url="unused", api_key="k", client=client,
                             sleep=sleep, **kwargs)  # fmt: skip


async def test_request_uses_openai_wire_format():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=completion({"role": "assistant", "content": "ok"}))

    history = [
        Message(role="user", content="cost?"),
        Message(
            role="assistant", tool_calls=[ToolCall(id="c1", name="read", arguments={"p": "a"})]
        ),
        Message(role="tool", content="data", tool_call_id="c1", tool_name="read"),
    ]
    await make(handler, temperature=0.7).complete(history, TOOLS)

    body = seen["body"]
    assert seen["path"] == "/v1/chat/completions"
    assert body["temperature"] == 0.7
    assert body["tools"][0]["function"]["parameters"] == {"type": "object"}
    assistant, tool = body["messages"][1], body["messages"][2]
    assert assistant["content"] is None
    assert assistant["tool_calls"][0] == {
        "id": "c1",
        "type": "function",
        "function": {"name": "read", "arguments": '{"p": "a"}'},  # JSON *string*, per the spec
    }
    assert tool == {"role": "tool", "tool_call_id": "c1", "content": "data"}


async def test_parses_tool_calls_reasoning_usage_and_provider_identity():
    def handler(request):
        return httpx.Response(200, json=completion(
            {
                "role": "assistant",
                "content": None,
                "reasoning": "I should read the file.",
                "tool_calls": [{"id": "call_9", "type": "function",
                                "function": {"name": "read", "arguments": '{"path": "/x"}'}}],
            },
            usage={"prompt_tokens": 300, "completion_tokens": 40},
            system_fingerprint="fp_abc",
        ))  # fmt: skip

    r = await make(handler).complete(USER, TOOLS)
    assert r.tool_calls == [ToolCall(id="call_9", name="read", arguments={"path": "/x"})]
    assert r.thinking == "I should read the file." and r.content == ""
    assert (r.usage.input_tokens, r.usage.output_tokens) == (300, 40)
    assert r.provider_meta == {"model": "openai/gpt-oss-120b", "system_fingerprint": "fp_abc"}


async def test_malformed_tool_arguments_are_the_models_mistake_not_a_crash():
    def handler(request):
        return httpx.Response(200, json=completion({"tool_calls": [
            {"id": "c1", "function": {"name": "read", "arguments": '{"path": "/x"'}}  # missing }
        ]}))  # fmt: skip

    r = await make(handler).complete(USER, TOOLS)
    assert r.tool_calls[0].parse_error

    registry = ToolRegistry([Tool(name="read", description="d", input_schema={"type": "object"},
                                  func=lambda **_: "never")])  # fmt: skip
    result = await registry.execute(r.tool_calls[0])
    assert result.error_type == "invalid_arguments"
    assert "Could not parse arguments" in result.content


async def test_429_waits_for_retry_after_then_succeeds_and_wait_is_reported():
    responses = [
        httpx.Response(429, headers={"retry-after": "7"}, json={"error": "rate limited"}),
        httpx.Response(429, headers={"retry-after": "3"}, json={"error": "rate limited"}),
        httpx.Response(200, json=completion({"content": "done"})),
    ]
    sleep = FakeSleep()
    r = await make(lambda req: responses.pop(0), sleep=sleep).complete(USER, TOOLS)
    assert r.content == "done"
    assert sleep.calls == [7.0, 3.0]
    assert r.rate_limit_wait_ms == 10_000


async def test_429_without_header_backs_off_exponentially():
    responses = [
        httpx.Response(429),
        httpx.Response(429),
        httpx.Response(200, json=completion({"content": "x"})),
    ]
    sleep = FakeSleep()
    await make(lambda req: responses.pop(0), sleep=sleep).complete(USER, TOOLS)
    assert sleep.calls == [2.0, 4.0]


async def test_quota_exhausted_raises_after_bounded_retries():
    sleep = FakeSleep()
    model = make(lambda req: httpx.Response(429, text="daily limit"), sleep=sleep,
                 max_rate_limit_retries=3)  # fmt: skip
    with pytest.raises(ProviderRateLimitError, match="daily quota"):
        await model.complete(USER, TOOLS)
    assert len(sleep.calls) == 3


@pytest.mark.parametrize(
    "status, error",
    [(401, ProviderAuthError), (403, ProviderAuthError), (404, ProviderModelNotFoundError)],
)
async def test_setup_errors_are_specific(status, error):
    with pytest.raises(error):
        await make(lambda req: httpx.Response(status, text="nope")).complete(USER, TOOLS)


async def test_requests_are_paced_under_a_per_minute_limit():
    sleep = FakeSleep()
    model = make(lambda req: httpx.Response(200, json=completion({"content": "x"})), sleep=sleep,
                 requests_per_minute=60)  # fmt: skip
    await model.complete(USER, TOOLS)
    second = await model.complete(USER, TOOLS)
    assert len(sleep.calls) == 1 and 0.9 < sleep.calls[0] <= 1.0  # ~1 s between requests
    assert second.rate_limit_wait_ms > 900


def test_missing_api_key_is_a_clear_error(monkeypatch):
    monkeypatch.delenv("AG_TEST_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="AG_TEST_KEY is not set"):
        OpenAICompatModel.from_env("m", base_url="https://x", api_key_env="AG_TEST_KEY")


def test_api_key_is_sent_as_bearer_header(monkeypatch):
    monkeypatch.setenv("AG_TEST_KEY", "secret-123")
    model = OpenAICompatModel.from_env("m", base_url="https://x/v1", api_key_env="AG_TEST_KEY")
    assert model._client.headers["authorization"] == "Bearer secret-123"
