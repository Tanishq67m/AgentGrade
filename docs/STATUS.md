# Project Status

_Last updated: 2026-10-21_

## Current objective
**Milestone 1 - agent loop with in-process tools.** Code + tests done. First real run passed but exposed a bug (fixed, ADR 0008); re-run with `qwen3:4b-instruct` pending.

## Completed
- **M0** - repo foundation (uv project, src layout, ADRs 0001-0006). Pushed to GitHub.
- **M1 (code)** - async agent loop, tool registry with JSON Schema validation, scripted fake model,
  Ollama adapter, demo command. 36 tests passing.
- **M1 real run #1** (`qwen3:4b`): correct 2-tool sequence, answer 12.5, 221 s, 3687 in / 1884 out tokens.

## Current implementation state
| Module | Responsibility |
|---|---|
| `types.py` | Provider-neutral Pydantic types: `Message`, `ToolCall`, `ToolSpec`, `ModelResponse`, `Usage` |
| `tools.py` | `Tool` + `ToolRegistry`: rejects unknown tools / invalid args before running; errors become data |
| `models/base.py` | `ModelAdapter` interface every provider implements |
| `models/fake.py` | `ScriptedModel` for deterministic, free tests |
| `models/ollama.py` | Local Ollama via `httpx` → `/api/chat` |
| `runner.py` | `run_agent()`: the loop, `max_steps` limit, `RunResult` with steps, messages, usage, timings |
| `demo.py` | `python -m agentgrade.demo` - one 2-tool task against a real local model |

## Known issues
- Answer check in the demo is a weak substring match - to be replaced by strict validators in M4.
- Model load time not recorded separately (add Ollama `load_duration` to M3 traces).

## Bug log
| Date | Bug | Root cause | Fix | Regression test |
|---|---|---|---|---|
| 2026-10-21 | Model reasoning leaked into `final_answer`; check still passed | `qwen3:4b` = always-thinking `qwen3:4b-thinking-2507`; ignores `think:false`; emits only `</think>` | `thinking` field + split in adapter; default model `qwen3:4b-instruct` (ADR 0008) | `tests/test_ollama.py::test_regression_*` |

## Approved decisions
See [decisions/README.md](decisions/README.md) (0001-0008).

## Unresolved questions
- Is `qwen3:4b-instruct` fast and reliable enough on 8 GB? (compare with run #1)
- M2: CLI library - stdlib `argparse` vs Typer?

## Milestones
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | Done |
| M1 | Agent loop with in-process Python tools + fake model | Code done - instruct-model re-run pending |
| M2 | MCP client over stdio (filesystem server, fixture data) | Not started |
| M3 | Agent loop over MCP tools + trace recording | Not started |
| M4 | YAML suite format + deterministic validators | Not started |
| M5 | Repeats, failure classification, report | Not started |
| M6 | First public results on 2-3 real servers + write-up | Not started |
