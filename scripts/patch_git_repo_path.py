"""Make measurable builds of the #5610 options for mcp-server-git (experiment only).

modelcontextprotocol/servers#5610 asks whether `repo_path` should default to the configured
`--repository`. This rewrites a checked-out `src/git/src/mcp_server_git/server.py` into one of the
options from that issue, so AgentGrade can measure them on real builds (ADR 0018). It is NOT a
proposed upstream change: that repo takes prompts, not code.

    python scripts/patch_git_repo_path.py <server.py> optional|described|instructions

  optional      repo_path becomes optional on every tool and prompt and defaults to --repository
                (keyword-only, so the parameter order is unchanged). It still goes through
                open_repo, so confinement checks are identical. Without --repository, omitting it
                is a call-time error that says so.
  described     repo_path stays required; every tool's repo_path gets a description that names
                the allowed repository when the server is confined.
  instructions  the server's initialize `instructions` name the allowed repository when confined.

Every edit is checked: if the upstream file no longer has the expected shape, the script fails
instead of producing a half-patched build.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FACTORY = "def create_server(repository: Path | None) -> MCPServer:\n"
REPO_DESC = (
    "    _REPO_PATH_DESCRIPTION = (\n"
    '        f"The path to the Git repository. This server is confined to {repository}: "\n'
    '        "pass exactly that path."\n'
    "        if repository is not None\n"
    '        else "The path to the Git repository."\n'
    "    )\n"
)
DOCSTRING = '    """The git server, confined to `repository` when one is given."""\n'

# `repo_path: str` as a plain parameter, and the Annotated form used by prompts/branch/remote.
PLAIN = re.compile(r"(?<!open_repo)(\(\s*)repo_path: str\b(?!\s*\|)")  # not open_repo itself
ANNOTATED = re.compile(
    r'(\(\s*)repo_path: Annotated\[str, Field\(description="The path to the Git repository\."\)\]'
)


def _insert_after_docstring(src: str, block: str) -> str:
    anchor = FACTORY + DOCSTRING
    if anchor not in src:
        raise SystemExit("create_server() no longer has the expected header; refusing to patch")
    return src.replace(anchor, anchor + block, 1)


def optional(src: str) -> str:
    n_plain = len(PLAIN.findall(src))
    n_ann = len(ANNOTATED.findall(src))
    src = PLAIN.sub(r"\1*, repo_path: str | None = None", src)
    src = ANNOTATED.sub(
        r'\1*, repo_path: Annotated[str | None, Field(description="The path to the Git '
        r'repository. Optional when the server was started with --repository.")] = None',
        src,
    )
    old = "    def open_repo(repo_path: str) -> git.Repo:\n        path = Path(repo_path)\n"
    new = (
        "    def open_repo(repo_path: str | None) -> git.Repo:\n"
        "        if repo_path is None:\n"
        "            if repository is None:\n"
        "                raise ValueError(\n"
        '                    "repo_path is required: this server was not started "\n'
        '                    "with --repository"\n'
        "                )\n"
        "            repo_path = str(repository)\n"
        "        path = Path(repo_path)\n"
    )
    if old not in src:
        raise SystemExit("open_repo() no longer has the expected shape; refusing to patch")
    src = src.replace(old, new, 1)
    print(f"optional: {n_plain} plain + {n_ann} annotated repo_path parameters made optional")
    if n_plain + n_ann < 10:
        raise SystemExit("fewer repo_path parameters than expected; refusing to patch")
    return src


def described(src: str) -> str:
    n_plain = len(PLAIN.findall(src))
    n_ann = len(ANNOTATED.findall(src))
    field = r"\1repo_path: Annotated[str, Field(description=_REPO_PATH_DESCRIPTION)]"
    src = PLAIN.sub(field, src)
    src = ANNOTATED.sub(field, src)
    src = _insert_after_docstring(src, REPO_DESC)
    print(f"described: {n_plain} plain + {n_ann} annotated repo_path parameters described")
    if n_plain + n_ann < 10:
        raise SystemExit("fewer repo_path parameters than expected; refusing to patch")
    return src


def instructions(src: str) -> str:
    old = '        "mcp-git",\n        version=SERVER_VERSION,\n'
    new = (
        '        "mcp-git",\n'
        "        version=SERVER_VERSION,\n"
        "        instructions=(\n"
        '            f"This server is confined to the git repository at {repository}. "\n'
        '            "Pass that exact path as repo_path to every tool."\n'
        "            if repository is not None\n"
        "            else None\n"
        "        ),\n"
    )
    if old not in src:
        raise SystemExit("MCPServer(...) no longer has the expected shape; refusing to patch")
    print("instructions: initialize instructions name the allowed repository")
    return src.replace(old, new, 1)


MODES = {"optional": optional, "described": described, "instructions": instructions}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[2] not in MODES:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1])
    src = path.read_text(encoding="utf-8")
    patched = MODES[argv[2]](src)
    compile(patched, str(path), "exec")  # a syntax error fails here, not inside a run
    path.write_text(patched, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
