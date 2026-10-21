"""M2 demo: connect to the official MCP filesystem server and call read-only tools.

Usage (needs Node.js for `npx`):
    uv run python -m agentgrade.mcp_demo

What it shows:
  1. The server is started as a subprocess, pointed at a throwaway COPY of fixtures/shop.
  2. Every tool the server offers, its read-only hint, and whether our allowlist exposes it.
  3. Two real tool calls going through the same ToolRegistry the agent loop uses.
No model is involved yet - that's M3.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

from agentgrade.mcp_client import McpError, McpServerConfig, ToolPolicyError, connect
from agentgrade.tools import ToolRegistry
from agentgrade.types import ToolCall

# Pinned: a moving tag can silently change what we test (see ADR 0008).
FILESYSTEM_SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem@2.0.0"
FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shop"

READ_ONLY_ALLOWLIST = [
    "list_allowed_directories",
    "list_directory",
    "directory_tree",
    "read_text_file",
    "search_files",
    "get_file_info",
]


def filesystem_server(root: Path) -> McpServerConfig:
    return McpServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", FILESYSTEM_SERVER_PACKAGE, str(root)],
        timeout_s=60,
    )


async def main() -> int:
    if shutil.which("npx") is None:
        print(
            "Error: `npx` not found. Install Node.js (e.g. `brew install node`).", file=sys.stderr
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="agentgrade-") as tmp:
        # resolve(): on macOS /var is a symlink to /private/var; give the server the real path
        root = Path(tmp).resolve() / "shop"
        shutil.copytree(FIXTURE_DIR, root)
        print(f"Sandbox copy: {root}")
        print(f"Starting {FILESYSTEM_SERVER_PACKAGE} (first run downloads it)...\n")

        try:
            async with connect(filesystem_server(root)) as conn:
                print(f"{'TOOL':28} {'READ-ONLY HINT':15} EXPOSED TO AGENT")
                for tool in conn.tools:
                    exposed = "yes" if tool.name in READ_ONLY_ALLOWLIST else "no (blocked)"
                    print(f"{tool.name:28} {str(tool.read_only_hint):15} {exposed}")

                registry = ToolRegistry(conn.agent_tools(READ_ONLY_ALLOWLIST))

                calls = [
                    ToolCall(
                        id="1", name="list_directory", arguments={"path": str(root / "orders")}
                    ),
                    ToolCall(
                        id="2",
                        name="read_text_file",
                        arguments={"path": str(root / "orders" / "A17.json")},
                    ),
                    ToolCall(
                        id="3",
                        name="write_file",
                        arguments={"path": str(root / "x"), "content": "x"},
                    ),
                    ToolCall(id="4", name="read_text_file", arguments={"path": "/etc/passwd"}),
                ]
                for call in calls:
                    result = await registry.execute(call)
                    status = "ok" if result.ok else result.error_type
                    print(f"\n> {call.name}({call.arguments})\n  [{status}] {result.content}")
        except (McpError, ToolPolicyError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    argparse.ArgumentParser(description="AgentGrade M2 demo (MCP filesystem server)").parse_args()
    sys.exit(asyncio.run(main()))
