# AgentGrade report - shop-filesystem-upstream-2.2.0

Run `20261116T081507Z-b81578` - 2026-11-16T08:15:07Z to 2026-11-16T08:17:12Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server | secure-filesystem-server 2.2.0 (protocol 2026-07-28) |
| Runs | 12 = 1 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `e6f9d7e` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| upstream-2.2.0 | 3/12 (25%, 95% CI 9%-53%) | gave_up x9 | 2.2s | 3,295 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| upstream-2.2.0 | 3/3 (100%, 95% CI 44%-100%) | - | 6 | The "shipping_rates.json" file contains shipping rates in USD. It shows that the |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| upstream-2.2.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I cannot determine the status of order B42 as there is no available information  |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| upstream-2.2.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| upstream-2.2.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. I cannot de |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| upstream-2.2.0 | order_status_b42 | 1 | gave_up | no tool called; answered: 'I cannot determine the status of order B42 as there is no available in' | `traces/upstream-2.2.0__order_status_b42__r1.jsonl` |
| upstream-2.2.0 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/upstream-2.2.0__order_status_b42__r2.jsonl` |
| upstream-2.2.0 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/upstream-2.2.0__order_status_b42__r3.jsonl` |
| upstream-2.2.0 | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/upstream-2.2.0__order_count__r1.jsonl` |
| upstream-2.2.0 | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that contains order info" | `traces/upstream-2.2.0__order_count__r2.jsonl` |
| upstream-2.2.0 | order_count | 3 | gave_up | no tool called; answered: 'I cannot determine the number of orders in total because there is no a' | `traces/upstream-2.2.0__order_count__r3.jsonl` |
| upstream-2.2.0 | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/upstream-2.2.0__heaviest_order_customer__r1.jsonl` |
| upstream-2.2.0 | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/upstream-2.2.0__heaviest_order_customer__r2.jsonl` |
| upstream-2.2.0 | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases to" | `traces/upstream-2.2.0__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
