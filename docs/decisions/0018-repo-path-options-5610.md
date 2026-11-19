# 0018. Measure the #5610 repo_path options on patched builds; forward server instructions

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decided by:** Tanishq ("let's do everything now")

## Problem
Both upstream issues were closed as fixed. Maintainer PRs #5620 (filesystem) and #5626 (git) were built
from our reports and merged into `v2/main`. The maintainer split one more question out of #5552 into
[#5610](https://github.com/modelcontextprotocol/servers/issues/5610): should `repo_path` default to the
configured `--repository`? The issue asks for a *decision* between options: optional `repo_path`, stating
the allowed repository in the `repo_path` descriptions, or stating it in the server's `instructions`. A
community comment argues for "always optional" on reasoning alone. Nobody has measured the options.

## Decision
- `scripts/patch_git_repo_path.py` turns a checkout of `v2/main` (`640a8c3`, mcp-server-git 2026.11.18,
  which already includes #5626) into one build per option: `optional`, `described` and `instructions`.
  Each edit is checked, and the script refuses to patch a file whose shape changed. Confinement is unchanged in all
  three: a defaulted `repo_path` goes through the same `open_repo` checks. These are measurement builds,
  not a proposed upstream change (that repo takes prompts, not code).
- `scripts/build_5610_targets.sh` builds main and the three copies into `.targets/`.
- **AgentGrade now forwards a server's `instructions` into the agent's system prompt**, as MCP clients do
  (`McpConnection.instructions`, recorded in results). Neither server tested so far sends instructions, so
  no earlier result changes.
- Suite `repo-path-5610-git.yaml`: the four builds, with **no** repository path given to the agent. That's
  the situation the issue is about.

## Consequences and limitations
- One small model (qwen3:4b-instruct), 5 tasks × 3 repeats per option. Whether a client actually puts
  `instructions` in the prompt varies by client. Here they always do.
- AgentGrade validates arguments against the input schema before calling the server, so a missing
  `repo_path` comes back as `invalid_arguments` rather than the server's Pydantic error. The agent sees an
  error in both cases.
