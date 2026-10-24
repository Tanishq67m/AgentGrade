# 0014. Second MCP server: git (suite setup step, server logs, prompt placeholders)

- **Status:** Accepted
- **Date:** 2026-10-24
- **Decided by:** Tanishq ("let's start next steps"; option A, the setup step, as recommended)

## Problem
All results come from one server. To show AgentGrade isn't a one-dataset trick it needs a second,
different MCP server, and that server needs a real git repository as test data.

## Why the official git server (`mcp-server-git`)
- Python, run with `uvx`: no Node dependency.
- Properly annotated: 7 read-only tools, 5 write tools (`git_commit`, `git_add`, `git_reset`,
  `git_create_branch`, `git_checkout`). The allowlist uses the annotations as-is.
- Pinned to `2026.10.10` (the newest release was 5 days old; a moving target was avoided, per ADR 0008/0009).

## Decisions
| Question | Choice | Why |
|---|---|---|
| Test repo | **(A) `server.setup`**: argv commands run in `{root}` before the server starts, every run | We can't commit a repo inside our repo. A script is readable and diffable; a `.tar` (option B) isn't. |
| Fixture builder | `fixtures/git_repo/build_repo.py`: fixed authors, dates and contents, user git config ignored | **Identical commit hashes every run** (verified), and no signing prompts or hooks from the user's machine. |
| Ground truth | `tests/test_git_fixture.py` checks the answers against real `git` output **and** against the suite's expected values | An edited fixture can't silently invalidate expected answers. |
| Placeholders | `{root}`, `{python}` (per run), `{suite_dir}` (at load time); `{root}` also allowed in task prompts and `system_prompt_suffix` | Setup and prompts can refer to the sandbox without hard-coded paths. |
| Setup failure | `SetupError`, **fatal** (stops the suite); a missing command is a `SetupError` too | Setup is deterministic: if it fails once it fails every time. |
| Server stderr | Written to `runs/<id>/server_logs/<run>.log`, not the console | This server runs MCP SDK 1.30: our v2 client's `server/discover` probe makes it log 31 validation warnings per start before falling back to `initialize`. Logs belong next to the trace. |

## What the probe found (inputs for task design)
- **Every tool requires `repo_path`, but no tool reveals it.** A wrong path returns
  "Repository path '.' is outside the allowed repository '<path>'", so an agent can recover
  if it reads errors. The baseline variant measures that; `repo-path-given` gives the path.
- `git_branch` requires `branch_type`, which is easy to omit.
- `git_show "<rev>:<path>"` is the only way to read file contents.

## Consequences and limitations
- Needs `git` and `uv` (for `uvx`) on the machine running the suite.
- Variants beyond the repo-path question are deliberately left out until baseline traces show
  where agents actually fail (the order that worked on the filesystem server).
