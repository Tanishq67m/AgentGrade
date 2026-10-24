# 0013. OpenAI-compatible model adapter (M5: stronger models, still free)

- **Status:** Accepted
- **Date:** 2026-10-22
- **Decided by:** Tanishq ("work on the next milestone"; recommended order accepted; everything free for now)

## Problem
All results so far come from one 4B local model. The obvious objection is "that's just a weak model".
We need to re-run the same suites on a much stronger model, at zero cost.

## Options considered
1. One adapter per provider (Groq SDK, Cerebras SDK, ...).
2. **One adapter for the OpenAI-compatible Chat Completions API**, used by Groq, Cerebras, OpenRouter,
   Ollama's `/v1` endpoint and OpenAI.

## Decision
Option 2: `models/openai_compat.py`, plain `httpx` (no SDK), configured by small YAML files in
`model_configs/` and selected with `agentgrade run <suite> --model <file>`.

| Detail | Choice | Why |
|---|---|---|
| Strong free model | `gpt-oss-120b` (open weights) on **Groq** or **Cerebras** free tiers | Much larger than qwen3:4b, tool-calling capable, free. Groq: fast but ~200K tokens/day. Cerebras: 5 req/min but ~1M tokens/day. |
| API keys | **Env var name** in the config (`api_key_env: GROQ_API_KEY`); value from the shell or a git-ignored `.env` (tiny built-in loader, no dependency) | Keys never enter suite files, traces or git. A config that looks like a pasted key is rejected. |
| HTTP 429 | Wait `Retry-After` (else exponential backoff), up to 8 retries; then `ProviderRateLimitError` **stops the suite** | Rate limits are expected on free tiers; exhausted retries mean the daily quota is gone. Not a way to hide errors: nothing else is retried. |
| Pacing | Optional `requests_per_minute` spaces requests; **one model instance per suite run**, so pacing spans runs | Avoids hammering 429s on 5-req/min tiers. |
| Latency | Rate-limit waiting recorded as `rate_limit_wait_ms` and **excluded** from latency | Queue time on a free tier says nothing about the model. |
| Malformed tool-call JSON | `ToolCall.parse_error`, reported to the model as `invalid_arguments` | It's the model's mistake (an agent failure), not a harness crash. |
| Reasoning models | `message.reasoning` / `reasoning_content` → `thinking`, plus the `</think>` split | Same rule as ADR 0008: reasoning is kept, never treated as the answer. |
| Identity | Provider's served `model` and `system_fingerprint` recorded per call (`provider_meta`) | Hosted models can change silently; the fingerprint is the closest thing to a digest. |
| Fatal errors | Missing key, 401/403, 404 model, quota exhausted | Fail fast instead of recording 72 identical failures. |

## Update after the first hosted run (2026-10-23)
- Groq rejects malformed tool-call JSON with HTTP 400 `tool_use_failed` instead of returning it. The adapter now
  converts that into a `ToolCall` with `parse_error`, so it counts as the model's `invalid_arguments`, consistent
  with providers that return the broken call.
- `system_fingerprint` changed on most calls (41 distinct in 159), so it identifies a deployment snapshot, not a model.
- Rate-limit waits are now also stored per run and excluded from report run times.

## Consequences and limitations
- Hosted models are less reproducible than a local digest: providers can update them. We record what they report.
- Free tiers send prompts to a third party. Fine for the synthetic `fixtures/shop` data; never use real private data.
- Groq's daily token budget fits a focused comparison (e.g. `--variants baseline,glob-rules-only`), not all 72 runs in a day.
