"""A "patched build" of notes_server.py for testing server overrides (variant `server:`).

Same notes and tools; only the server name and read_note's description differ, the way a
proposed upstream patch would change a tool description.
"""

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

NOTES = {
    "groceries": "milk, eggs, coffee",
    "todo": "finish AgentGrade M2",
}

server = MCPServer("agentgrade-test-notes-patched")


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def list_notes() -> list[str]:
    """List the names of all notes."""
    return sorted(NOTES)


@server.tool(annotations=ToolAnnotations(read_only_hint=True))
def read_note(name: str) -> str:
    """Read one note by its exact name. Call list_notes first to see the names."""
    if name not in NOTES:
        raise KeyError(f"no note named {name!r}")
    return NOTES[name]


if __name__ == "__main__":
    server.run()
