# 0019. Publish as `agentgrade-mcp` on PyPI with Trusted Publishing; CI on every push

- **Status:** Accepted
- **Date:** 2026-11-19
- **Decided by:** Tanishq (chose `agentgrade-mcp`)

## Problem
People who see the upstream issues or the posts should be able to try AgentGrade in one command, and every
change should be tested automatically. The PyPI name `agentgrade` is taken by an unrelated project ("Pytest
for multi-agent systems", first released 2026-06-28).

## Options considered
| Option | For | Against |
|---|---|---|
| **`agentgrade-mcp`** | Keeps the name, repo and every link (issues, case study, posts); says what it is for | `pip install agentgrade` installs the other project |
| Rename everything | No ambiguity | Breaks the name used in upstream issues and posts just published |
| GitHub-only install | No decision needed | One more hurdle for every visitor |

## Decision
- Distribution `agentgrade-mcp`, version 0.1.0; import package and command stay `agentgrade`.
- The wheel bundles five example suites with their fixtures and the model configs, in the repo's layout;
  `agentgrade init <dir>` copies them out, so a fresh install can run a suite. The PR/patch suites stay
  in the repo (they need `.targets/` builds).
- CI (`.github/workflows/ci.yml`): ruff, format check, tests and a package build on Python 3.12 and 3.13.
- Release (`.github/workflows/release.yml`): on a `v*` tag, tests, check that the tag equals `__version__`,
  build, and publish with **PyPI Trusted Publishing** (no API token stored anywhere).

## Consequences
- Installing both `agentgrade` (the other project) and `agentgrade-mcp` would clash on the command name.
- One-time manual step on pypi.org: register the pending publisher for `agentgrade-mcp`.
