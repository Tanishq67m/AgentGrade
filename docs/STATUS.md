# Project Status

_Last updated: 2026-10-21_

## Current objective
**Milestone 3 - agent loop over MCP tools + trace recording.** Done: first real traced run
completed (FAIL - see results). Optional ablation experiment (`--tools`) pending, then M4.

## Completed
- **M0** - repo foundation (ADRs 0001-0006).
- **M1** - async agent loop, tool registry, scripted fake model, Ollama adapter (ADRs 0007-0008).
  - Run #1 `qwen3:4b` (always-thinking): correct, but 221 s, 1884 output tokens, reasoning leaked into the answer.
  - Run #2 `qwen3:4b-instruct`: correct, 14.2 s, 73 output tokens, clean answer.
- **M2** - MCP client over stdio, read-only allowlist, fixture server (ADR 0009). Verified on the Mac:
  14 tools offered, 6 exposed; write blocked by the allowlist, `/etc/passwd` blocked by the server sandbox.
- **M3 (code)** - JSONL traces, environment/model/server capture, secret redaction, numeric answer
  check, `mcp_agent_demo` (ADR 0010), `--tools` flag to narrow the allowlist. 84 tests passing.

## Results log
| Date | Task | Model | Tools | Result | Notes |
|---|---|---|---|---|---|
| 2026-10-22 | `shop.shipping_cost_a17` | `qwen3:4b-instruct` (`0edcdef34593`, Q4_K_M) | 6 read-only filesystem tools | **FAIL** - `max_steps` (10), no answer, 40.2 s, 14167 in / 853 out tokens | Trace `20261022T085044Z-227814`. Used only `search_files`, with 9 non-recursive glob patterns (`order*.json`, `A17*.csv`, ...) though the file is at `orders/A17.json` and the description says to use `**/` for subfolders. Steps 4-10 repeat "try a broader pattern" without broadening. Never tried `list_directory`/`directory_tree`. Server verified correct: `**/A17*` and `shipping*.json` match. |

**Findings from run 1** (inputs for M5's failure taxonomy and recommendations):
- Model-side: wrong tool mental model (non-recursive globs), **repetition loop without progress**, no strategy switch.
- Tool-side (server UX): a bare `No matches found` gives no recovery hint; a message about `**/` would likely let the agent recover.
- Harness: input tokens grow every step because the full history is resent (14k in for 10 steps).

## Current implementation state
| Module | Responsibility |
|---|---|
| `types.py` | Provider-neutral Pydantic types |
| `tools.py` | `Tool` + `ToolRegistry`: validation before execution; errors as data; tool latency |
| `models/` | `ModelAdapter`, `ScriptedModel`, `OllamaModel` (+ `describe()` -> digest) |
| `runner.py` | `run_agent()`: loop, `max_steps`, optional trace |
| `mcp_client.py` | stdio connection, tool listing, allowlist, adapter into `Tool`, `describe()` |
| `servers.py` | Pinned, trusted server configs (`server-filesystem@2.0.0`) and allowlists |
| `trace.py` | `TraceWriter` (JSONL, flushed per event), `redact()` |
| `environment.py` | Python/Node/package/git capture (best-effort) |
| `checks.py` | `answer_has_number()` - first deterministic validator |
| `console.py` | Human-readable run printout |
| `demo.py`, `mcp_demo.py`, `mcp_agent_demo.py` | M1 / M2 / M3 manual demos |

## Known issues
- A server that dies during startup is only reported after the full `initialize` timeout (60 s).
- Redaction is key-based only (ADR 0010).
- Ollama model load time is not separated from the first step's latency.

## Bug log
| Date | Bug | Root cause | Fix | Regression test |
|---|---|---|---|---|
| 2026-10-21 | Model reasoning leaked into `final_answer`; check still passed | `qwen3:4b` = always-thinking `qwen3:4b-thinking-2507`; ignores `think:false`; emits only `</think>` | `thinking` field + split in adapter; default `qwen3:4b-instruct` (ADR 0008) | `test_ollama.py::test_regression_*` |
| 2026-10-21 | `call_tool("read_note", name="todo")` raised "multiple values for argument 'name'" | Helper's first parameter was also called `name` | Positional-only `tool_name, /` | `test_runner.py::test_regression_fake_call_tool_accepts_an_argument_called_name` |
| 2026-10-21 | `pyproject.toml` allowed `mcp>=1.0` though the code needs v2 | Bound written before checking the API | `mcp>=2.3,<3` | (review) |
| 2026-10-21 | Trace showed `input_tokens: [REDACTED]` | Secret detection used substring `token` | Whole-word key matching | `test_trace.py::test_secret_key_detection` |

## Approved decisions
See [decisions/README.md](decisions/README.md) (0001-0010).

## Unresolved questions
- M4: YAML suite schema - which check types beyond `answer_has_number`?
- M4: CLI - stay on argparse or move to Typer for `agentgrade run`?

## Milestones
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | Done |
| M1 | Agent loop with in-process Python tools + fake model | Done |
| M2 | MCP client over stdio (filesystem server, fixture data) | Done |
| M3 | Agent loop over MCP tools + trace recording | Done |
| M4 | YAML suite format + deterministic validators | Not started |
| M5 | Repeats, failure classification, report | Not started |
| M6 | First public results on 2-3 real servers + write-up | Not started |
