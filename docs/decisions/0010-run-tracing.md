# 0010. Run tracing (Milestone 3)

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq ("go M3" - accepted the recommendations)

## Problem
When an agent fails a task we need to see exactly where and why, and to know precisely
what ran (model weights, server version, code version) so the result can be reproduced.

## Decisions

| Question | Options | Choice | Why |
|---|---|---|---|
| Format | one JSON per run / **JSONL event stream** | **`runs/<run_id>/trace.jsonl`**, one event per line, flushed immediately | A crash halfway still leaves a readable partial trace; greppable; streamable. |
| Events | - | `run_started`, `model_call`, `tool_result`, `run_finished` / `run_failed`, `check` | Covers every decision the model made and every observation it got back. |
| Run metadata | - | environment (Python, Node, packages, git commit + dirty flag), model digest (Ollama `/api/tags`), MCP server name/version/protocol, tool allowlist, sandbox path, task id, expected answer | Lessons from M1/M2: a tag can hide a different model (ADR 0008), and Node 22 vs the required 24 went unnoticed until an npm warning. |
| Secrets | none / regex on values / **key-name redaction** | **values of secret-looking keys replaced with `[REDACTED]`, matched on whole words** (`access_token` yes, `input_tokens` no) | Built in before any authenticated target exists. Whole-word matching came from a bug: substring matching hid token counts. |
| Crashes | swallow / **record then re-raise** | `run_failed` event, then the exception propagates | Visible in the trace and to the caller; nothing hidden. |
| Answer check | substring / **number extraction** | `checks.answer_has_number` | `"12.5" in answer` passed `112.5` and reasoning dumps. |
| CLI library | Typer / **argparse** | **argparse until M4** | No new dependency until we know which commands we need. |

## Consequences and limitations
- Redaction is key-based only: a secret inside a free-text value (e.g. a tool result echoing a
  token) is not detected. Acceptable for the trusted, secret-free MVP targets.
- Tool results are stored in full; large outputs make large traces. Truncation can come later.
- The `run_id` folder is git-ignored; results worth publishing are committed deliberately.
