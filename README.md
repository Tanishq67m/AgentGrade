# AgentGrade

**Reliability testing for AI agents and MCP servers.**

An agent that works in a demo often fails in real use, and nobody can say why or whether the fix
helped. AgentGrade runs an agent on defined tasks against a real **MCP server**, repeats every task,
checks each answer **in code** (no model grades another model), classifies every failure from a full
execution trace, and compares variants **before and after a change**.

> **Status:** early development, Milestone 4 of 6. Suites, repeated runs, failure classification and
> before/after reports work end to end. See [docs/PROJECT.md](docs/PROJECT.md).

## The problems it targets

| | |
|---|---|
| "It worked yesterday, fails today." | Every run records the model digest, server version, code commit and environment. |
| "We don't know why it failed." | A full trace per run, and a failure category: `loop`, `step_limit`, `wrong_answer`, `no_answer`, ... |
| "It passed once. Is it reliable?" | Repeated runs, pass rates with 95% confidence intervals. |
| "The model says it's correct." | Deterministic checks only. |
| "Did our fix help?" | Variants: same tasks, one change (e.g. a rewritten tool description), compared side by side. |

Who it's for: teams building agents on tools and APIs, teams that need evidence before putting an agent into a
real workflow, and MCP server authors who want to see where models struggle with their tools.

## Quick start

Requires [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) and Node.js 24+ (for the filesystem MCP server).

```bash
git clone https://github.com/Tanishq67m/AgentGrade.git
cd AgentGrade
uv sync
ollama pull qwen3:4b-instruct
uv run agentgrade run suites/shop.yaml
```

This runs 4 tasks x 3 variants x 3 repeats against `@modelcontextprotocol/server-filesystem@2.0.0`.
Each run gets a fresh copy of [`fixtures/shop`](fixtures/shop) and a fresh server process. Output:

```
runs/<run_id>/
  report.md        pass rates (with 95% CI), failure categories, before/after table, failed runs + why
  results.json     everything, machine-readable
  traces/          one JSONL trace per run: every model call, tool call and result
```

Useful flags: `--repeats 5`, `--variants baseline,no-search`, `--tasks order_count`.

## A suite in brief

```yaml
name: shop-filesystem
model: {provider: ollama, name: qwen3:4b-instruct, temperature: 0.7}
server:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem@2.0.0", "{root}"]
  fixture: ../fixtures/shop            # copied fresh into {root} for every run
tools: [list_directory, directory_tree, read_text_file, search_files]   # read-only allowlist
repeats: 3
variants:
  - name: baseline
  - name: clear-search-description     # ONE change: what the model is told about search_files
    description_overrides:
      search_files: "...patterns are relative and non-recursive unless they start with '**/'..."
tasks:
  - id: shipping_cost_a17
    prompt: What is the shipping cost in USD for order A17? ...
    checks:
      - {type: answer_number, expected: 12.5}
```

Checks: `answer_number`, `answer_contains`, `answer_regex`, `tool_called`. Full example: [suites/shop.yaml](suites/shop.yaml).

## How it works

```
suite.yaml ──► for each variant x task x repeat:
                 fresh sandbox + MCP server (pinned, read-only allowlist)
                 agent loop:  model ──► tool call ──► validate (allowlisted? schema-valid?) ──► server
                                ▲                                                         │
                                └──────────────────── tool result ◄───────────────────────┘
                 trace every event ──► code checks ──► failure category
           ──► report.md + results.json
```

Design principles:
- **Deterministic validation:** a task passes only when code says so.
- **Reproducible:** exact model weights, server version, git commit and environment in every trace.
- **Honest numbers:** k/n with confidence intervals; small samples are labelled.
- **Safe by default:** explicit read-only allowlist, pinned trusted servers, throwaway data.
- **Free to run:** local models via Ollama; paid providers plug in as adapters.

## Smaller demos

```bash
uv run python -m agentgrade.mcp_agent_demo   # one traced task on the real server
uv run python -m agentgrade.mcp_demo         # server tools + what the allowlist exposes
uv run python -m agentgrade.demo             # agent loop with plain Python tools
```

## Project layout

```
src/agentgrade/
  cli.py           `agentgrade run`
  suite.py         YAML suites + validation
  evaluate.py      variants x tasks x repeats, fresh sandbox per run
  checks.py        deterministic checks
  classify.py      failure categories from traces
  report.py        markdown report with confidence intervals
  runner.py        agent loop
  tools.py         tool registry (validation before execution)
  mcp_client.py    MCP over stdio, read-only allowlist, description overrides
  trace.py         JSONL traces + secret redaction
  environment.py   Python / Node / package / git capture
  models/          Ollama adapter, scripted fake model (tests)
suites/            evaluation suites
fixtures/          ground-truth data agents work on
docs/              PROJECT.md, STATUS.md, decisions/
```

## Roadmap

| Milestone | |
|---|---|
| M0-M3 Foundation, agent loop, MCP client, traces | done |
| M4 Suites, variants, repeats, failure classification, reports | done (code), showcase run next |
| M5 More MCP servers, actionable recommendations in reports | next |
| M6 Public before/after case study | |
| Later | CI mode (fail a PR when reliability drops), HTML report, paid models |

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

Decisions: [docs/decisions/](docs/decisions/). State and bug log: [docs/STATUS.md](docs/STATUS.md).

## License

MIT
