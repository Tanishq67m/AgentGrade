# AgentGrade

**Can an AI agent actually use your product's tools - and when it fails, why?**

AgentGrade runs an AI agent against a real **MCP server** on a defined task, records every step
it takes, checks the outcome **in code** (never by asking another model), and tells you where it
went wrong: wrong tool, bad arguments, a tool error, a loop, or a wrong answer.

> **Status:** early development - Milestone 3 of 6. The agent loop, the MCP client and run tracing
> work end to end. Task suites, repeated runs and reports are next. See [docs/PROJECT.md](docs/PROJECT.md).

## How it works

```
task ──► agent loop ──► model (local Ollama)  ──►  "call read_text_file(path=...)"
              │                                              │
              │         validate: allowlisted? schema-valid? ◄┘
              │                     │
              │                     ▼
              │         MCP server (subprocess, sandboxed, read-only tools only)
              │                     │
              ◄──── tool result ────┘          ...repeat until answer or step limit
              │
              ├──► runs/<run_id>/trace.jsonl   every event, flushed live, secrets redacted
              ▼
        deterministic check ──► PASS / FAIL
```

Design principles:
- **Deterministic validation** - a task passes only when code says so.
- **Reproducible** - each trace records model digest, server version, git commit and environment.
- **Safe by default** - explicit read-only tool allowlist, pinned trusted servers, throwaway data copies.
- **Free to run** - local models via [Ollama](https://ollama.com); paid providers can be added as adapters later.

## Requirements

- [uv](https://docs.astral.sh/uv/) (`brew install uv`)
- [Ollama](https://ollama.com) for the model demos
- Node.js **24+** for the official filesystem MCP server (`brew install node@24`)

## Setup

```bash
git clone https://github.com/Tanishq67m/AgentGrade.git
cd AgentGrade
uv sync
uv run pytest
```

## Demos

**1. A local model uses an MCP server (M3)** - the main demo:

```bash
ollama pull qwen3:4b-instruct
uv run python -m agentgrade.mcp_agent_demo
```

The model gets only read-only filesystem tools on a copy of [`fixtures/shop`](fixtures/shop) and must
work out the shipping cost for order A17 (ground truth: 12.5 USD). The full trace is written to `runs/`.

**2. Inspect an MCP server and the safety allowlist (M2):**

```bash
uv run python -m agentgrade.mcp_demo
```

**3. The agent loop with plain Python tools (M1):**

```bash
uv run python -m agentgrade.demo
```

## Reading a trace

```bash
cat runs/<run_id>/trace.jsonl
```

One JSON object per line: `run_started` (model, tools, environment), then `model_call` /
`tool_result` pairs, then `run_finished` (or `run_failed`) and `check`.

## Project layout

```
src/agentgrade/
  runner.py          agent loop (run_agent)
  tools.py           Tool + ToolRegistry (validation before execution)
  mcp_client.py      MCP over stdio, read-only allowlist
  servers.py         pinned, trusted server configs
  trace.py           JSONL traces + secret redaction
  environment.py     Python / Node / package / git capture
  checks.py          deterministic answer checks
  models/            ModelAdapter interface, Ollama, scripted fake (tests)
tests/               unit + real-stdio integration tests
fixtures/shop/       ground-truth data the agent works on
docs/                PROJECT.md, STATUS.md, decisions/ (ADRs)
```

## Roadmap

| Milestone | |
|---|---|
| M0 Foundation | done |
| M1 Agent loop + local model | done |
| M2 MCP client + safety allowlist | done |
| M3 Agent over MCP + traces | done (code) |
| M4 YAML task suites + validators | next |
| M5 Repeated runs, failure taxonomy, reports | |
| M6 First public results on real MCP servers | |

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

Design decisions are recorded in [docs/decisions/](docs/decisions/); current state and the bug log
are in [docs/STATUS.md](docs/STATUS.md).

## License

MIT
