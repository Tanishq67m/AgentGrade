"""Trace recording: complete, ordered, crash-safe, and free of secrets."""

import json
import sys
from pathlib import Path

import pytest

from agentgrade.environment import collect_environment
from agentgrade.mcp_client import McpServerConfig, connect
from agentgrade.models.fake import ScriptedModel, ScriptExhaustedError, call_tool, final_answer
from agentgrade.runner import run_agent
from agentgrade.tools import Tool, ToolRegistry
from agentgrade.trace import REDACTED, TraceWriter, read_trace, redact
from agentgrade.types import Usage

TASK = "What is the shipping cost for order A17?"


def test_redact_masks_secret_keys_at_any_depth():
    data = {
        "path": "/tmp/x",
        "api_key": "sk-123",
        "headers": {"Authorization": "Bearer abc", "Accept": "json"},
        "items": [{"access_token": "t"}, {"name": "ok"}],
    }
    assert redact(data) == {
        "path": "/tmp/x",
        "api_key": REDACTED,
        "headers": {"Authorization": REDACTED, "Accept": "json"},
        "items": [{"access_token": REDACTED}, {"name": "ok"}],
    }


def test_events_are_numbered_and_on_disk_immediately(tmp_path: Path):
    trace = TraceWriter.create(tmp_path, run_id="r1")
    trace.event("a", x=1)
    trace.event("b", x=2)
    # read BEFORE close: proves each event is flushed as it happens (crash-safety)
    events = read_trace(trace.path)
    trace.close()

    assert trace.path == tmp_path / "r1" / "trace.jsonl"
    assert [(e["seq"], e["type"]) for e in events] == [(1, "a"), (2, "b")]
    assert all("ts" in e for e in events)


async def test_full_run_is_traced_in_order(registry, tmp_path: Path):
    model = ScriptedModel(
        [
            call_tool(
                "lookup_order", usage=Usage(input_tokens=50, output_tokens=5), order_id="A17"
            ),
            call_tool("get_shipping_cost", country="IN", weight_kg=2.0),
            final_answer("12.5 USD"),
        ]
    )
    with TraceWriter.create(tmp_path, run_id="r1") as trace:
        await run_agent(model, registry, TASK, trace=trace, metadata={"task_id": "t1"})
    events = read_trace(trace.path)

    assert [e["type"] for e in events] == [
        "run_started",
        "model_call", "tool_result",
        "model_call", "tool_result",
        "model_call",
        "run_finished",
    ]  # fmt: skip
    started, finished = events[0], events[-1]
    assert started["metadata"] == {"task_id": "t1"}
    assert {t["name"] for t in started["tools"]} == {"lookup_order", "get_shipping_cost"}
    assert events[1]["usage"] == {"input_tokens": 50, "output_tokens": 5}
    assert events[2]["tool_name"] == "lookup_order" and events[2]["ok"] is True
    assert events[2]["latency_ms"] >= 0
    assert finished["stop_reason"] == "final_answer"
    assert finished["final_answer"] == "12.5 USD"


async def test_secret_tool_arguments_never_reach_the_trace(tmp_path: Path):
    tool = Tool(
        name="fetch",
        description="d",
        input_schema={"type": "object", "properties": {"url": {}, "api_key": {}}},
        func=lambda url, api_key: "ok",
    )
    model = ScriptedModel(
        [call_tool("fetch", url="https://x", api_key="sk-SECRET"), final_answer("ok")]
    )
    with TraceWriter.create(tmp_path, run_id="r1") as trace:
        await run_agent(model, ToolRegistry([tool]), TASK, trace=trace)

    raw = trace.path.read_text()
    assert "sk-SECRET" not in raw
    model_call, tool_result = read_trace(trace.path)[1:3]
    assert model_call["tool_calls"][0]["arguments"]["api_key"] == REDACTED
    assert tool_result["arguments"] == {"url": "https://x", "api_key": REDACTED}


async def test_crash_mid_run_leaves_partial_trace_and_still_raises(registry, tmp_path: Path):
    model = ScriptedModel([call_tool("lookup_order", order_id="A17")])  # 2nd call -> crash
    with TraceWriter.create(tmp_path, run_id="r1") as trace:
        with pytest.raises(ScriptExhaustedError):
            await run_agent(model, registry, TASK, trace=trace)
    events = read_trace(trace.path)

    assert [e["type"] for e in events] == ["run_started", "model_call", "tool_result", "run_failed"]
    assert events[-1]["error_type"] == "ScriptExhaustedError"


async def test_traced_run_over_real_mcp_server(tmp_path: Path):
    server = McpServerConfig(
        name="notes",
        command=sys.executable,
        args=[str(Path(__file__).parent / "fixtures" / "notes_server.py")],
    )
    model = ScriptedModel(
        [call_tool("read_note", name="todo"), final_answer("finish AgentGrade M2")]
    )
    async with connect(server) as conn:
        info = conn.describe()
        registry = ToolRegistry(conn.agent_tools(["read_note"]))
        with TraceWriter.create(tmp_path, run_id="r1") as trace:
            await run_agent(model, registry, "What is on my todo note?", trace=trace,
                            metadata={"server": info})  # fmt: skip
    events = read_trace(trace.path)

    assert info["server_name"] == "agentgrade-test-notes"
    assert info["protocol_version"]
    assert events[0]["metadata"]["server"]["tools_offered"] == [
        "list_notes", "read_note", "delete_note", "echo",
    ]  # fmt: skip
    assert events[2]["content"] == "finish AgentGrade M2"
    json.dumps(events)  # everything in the trace is plain JSON


def test_environment_is_best_effort(monkeypatch):
    monkeypatch.setattr("agentgrade.environment.shutil.which", lambda _: None)  # no node, no git
    env = collect_environment()
    assert env["node"] is None and env["git"] is None
    assert env["python"] and env["packages"]["mcp"]


@pytest.mark.parametrize(
    "key, secret",
    [
        ("api_key", True), ("X-Api-Key", True), ("apiKey", True), ("access_token", True),
        ("accessToken", True), ("Authorization", True), ("client_secret", True),
        ("password", True), ("private_key", True),
        # Regression (M3): substring matching treated these as secrets and hid our metrics
        ("input_tokens", False), ("output_tokens", False), ("max_tokens", False),
        ("tokenizer", False), ("path", False), ("keyboard", False),
    ],
)  # fmt: skip
def test_secret_key_detection(key, secret):
    from agentgrade.trace import is_secret_key

    assert is_secret_key(key) is secret
