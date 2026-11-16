# AgentGrade report - shop-filesystem

Run `20261116T095521Z-4ff742` - 2026-11-16T09:55:21Z to 2026-11-16T10:06:40Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server | secure-filesystem-server 2.0.0 (protocol 2026-07-28) |
| Runs | 48 = 4 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `082620e` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| baseline | 2/12 (17%, 95% CI 5%-45%) | gave_up x9, wrong_answer x1 | 2.7s | 3,850 |
| glob-rules-only | 9/12 (75%, 95% CI 47%-91%) | gave_up x3 | 23.1s | 7,914 |
| upstream-2.2.0-description | 2/12 (17%, 95% CI 5%-45%) | gave_up x9, wrong_answer x1 | 3.0s | 3,609 |
| glob-rules-generic-examples | 3/12 (25%, 95% CI 9%-53%) | gave_up x9 | 3.1s | 3,220 |

## Change vs `baseline`

| Task | baseline | glob-rules-only | upstream-2.2.0-description | glob-rules-generic-examples |
|---|---|---|---|---|
| shipping_cost_a17 | 2/3 | 3/3 | 2/3 | 3/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 | 0/3 |
| order_count | 0/3 | 3/3 | 0/3 | 0/3 |
| heaviest_order_customer | 0/3 | 3/3 | 0/3 | 0/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 2/3 (67%, 95% CI 21%-94%) | wrong_answer x1 | 8 | The shipping rates file shows that the rate per kilogram for India (IN) is $6.25 |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 7 | The shipping rates file shows that the rate per kilogram for India (IN) is $6.25 |
| upstream-2.2.0-description | 2/3 (67%, 95% CI 21%-94%) | wrong_answer x1 | 8 | The shipping rates file shows that the rate per kilogram for India (IN) is $6.25 |
| glob-rules-generic-examples | 3/3 (100%, 95% CI 44%-100%) | - | 6 | The shipping cost for order A17 can be calculated using the shipping rates and o |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order management systems or databases to check the st |
| glob-rules-only | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that would contain information abo |
| upstream-2.2.0-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order management systems or databases. I cannot provi |
| glob-rules-generic-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders, so I cannot pr |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that tracks orders. The query abou |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I have examined both order files:  1. A17.json contains one order (order_id: A17 |
| upstream-2.2.0-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| glob-rules-generic-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. I cannot de |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 9 | After examining both order files, I can see that:  - Order A17 (customer: Asha)  |
| upstream-2.2.0-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or a file system that contains su |
| glob-rules-generic-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The availab |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| baseline | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/baseline__shipping_cost_a17__r3.jsonl` |
| baseline | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/baseline__order_status_b42__r1.jsonl` |
| baseline | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/baseline__order_status_b42__r2.jsonl` |
| baseline | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/baseline__order_status_b42__r3.jsonl` |
| baseline | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/baseline__order_count__r1.jsonl` |
| baseline | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/baseline__order_count__r2.jsonl` |
| baseline | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/baseline__order_count__r3.jsonl` |
| baseline | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/baseline__heaviest_order_customer__r1.jsonl` |
| baseline | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/baseline__heaviest_order_customer__r2.jsonl` |
| baseline | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/baseline__heaviest_order_customer__r3.jsonl` |
| glob-rules-only | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that would contain infor" | `traces/glob-rules-only__order_status_b42__r1.jsonl` |
| glob-rules-only | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any order status or related databases. I cannot" | `traces/glob-rules-only__order_status_b42__r2.jsonl` |
| glob-rules-only | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order status or database information. I can" | `traces/glob-rules-only__order_status_b42__r3.jsonl` |
| upstream-2.2.0-description | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/upstream-2.2.0-description__shipping_cost_a17__r3.jsonl` |
| upstream-2.2.0-description | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases. I ca" | `traces/upstream-2.2.0-description__order_status_b42__r1.jsonl` |
| upstream-2.2.0-description | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/upstream-2.2.0-description__order_status_b42__r2.jsonl` |
| upstream-2.2.0-description | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/upstream-2.2.0-description__order_status_b42__r3.jsonl` |
| upstream-2.2.0-description | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/upstream-2.2.0-description__order_count__r1.jsonl` |
| upstream-2.2.0-description | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/upstream-2.2.0-description__order_count__r2.jsonl` |
| upstream-2.2.0-description | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/upstream-2.2.0-description__order_count__r3.jsonl` |
| upstream-2.2.0-description | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or a file system that c" | `traces/upstream-2.2.0-description__heaviest_order_customer__r1.jsonl` |
| upstream-2.2.0-description | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/upstream-2.2.0-description__heaviest_order_customer__r2.jsonl` |
| upstream-2.2.0-description | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/upstream-2.2.0-description__heaviest_order_customer__r3.jsonl` |
| glob-rules-generic-examples | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/glob-rules-generic-examples__order_status_b42__r1.jsonl` |
| glob-rules-generic-examples | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/glob-rules-generic-examples__order_status_b42__r2.jsonl` |
| glob-rules-generic-examples | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/glob-rules-generic-examples__order_status_b42__r3.jsonl` |
| glob-rules-generic-examples | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/glob-rules-generic-examples__order_count__r1.jsonl` |
| glob-rules-generic-examples | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/glob-rules-generic-examples__order_count__r2.jsonl` |
| glob-rules-generic-examples | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/glob-rules-generic-examples__order_count__r3.jsonl` |
| glob-rules-generic-examples | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/glob-rules-generic-examples__heaviest_order_customer__r1.jsonl` |
| glob-rules-generic-examples | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/glob-rules-generic-examples__heaviest_order_customer__r2.jsonl` |
| glob-rules-generic-examples | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/glob-rules-generic-examples__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
