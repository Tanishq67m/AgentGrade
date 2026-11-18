# Project Status

_Last updated: 2026-11-18_

## Current objective
**M7a done (2026-11-18).** TDQS graded all six measured `search_files` descriptions **A** while agents passed
8%-75% (Spearman -0.09 / +0.20, two judges). The 3/12 and 9/12 descriptions scored the same (3.92). All three
pre-registered predictions held. TDQS did catch the one-line `git_log` description (C vs A). Case study v1.1,
Finding 6. Next: **M7b `agentgrade improve`**, plus talking to 5 MCP server authors.

Previous: **M7a - static vs measured** (ADR 0016). Positioning reviewed 2026-11-17 (ADR 0015,
[POSITIONING.md](POSITIONING.md)): harness features (repeats, traces, CI gates) are commodity; the gap
is proving *which line* of a tool description breaks agents and *which rewrite* fixes it. First test
of that claim: re-implement Glama's published TDQS, score the 8 descriptions we already measured, and
compare scores with measured pass rates. Predictions are written in ADR 0016 before running. New command:
`agentgrade static-score`. Next: M7b `agentgrade improve`; in parallel, talk to 5 MCP server authors.
CI mode moved to "later" (Braintrust etc. already ship it).

Previous:
**M6 - public case study.** Draft `docs/CASE_STUDY.md` written from the 222 recorded runs; upstream issue draft for git
(`docs/upstream/`). gpt-oss-120b on git done (14/15 both variants). Upstream filesystem 2.2.0 measured: 3/12. That
corrected our ablation claim. Examples-vs-rules experiment done: concrete examples, not the rules, stop the refusals
(9/12 vs 3/12). **Case study v1 complete (312 runs).** Upstream issues filed 2026-11-16:
[#5552](https://github.com/modelcontextprotocol/servers/issues/5552) (git `git_log`),
[#5553](https://github.com/modelcontextprotocol/servers/issues/5553) (filesystem `search_files` examples). Next: respond to
triage; choose the next build milestone (CI mode or recommendations in reports). Upstream
filesystem 2.2.0 (2026-11-04) independently rewrote `search_files`' description along the lines of our
`glob-rules-only` variant, so no filesystem issue is needed; that release gets measured instead.

Previous: **M5b - second MCP server (git).** Suite `setup` step, deterministic git fixture, server logs to file,
`suites/git.yaml` done (ADR 0014). Git suite run 1 completed; taxonomy (`stopped_after_error`) and variants
revised from its traces (157 tests). Git suite run 2 done: the server-side git_log description fix reached 15/15;
the generic agent-side "retry on error" line didn't help. M5b done. Next: public case study + upstream issues (M6).

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

**2026-11-18 - static vs measured (TDQS, 70 scorings, no new agent runs).** Filesystem `search_files`, judge
gpt-oss-120b / gpt-oss-20b: baseline 3.62 / 3.80 (measured 4/36), explore-first-only 4.12 / 4.40 (1/12),
upstream-2.2.0 4.04 / 4.38 (2/12), generic-examples 3.92 / 4.46 (3/12), clear-search 4.12 / 4.56 (17/24),
glob-rules-only 3.92 / 4.26 (18/24). All tier A. Spearman -0.09 / +0.20. Git `git_log` (120B): original 2.70 C
(25/30) vs rewrite 3.98 A (15/15). Reports: `results/2026-11-1[78]-static-tdqs-*.md`.
| Date | Task | Model | Tools | Result | Notes |
|---|---|---|---|---|---|
| 2026-10-22 | `shop.shipping_cost_a17` | `qwen3:4b-instruct` (`0edcdef34593`, Q4_K_M) | 6 read-only filesystem tools | **FAIL** - `max_steps` (10), no answer, 40.2 s, 14167 in / 853 out tokens | Trace `20261022T085044Z-227814`. Used only `search_files`, with 9 non-recursive glob patterns (`order*.json`, `A17*.csv`, ...) though the file is at `orders/A17.json` and the description says to use `**/` for subfolders. Steps 4-10 repeat "try a broader pattern" without broadening. Never tried `list_directory`/`directory_tree`. Server verified correct: `**/A17*` and `shipping*.json` match. |

| 2026-10-22 | **Suite run 1** `shop-filesystem`, 4 tasks x 3 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | per variant | baseline **1/12** (CI 1-35%) · clear-search-description **9/12** (CI 47-91%) · no-search **1/12** | Run `20261022T093534Z-654798`. 23/25 failures = `gave_up` (refused on step 1, zero tool calls: "I don't have access to any system or database..."). `order_status_b42` 0/3 in every variant. The winning description mixes two ideas -> ablation in run 2. |

| 2026-10-22 | **Suite run 2** `shop-filesystem`, 4 tasks x 6 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | per variant | baseline **1/12** · glob-rules-only **9/12** (CI 47-91%) · explore-first-only **1/12** · clear-search-description **8/12** · no-search **1/12** · agent-context **3/12** (CI 9-53%) | Run `20261022T095739Z-f2965e`. Baseline (1/12) and combined description (9 -> 8/12) **replicated** across independent runs. Ablation: the precise glob rules carry the whole effect; the "explore first" sentence adds nothing. The agent-side system-prompt sentence only helped the one task whose prompt mentions files. `order_status_b42`: 0/18 (0/27 across both runs). |

| 2026-10-23 | **Suite run 3** `shop-filesystem`, 4 tasks x 2 variants x 3 | `openai/gpt-oss-120b` on Groq free tier, temp 0.7 | per variant | baseline **11/12** (CI 65-99%) · glob-rules-only **12/12** (CI 76-100%) | Run `20261023T115016Z-9b0ee9`. The strong model barely needs the description fix (the 4B model went 1/12 -> 9/12). `order_status_b42` 3/3 in both variants (0/27 for the 4B model). The one failure was the model emitting malformed tool-call JSON (Groq 400 `tool_use_failed`), recorded as `harness_error` before the fix below. 129/159 model calls waited on rate limits (562 s total). |

| 2026-10-24 | **Git suite run 1** `git-repo`, 5 tasks x 2 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | 7 read-only git tools | baseline **6/15** (CI 20-64%) · repo-path-given **12/15** (CI 55-93%) | Run `20261024T170846Z-4dec97`. **All 9 baseline failures = `stopped_after_error`**: called a tool with `repo_path="."`, got an error naming the correct path, answered "please check the path" instead of retrying. `last_commit_author` **0/6 in both variants**: `git_log(start_timestamp="now", end_timestamp="now")` returned an empty history and the agent concluded "no commits / unknown author". |

| 2026-10-25 | **Git suite run 2**, 5 tasks x 4 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | 7 read-only git tools | baseline **7/15** · repo-path-given **13/15** · retry-on-error **8/15** · path-given-clear-log **15/15** (CI 80-100%) | Run `20261025T061929Z-496013`. Run 1 **replicated** (6->7/15, 12->13/15). `last_commit_author`: 1/6 across both runs with the path, 3/3 with the clearer git_log description. retry-on-error: no net effect, with side effects (rounding task 0/3 `gave_up`; 2 runs said "Let me retry with the correct path" and then ended the turn without a tool call). |

| 2026-11-10 | **Git suite, strong model**, 5 tasks x 2 variants x 3 | `openai/gpt-oss-120b` on Groq free tier, temp 0.7 | 7 read-only git tools | baseline **14/15** · repo-path-given **14/15** | Run `20261110T162354Z-0bdeb7`. All 15 baseline runs hit the wrong-path error; 14 recovered (the 4B model mostly gave up). 0 `git_log` timestamp filters used. Both failures: `step_limit` on `unmerged_branch`, repeatedly passing range syntax (`main..feature/discounts`) to `git_diff`, which doesn't support it. Twice mis-copied the long sandbox path (dropped one digit). 511 s of rate-limit waits. |

| 2026-11-16 | **Upstream filesystem 2.2.0**, 4 tasks x 1 variant x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | 6 read-only tools | **3/12** (CI 9-53%) | Run `20261116T081507Z-b81578`. 2.2.0 ships precise matching rules with generic examples. shipping_cost 3/3 (was 1/3), other 3 tasks 0/9, all `gave_up`. So the rules fix searching, not refusals; our "glob-rules-only" variant (9/12) also had concrete examples (`**/*.json`, `**/*invoice*`). 2.2.0 also changed directory_tree, get_file_info and read_text_file, so it's not a single-variable comparison. |

| 2026-11-16 | **Examples vs rules**, 4 tasks x 4 variants x 3 | `qwen3:4b-instruct` (`0edcdef34593`), temp 0.7 | 6 read-only tools, server 2.0.0 | baseline **2/12** · glob-rules-only **9/12** (3rd time) · upstream-2.2.0-description **2/12** · glob-rules-generic-examples **3/12** | Run `20261116T095521Z-4ff742`. Swapping only the two examples (`**/*.json`, `**/*invoice*` to `**/*.ext`, `**/name`) took order_count + heaviest from 6/6 to 0/6, all `gave_up`. With concrete examples the model searched `**/*order*`, `**/*.order` and `**/*.invoice` (a literal echo). Rules fix *how* to search; concrete examples make it search at all. |

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

**Findings from git suite run 1:**
- **Recoverable errors aren't recovered.** The error message contained the exact fix (the allowed path), and the
  agent passed every time it did retry, but it usually stopped and asked the user instead. New category: `stopped_after_error`.
- **An empty result plus an optional filter leads to a confident wrong answer.** "Most recent" was translated into a
  zero-length time window. The server's empty `Commit history:` gave no hint, the same pattern as the filesystem's
  bare "No matches found". Two servers, same anti-pattern: empty results without guidance.
- Next variants: `retry-on-error` (agent-side, vs baseline) and `path-given-clear-log` (server-side git_log
  description, vs repo-path-given).

**Findings from git suite run 2:**
- **Server-side description fix: 13/15 -> 15/15.** With git_log's description saying "newest first, timestamp
  filters optional", the zero-length `now`..`now` window never appeared again (last_commit_author 3/3, was 1/6).
- **Generic agent-side advice didn't help:** "If a tool errors, read it and retry" scored 8/15 vs baseline 7/15.
  It fixed one task (uncommitted_file 0/3 -> 3/3), broke another (rounding_fix_author 2/3 -> 0/3, refusing
  without any tool call), and twice the model *wrote* "Let me retry with the correct path" and then ended its
  turn without calling a tool.
- **Concrete context helped, generic advice didn't:** giving the repo path (a fact) took 7/15 to 13/15; telling
  the agent how to behave did almost nothing. The filesystem suite showed the same thing (agent-context 3/12).
- Across both servers and both runs, **fixing the tool description beat changing the agent's prompt.**

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
See [decisions/README.md](decisions/README.md) (0001-0016).

## Unresolved questions
- Will MCP server authors run this before a release? (Talk to 5 of them; see POSITIONING.md.)
- How to remove the task-writing barrier: generated tasks vs ready-made suites for popular servers?
- Which 2nd and 3rd MCP servers for M5? (Python-based ones avoid the Node dependency.)
- Repeats for the public result: 3 (fast) vs 5+ (narrower intervals, ~2x time)?

## Milestones (re-planned 2026-10-22: repeats/classification/report pulled into M4 for the showcase)
| # | Milestone | Status |
|---|---|---|
| M0 | Repo foundation | Done |
| M1 | Agent loop with in-process Python tools + fake model | Done |
| M2 | MCP client over stdio (filesystem server, fixture data) | Done |
| M3 | Agent loop over MCP tools + trace recording | Done |
| M4 | Suites, variants, repeats, failure classification, reports | Done |
| M5a | Stronger model via OpenAI-compatible adapter (free tiers) | Done |
| M5b | Second server: git (`suites/git.yaml`) | Done |
| M5 | Third server; refine taxonomy; actionable recommendations in reports | Not started |
| M6 | Public case study: before/after results + write-up; README results section | Done (case study v1; issues #5552, #5553) |
| M7a | Static vs measured: TDQS scores vs measured pass rates (ADR 0016) | Done (Finding 6) |
| M7b | `agentgrade improve`: generate description rewrites, run them as variants, recommend the measured winner | Next |
| Later | Generated tasks / ready-made suites, CI mode, public index, HTML report, paid model adapters, container isolation | - |
