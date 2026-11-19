# AgentGrade report - pr-5620-filesystem

Run `20261118T203524Z-80ed5a` - 2026-11-18T20:35:24Z to 2026-11-18T20:52:20Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server builds | **main-2.4.0**: main 7f383a8 (filesystem 2.4.0) (secure-filesystem-server 2.4.0); **pr-5620**: PR #5620 731abb0 (secure-filesystem-server 2.4.0); **main-2.4.0-context**: main 7f383a8 (filesystem 2.4.0) (secure-filesystem-server 2.4.0); **pr-5620-context**: PR #5620 731abb0 (secure-filesystem-server 2.4.0) |
| Runs | 48 = 4 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `5057f3a` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| main-2.4.0 | 0/12 (0%, 95% CI 0%-24%) | gave_up x11, wrong_answer x1 | 5.7s | 2,013 |
| pr-5620 | 2/12 (17%, 95% CI 5%-45%) | gave_up x9, wrong_answer x1 | 9.1s | 4,322 |
| main-2.4.0-context | 0/12 (0%, 95% CI 0%-24%) | gave_up x9, wrong_answer x3 | 5.6s | 3,930 |
| pr-5620-context | 0/12 (0%, 95% CI 0%-24%) | gave_up x9, wrong_answer x3 | 5.8s | 3,573 |

## Change vs `main-2.4.0`

| Task | main-2.4.0 | pr-5620 | main-2.4.0-context | pr-5620-context |
|---|---|---|---|---|
| shipping_cost_a17 | 0/3 | 2/3 | 0/3 | 0/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 | 0/3 |
| order_count | 0/3 | 0/3 | 0/3 | 0/3 |
| heaviest_order_customer | 0/3 | 0/3 | 0/3 | 0/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.4.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x2, wrong_answer x1 | 1 | I need to find the shipping cost for order A17, but I don't have any files or da |
| pr-5620 | 2/3 (67%, 95% CI 21%-94%) | wrong_answer x1 | 7 | The shipping cost for order A17 can be calculated as follows:  - Order A17 has a |
| main-2.4.0-context | 0/3 (0%, 95% CI 0%-56%) | wrong_answer x3 | 5 | The file contains order data for order A17, but it doesn't include the shipping  |
| pr-5620-context | 0/3 (0%, 95% CI 0%-56%) | wrong_answer x3 | 5 | The file for order A17 does not contain any information about the shipping cost. |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.4.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders. I cannot provi |
| pr-5620 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |
| main-2.4.0-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order status information or related databases. Please |
| pr-5620-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.4.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| pr-5620 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| main-2.4.0-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| pr-5620-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have any information about orders or related data in the provided contex |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.4.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The provide |
| pr-5620 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The provide |
| main-2.4.0-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. The available t |
| pr-5620-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. The requested i |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| main-2.4.0 | shipping_cost_a17 | 1 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/main-2.4.0__shipping_cost_a17__r1.jsonl` |
| main-2.4.0 | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found [9.0] | `traces/main-2.4.0__shipping_cost_a17__r2.jsonl` |
| main-2.4.0 | shipping_cost_a17 | 3 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/main-2.4.0__shipping_cost_a17__r3.jsonl` |
| main-2.4.0 | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/main-2.4.0__order_status_b42__r1.jsonl` |
| main-2.4.0 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-2.4.0__order_status_b42__r2.jsonl` |
| main-2.4.0 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-2.4.0__order_status_b42__r3.jsonl` |
| main-2.4.0 | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.4.0__order_count__r1.jsonl` |
| main-2.4.0 | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.4.0__order_count__r2.jsonl` |
| main-2.4.0 | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.4.0__order_count__r3.jsonl` |
| main-2.4.0 | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/main-2.4.0__heaviest_order_customer__r1.jsonl` |
| main-2.4.0 | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/main-2.4.0__heaviest_order_customer__r2.jsonl` |
| main-2.4.0 | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/main-2.4.0__heaviest_order_customer__r3.jsonl` |
| pr-5620 | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/pr-5620__shipping_cost_a17__r3.jsonl` |
| pr-5620 | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/pr-5620__order_status_b42__r1.jsonl` |
| pr-5620 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/pr-5620__order_status_b42__r2.jsonl` |
| pr-5620 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/pr-5620__order_status_b42__r3.jsonl` |
| pr-5620 | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/pr-5620__order_count__r1.jsonl` |
| pr-5620 | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/pr-5620__order_count__r2.jsonl` |
| pr-5620 | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/pr-5620__order_count__r3.jsonl` |
| pr-5620 | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/pr-5620__heaviest_order_customer__r1.jsonl` |
| pr-5620 | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/pr-5620__heaviest_order_customer__r2.jsonl` |
| pr-5620 | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/pr-5620__heaviest_order_customer__r3.jsonl` |
| main-2.4.0-context | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/main-2.4.0-context__shipping_cost_a17__r1.jsonl` |
| main-2.4.0-context | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found none | `traces/main-2.4.0-context__shipping_cost_a17__r2.jsonl` |
| main-2.4.0-context | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found [2.0] | `traces/main-2.4.0-context__shipping_cost_a17__r3.jsonl` |
| main-2.4.0-context | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order status information or related databas" | `traces/main-2.4.0-context__order_status_b42__r1.jsonl` |
| main-2.4.0-context | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. Ther" | `traces/main-2.4.0-context__order_status_b42__r2.jsonl` |
| main-2.4.0-context | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. Ther" | `traces/main-2.4.0-context__order_status_b42__r3.jsonl` |
| main-2.4.0-context | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.4.0-context__order_count__r1.jsonl` |
| main-2.4.0-context | order_count | 2 | gave_up | no tool called; answered: "I don't have any information about orders or related data in the avail" | `traces/main-2.4.0-context__order_count__r2.jsonl` |
| main-2.4.0-context | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any data about orders or related databases. The" | `traces/main-2.4.0-context__order_count__r3.jsonl` |
| main-2.4.0-context | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/main-2.4.0-context__heaviest_order_customer__r1.jsonl` |
| main-2.4.0-context | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/main-2.4.0-context__heaviest_order_customer__r2.jsonl` |
| main-2.4.0-context | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/main-2.4.0-context__heaviest_order_customer__r3.jsonl` |
| pr-5620-context | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/pr-5620-context__shipping_cost_a17__r1.jsonl` |
| pr-5620-context | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found none | `traces/pr-5620-context__shipping_cost_a17__r2.jsonl` |
| pr-5620-context | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/pr-5620-context__shipping_cost_a17__r3.jsonl` |
| pr-5620-context | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/pr-5620-context__order_status_b42__r1.jsonl` |
| pr-5620-context | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any order status or related databases. The prov" | `traces/pr-5620-context__order_status_b42__r2.jsonl` |
| pr-5620-context | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order status or related databases. The requ" | `traces/pr-5620-context__order_status_b42__r3.jsonl` |
| pr-5620-context | order_count | 1 | gave_up | no tool called; answered: "I don't have any information about orders or related data in the provi" | `traces/pr-5620-context__order_count__r1.jsonl` |
| pr-5620-context | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/pr-5620-context__order_count__r2.jsonl` |
| pr-5620-context | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/pr-5620-context__order_count__r3.jsonl` |
| pr-5620-context | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The r" | `traces/pr-5620-context__heaviest_order_customer__r1.jsonl` |
| pr-5620-context | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/pr-5620-context__heaviest_order_customer__r2.jsonl` |
| pr-5620-context | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The r" | `traces/pr-5620-context__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
