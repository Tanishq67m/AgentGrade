# AgentGrade report - pr-5553-filesystem

Run `20261118T082237Z-0190a7` - 2026-11-18T08:22:37Z to 2026-11-18T08:35:39Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server builds | **v2.0.0-agentgrade-9of12**: npm server-filesystem@2.0.0 (secure-filesystem-server 2.0.0); **main-with-2.0.0-descriptions**: main e1d154e + 2.0.0 descriptions (secure-filesystem-server 2.3.0); **v2.0.0-with-2.3.0-descriptions**: npm server-filesystem@2.0.0 + 2.3.0 descriptions (secure-filesystem-server 2.0.0) |
| Runs | 36 = 3 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `e86afdd` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | 7/12 (58%, 95% CI 32%-81%) | gave_up x3, wrong_answer x2 | 25.0s | 8,442 |
| main-with-2.0.0-descriptions | 5/12 (42%, 95% CI 19%-68%) | gave_up x7 | 3.7s | 4,702 |
| v2.0.0-with-2.3.0-descriptions | 6/12 (50%, 95% CI 25%-75%) | gave_up x4, wrong_answer x2 | 27.1s | 6,420 |

## Change vs `v2.0.0-agentgrade-9of12`

| Task | v2.0.0-agentgrade-9of12 | main-with-2.0.0-descriptions | v2.0.0-with-2.3.0-descriptions |
|---|---|---|---|
| shipping_cost_a17 | 1/3 | 3/3 | 1/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 |
| order_count | 3/3 | 2/3 | 3/3 |
| heaviest_order_customer | 3/3 | 0/3 | 2/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | 1/3 (33%, 95% CI 6%-79%) | wrong_answer x2 | 8 | The file contains order data for order A17, but it does not include the shipping |
| main-with-2.0.0-descriptions | 3/3 (100%, 95% CI 44%-100%) | - | 5 | The shipping rates file shows that the rate is $6.25 per kg for India (IN) and $ |
| v2.0.0-with-2.3.0-descriptions | 1/3 (33%, 95% CI 6%-79%) | wrong_answer x2 | 5 | I don't see any shipping cost information in the order A17.json file. The file c |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders, including orde |
| main-with-2.0.0-descriptions | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders, so I cannot de |
| v2.0.0-with-2.3.0-descriptions | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I have examined both JSON files in the orders directory:  - A17.json contains 1  |
| main-with-2.0.0-descriptions | 2/3 (67%, 95% CI 21%-94%) | gave_up x1 | 6 | I found two order files: A17.json and B42.json. Each file represents one order,  |
| v2.0.0-with-2.3.0-descriptions | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I found two files in the orders directory: A17.json and B42.json. These are like |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | 3/3 (100%, 95% CI 44%-100%) | - | 8 | I have examined both order files:  - Order A17: Customer "Asha" with a weight of |
| main-with-2.0.0-descriptions | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or a database of orders. The tool |
| v2.0.0-with-2.3.0-descriptions | 2/3 (67%, 95% CI 21%-94%) | gave_up x1 | 7 | I have analyzed both order files:  - Order A17: Customer "Asha" with a weight of |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| v2.0.0-agentgrade-9of12 | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/v2.0.0-agentgrade-9of12__shipping_cost_a17__r1.jsonl` |
| v2.0.0-agentgrade-9of12 | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found [9.0] | `traces/v2.0.0-agentgrade-9of12__shipping_cost_a17__r3.jsonl` |
| v2.0.0-agentgrade-9of12 | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, incl" | `traces/v2.0.0-agentgrade-9of12__order_status_b42__r1.jsonl` |
| v2.0.0-agentgrade-9of12 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/v2.0.0-agentgrade-9of12__order_status_b42__r2.jsonl` |
| v2.0.0-agentgrade-9of12 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/v2.0.0-agentgrade-9of12__order_status_b42__r3.jsonl` |
| main-with-2.0.0-descriptions | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-with-2.0.0-descriptions__order_status_b42__r1.jsonl` |
| main-with-2.0.0-descriptions | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/main-with-2.0.0-descriptions__order_status_b42__r2.jsonl` |
| main-with-2.0.0-descriptions | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/main-with-2.0.0-descriptions__order_status_b42__r3.jsonl` |
| main-with-2.0.0-descriptions | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that contains order info" | `traces/main-with-2.0.0-descriptions__order_count__r3.jsonl` |
| main-with-2.0.0-descriptions | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/main-with-2.0.0-descriptions__heaviest_order_customer__r1.jsonl` |
| main-with-2.0.0-descriptions | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/main-with-2.0.0-descriptions__heaviest_order_customer__r2.jsonl` |
| main-with-2.0.0-descriptions | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/main-with-2.0.0-descriptions__heaviest_order_customer__r3.jsonl` |
| v2.0.0-with-2.3.0-descriptions | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/v2.0.0-with-2.3.0-descriptions__shipping_cost_a17__r1.jsonl` |
| v2.0.0-with-2.3.0-descriptions | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/v2.0.0-with-2.3.0-descriptions__shipping_cost_a17__r3.jsonl` |
| v2.0.0-with-2.3.0-descriptions | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/v2.0.0-with-2.3.0-descriptions__order_status_b42__r1.jsonl` |
| v2.0.0-with-2.3.0-descriptions | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/v2.0.0-with-2.3.0-descriptions__order_status_b42__r2.jsonl` |
| v2.0.0-with-2.3.0-descriptions | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/v2.0.0-with-2.3.0-descriptions__order_status_b42__r3.jsonl` |
| v2.0.0-with-2.3.0-descriptions | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/v2.0.0-with-2.3.0-descriptions__heaviest_order_customer__r2.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
