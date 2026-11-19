# Changelog

## 0.1.0 - 2026-11-19

First release on PyPI, as **`agentgrade-mcp`** (the command is `agentgrade`).

- `agentgrade run`: repeated agent runs against a real MCP server, answers checked in code, a JSONL trace per
  run, failure categories, pass rates with 95% intervals, and before/after variants (tool subsets, description
  overrides, agent-prompt suffixes, and **different server builds**, e.g. a proposed patch).
- `agentgrade report`: re-render and re-classify an existing run.
- `agentgrade static-score`: Glama's TDQS description score, re-implemented from its spec, next to measured
  pass rates.
- `agentgrade init`: copy the example suites (filesystem, git, memory, sqlite, time) with their fixtures.
- Model adapters: Ollama, and any OpenAI-compatible API (Groq, Cerebras, OpenRouter, OpenAI).
- MCP server `instructions` are passed into the agent's system prompt, as MCP clients do.

Findings so far: [docs/CASE_STUDY.md](docs/CASE_STUDY.md).
