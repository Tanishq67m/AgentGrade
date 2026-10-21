"""Connect to an MCP server over stdio and expose its tools to the agent loop.

Flow:  McpServerConfig -> connect() spawns the server as a subprocess
       -> MCP handshake + tools/list -> McpConnection
       -> agent_tools(allow=[...]) -> list[Tool] for the M1 ToolRegistry.

Security (ADR 0005 / 0009): the model only ever sees tools on an explicit allowlist, and
tools the server doesn't mark read-only are refused unless explicitly permitted. The
server's own annotations are hints from an untrusted source, so the allowlist - not the
hint - is the real control.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp import Client, StdioServerParameters
from mcp.types import CallToolResult
from mcp.types import Tool as McpTool
from pydantic import BaseModel, Field

from agentgrade.tools import Tool


class McpServerConfig(BaseModel):
    """How to launch one MCP server as a local subprocess."""

    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None  # extra env vars; the SDK passes only a safe default set
    cwd: str | None = None
    timeout_s: float = 30.0  # per-request read timeout


class McpError(RuntimeError):
    """Base class for MCP client failures."""


class McpServerStartError(McpError):
    """The server process could not be started or did not complete the handshake."""


class McpToolError(McpError):
    """The server ran the tool and reported an error (CallToolResult.is_error)."""


class ToolPolicyError(ValueError):
    """The requested tool allowlist violates the safety policy."""


@dataclass(frozen=True)
class McpToolInfo:
    """Our own view of one server tool (decoupled from the SDK's types)."""

    name: str
    description: str
    input_schema: dict[str, Any]
    read_only_hint: bool | None  # None = server didn't say

    @classmethod
    def from_mcp(cls, tool: McpTool) -> McpToolInfo:
        hint = tool.annotations.read_only_hint if tool.annotations else None
        return cls(
            name=tool.name,
            description=tool.description or "",
            input_schema=tool.input_schema,
            read_only_hint=hint,
        )


class McpConnection:
    def __init__(self, config: McpServerConfig, client: Client, tools: list[McpToolInfo]):
        self.config = config
        self.tools = tools
        self._client = client

    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Raw tools/call. Tool-level errors come back as is_error=True, not exceptions."""
        return await self._client.call_tool(name, arguments)

    async def call_tool_text(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self.call_tool(name, arguments)
        text = result_to_text(result)
        if result.is_error:
            raise McpToolError(text)
        return text

    def agent_tools(self, allow: Iterable[str], *, allow_non_read_only: bool = False) -> list[Tool]:
        """Wrap allowlisted server tools as agentgrade Tools for the ToolRegistry."""
        allow = list(allow)
        by_name = {t.name: t for t in self.tools}

        missing = [name for name in allow if name not in by_name]
        if missing:
            raise ToolPolicyError(
                f"Allowlisted tools not offered by server {self.config.name!r}: {missing}. "
                f"Server offers: {sorted(by_name)}"
            )

        if not allow_non_read_only:
            unsafe = [name for name in allow if by_name[name].read_only_hint is not True]
            if unsafe:
                raise ToolPolicyError(
                    f"Tools not marked read-only by the server: {unsafe}. MVP tasks are "
                    "read-only (ADR 0005); pass allow_non_read_only=True only for a vetted reason."
                )

        return [self._wrap(by_name[name]) for name in allow]

    def _wrap(self, info: McpToolInfo) -> Tool:
        async def call(**arguments: Any) -> str:
            return await self.call_tool_text(info.name, arguments)

        return Tool(
            name=info.name,
            description=info.description,
            input_schema=info.input_schema,
            func=call,
        )


@asynccontextmanager
async def connect(config: McpServerConfig) -> AsyncIterator[McpConnection]:
    """Start the server, do the MCP handshake, list its tools; stop the server on exit."""
    params = StdioServerParameters(
        command=config.command, args=config.args, env=config.env, cwd=config.cwd
    )
    async with AsyncExitStack() as stack:
        try:
            client = await stack.enter_async_context(
                Client(params, read_timeout_seconds=config.timeout_s)
            )
        except Exception as exc:  # noqa: BLE001 - every startup failure means the same thing
            raise McpServerStartError(
                f"Could not start MCP server {config.name!r} "
                f"(command: {config.command} {' '.join(config.args)}): {_describe(exc)}"
            ) from exc

        tools = await _list_all_tools(client)
        yield McpConnection(config, client, tools)
    # leaving the stack closes the session and shuts the server process down


async def _list_all_tools(client: Client) -> list[McpToolInfo]:
    """tools/list is paginated: keep fetching while the server returns a next_cursor."""
    tools: list[McpToolInfo] = []
    cursor: str | None = None
    while True:
        page = await client.list_tools(cursor=cursor)
        tools.extend(McpToolInfo.from_mcp(t) for t in page.tools)
        cursor = page.next_cursor
        if not cursor:
            return tools


def result_to_text(result: CallToolResult) -> str:
    """Flatten a tool result into the text the model will see."""
    parts: list[str] = []
    for block in result.content:
        if block.type == "text":
            parts.append(block.text)
        else:  # images, audio, resources: not supported in the MVP - say so explicitly
            parts.append(f"[{block.type} content omitted]")
    if not parts and result.structured_content is not None:
        parts.append(json.dumps(result.structured_content, ensure_ascii=False))
    return "\n".join(parts)


def _describe(exc: BaseException) -> str:
    """Unwrap exception groups (from anyio task groups) to the first real cause."""
    while isinstance(exc, BaseExceptionGroup) and exc.exceptions:
        exc = exc.exceptions[0]
    return f"{type(exc).__name__}: {exc}"
