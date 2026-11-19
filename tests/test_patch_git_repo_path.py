"""scripts/patch_git_repo_path.py (#5610 experiment, ADR 0018) on a minimal server.py of the
same shape as upstream's: each mode makes its edit, compiles, and refuses a changed file."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "patch_git_repo_path", Path(__file__).parents[1] / "scripts" / "patch_git_repo_path.py"
)
patch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patch)

TOOLS = "\n".join(
    f"    def tool{i}(repo_path: str, x: int = 1) -> str:\n"
    "        return str(open_repo(repo_path))\n"
    for i in range(9)
)
SERVER = f'''from pathlib import Path
from typing import Annotated
from pydantic import Field


def create_server(repository: Path | None) -> MCPServer:
    """The git server, confined to `repository` when one is given."""

    server = MCPServer(
        "mcp-git",
        version=SERVER_VERSION,
    )

    def open_repo(repo_path: str) -> git.Repo:
        path = Path(repo_path)
        return path

    def branch(
        repo_path: Annotated[str, Field(description="The path to the Git repository.")],
        kind: str,
    ) -> str:
        return ""

    def show(repo_path: str, revision: str) -> str:
        return ""

{TOOLS}'''


def test_optional_makes_every_repo_path_keyword_only_and_defaulted():
    out = patch.optional(SERVER)
    compile(out, "server.py", "exec")
    assert "def show(*, repo_path: str | None = None, revision: str)" in out
    assert out.count("*, repo_path: str | None = None") == 10
    assert "*, repo_path: Annotated[str | None" in out
    assert "def open_repo(repo_path: str | None) -> git.Repo:" in out  # not keyword-only
    assert "repo_path = str(repository)" in out


def test_described_names_the_repository_on_every_tool():
    out = patch.described(SERVER)
    compile(out, "server.py", "exec")
    assert out.count("repo_path: Annotated[str, Field(description=_REPO_PATH_DESCRIPTION)]") == 11
    assert "def open_repo(repo_path: str)" in out  # helper left alone
    assert "This server is confined to {repository}" in out


def test_instructions_name_the_repository():
    out = patch.instructions(SERVER)
    compile(out, "server.py", "exec")
    assert "instructions=(" in out and "Pass that exact path as repo_path" in out


@pytest.mark.parametrize("mode", ["optional", "described", "instructions"])
def test_a_changed_upstream_file_is_refused(mode):
    changed = SERVER.replace("def open_repo(repo_path: str)", "def open_repo(path: str)")
    changed = changed.replace('"mcp-git",\n        version=', '"mcp-git", version=')
    changed = changed.replace('"""The git server, confined', '"""Git server, confined')
    with pytest.raises(SystemExit):
        patch.MODES[mode](changed)
