# AgentGrade - Project Overview

The whole project on one page: the goal, what has been built and why, the decisions
and their trade-offs, what went wrong, and what comes next. Details live in
[decisions/](decisions/) (one record per decision) and [STATUS.md](STATUS.md) (live state + bug log).

## 1. Goal

Products are increasingly used by AI agents rather than people, mostly through
**MCP (Model Context Protocol) servers**: a server exposes "tools" (name, description,
JSON Schema for arguments) and an LLM decides which to call. Server authors rarely know
whether agents can actually use their tools: whether the model picks the right one,
fills the arguments correctly, recovers from errors, and reaches the right answer.

AgentGrade answers that with evidence: **run an agent on a defined task against a real
MCP server, record everything it does, check the outcome in code, repeat to measure
variability, and report why it succeeded or failed.**

**Who it's for:** teams building AI agents on tools/APIs, companies that need evidence an agent is
reliable before putting it into real workflows, and MCP server developers who want to know where
models struggle with their tools. The problem is the gap between an agent that works in a demo and
one that works consistently:

| Problem | What AgentGrade does about it |
|---|---|
| "It worked yesterday, fails today." | Records exact model digest, server version, code commit and environment. |
| "We don't know why it failed." | Full execution traces plus a failure category for every run. |
| "It passed once. Is it reliable?" | Repeats every task and reports pass rates with confidence intervals. |
| "The model says it's correct." | Checks results in code; the model never grades itself. |
| "Did our fix actually help?" | Variants: the same tasks run before/after one change (e.g. a rewritten tool description), compared side by side. |

These are the intended benefits. So far they are demonstrated on one server and a local model, not yet proven with users.

Core principles:
- **Deterministic validation.** A task passes only when code says so. The model never grades itself.
- **Reproducibility.** Every result records the exact model weights, server version, code commit and environment.
- **Safety first.** Trusted servers, read-only tasks and throwaway data until stronger isolation exists.
- **Smallest architecture that works.** A modular monolith with CLI + files; no database or web stack until the data shapes are proven.

## 2. Architecture

```
task + expected answer
        │
        ▼
   run_agent()  ── loop ──►  ModelAdapter.complete(messages, tools)   (Ollama / fake / later paid)
        │                         │ returns text and/or tool calls
        │                         ▼
        │                    ToolRegistry.execute(call)
        │                      1. tool exists?        (allowlist - unknown_tool)
        │                      2. args match schema?  (jsonschema - invalid_arguments)
        │                      3. run it              (errors - tool_error)
        │                         │
        │                         ▼
        │                    McpConnection  ── JSON-RPC over stdio ──►  MCP server subprocess
        │                                                              (pinned, sandboxed to a temp copy)
        ├──► TraceWriter: runs/<id>/trace.jsonl  (every event, flushed as it happens, secrets redacted)
        ▼
   RunResult ──► checks ──► failure classification ──► results.json + report.md

suite.yaml = model + server + allowlist + tasks (with checks) + variants
agentgrade run = every variant x task x repeat, each in a fresh sandbox + fresh server process
```

- **Python 3.12, uv, pytest, ruff** - lockfile-based, reproducible setup.
- **Pydantic** for every data shape; **jsonschema** for tool arguments.
- **Async throughout**, because the MCP SDK is async.
- Everything provider-specific sits behind one small interface (`ModelAdapter`), so a paid model is a new adapter, not a rewrite.

## 3. What was built, milestone by milestone

**M0 - Foundation.** `uv` project with a src layout, a lockfile, pytest and ruff, plus architecture
decision records (ADRs). The MVP scope was fixed up front: MCP over stdio, trusted servers,
read-only tasks, code-based checks. A web UI, database, auth targets, LLM judges and a leaderboard are explicitly deferred.

**M1 - Agent loop.** The core mechanism every agent framework hides: the model *requests* a tool
call, our code validates and runs it, the result goes back as a `tool` message, and the loop repeats
until a final answer or `max_steps`.
- A **scripted fake model** makes tests free and deterministic. You can force a wrong tool, bad arguments or an infinite loop on demand.
- **Errors are fed back to the model, not raised**, because recovery from mistakes is what we measure.
- **Ollama adapter** written with plain `httpx` against `/api/chat`, to keep the wire format visible and to stay free on an 8 GB laptop.

**M2 - MCP client.** Starts an MCP server as a subprocess using the official Python SDK (v2), lists
tools (with pagination) and wraps them as normal `Tool`s, so the M1 loop runs unchanged.
- **Security model:** the model sees only an **explicit allowlist**. Allowlisted tools must be marked read-only, or the run refuses to start. The server's `readOnlyHint` is untrusted input, so the allowlist is the real control.
- Verified on the official filesystem server: `write_file` was refused by our allowlist, and `/etc/passwd` by the server's own sandbox. Two independent layers.
- A tiny **Python fixture MCP server** runs the integration tests over real stdio without Node.js.

**M3 - Tracing.** JSONL trace per run. Each event is flushed immediately, so a crash still leaves a
readable partial trace. Run metadata records the Python/Node/package versions, git commit + dirty flag,
the Ollama model digest, the MCP server's name/version/protocol, the allowlist and the sandbox path.
Secret-looking keys are redacted. Crashes are recorded and then re-raised.
The demo answer check now extracts numbers instead of matching substrings.
The first real run failed; the trace explained why (see section 6).

**M4 - Suites, variants, repeats, reports.** Pulled forward so the project ends in a showcase:
**fail → trace → fix → repeatable before/after numbers.**
- **YAML suites** (strict validation: a typo fails loudly) define the model, server, allowlist, tasks and their code checks
  (`answer_number`, `answer_contains`, `answer_regex`, `tool_called`).
- **Variants** each change ONE thing vs baseline: a tool subset, or a **rewritten tool description**. Description
  overrides let a server author test a better description *without redeploying the server*. Overrides must be
  generic; a hint about the task would measure the leak, not the description.
- Every run gets a **fresh fixture copy and a fresh server process**, so no state leaks between runs.
- **Failure classification** from the trace: `loop` (the same tool returned an identical result 3+ times in a row,
  the pattern of real run 1), `step_limit`, `no_answer`, `wrong_answer`, `harness_error` (infrastructure, not the agent).
- **Reports** show pass rates as k/n with a **95% Wilson interval** and a small-sample warning: 3/3 means
  "probably good" (interval 44-100%), not "100% reliable".
- `agentgrade run suites/shop.yaml` gives `report.md`, `results.json` and one trace per run.

## 4. Key decisions and trade-offs

| Decision | Alternative | Why this |
|---|---|---|
| MCP first | OpenAPI, docs | Tool discovery is built into the protocol; no spec conversion or auth. |
| CLI + files | FastAPI + Postgres + React | Don't freeze a DB schema before real runs prove the data shape. |
| Local Ollama model | Paid APIs | Zero cost, unlimited reproducible runs. The trade-off is weaker models, so results are always labelled with the model. |
| Feed tool errors back | Abort the run | Recovery behaviour is a core metric. |
| Explicit allowlist | Trust server hints | Hints come from the system under test. |
| Pin model digest and server version | `latest` tags | A tag silently changed which model ran (see mistakes). |
| JSONL traces | One JSON per run | Crash-safe, streamable, greppable. |
| Fake model + fake HTTP in tests | Test with real models | Real models are non-deterministic and slow; tests must be exact. Real runs are manual demos. |
| One-change variants | Free-form A/B configs | A difference in pass rate is attributable to one change. |
| Fresh sandbox + server per run | Reuse one server | Isolation and reproducibility beat ~1-2 s of startup per run. |
| Wilson interval | Raw percentage | Honest at small n and at 0% or 100%. |
| Temperature 0.7 in suites | Temperature 0 | Reliability is about variation; at 0, repeats are near-identical. |

## 5. Mistakes and what they taught

1. **Wrong model behind a familiar tag.** `qwen3:4b` on Ollama is actually the always-thinking
   `qwen3:4b-thinking-2507` (same digest). It ignored `think: false`, its whole reasoning monologue became the
   "final answer", and the run took 221 s. Diagnosed from the evidence: a closing `</think>` with no opening
   tag, then matching digests. Fix: separate reasoning into its own field and switch to `qwen3:4b-instruct`
   (14.2 s, 73 vs 1884 output tokens). **Lesson:** record exact identities (digests, versions), not names.
2. **A grader that passed a bad answer.** `"12.5" in answer` passed the reasoning dump above and would pass
   `112.5`. **Lesson:** an evaluation tool's checks need tests of their own. Replaced with numeric extraction;
   strict validators are M4's job.
3. **Over-redaction.** The secret filter matched the substring `token`, so `input_tokens` was hidden in traces.
   A silent failure: nothing crashed, the data was just gone. A test caught it. Fixed with whole-word key matching.
4. **Dependency bound written before checking the API.** `mcp>=1.0` was declared while the code needed v2's
   `Client`/`MCPServer`. Caught in review; now `>=2.3,<3`. **Lesson:** read the installed library's
   actual API before relying on it.
5. **Name clash in a test helper.** `call_tool(name, **arguments)` broke for a tool whose own argument was
   called `name`. Fixed with a positional-only parameter.
6. **Environment drift.** `uv` picked up Anaconda's Python, and the filesystem server needs Node ≥ 24 while the
   machine had 22. Both worked "by accident". Fixing Node took two attempts: the first install went into the
   project folder as an npm package instead of the system. This is why traces now record the environment.
7. **The same bug class twice.** `trace.event(type, **data)` broke when the data had its own `type` field, just like
   mistake 5. Worse, once that was fixed, the data could have silently overwritten the event's type. Fix: positional-only
   parameter plus reserved keys rejected. **Lesson:** any function that takes `**kwargs` must protect its own names.
8. **Wrapped exceptions hiding fatal errors.** Errors inside the MCP client arrive wrapped in an `ExceptionGroup`
   (anyio task groups), so "Ollama is down" would have been recorded as an ordinary failed run while the suite ground
   through every remaining run. Caught by a test before any real suite run. Fix: unwrap to the root cause before deciding.

Each fixed bug has a regression test and an entry in the STATUS bug log.

## 6. Current state and known limitations

- 116 automated tests (unit, fake-HTTP, real-stdio integration, end-to-end suite runs).
- **First real result (failed, and informative):** `qwen3:4b-instruct` on the official filesystem server hit the
  10-step limit. It searched with non-recursive glob patterns (`order*.json`) for a file in a subfolder,
  repeated near-identical searches 7 times, and never tried the listing tools. The server was verified correct.
  The finding has two sides: a model weakness (wrong mental model of the tool, a loop without progress) and a
  tool-UX gap (`No matches found` gives no hint about `**/`). Failures with this kind of explanation are the product.
- **The showcase run is next:** `suites/shop.yaml` runs 4 tasks x 3 variants (baseline, clearer `search_files`
  description, search tool removed) x 3 repeats on the real server. The pipeline is verified with scripted agents;
  real-model numbers are pending.
- Limitations: stdio only; one model provider; only `max_steps` as a limit (no token/time/cost limits yet);
  key-based redaction only; trusted servers only. Server tool descriptions go straight into the prompt, which is a
  prompt-injection risk accepted only because the servers are trusted. Startup failures are reported only after a 60 s timeout.

## 7. Next

- **M4 showcase run** on the Mac, then publish the before/after report honestly, whatever it shows.
- **M5 - More servers + recommendations.** Suites for 2-3 more MCP servers (Python-based ones avoid the Node dependency),
  refine the failure taxonomy, and have reports suggest concrete fixes (e.g. "search returned identical
  empty results 9x: say in the description that patterns are non-recursive").
- **M6 - Public case study:** before/after results across servers, a write-up, and a results section in the README.
- **Later, driven by demand:** CI mode (fail a pull request when reliability drops), HTML report, paid model
  adapters, FastAPI + PostgreSQL for run history, container isolation before running any untrusted server.
