# AgentGrade report - shop-filesystem

Run `20261023T115016Z-9b0ee9` - 2026-10-23T11:50:16Z to 2026-10-23T12:03:16Z

| | |
|---|---|
| Model | `openai/gpt-oss-120b` (hosted at https://api.groq.com/openai/v1/; identity per call in traces, temperature 0.7) |
| Server | secure-filesystem-server 2.0.0 (protocol 2026-07-28) |
| Runs | 24 = 2 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `ad1f6e2` |
| Rate-limit waits | 562s queued by the provider (excluded from times below) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| baseline | 11/12 (92%, 95% CI 65%-99%) | harness_error x1 | 8.7s | 6,481 |
| glob-rules-only | 12/12 (100%, 95% CI 76%-100%) | - | 9.4s | 7,121 |

## Change vs `baseline`

| Task | baseline | glob-rules-only |
|---|---|---|
| shipping_cost_a17 | 3/3 | 3/3 |
| order_status_b42 | 3/3 | 3/3 |
| order_count | 2/3 | 3/3 |
| heaviest_order_customer | 3/3 | 3/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 3/3 (100%, 95% CI 44%-100%) | - | 7 | The shipping cost for order **A17** is **$12.50 USD**. |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 7 | The shipping cost for order **A17** is **$12.50 USD**. |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 3/3 (100%, 95% CI 44%-100%) | - | 7 | The current status of order **B42** is **processing**. |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 5 | The current status of order **B42** is **processing**. |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 2/3 (67%, 95% CI 21%-94%) | harness_error x1 | 7 | There are **2** orders in total. |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 8 | There are **2 orders** in total. |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 3/3 (100%, 95% CI 44%-100%) | - | 7 | Asha placed the heaviest order. |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 7 | Asha placed the heaviest order. |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| baseline | order_count | 2 | harness_error | ProviderResponseError: HTTP 400: {"error":{"message":"Failed to parse tool call arguments as JSON","type":"invalid_reque | `traces/baseline__order_count__r2.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
