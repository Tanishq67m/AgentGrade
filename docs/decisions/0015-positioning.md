# 0015. Positioning: measured "fix and prove" for MCP server authors; CI mode deprioritized

- **Status:** Accepted
- **Date:** 2026-11-17
- **Decided by:** Tanishq ("ok great, add everything we discussed", after the positioning review)

## Problem
Anyone can write their own test cases for their agent. If AgentGrade's value is "run an agent on test
cases with traces and pass rates", it has no reason to exist: agent eval platforms (Braintrust,
MCPJam, mcp-eval, DeepEval) already do that, CI gates included. Static graders (Arcade ToolBench,
Glama TDQS) already grade tool definitions across tens of thousands of servers. The next milestone
(CI mode was the previous recommendation) had to be chosen with that in mind.

## Options considered
| Option | For | Against |
|---|---|---|
| A. CI mode (`--fail-under`, baseline diff, GitHub Action) | Easy to build; makes the tool "runnable every PR" | Commodity: Braintrust already ships it. Adds no reason to choose us. |
| B. Recommendations in reports (heuristics) | Useful, cheap | Still a guess, like static graders, unless each recommendation is tested |
| C. **"Fix and prove" for server authors**: measure behavior across model sizes, generate description rewrites, A/B them, recommend only what measurably helps | The one thing neither group does; builds directly on `description_overrides` + variants; backed by our own result (2.2.0 rules 3/12 vs realistic examples 9/12) | Needs validation; cost per measurement; task authoring still a barrier |

## Decision
**C.** AgentGrade is positioned as *"Static graders guess. AgentGrade proves which line of your tool
description breaks agents, and which rewrite fixes it."* The primary audience is MCP server authors.

Order of work:
1. **M7a - static vs measured experiment** (ADR 0016): test the claim that static scores don't predict
   our measured differences, before building on it.
2. **M7b - `agentgrade improve`**: generate candidate rewrites, run them as variants, report the winner.
3. In parallel, talk to 5 MCP server authors.
4. CI mode moves to "later", as a small add-on.

## Rationale
- It differentiates on evidence we already have, instead of on features others already ship.
- It tests the riskiest assumption first (M7a is about 2 days and reuses existing runs).
- It suits the project's job-search goal too: a measured, falsifiable claim is stronger proof of
  engineering judgment than another feature.

## Consequences and limitations
- If M7a shows TDQS *does* separate our good and bad descriptions, this positioning weakens. Then the
  pivot is model-size coverage, or using static scores as a cheap first pass before measuring.
- Full write-up, competitor table, risks and kill criteria: [POSITIONING.md](../POSITIONING.md).
