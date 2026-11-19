# AgentGrade

[![CI](https://github.com/Tanishq67m/AgentGrade/actions/workflows/ci.yml/badge.svg)](https://github.com/Tanishq67m/AgentGrade/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agentgrade-mcp)](https://pypi.org/project/agentgrade-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Reliability testing for AI agents and MCP servers.**

*Static graders guess. AgentGrade measures which line of your tool description breaks agents, and
proves which rewrite fixes it.* ([why this matters](docs/POSITIONING.md))

An agent that works in a demo often fails in real use, and nobody can say why or whether the fix
helped. AgentGrade runs an agent on defined tasks against a real **MCP server**, repeats every task,
checks each answer **in code** (no model grades another model), classifies every failure from a full
execution trace, and compares variants **before and after a change**.

> **Status:** early development, 570+ measured agent runs on official MCP servers. Two upstream issues it found
> ([#5552](https://github.com/modelcontextprotocol/servers/issues/5552), [#5553](https://github.com/modelcontextprotocol/servers/issues/5553))
> were fixed and merged for v2.6.0, and its measurements are informing the design question
> [#5610](https://github.com/modelcontextprotocol/servers/issues/5610).
> **Read the findings: [docs/CASE_STUDY.md](docs/CASE_STUDY.md).** Project overview: [docs/PROJECT.md](docs/PROJECT.md).

## The problems it targets

| | |
|---|---|
| "It worked yesterday, fails today." | Every run records the model digest, server version, code commit and environment. |
| "We don't know why it failed." | A full trace per run, and a failure category: `loop`, `step_limit`, `wrong_answer`, `no_answer`, ... |
| "It passed once. Is it reliable?" | Repeated runs, pass rates with 95% confidence intervals. |
| "The model says it's correct." | Deterministic checks only. |
| "Did our fix help?" | Variants: same tasks, one change (e.g. a rewritten tool description), compared side by side. |

Who it's for: first, **MCP server authors**. They don't control which agent or model calls their server, so
they need to see where models (small ones included) struggle with their tools. Also teams that need evidence
before putting an agent into a real workflow, or before switching to a smaller, cheaper model.

## Install

```bash
uv tool install agentgrade-mcp      # or: pip install agentgrade-mcp
agentgrade init my-evals             # copies example suites, fixtures and model configs
cd my-evals
ollama pull qwen3:4b-instruct
agentgrade run suites/shop.yaml --repeats 1
```

The PyPI package is **`agentgrade-mcp`** (an unrelated project already uses the name `agentgrade`). The
command is `agentgrade`. Running the example servers needs [Ollama](https://ollama.com), Node.js 24+
(filesystem and memory servers) and [uv](https://docs.astral.sh/uv/) (git and time servers).

## Quick start (from source)

Requires [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com), Node.js 24+ (filesystem MCP server) and git (git MCP server).

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

A second suite runs against the official **git** MCP server, on a repository rebuilt identically before every run:

```bash
uv run agentgrade run suites/git.yaml
```

Useful flags: `--repeats 5`, `--variants baseline,no-search`, `--tasks order_count`.

## Other models (free tiers included)

Any OpenAI-compatible API works: Groq, Cerebras, OpenRouter, OpenAI, or Ollama's `/v1` endpoint.
Pick a config from [`model_configs/`](model_configs/) and put your key in a git-ignored `.env`:

```bash
cp .env.example .env          # then fill in e.g. GROQ_API_KEY=...
uv run agentgrade run suites/shop.yaml --model model_configs/groq-gpt-oss-120b.yaml --variants baseline,glob-rules-only
```

Rate limits (HTTP 429) are handled automatically; time spent waiting is recorded separately and excluded from latency.

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
  models/          Ollama + OpenAI-compatible adapters, scripted fake model (tests)
model_configs/     model choices (local Ollama, Groq, Cerebras, ...)
suites/            evaluation suites (shop.yaml: filesystem server, git.yaml: git server)
fixtures/          ground-truth data agents work on (git_repo/build_repo.py builds a deterministic repo)
docs/              PROJECT.md, STATUS.md, decisions/
```

## Test a proposed server patch

A variant can run a different build of the server, so you can measure a patch on the real code before it
merges ([ADR 0017](docs/decisions/0017-measure-proposed-patches.md)):

```yaml
variants:
  - name: main
  - name: patch
    server:
      args: ["{suite_dir}/../.targets/my-patch/src/filesystem/dist/index.js", "{root}"]
      label: my-fork@abc1234
```

`scripts/build_server_target.sh <repo-url> <commit> <name>` checks out and builds one commit into `.targets/`.
Live examples: [`suites/pr-5553-filesystem.yaml`](suites/pr-5553-filesystem.yaml) and
[`suites/pr-5552-git.yaml`](suites/pr-5552-git.yaml) measure the community patch for our upstream issues
#5553 and #5552.

## Roadmap

| Milestone | |
|---|---|
| M0-M5 Foundation, agent loop, MCP client, traces, suites/variants/reports, second server, hosted models | done |
| M6 Public case study ([CASE_STUDY.md](docs/CASE_STUDY.md)), upstream issues #5552, #5553 | done |
| M7a Static vs measured: TDQS graded all six descriptions A; agents passed 8%-75% ([Finding 6](docs/CASE_STUDY.md#finding-6-a-published-static-score-could-not-see-the-difference)) | done |
| Patch check: the community patch for #5553 didn't fix 2.3.0 (2/12), and neither did our own 9/12 text (4/12); git patch held 15/15 ([Finding 7](docs/CASE_STUDY.md#finding-7-a-fix-measured-on-one-version-did-not-survive-the-next)) | done |
| M7b `agentgrade improve`: generate description rewrites, A/B them, recommend only what measurably helps | next |
| Later | Generated tasks / ready-made suites for popular servers, CI mode, public index, paid models |

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

Decisions: [docs/decisions/](docs/decisions/). State and bug log: [docs/STATUS.md](docs/STATUS.md).

## License

MIT
