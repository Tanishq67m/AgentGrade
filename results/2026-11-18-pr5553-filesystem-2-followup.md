# AgentGrade report - pr-5553-filesystem

Run `20261118T074412Z-63d571` - 2026-11-18T07:44:12Z to 2026-11-18T07:50:46Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server builds | **main-2.3.0**: main e1d154e (filesystem 2.3.0) (secure-filesystem-server 2.3.0); **main-agentgrade-9of12-description**: main e1d154e + description override (secure-filesystem-server 2.3.0); **patch-softened-first-sentence**: fork b3c9386b + description override (secure-filesystem-server 2.3.0) |
| Runs | 36 = 3 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `e86afdd` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| main-2.3.0 | 0/12 (0%, 95% CI 0%-24%) | gave_up x10, wrong_answer x2 | 1.7s | 2,622 |
| main-agentgrade-9of12-description | 4/12 (33%, 95% CI 14%-61%) | gave_up x6, wrong_answer x2 | 11.1s | 5,638 |
| patch-softened-first-sentence | 0/12 (0%, 95% CI 0%-24%) | gave_up x9, wrong_answer x3 | 3.3s | 3,493 |

## Change vs `main-2.3.0`

| Task | main-2.3.0 | main-agentgrade-9of12-description | patch-softened-first-sentence |
|---|---|---|---|
| shipping_cost_a17 | 0/3 | 1/3 | 0/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 |
| order_count | 0/3 | 3/3 | 0/3 |
| heaviest_order_customer | 0/3 | 0/3 | 0/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | wrong_answer x2, gave_up x1 | 5 | The JSON file for order A17 contains the following information: {"order_id": "A1 |
| main-agentgrade-9of12-description | 1/3 (33%, 95% CI 6%-79%) | wrong_answer x2 | 5 | The shipping rates file indicates that the rate per kilogram for India (IN) is $ |
| patch-softened-first-sentence | 0/3 (0%, 95% CI 0%-56%) | wrong_answer x3 | 5 | The file for order A17 does not contain any information about the shipping cost. |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders, so I cannot pr |
| main-agentgrade-9of12-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |
| patch-softened-first-sentence | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have any information or tools to retrieve data about orders. You may nee |
| main-agentgrade-9of12-description | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I have examined the contents of both order files:  1. A17.json contains one orde |
| patch-softened-first-sentence | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have any information or access to databases, order systems, or external  |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| main-2.3.0 | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The provide |
| main-agentgrade-9of12-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. I cannot determ |
| patch-softened-first-sentence | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The provide |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| main-2.3.0 | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found [2.0] | `traces/main-2.3.0__shipping_cost_a17__r1.jsonl` |
| main-2.3.0 | shipping_cost_a17 | 2 | gave_up | no tool called; answered: "I need to find the shipping cost for order A17, but I don't have any f" | `traces/main-2.3.0__shipping_cost_a17__r2.jsonl` |
| main-2.3.0 | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/main-2.3.0__shipping_cost_a17__r3.jsonl` |
| main-2.3.0 | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-2.3.0__order_status_b42__r1.jsonl` |
| main-2.3.0 | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-2.3.0__order_status_b42__r2.jsonl` |
| main-2.3.0 | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/main-2.3.0__order_status_b42__r3.jsonl` |
| main-2.3.0 | order_count | 1 | gave_up | no tool called; answered: "I don't have any information or tools to retrieve data about orders. Y" | `traces/main-2.3.0__order_count__r1.jsonl` |
| main-2.3.0 | order_count | 2 | gave_up | no tool called; answered: "I don't have any information about orders or related data. The availab" | `traces/main-2.3.0__order_count__r2.jsonl` |
| main-2.3.0 | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/main-2.3.0__order_count__r3.jsonl` |
| main-2.3.0 | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/main-2.3.0__heaviest_order_customer__r1.jsonl` |
| main-2.3.0 | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases to" | `traces/main-2.3.0__heaviest_order_customer__r2.jsonl` |
| main-2.3.0 | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases to" | `traces/main-2.3.0__heaviest_order_customer__r3.jsonl` |
| main-agentgrade-9of12-description | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found none | `traces/main-agentgrade-9of12-description__shipping_cost_a17__r2.jsonl` |
| main-agentgrade-9of12-description | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found none | `traces/main-agentgrade-9of12-description__shipping_cost_a17__r3.jsonl` |
| main-agentgrade-9of12-description | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/main-agentgrade-9of12-description__order_status_b42__r1.jsonl` |
| main-agentgrade-9of12-description | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/main-agentgrade-9of12-description__order_status_b42__r2.jsonl` |
| main-agentgrade-9of12-description | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/main-agentgrade-9of12-description__order_status_b42__r3.jsonl` |
| main-agentgrade-9of12-description | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/main-agentgrade-9of12-description__heaviest_order_customer__r1.jsonl` |
| main-agentgrade-9of12-description | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/main-agentgrade-9of12-description__heaviest_order_customer__r2.jsonl` |
| main-agentgrade-9of12-description | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or a file system that c" | `traces/main-agentgrade-9of12-description__heaviest_order_customer__r3.jsonl` |
| patch-softened-first-sentence | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/patch-softened-first-sentence__shipping_cost_a17__r1.jsonl` |
| patch-softened-first-sentence | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found [2.0, 9.0, 2.0, 9.0, 2.0, 9.0, 18.0, 18.0] | `traces/patch-softened-first-sentence__shipping_cost_a17__r2.jsonl` |
| patch-softened-first-sentence | shipping_cost_a17 | 3 | wrong_answer | expected number 12.5; found [2.0] | `traces/patch-softened-first-sentence__shipping_cost_a17__r3.jsonl` |
| patch-softened-first-sentence | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/patch-softened-first-sentence__order_status_b42__r1.jsonl` |
| patch-softened-first-sentence | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/patch-softened-first-sentence__order_status_b42__r2.jsonl` |
| patch-softened-first-sentence | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/patch-softened-first-sentence__order_status_b42__r3.jsonl` |
| patch-softened-first-sentence | order_count | 1 | gave_up | no tool called; answered: "I don't have any information or access to databases, order systems, or" | `traces/patch-softened-first-sentence__order_count__r1.jsonl` |
| patch-softened-first-sentence | order_count | 2 | gave_up | no tool called; answered: "I don't have any information about orders or related data in the avail" | `traces/patch-softened-first-sentence__order_count__r2.jsonl` |
| patch-softened-first-sentence | order_count | 3 | gave_up | no tool called; answered: "I don't have any information about orders or related data in the provi" | `traces/patch-softened-first-sentence__order_count__r3.jsonl` |
| patch-softened-first-sentence | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/patch-softened-first-sentence__heaviest_order_customer__r1.jsonl` |
| patch-softened-first-sentence | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The r" | `traces/patch-softened-first-sentence__heaviest_order_customer__r2.jsonl` |
| patch-softened-first-sentence | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or a database of orders" | `traces/patch-softened-first-sentence__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `stopped_after_error` = every tool call errored and the agent answered instead of retrying; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
