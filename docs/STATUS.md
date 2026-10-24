# Project Status

_Last updated: 2026-10-21_

## Current objective
**M5b - second MCP server (git).** Suite `setup` step, deterministic git fixture, server logs to file,
`suites/git.yaml` (5 tasks x 2 variants) done and verified on the real `mcp-server-git` with a staged agent
(ADR 0014, 155 tests). Next: first real run on the Mac.

Previous:
**M5a - stronger model, still free.** Done: adapter works locally (Ollama /v1 smoke run PASS) and on Groq
(`gpt-oss-120b`, 24 runs). Two reporting bugs found by that run and fixed (147 tests). Next: M5b second MCP server.

Previous objective:
**Milestone 4 - suites, variants, repeated runs, failure classification, reports.** Code + tests
done. Suite runs 1 and 2 completed on the Mac; the before/after result replicated and the ablation
identified the active change (results below). Next: M5 (more servers + a stronger model) and the public case study.

## Completed
- **M0** - repo foundation (ADRs 0001-0006).
- **M1** - async agent loop, tool registry, scripted fake model, Ollama adapter (ADRs 0007-0008).
  - Run #1 `qwen3:4b` (always-thinking): correct, but 221 s, 1884 output tokens, reasoning leaked into the answer.
  - Run #2 `qwen3:4b-instruct`: correct, 14.2 s, 73 output tokens, clean answer.
- **M2** - MCP client over stdio, read-only allowlist, fixture server (ADR 0009). Verified on the Mac:
  14 tools offered, 6 exposed; write blocked by the allowlist, `/etc/passwd` blocked by the server sandbox.
- **M3 (code)** - JSONL traces, environment/model/server capture, secret redaction, numeric answer
  check, `mcp_agent_demo` (ADR 0010), `--tools` flag to narrow the allowlist.
- **M4 (code)** - `suite.py` (YAML + validation), suite checks, `classify.py` (failure categories),
  `evaluate.py` (variants x tasks x repeats, fresh sandbox per run), `report.py` (Wilson intervals),
  `agentgrade run` CLI, `suites/shop.yaml` (ADR 0011). After run 1: `gave_up` category, `agentgrade report`
  re-classification, ablation + agent-side variants (ADR 0012). 120 tests passing.

## Results log
| Date | Task | Model | Tools | Result | Notes |
|---|---|---|---|---|---|
| 2026-10-22 | `shop.shipping_cost_a17` | `qwen3:4b-instruct` (`0edcdef34593`, Q4_K_M) | 6 read-only filesystem tools | **FAIL** - `max_steps` (10), no answer, 40.2 s, 14167 in / 853 out tokens | Trace `20261022T085044Z-227814`. Used only `search_files`, with 9 non-recursive glob patterns (`order*.json`, `A17*.csv`, ...) though the file is at `orders/A17.json` and the description says to use `**/` for subfolders. Steps 4-10 repeat "try a broader pattern" without broadening. Never tried `list_directory`/`directory_tree`. Server verified correct: `**/A17*` and `shipping*.json` match. |

| 2026-10-22 | **Suite run 1** `shop-filesystem`, 4 tasks x 3 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | per variant | baseline **1/12** (CI 1-35%) · clear-search-description **9/12** (CI 47-91%) · no-search **1/12** | Run `20261022T093534Z-654798`. 23/25 failures = `gave_up` (refused on step 1, zero tool calls: "I don't have access to any system or database..."). `order_status_b42` 0/3 in every variant. The winning description mixes two ideas -> ablation in run 2. |

| 2026-10-22 | **Suite run 2** `shop-filesystem`, 4 tasks x 6 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | per variant | baseline **1/12** · glob-rules-only **9/12** (CI 47-91%) · explore-first-only **1/12** · clear-search-description **8/12** · no-search **1/12** · agent-context **3/12** (CI 9-53%) | Run `20261022T095739Z-f2965e`. Baseline (1/12) and combined description (9 -> 8/12) **replicated** across independent runs. Ablation: the precise glob rules carry the whole effect; the "explore first" sentence adds nothing. The agent-side system-prompt sentence only helped the one task whose prompt mentions files. `order_status_b42`: 0/18 (0/27 across both runs). |

| 2026-10-23 | **Suite run 3** `shop-filesystem`, 4 tasks x 2 variants x 3 | `openai/gpt-oss-120b` on Groq free tier, temp 0.7 | per variant | baseline **11/12** (CI 65-99%) · glob-rules-only **12/12** (CI 76-100%) | Run `20261023T115016Z-9b0ee9`. The strong model barely needs the description fix (the 4B model went 1/12 -> 9/12). `order_status_b42` 3/3 in both variants (0/27 for the 4B model). The one failure was the model emitting malformed tool-call JSON (Groq 400 `tool_use_failed`), recorded as `harness_error` before the fix below. 129/159 model calls waited on rate limits (562 s total). |

**Findings from run 1** (inputs for M5's failure taxonomy and recommendations):
- Model-side: wrong tool mental model (non-recursive globs), **repetition loop without progress**, no strategy switch.
- Tool-side (server UX): a bare `No matches found` gives no recovery hint; a message about `**/` would likely let the agent recover.
- Harness: input tokens grow every step because the full history is resent (14k in for 10 steps).

**Findings from suite run 1:**
- The dominant failure is not bad tool use but **no tool use**: the model assumes it has no access and declines.
- Changing **one tool's description** turned 1/12 into 9/12. The model then used `**/` patterns and `directory_tree`.
  Which of the two ideas in that description mattered is unknown -> `glob-rules-only` / `explore-first-only`.
- Removing `search_files` didn't help (1/12): the refusal happens before any tool choice.
- `order_status_b42` failed everywhere. Hypothesis (unverified): "status" suggests an order-management system, not files.
- The official `search_files` description begins "Recursively search..." though matching is non-recursive without `**/`.

**Findings from suite run 2 (ablation):**
- **The active ingredient is the precise matching rules** (glob-rules-only 9/12 vs explore-first-only 1/12, same as baseline).
  In passing runs the model's first search used `**/` (`**/*order*`) instead of `order*.txt`.
- Rewriting that one description also cut `gave_up` from 9 to 3. *Why* a clearer search description makes the model
  attempt the task at all is unverified. Hypothesis: concrete, business-flavoured examples (`**/*invoice*`) signal that
  the files hold user data. One run even searched `**/*.invoice`, copying the example literally.
- **Agent-side fix (system prompt) < server-side fix (tool description)** for this model: 3/12 vs 9/12; it only fixed
  the task whose prompt already mentions files.
- **New secondary failure:** stopping after the first file ("the order data doesn't include the shipping cost") instead of
  looking for the rates file: 5 `wrong_answer` runs on `shipping_cost_a17`. Candidate category: `incomplete_exploration`.
- `order_status_b42` is never attempted (0/27). Unverified hypothesis: "current status" reads as a live-system query.
- Caveat: one 4B local model, one small dataset, 3 repeats per cell. These are findings about this setup.

**Findings from suite run 3 (strong model):**
- **Tool-description quality matters most for small models.** gpt-oss-120b solved 11/12 with the original
  description; the 4B model solved 1/12. Same tasks, same server.
- The small model's dominant failure (`gave_up`, refusing without trying) **did not occur once** with the strong model.
- Groq returned **41 distinct `system_fingerprint`s in 159 calls** of the same model id: a hosted model can't be
  pinned like a local digest. Results on hosted models are reproducible only "as of that date".

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
| 2026-10-22 | `trace.event("check", **outcome)` raised TypeError; once fixed, the data's `type` would silently replace the event type | Keyword argument named `type` + data allowed to overwrite envelope keys (same class of bug as the M2 `name` clash) | Positional-only `event_type, /`; reserved keys `seq/ts/type` rejected | `test_trace.py::test_regression_event_data_cannot_overwrite_the_envelope` |
| 2026-10-23 | Model's malformed tool-call JSON recorded as `harness_error` (blamed AgentGrade) | Groq validates tool JSON server-side and returns HTTP 400 `tool_use_failed` instead of the bad call; the adapter treated every 400 as a provider error | Recognise `tool_use_failed`, turn it into a `ToolCall` with `parse_error`, and feed it back as `invalid_arguments` (same as malformed JSON returned to us) | `test_openai_compat.py::test_regression_provider_rejecting_malformed_tool_json_is_the_models_failure` |
| 2026-10-23 | Report "median time" 33 s, mostly free-tier queueing | Per-call latency excluded rate-limit waits, but the per-run duration in the report didn't | `RunSummary.rate_limit_wait_ms`; report times exclude it (8.7 s real median); old runs backfilled from traces | `test_evaluate.py::test_report_times_exclude_rate_limit_waits` |
| 2026-10-22 | "Ollama is down" would be recorded as an ordinary failed run and the suite would keep going; error text read "unhandled errors in a TaskGroup" | Errors inside the MCP client context arrive wrapped in an `ExceptionGroup` (anyio), so `except FatalError` never matched | `root_cause()` unwraps before deciding fatal vs per-run | `test_evaluate.py::test_regression_fatal_error_inside_mcp_context_stops_the_suite` |

## Approved decisions
See [decisions/README.md](decisions/README.md) (0001-0010).

## Unresolved questions
- Which 2nd and 3rd MCP servers for M5? (Python-based ones avoid the Node dependency.)
- Repeats for the public result: 3 (fast) vs 5+ (narrower intervals, ~2x time)?

## Milestones (re-planned 2026-10-22: repeats/classification/report pulled into M4 for the showcase)
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | Done |
| M1 | Agent loop with in-process Python tools + fake model | Done |
| M2 | MCP client over stdio (filesystem server, fixture data) | Done |
| M3 | Agent loop over MCP tools + trace recording | Done |
| M4 | Suites, variants, repeats, failure classification, reports | Code done - real run pending |
| M5a | Stronger model via OpenAI-compatible adapter (free tiers) | Done |
| M5b | Second server: git (`suites/git.yaml`) | Code done - real run pending |
| M5 | Third server; refine taxonomy; actionable recommendations in reports | Not started |
| M6 | Public case study: before/after results + write-up; README results section | Not started |
| Later | CI mode (fail a PR on reliability regression), HTML report, paid model adapters, container isolation | - |
