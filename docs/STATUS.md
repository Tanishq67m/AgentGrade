# Project Status

_Last updated: 2026-10-21_

## Current objective
**Milestone 0 - repository foundation.**

## Completed
- Project discovery: folder was empty, starting fresh.
- MVP, architecture and tooling decisions recorded (ADR 0001-0006).
- M0 skeleton: `pyproject.toml`, src layout, smoke test, `.gitignore`, README, LICENSE.

## Current implementation state
No application logic yet. `agentgrade` is an importable package with a version string.

## Known issues
- None yet.

## Approved decisions
See [decisions/README.md](decisions/README.md).

## Unresolved questions
- M1: which local Ollama model (depends on the laptop's RAM and tool-calling quality)?
- M1: Ollama client - official `ollama` Python library vs OpenAI-compatible SDK vs plain `httpx`?
- M2: CLI library - stdlib `argparse` vs Typer?

## Milestones
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | In progress (awaiting first commit) |
| M1 | Agent loop with in-process Python tools + fake model | Not started |
| M2 | MCP client over stdio (filesystem server, fixture data) | Not started |
| M3 | Agent loop over MCP tools + trace recording | Not started |
| M4 | YAML suite format + deterministic validators | Not started |
| M5 | Repeats, failure classification, report | Not started |
| M6 | First public results on 2-3 real servers + write-up | Not started |
