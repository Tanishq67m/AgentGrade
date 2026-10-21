"""A tiny, fully deterministic MCP server used only by AgentGrade's own tests.

Runs as a real stdio subprocess, so tests exercise the actual MCP protocol,
without needing Node.js or any third-party server.
"""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

NOTES = {
    "groceries": "milk, eggs, coffee",
    "todo": "finish AgentGrade M2",
}

server = MCPServer("agentgrade-test-notes")


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_notes() -> list[str]:
    """List the names of all notes."""
    return sorted(NOTES)


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def read_note(name: str) -> str:
    """Read one note by name."""
    if name not in NOTES:
        raise KeyError(f"no note named {name!r}")
    return NOTES[name]


@server.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True))
def delete_note(name: str) -> str:
    """Delete a note. (Destructive - must never be exposed to read-only tasks.)"""
    NOTES.pop(name, None)
    return f"deleted {name}"


@server.tool()
def echo(text: str) -> str:
    """Echo text back. Has no annotations at all."""
    return text


if __name__ == "__main__":
    server.run()
