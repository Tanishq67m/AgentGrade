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
   RunResult ──► checks (answer_has_number) ──► PASS / FAIL
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
   machine had 22. Both worked "by accident". This is why traces now record the environment.

Each fixed bug has a regression test and an entry in the STATUS bug log.

## 6. Current state and known limitations

- 84 automated tests (unit, fake-HTTP and real-stdio integration).
- **First real result (failed, and informative):** `qwen3:4b-instruct` on the official filesystem server hit the
  10-step limit. It searched with non-recursive glob patterns (`order*.json`) for a file in a subfolder,
  repeated near-identical searches 7 times, and never tried the listing tools. The server was verified correct.
  The finding has two sides: a model weakness (wrong mental model of the tool, a loop without progress) and a
  tool-UX gap (`No matches found` gives no hint about `**/`). Failures with this kind of explanation are the product.
- Limitations: stdio only; one model provider; only `max_steps` as a limit (no token/time/cost limits yet);
  key-based redaction only; trusted servers only. Server tool descriptions go straight into the prompt, which is a
  prompt-injection risk accepted only because the servers are trusted. Startup failures are reported only after a 60 s timeout.

## 7. Next

- **M4 - Suites.** Tasks defined in YAML (task, target server, allowlist, expected outcome, check type) and a
  set of deterministic validators. Command: `agentgrade run suite.yaml`.
- **M5 - Reliability.** N repeats per task, pass rate with honest small-sample notes, a **failure taxonomy**
  derived from traces (wrong tool, invalid arguments, tool error, step limit, wrong answer, no answer), and a
  markdown report with latency/tokens.
- **M6 - First public results** on 2-3 real MCP servers, plus a write-up.
- **Later, once data shapes are stable:** FastAPI + PostgreSQL for run history and before/after comparisons,
  paid model adapters, HTTP transports, container isolation before running any untrusted server, CI integration.
