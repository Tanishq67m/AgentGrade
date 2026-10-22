"""Known MCP server configurations (trusted, pinned - ADR 0005 / 0009)."""

from __future__ import annotations

from pathlib import Path

from agentgrade.mcp_client import McpServerConfig

# Pinned: a moving tag can silently change what we evaluate (ADR 0008).
FILESYSTEM_SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem@2.0.0"

FILESYSTEM_READ_ONLY_TOOLS = [
    "list_allowed_directories",
    "list_directory",
    "directory_tree",
    "read_text_file",
    "search_files",
    "get_file_info",
]

REPO_ROOT = Path(__file__).resolve().parents[2]
SHOP_FIXTURE = REPO_ROOT / "fixtures" / "shop"


def filesystem_server(root: Path) -> McpServerConfig:
    return McpServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", FILESYSTEM_SERVER_PACKAGE, str(root)],
        timeout_s=60,
    )
