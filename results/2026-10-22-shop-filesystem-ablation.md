# AgentGrade report - shop-filesystem

Run `20261022T095739Z-f2965e` - 2026-10-22T09:57:39Z to 2026-10-22T10:18:22Z

| | |
|---|---|
| Model | `qwen3:4b-instruct` (digest `0edcdef34593`, temperature 0.7) |
| Server | secure-filesystem-server 2.0.0 (protocol 2026-07-28) |
| Runs | 72 = 6 variant(s) x 4 task(s) x 3 repeat(s) |
| Code | agentgrade 0.0.1, commit `1db43f7` (dirty) |
| Environment | Python 3.12.2, Node v24.22.1, macOS-26.6.2-arm64-arm-64bit |

## Summary by variant

| Variant | Pass rate | Failures | Median time | Mean tokens |
|---|---|---|---|---|
| baseline | 1/12 (8%, 95% CI 1%-35%) | gave_up x9, wrong_answer x2 | 2.7s | 3,256 |
| glob-rules-only | 9/12 (75%, 95% CI 47%-91%) | gave_up x3 | 37.5s | 7,723 |
| explore-first-only | 1/12 (8%, 95% CI 1%-35%) | gave_up x9, wrong_answer x2 | 3.8s | 2,831 |
| clear-search-description | 8/12 (67%, 95% CI 39%-86%) | gave_up x3, wrong_answer x1 | 27.6s | 6,620 |
| no-search | 1/12 (8%, 95% CI 1%-35%) | gave_up x11 | 3.1s | 1,380 |
| agent-context | 3/12 (25%, 95% CI 9%-53%) | gave_up x9 | 4.6s | 2,986 |

## Change vs `baseline`

| Task | baseline | glob-rules-only | explore-first-only | clear-search-description | no-search | agent-context |
|---|---|---|---|---|---|---|
| shipping_cost_a17 | 1/3 | 3/3 | 1/3 | 2/3 | 1/3 | 3/3 |
| order_status_b42 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| order_count | 0/3 | 3/3 | 0/3 | 3/3 | 0/3 | 0/3 |
| heaviest_order_customer | 0/3 | 3/3 | 0/3 | 3/3 | 0/3 | 0/3 |

## Detail by task

### shipping_cost_a17

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 1/3 (33%, 95% CI 6%-79%) | wrong_answer x2 | 6 | The file contains order data for A17, but it does not include a shipping cost. T |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 7 | The shipping rates file shows that the shipping cost is calculated at $6.25 per  |
| explore-first-only | 1/3 (33%, 95% CI 6%-79%) | wrong_answer x2 | 6 | The file containing order A17 data does not include any information about the sh |
| clear-search-description | 2/3 (67%, 95% CI 21%-94%) | wrong_answer x1 | 5 | The shipping cost for order A17 is not explicitly provided in the order data. Ho |
| no-search | 1/3 (33%, 95% CI 6%-79%) | gave_up x2 | 1 | I don't have access to any files or databases containing order data or shipping  |
| agent-context | 3/3 (100%, 95% CI 44%-100%) | - | 6 | The shipping cost for order A17 can be calculated using the shipping rates and t |

### order_status_b42

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |
| glob-rules-only | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order status or database information. I cannot provid |
| explore-first-only | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any order management systems or databases to check the st |
| clear-search-description | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders or their status |
| no-search | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders. I cannot provi |
| agent-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any system or database that tracks orders, so I cannot pr |

### order_count

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I've examined both order files:  1. A17.json contains information about one orde |
| explore-first-only | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |
| clear-search-description | 3/3 (100%, 95% CI 44%-100%) | - | 6 | I've examined both files:  - A17.json contains one order (order_id: A17) - B42.j |
| no-search | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that tracks orders. The tools avai |
| agent-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any database or system that would contain order informati |

### heaviest_order_customer

| Variant | Pass rate | Failures | Median steps | Example answer |
|---|---|---|---|---|
| baseline | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The tools a |
| glob-rules-only | 3/3 (100%, 95% CI 44%-100%) | - | 8 | Asha placed the heaviest order with a weight of 2.0 kg, which is heavier than Be |
| explore-first-only | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. I cannot de |
| clear-search-description | 3/3 (100%, 95% CI 44%-100%) | - | 7 | I have examined both order files:  - Order A17: Customer "Asha" with a weight of |
| no-search | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related databases. The provide |
| agent-context | 0/3 (0%, 95% CI 0%-56%) | gave_up x3 | 1 | I don't have access to any customer order data or related files. The available t |

## Failed runs

| Variant | Task | # | Category | Why | Trace |
|---|---|---|---|---|---|
| baseline | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found none | `traces/baseline__shipping_cost_a17__r1.jsonl` |
| baseline | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found [2.0] | `traces/baseline__shipping_cost_a17__r2.jsonl` |
| baseline | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/baseline__order_status_b42__r1.jsonl` |
| baseline | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/baseline__order_status_b42__r2.jsonl` |
| baseline | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/baseline__order_status_b42__r3.jsonl` |
| baseline | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/baseline__order_count__r1.jsonl` |
| baseline | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/baseline__order_count__r2.jsonl` |
| baseline | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/baseline__order_count__r3.jsonl` |
| baseline | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/baseline__heaviest_order_customer__r1.jsonl` |
| baseline | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/baseline__heaviest_order_customer__r2.jsonl` |
| baseline | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. I can" | `traces/baseline__heaviest_order_customer__r3.jsonl` |
| glob-rules-only | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order status or database information. I can" | `traces/glob-rules-only__order_status_b42__r1.jsonl` |
| glob-rules-only | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/glob-rules-only__order_status_b42__r2.jsonl` |
| glob-rules-only | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/glob-rules-only__order_status_b42__r3.jsonl` |
| explore-first-only | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found [2.0] | `traces/explore-first-only__shipping_cost_a17__r1.jsonl` |
| explore-first-only | shipping_cost_a17 | 2 | wrong_answer | expected number 12.5; found none | `traces/explore-first-only__shipping_cost_a17__r2.jsonl` |
| explore-first-only | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/explore-first-only__order_status_b42__r1.jsonl` |
| explore-first-only | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases to ch" | `traces/explore-first-only__order_status_b42__r2.jsonl` |
| explore-first-only | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order management systems or databases. I ca" | `traces/explore-first-only__order_status_b42__r3.jsonl` |
| explore-first-only | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/explore-first-only__order_count__r1.jsonl` |
| explore-first-only | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/explore-first-only__order_count__r2.jsonl` |
| explore-first-only | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/explore-first-only__order_count__r3.jsonl` |
| explore-first-only | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/explore-first-only__heaviest_order_customer__r1.jsonl` |
| explore-first-only | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/explore-first-only__heaviest_order_customer__r2.jsonl` |
| explore-first-only | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or a file system that w" | `traces/explore-first-only__heaviest_order_customer__r3.jsonl` |
| clear-search-description | shipping_cost_a17 | 1 | wrong_answer | expected number 12.5; found [2.0] | `traces/clear-search-description__shipping_cost_a17__r1.jsonl` |
| clear-search-description | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/clear-search-description__order_status_b42__r1.jsonl` |
| clear-search-description | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that would contain infor" | `traces/clear-search-description__order_status_b42__r2.jsonl` |
| clear-search-description | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders or th" | `traces/clear-search-description__order_status_b42__r3.jsonl` |
| no-search | shipping_cost_a17 | 1 | gave_up | no tool called; answered: "I don't have access to any files or databases containing order data or" | `traces/no-search__shipping_cost_a17__r1.jsonl` |
| no-search | shipping_cost_a17 | 3 | gave_up | no tool called; answered: "I don't have access to any order data or shipping rates files, and the" | `traces/no-search__shipping_cost_a17__r3.jsonl` |
| no-search | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/no-search__order_status_b42__r1.jsonl` |
| no-search | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders. I ca" | `traces/no-search__order_status_b42__r2.jsonl` |
| no-search | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any order status information or related databas" | `traces/no-search__order_status_b42__r3.jsonl` |
| no-search | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/no-search__order_count__r1.jsonl` |
| no-search | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/no-search__order_count__r2.jsonl` |
| no-search | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/no-search__order_count__r3.jsonl` |
| no-search | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/no-search__heaviest_order_customer__r1.jsonl` |
| no-search | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. I" | `traces/no-search__heaviest_order_customer__r2.jsonl` |
| no-search | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related databases. T" | `traces/no-search__heaviest_order_customer__r3.jsonl` |
| agent-context | order_status_b42 | 1 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/agent-context__order_status_b42__r1.jsonl` |
| agent-context | order_status_b42 | 2 | gave_up | no tool called; answered: "I don't have access to any order status information or a database of o" | `traces/agent-context__order_status_b42__r2.jsonl` |
| agent-context | order_status_b42 | 3 | gave_up | no tool called; answered: "I don't have access to any system or database that tracks orders, so I" | `traces/agent-context__order_status_b42__r3.jsonl` |
| agent-context | order_count | 1 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/agent-context__order_count__r1.jsonl` |
| agent-context | order_count | 2 | gave_up | no tool called; answered: "I don't have access to any database or system that would contain order" | `traces/agent-context__order_count__r2.jsonl` |
| agent-context | order_count | 3 | gave_up | no tool called; answered: "I don't have access to any database or system that tracks orders. The " | `traces/agent-context__order_count__r3.jsonl` |
| agent-context | heaviest_order_customer | 1 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/agent-context__heaviest_order_customer__r1.jsonl` |
| agent-context | heaviest_order_customer | 2 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The r" | `traces/agent-context__heaviest_order_customer__r2.jsonl` |
| agent-context | heaviest_order_customer | 3 | gave_up | no tool called; answered: "I don't have access to any customer order data or related files. The a" | `traces/agent-context__heaviest_order_customer__r3.jsonl` |

## How to read this

- A run passes only when **every** code-based check passes. No model grades another model.
- Categories: `loop` = step limit hit while one tool kept returning the same result; `step_limit` = step limit without repetition; `gave_up` = answered without calling any tool; `wrong_answer` = used tools and answered, but a check failed; `no_answer`; `harness_error` = infrastructure failure, not the agent's fault.
- **Small sample:** 3 repeat(s) per task. The 95% intervals are wide; treat differences between variants as indicative unless the intervals clearly separate.
- Every run's full trace (every model call, tool call and result) is in `traces/`.
