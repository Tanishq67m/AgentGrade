# Positioning: why would anyone use AgentGrade?

_Written 2026-11-17, after case study v1 (312 runs). This is a working hypothesis to be validated by the
experiment and conversations below. It is not yet a proven fact. Decision record: [ADR 0015](decisions/0015-positioning.md)._

## The question

Anyone can write their own test cases for their agent. So what does AgentGrade offer that a team cannot
get from its own tests or from an existing eval tool?

## What already exists (checked November 2026)

| Group | Examples | What they do | What they don't do |
|---|---|---|---|
| Agent eval platforms | Braintrust, MCPJam, mcp-eval, DeepEval, promptfoo | Run **your** agent against an MCP server; assert tool calls and arguments; repeated trials; traces; CI gates against a baseline (Braintrust ships a GitHub Action). | Tell you *which line of a tool definition* caused a failure, or prove a rewrite fixes it. You bring the tests and the diagnosis. |
| Protocol inspectors | MCP Inspector, MCPJam inspector | Check JSON-RPC traffic, OAuth, schema conformance. | Run no model, so they can't see behavioral failures. |
| Static graders | Arcade ToolBench (about 42,000 servers graded A+ to F), Glama TDQS (per-tool score 1-5, six dimensions) | An LLM or rules read tool definitions and grade them. Fast, cheap, runs at registry scale. | Run an agent. The TDQS spec says this directly: *"TDQS scores definitions, not behavior. It does not run an agent and observe which tool gets picked."* Glama's own post says its validation data is "still populating". |

**Hard truth:** repeats, traces, pass rates, tool-call assertions and CI gates are **commodity**. If
AgentGrade is "run your agent on your test cases", nobody needs it, and CI mode alone would be a copy
of what Braintrust already ships.

## The gap

- Your own tests tell you **that** the agent failed.
- Static graders **guess why**, from the text alone.
- Nobody tells you **which exact line of the tool description caused the failure** and then **proves the
  fix** with a controlled before/after experiment.

Our own data shows why the guess is not enough. Upstream filesystem 2.2.0 rewrote `search_files` with
precise matching rules. A description reviewer would very likely call that an improvement. Measured on a
small model, it still scored 3/12. Changing only two example strings ('`**/*.ext`' → '`**/*.json`')
scored 9/12, replicated. Only measurement could reveal that.

**Analogy.** Students keep failing one exam question.
- Your own tests are the exam result: "3 out of 12 failed."
- A static grader is a grammar check on the question paper: "the wording looks unclear."
- AgentGrade rewrites the question several ways, gives each version to fresh students, and reports:
  "version B took the pass rate from 3/12 to 9/12, and here is the proof."

## Positioning

> **Static graders guess. AgentGrade proves which line of your tool description breaks agents, and
> which rewrite fixes it.**

### Who it is for
1. **MCP server authors** (primary). A company shipping an MCP server for payments, CRM, docs, etc.
   does not control which agent or model will call it, so it has no "own test cases" to start from.
   Existing eval platforms are mostly built for teams testing *their own* agent.
2. **Teams choosing small or cheap models** (secondary). They need to know which tools break when
   they move from a frontier model to a 4B-30B one.

### Differentiators
1. **Measured, not linted.** Every claim comes from repeated agent runs with traces and confidence
   intervals, and anyone can reproduce it.
2. **A ladder of model sizes, including small ones.** Our 4B vs 120B result (filesystem 1/12 vs 11/12)
   is exactly the risk a server author can't see when testing only with a frontier model.
3. **Fix and prove.** Generate candidate description rewrites, A/B-test them automatically through
   `description_overrides` (nothing is redeployed), and recommend only a change that measurably
   helps. Most of the machinery already exists.
4. **Evidence over opinion.** Public traces, upstream issues filed with data (#5552, #5553), and
   honest corrections of our own earlier claims.

## Risks

- **Writing tasks is the adoption barrier.** If authors must hand-write YAML suites, we are just
  another eval tool. We'll eventually need generated tasks, or ready-made suites for popular servers.
- **A large platform could copy this.** Protection is focus and credibility: real findings, upstream
  issues, public work. That protection is thin.
- **Cost.** Every measurement costs model calls. Free tiers are enough for research, but not for a
  service.
- **Small-sample results.** 12-15 runs per variant, mostly one small model. Findings are
  indicative, not universal.

## What would prove this positioning wrong

- **The static score predicts our measured differences.** If a static grader (TDQS) clearly separates
  3/12 descriptions from 9/12 ones, the "static graders guess" claim is weak. We would reposition
  around model-size coverage, or around using static scores as a cheap first pass.
- **Server authors don't care.** If 5 MCP server authors say they would not run this before a release,
  the primary audience is wrong.

## Result of the first test (M7a, 2026-11-18)

The first kill criterion was checked, and it **did not** kill the positioning. It refined it.
- All six measured `search_files` descriptions were graded **A** by TDQS, while agents passed **8% to 75%** of
  runs. Rank correlation -0.09 / +0.20 (two judges). The 3/12 and 9/12 descriptions scored the same.
- But TDQS **did** flag the one-line `git_log` description (C vs A), in the same direction as the measured change.

**Refined positioning:** static scores catch *missing* information. They miss *misleading* information that
only shows up when a real model uses the tool. So AgentGrade runs both. `agentgrade static-score` is the cheap
first pass, and measured runs are the proof. Details: [CASE_STUDY.md, Finding 6](CASE_STUDY.md#finding-6-a-published-static-score-could-not-see-the-difference).

## Plan (replaces "CI mode next")

| Step | What | Why first |
|---|---|---|
| **M7a** ✅ | **Static vs measured experiment** (done 2026-11-18, see above). Re-implement Glama's published TDQS rubric, score every tool description we have already measured, and compare with measured pass rates. Predictions are written down before running. | Cheap (about 2 days, reuses existing runs). It either proves the positioning or kills it early. It's also strong public content. |
| **M7b** | **`agentgrade improve`.** For a failing tool, generate 3-4 candidate rewrites, run each as a variant, and report the winner and by how much. | The core product: fix and prove. |
| Parallel | **Talk to 5 MCP server authors** (DMs on X or GitHub): "Would you run this before every release?" | Validate the audience before building onboarding. |
| Later | Generated tasks / ready-made suites for popular servers; then CI mode as a small add-on; then a public index. | Adoption, once the core is proven. |

## Sources
- Braintrust, [Best MCP testing tools for agent evals (2026)](https://www.braintrust.dev/articles/best-mcp-testing-tools-agent-evals-2026)
- Arcade, [Introducing ToolBench](https://www.arcade.dev/blog/introducing-toolbench-quality-benchmark-mcp-servers/) (2026-03-18)
- Glama, [Tool Definition Quality Score](https://glama.ai/blog/2026-04-03-tool-definition-quality-score-tdqs) and the
  [TDQS specification](https://github.com/glama-ai/tool-definition-quality-score)
- [mcp-evals](https://github.com/mclenhard/mcp-evals)
- Our data: [CASE_STUDY.md](CASE_STUDY.md)
