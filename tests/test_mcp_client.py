"""MCP client against a real stdio subprocess (tests/fixtures/notes_server.py).

These are integration tests: they spawn a process and speak the real MCP protocol.
"""

import sys
from pathlib import Path

import pytest
from mcp.types import CallToolResult, ImageContent, TextContent

from agentgrade.mcp_client import (
    McpServerConfig,
    McpServerStartError,
    McpToolError,
    ToolPolicyError,
    connect,
    result_to_text,
)
from agentgrade.models.fake import ScriptedModel, call_tool, final_answer
from agentgrade.runner import run_agent
from agentgrade.tools import ToolRegistry

NOTES_SERVER = McpServerConfig(
    name="notes",
    command=sys.executable,  # the venv's Python, which has the mcp package
    args=[str(Path(__file__).parent / "fixtures" / "notes_server.py")],
)


async def test_lists_tools_with_schemas_and_read_only_hints():
    async with connect(NOTES_SERVER) as conn:
        tools = {t.name: t for t in conn.tools}

    assert set(tools) == {"list_notes", "read_note", "delete_note", "echo"}
    assert tools["read_note"].input_schema["required"] == ["name"]
    assert tools["read_note"].read_only_hint is True
    assert tools["delete_note"].read_only_hint is False
    assert tools["echo"].read_only_hint is None  # no annotations at all


async def test_calls_a_tool_and_gets_text_back():
    async with connect(NOTES_SERVER) as conn:
        text = await conn.call_tool_text("read_note", {"name": "groceries"})
    assert text == "milk, eggs, coffee"


async def test_tool_side_error_becomes_mcp_tool_error():
    async with connect(NOTES_SERVER) as conn:
        with pytest.raises(McpToolError):
            await conn.call_tool_text("read_note", {"name": "missing"})


async def test_allowlist_hides_everything_else():
    async with connect(NOTES_SERVER) as conn:
        tools = conn.agent_tools(["list_notes", "read_note"])
    assert [t.name for t in tools] == ["list_notes", "read_note"]


@pytest.mark.parametrize(
    "allow, message",
    [
        (["delete_note"], "not marked read-only"),
        (["echo"], "not marked read-only"),  # missing hint is treated as NOT read-only
        (["read_notes_typo"], "not offered by server"),
    ],
)
async def test_policy_refuses_unsafe_or_unknown_tools(allow, message):
    async with connect(NOTES_SERVER) as conn:
        with pytest.raises(ToolPolicyError, match=message):
            conn.agent_tools(allow)


async def test_non_read_only_tools_need_explicit_opt_in():
    async with connect(NOTES_SERVER) as conn:
        tools = conn.agent_tools(["echo"], allow_non_read_only=True)
    assert tools[0].name == "echo"


async def test_mcp_tools_plug_into_the_m1_agent_loop():
    """End to end: scripted model -> runner -> registry -> MCP -> subprocess, and back."""
    model = ScriptedModel(
        [
            call_tool("delete_note", name="todo"),  # hidden tool: must be refused, never run
            call_tool("read_note", name="todo"),
            final_answer("finish AgentGrade M2"),
        ]
    )
    async with connect(NOTES_SERVER) as conn:
        registry = ToolRegistry(conn.agent_tools(["list_notes", "read_note"]))
        result = await run_agent(model, registry, "What is on my todo note?")
        still_there = await conn.call_tool_text("read_note", {"name": "todo"})

    refused, read = result.steps[0].tool_results[0], result.steps[1].tool_results[0]
    assert refused.error_type == "unknown_tool"
    assert read.ok and read.content == "finish AgentGrade M2"
    assert still_there == "finish AgentGrade M2"  # proof the delete never reached the server
    assert result.stop_reason == "final_answer"


async def test_server_that_cannot_start_gives_a_clear_error():
    broken = McpServerConfig(name="broken", command="definitely-not-a-real-command-xyz")
    with pytest.raises(McpServerStartError, match="Could not start MCP server 'broken'"):
        async with connect(broken):
            pass


def test_result_to_text_handles_non_text_and_structured_content():
    mixed = CallToolResult(
        content=[
            TextContent(type="text", text="hello"),
            ImageContent(type="image", data="aGk=", mime_type="image/png"),
        ]
    )
    assert result_to_text(mixed) == "hello\n[image content omitted]"

    structured_only = CallToolResult(content=[], structured_content={"cost": 12.5})
    assert result_to_text(structured_only) == '{"cost": 12.5}'
