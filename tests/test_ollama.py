"""Ollama adapter: checked against a fake HTTP server (httpx.MockTransport).

These tests pin our understanding of Ollama's /api/chat JSON format without
needing Ollama installed. They can't prove a real model behaves well - the demo does that.
"""

import json

import httpx
import pytest

from agentgrade.models.ollama import (
    OllamaModel,
    OllamaModelNotFoundError,
    OllamaResponseError,
    OllamaUnavailableError,
    split_thinking,
)
from agentgrade.types import Message, ToolCall, ToolSpec

TOOLS = [
    ToolSpec(
        name="lookup_order",
        description="Look up an order.",
        input_schema={"type": "object", "properties": {"order_id": {"type": "string"}}},
    )
]


def make_model(handler) -> OllamaModel:
    client = httpx.AsyncClient(
        base_url="http://ollama.test", transport=httpx.MockTransport(handler)
    )
    return OllamaModel("qwen3:4b", client=client)


async def test_request_payload_matches_ollama_format():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "hi"}})

    model = make_model(handler)
    history = [
        Message(role="user", content="cost of A17?"),
        Message(
            role="assistant",
            tool_calls=[ToolCall(id="c1", name="lookup_order", arguments={"order_id": "A17"})],
        ),
        Message(
            role="tool", content='{"country": "IN"}', tool_call_id="c1", tool_name="lookup_order"
        ),
    ]

    await model.complete(history, TOOLS)

    body = seen["body"]
    assert seen["path"] == "/api/chat"
    assert body["model"] == "qwen3:4b"
    assert body["stream"] is False
    assert "think" not in body  # only sent when explicitly chosen
    assert body["tools"][0] == {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order.",
            "parameters": TOOLS[0].input_schema,
        },
    }
    assert body["messages"][1]["tool_calls"] == [
        {"function": {"name": "lookup_order", "arguments": {"order_id": "A17"}}}
    ]
    assert body["messages"][2] == {
        "role": "tool",
        "content": '{"country": "IN"}',
        "tool_name": "lookup_order",
    }


async def test_parses_tool_calls_and_usage():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "lookup_order", "arguments": {"order_id": "A17"}}}
                    ],
                },
                "done": True,
                "prompt_eval_count": 120,
                "eval_count": 18,
            },
        )

    response = await make_model(handler).complete([Message(role="user", content="x")], TOOLS)

    assert response.content == ""
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert (call.name, call.arguments) == ("lookup_order", {"order_id": "A17"})
    assert call.id.startswith("call_")  # generated, since Ollama doesn't send one
    assert (response.usage.input_tokens, response.usage.output_tokens) == (120, 18)


def test_string_arguments_are_decoded():
    data = {"message": {"tool_calls": [{"function": {"name": "t", "arguments": '{"a": 1}'}}]}}
    assert OllamaModel.parse_response(data).tool_calls[0].arguments == {"a": 1}


@pytest.mark.parametrize(
    "data",
    [
        {"no_message": True},
        {"message": {"tool_calls": [{"function": {"arguments": {}}}]}},
        {"message": {"tool_calls": [{"function": {"name": "t", "arguments": "{not json"}}]}},
        {"message": {"tool_calls": [{"function": {"name": "t", "arguments": [1, 2]}}]}},
    ],
)
def test_malformed_responses_raise_clear_errors(data):
    with pytest.raises(OllamaResponseError):
        OllamaModel.parse_response(data)


async def test_missing_model_gives_pull_hint():
    model = make_model(lambda r: httpx.Response(404, json={"error": "model 'qwen3:4b' not found"}))
    with pytest.raises(OllamaModelNotFoundError, match="ollama pull qwen3:4b"):
        await model.complete([Message(role="user", content="x")], TOOLS)


async def test_connection_refused_gives_start_hint():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(OllamaUnavailableError, match="Is it running"):
        await make_model(handler).complete([Message(role="user", content="x")], TOOLS)


def test_think_option_is_sent_only_when_chosen():
    assert OllamaModel("qwen3:4b", think=False).build_payload([], [])["think"] is False


# --- Regression: bug found in the first real demo run (2026-10-21) -------------------
# qwen3:4b (= qwen3:4b-thinking-2507) ignored "think": false and leaked its reasoning into
# `content` with only a closing </think> tag. The whole monologue became the final answer,
# and the "contains 12.5" check still passed.

LEAKED_CONTENT = (
    "Okay, let's see. The user asked for the shipping cost in USD for order A17.\n\n"
    "The final answer should be $12.50.\n"
    "So the final answer is 12.5 USD.\n"
    "</think>\n\n"
    "The shipping cost in USD for order A17 is 12.5."
)


def test_regression_leaked_reasoning_is_split_from_the_answer():
    response = OllamaModel.parse_response(
        {"message": {"role": "assistant", "content": LEAKED_CONTENT}}
    )

    assert response.content == "The shipping cost in USD for order A17 is 12.5."
    assert response.thinking.startswith("Okay, let's see.")
    assert "</think>" not in response.content
    assert "</think>" not in response.thinking


def test_regression_leaked_reasoning_before_a_tool_call():
    data = {
        "message": {
            "content": "I should call lookup_order first.\n</think>\n\n",
            "tool_calls": [
                {"function": {"name": "lookup_order", "arguments": {"order_id": "A17"}}}
            ],
        }
    }
    response = OllamaModel.parse_response(data)

    assert response.content == ""
    assert response.thinking == "I should call lookup_order first."
    assert response.tool_calls[0].name == "lookup_order"


def test_thinking_field_from_ollama_is_kept_separately():
    data = {"message": {"content": "12.5 USD", "thinking": "2 kg times 6.25..."}}
    response = OllamaModel.parse_response(data)
    assert (response.thinking, response.content) == ("2 kg times 6.25...", "12.5 USD")


@pytest.mark.parametrize(
    "thinking, content, expected",
    [
        ("", "plain answer", ("", "plain answer")),
        ("", "<think>reasoning</think>answer", ("reasoning", "answer")),
        ("from field", "leaked</think>answer", ("from field\n\nleaked", "answer")),
        ("", "a</think>b</think>final", ("a</think>b", "final")),
    ],
)
def test_split_thinking_cases(thinking, content, expected):
    assert split_thinking(thinking, content) == expected
