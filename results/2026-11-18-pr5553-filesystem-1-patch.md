# AgentGrade report - pr-5553-filesystem

Run `20261118T065039Z-a2c8bb` - 2026-11-18T06:50:39Z to 2026-11-18T07:03:04Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server builds | **main-2.3.0**: main e1d154e (filesystem 2.3.0) (secure-filesystem-server 2.3.0); **patch-b3c9386b**: fork b3c9386b (proposed patch) (secure-filesystem-server 2.3.0); **patch-user-data-examples**: fork b3c9386b + description override (secure-filesystem-server 2.3.0) |
| Runs | 36 = 3 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `e86afdd` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| main-2.3.0 | 1/12 (8%, 95% CI 1%-35%) | gave_up x11 | 5.0s | 2,237 |
| patch-b3c9386b | 2/12 (17%, 95% CI 5%-45%) | gave_up x10 | 7.6s | 3,522 |
| patch-user-data-examples | 2/12 (17%, 95% CI 5%-45%) | gave_up x9, wrong_answer x1 | 6.1s | 4,286 |

## Change vs `main-2.3.0`

| Task | main-2.3.0 | patch-b3c9386b | patch-user-data-examples |
|---|---|---|---|
| shipping_cost_a17 | 1/3 | 2/3 | 2/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 |
| order_count | 0/3 | 0/3 | 0/3 |
| heaviest_order_customer | 0/3 | 0/3 | 0/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 1/3 (33%, 95% CI 6%-79%) | gave_up x2 | 1 | I need to find the shipping cost for order A17, but I don't have any files or da |
| patch-b3c9386b | 2/3 (67%, 95% CI 21%-94%) | gave_up x1 | 7 | The shipping rates file shows that the rate per kilogram is $6.25 for India (IN) |
| patch-user-data-examples | 2/3 (67%, 95% CI 21%-94%) | wrong_answer x1 | 7 | The shipping cost for order A17 is calculated based on the country and weight. F |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order status or related databases. Please consult the |
| patch-b3c9386b | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders. I cannot provi |
| patch-user-data-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that tracks orders. The provided t |
| patch-b3c9386b | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| patch-user-data-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have any information about orders or related data in the provided tools  |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related systems. I cannot dete |
| patch-b3c9386b | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. I cannot determ |
| patch-user-data-examples | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. I cannot determ |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| main-2.3.0 | shipping_cost_a17 | 1 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/main-2.3.0__shipping_cost_a17__r1.jsonl` |
| main-2.3.0 | shipping_cost_a17 | 3 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/main-2.3.0__shipping_cost_a17__r3.jsonl` |
| main-2.3.0 | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order status or related databases. Please c" | `traces/main-2.3.0__order_status_b42__r1.jsonl` |
| main-2.3.0 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-2.3.0__order_status_b42__r2.jsonl` |
| main-2.3.0 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/main-2.3.0__order_status_b42__r3.jsonl` |
| main-2.3.0 | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/main-2.3.0__order_count__r1.jsonl` |
| main-2.3.0 | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.3.0__order_count__r2.jsonl` |
| main-2.3.0 | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.3.0__order_count__r3.jsonl` |
| main-2.3.0 | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related systems. I c" | `traces/main-2.3.0__heaviest_order_customer__r1.jsonl` |
| main-2.3.0 | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/main-2.3.0__heaviest_order_customer__r2.jsonl` |
| main-2.3.0 | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/main-2.3.0__heaviest_order_customer__r3.jsonl` |
| patch-b3c9386b | shipping_cost_a17 | 2 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/patch-b3c9386b__shipping_cost_a17__r2.jsonl` |
| patch-b3c9386b | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/patch-b3c9386b__order_status_b42__r1.jsonl` |
| patch-b3c9386b | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/patch-b3c9386b__order_status_b42__r2.jsonl` |
| patch-b3c9386b | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/patch-b3c9386b__order_status_b42__r3.jsonl` |
| patch-b3c9386b | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/patch-b3c9386b__order_count__r1.jsonl` |
| patch-b3c9386b | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/patch-b3c9386b__order_count__r2.jsonl` |
| patch-b3c9386b | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/patch-b3c9386b__order_count__r3.jsonl` |
| patch-b3c9386b | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/patch-b3c9386b__heaviest_order_customer__r1.jsonl` |
| patch-b3c9386b | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/patch-b3c9386b__heaviest_order_customer__r2.jsonl` |
| patch-b3c9386b | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/patch-b3c9386b__heaviest_order_customer__r3.jsonl` |
| patch-user-data-examples | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/patch-user-data-examples__shipping_cost_a17__r3.jsonl` |
| patch-user-data-examples | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/patch-user-data-examples__order_status_b42__r1.jsonl` |
| patch-user-data-examples | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/patch-user-data-examples__order_status_b42__r2.jsonl` |
| patch-user-data-examples | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/patch-user-data-examples__order_status_b42__r3.jsonl` |
| patch-user-data-examples | order_count | 1 | gave_up | no tool called; answered: "I don't have any information about orders or related data in the provi" | `traces/patch-user-data-examples__order_count__r1.jsonl` |
| patch-user-data-examples | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/patch-user-data-examples__order_count__r2.jsonl` |
| patch-user-data-examples | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/patch-user-data-examples__order_count__r3.jsonl` |
| patch-user-data-examples | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/patch-user-data-examples__heaviest_order_customer__r1.jsonl` |
| patch-user-data-examples | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/patch-user-data-examples__heaviest_order_customer__r2.jsonl` |
| patch-user-data-examples | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/patch-user-data-examples__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
