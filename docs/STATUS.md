# Project Status

_Last updated: 2026-10-21_

## Current objective
**Milestone 3 - agent loop over MCP tools + trace recording (planning).**

## Completed
- **M0** - repo foundation (ADRs 0001-0006).
- **M1** - async agent loop, tool registry, scripted fake model, Ollama adapter, demo (ADRs 0007-0008).
  - Run #1 `qwen3:4b` (always-thinking): correct, but 221 s, 1884 output tokens, reasoning leaked into the answer.
  - Run #2 `qwen3:4b-instruct`: correct, **14.2 s, 73 output tokens**, clean answer.
- **M2 (code)** - `mcp_client.py` (connect, list tools with pagination, call tools, read-only
  allowlist, adapter into `Tool`), fixture MCP server for tests, `fixtures/shop` dataset,
  `mcp_demo.py` against `@modelcontextprotocol/server-filesystem@2.0.0` (ADR 0009). 49 tests passing.
  - Verified on Tanishq's Mac 2026-10-21: 49 passed; demo listed 14 tools, 6 exposed; write blocked by allowlist, `/etc/passwd` blocked by server sandbox.

## Current implementation state
| Module | Responsibility |
|---|---|
| `types.py` | Provider-neutral Pydantic types (`Message`, `ToolCall`, `ToolSpec`, `ModelResponse` incl. `thinking`, `Usage`) |
| `tools.py` | `Tool` + `ToolRegistry`: rejects unknown tools / invalid args (any JSON Schema draft) before running |
| `models/` | `ModelAdapter` interface, `ScriptedModel` (tests), `OllamaModel` (local) |
| `runner.py` | `run_agent()`: the loop, `max_steps`, `RunResult` |
| `mcp_client.py` | `connect(McpServerConfig)` -> `McpConnection`: tools, `call_tool_text`, `agent_tools(allow=...)` |
| `demo.py` / `mcp_demo.py` | Manual demos for M1 (model + Python tools) and M2 (real MCP server, no model) |

## Known issues
- The demo's answer check is a weak substring match - strict validators come in M4.
- Model load time not recorded separately (record Ollama `load_duration` in M3 traces).
- A server that dies during startup is only reported after the full `initialize` timeout (60 s).
- `server-filesystem@2.0.0` declares `node >=24`; Tanishq's Mac has Node 22.17.1 (npm `EBADENGINE` warning). It works, but it's unsupported - upgrade Node to 24. Also: traces should record the environment (Node/Python/server versions).

## Bug log
| Date | Bug | Root cause | Fix | Regression test |
|---|---|---|---|---|
| 2026-10-21 | Model reasoning leaked into `final_answer`; check still passed | `qwen3:4b` = always-thinking `qwen3:4b-thinking-2507`; ignores `think:false`; emits only `</think>` | `thinking` field + split in adapter; default model `qwen3:4b-instruct` (ADR 0008) | `tests/test_ollama.py::test_regression_*` |
| 2026-10-21 | `call_tool("read_note", name="todo")` raised "multiple values for argument 'name'" | Test helper's first parameter was also called `name`, clashing with a tool argument of the same name | First parameter made positional-only (`tool_name, /`) | `tests/test_runner.py::test_regression_fake_call_tool_accepts_an_argument_called_name` |
| 2026-10-21 | `pyproject.toml` allowed `mcp>=1.0` though the code needs the v2 API | Dependency bound added before the API was checked | Bound to `mcp>=2.3,<3` | (caught in review; fresh installs resolve 2.x) |

## Approved decisions
See [decisions/README.md](decisions/README.md) (0001-0009).

## Unresolved questions
- M3: trace file format (one JSONL line per event vs one JSON per run) - to decide at M3 start.
- M2/M3: CLI library - stdlib `argparse` vs Typer?

## Milestones
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | Done |
| M1 | Agent loop with in-process Python tools + fake model | Done |
| M2 | MCP client over stdio (filesystem server, fixture data) | Done |
| M3 | Agent loop over MCP tools + trace recording | Planning |
| M4 | YAML suite format + deterministic validators | Not started |
| M5 | Repeats, failure classification, report | Not started |
| M6 | First public results on 2-3 real servers + write-up | Not started |
