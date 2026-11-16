# Case study: what makes agents fail on MCP servers, and which fixes actually work

**252 evaluated agent runs on two official MCP servers** (filesystem, git), two models, every answer checked in
code, every run traced. Run with [AgentGrade](../README.md), October 2026.

> **Status: draft.** One run is pending, marked ⏳: the upstream filesystem 2.2.0 release, which shipped a fix
> similar to ours.

## TL;DR

1. **The tool description is the highest-leverage fix.** Rewriting one tool's description raised a small model's
   pass rate from **1/12 to 9/12** on the filesystem server (the baseline and the gain both reproduced in a second,
   independent run), and from **13/15 to 15/15** on the git server (measured once so far).
2. **Generic advice in the agent's prompt barely helps.** "Explore with your tools first": 1/12 → 3/12.
   "If a tool errors, read it and retry": 7/15 → 8/15, fixing one task while breaking another.
   **Concrete facts help a lot**: telling the agent where the repository is took 7/15 → 13/15.
3. **Empty results with no guidance produce confident wrong answers.** On both servers an agent received an empty
   result, either `No matches found` or an empty `Commit history:`, after misusing a parameter, and concluded the
   data didn't exist.
4. **The most common failure wasn't bad tool use but no tool use.** The small model often answered
   "I don't have access to any database" without calling a tool, or gave up after one recoverable error.
   A strong model (gpt-oss-120b) did neither: **11/12** and **14/15** on the original servers. **Vague
   descriptions and unhelpful errors mostly hurt small, cheap models.**
5. **Strong models fail differently:** they assume real-CLI semantics the tool doesn't support (git range syntax),
   and mis-copy long opaque paths. They're better, not immune.

These are findings about the specific setups below, not universal laws. See [Limitations](#limitations).

## Method

| | |
|---|---|
| Servers | `@modelcontextprotocol/server-filesystem@2.0.0`, `mcp-server-git==2026.10.10` (both pinned) |
| Models | `qwen3:4b-instruct` (local via Ollama, digest `0edcdef34593`); `openai/gpt-oss-120b` (Groq free tier) |
| Sampling | temperature 0.7 (reliability is about variation across runs); 3 repeats per task and variant |
| Tools | read-only allowlist only, using the servers' own `readOnlyHint` annotations; write tools never exposed |
| Data | synthetic, ground truth known: a small shop dataset, and a git repo rebuilt **byte-identically** every run (same commit hashes) |
| Isolation | fresh data copy and fresh server process for every run |
| Scoring | deterministic code checks only (number in answer, text in answer, regex, tool called). **No LLM judge.** |
| Uncertainty | pass rates reported as k/n with **95% Wilson intervals** |
| Variants | each changes **one** thing vs. its comparison: a tool description, the tool set, or one system-prompt line |
| Failure categories | derived from traces: `gave_up` (no tool called), `stopped_after_error` (every call errored, then answered), `loop`, `step_limit`, `wrong_answer`, `harness_error` |

Every run has a full JSONL trace: each model call, tool call, argument and result. That's how every claim below was
diagnosed, not guessed.

## Finding 1: a misleading first word cost 8 of 12 runs (filesystem)

The 2.0.0 `search_files` description began **"Recursively search for files…"**, but its glob patterns only reach
subdirectories when they start with `**/`. The agent searched `order*.json` for a file at `orders/A17.json`, got
`No matches found`, and repeated variations of the same pattern.

| Variant (4 tasks x 3 repeats) | Run 1 | Run 2 (ablation) |
|---|---|---|
| baseline: server as shipped | 1/12 | 1/12 (CI 1-35%) |
| description: precise glob rules **+** "explore the layout first" | 9/12 | 8/12 |
| precise glob rules only | - | **9/12** (CI 47-91%) |
| "explore the layout first" only | - | 1/12 |
| `search_files` removed | 1/12 | 1/12 |

The first "improved" description changed two things at once, so we ran the ablation. **All of the gain came from
stating the matching rules precisely.** The exploration advice added nothing. Removing the tool didn't help either,
because the main failure happened before any tool was chosen (Finding 3).

**Upstream independently shipped the same idea.** Filesystem server **2.2.0** (2026-11-04) describes the pattern as
matching paths *relative to `path`*, with `**/` needed "to match at any depth". ⏳ *Measured on 2.2.0 with the same
tasks: pending (`suites/shop-upstream-2.2.0.yaml`).*

## Finding 2: an optional filter plus an empty result produced "there are no commits" (git)

Asked "who made the most recent commit?", the model called
`git_log(start_timestamp="now", end_timestamp="now")`, a zero-length window. The server returned an empty
`Commit history:`, and the agent answered *"the commit history is empty… unknown author"*. The tool's description
is just "Shows the commit logs"; nothing says the filters are optional or that results are newest first.

| Variant (5 tasks x 3 repeats), repo path given | Run 1 | Run 2 |
|---|---|---|
| server as shipped | 12/15 | 13/15 |
| + `git_log` described as "newest first; timestamp filters optional" | - | **15/15** (CI 80-100%) |
| `last_commit_author` task alone | 0/3 | 1/3, then **3/3** with the description |

## Finding 3: recoverable errors aren't recovered (git), and refusing is the top failure (both)

Every git tool requires `repo_path`, and no tool reveals it. A wrong path returns
*"Repository path '.' is outside the allowed repository '<the correct path>'"*: **the fix is in the error.**

| Variant (git, 5 tasks x 3 repeats) | Run 1 | Run 2 |
|---|---|---|
| agent not told where the repo is | 6/15 | 7/15 |
| + one generic line: "if a tool errors, read it and retry" | - | 8/15 |
| agent told the repo path (one sentence, a fact) | 12/15 | 13/15 |

In run 1, **all 9** baseline failures were `stopped_after_error`: one failed call, then "please check the path".
With the "retry" advice, the model twice *wrote* "Let me retry with the correct repository path" and ended its turn
without calling anything. On the filesystem server, **44 of 49 failures** in the ablation run were `gave_up`:
"I don't have access to any system or database that tracks orders", with zero tool calls.

## Finding 4: a bigger model hides most of it

| Model | Filesystem, original description | Filesystem, precise glob rules | Git, not told the path | Git, path given |
|---|---|---|---|---|
| qwen3:4b-instruct (local) | 1/12 | 9/12 | 6/15, 7/15 | 12/15, 13/15 |
| gpt-oss-120b (hosted) | **11/12** | 12/12 | **14/15** | 14/15 |

- The 120B model never refused without trying. It solved `order_status_b42` in 6 of 6 runs, a task the 4B model
  didn't even attempt in any of its 27 runs.
- On git it hit the same wrong-path error in **all 15** baseline runs and **recovered in 14**. Where the 4B model
  stopped and asked the user, the 120B model read the path out of the error and carried on.
- It **never** used `git_log`'s timestamp filters (0 calls), so the empty-window trap of Finding 2 didn't arise.

## Finding 5: strong models fail differently

All 3 failures of the 120B model across 54 runs:

- **Assuming command-line semantics.** Asked for unmerged work, it called `git_diff` with
  `target: "main..feature/discounts"`, `"main...feature/discounts"`, `"feature/discounts..main"` and more. `git diff`
  understands these; the tool's `target` doesn't, and replies only "Ref '…' did not resolve to an object". It tried
  4-6 range variants before hitting the 10-step limit (2 runs, both on `unmerged_branch`).
- **Mis-copying long opaque IDs.** Twice it re-typed the sandbox path as `…mdc1r4…` instead of `…mdc21r4…`, dropping
  the **same digit** both times. The server's error caught it, and it recovered in one run.
- One run (filesystem) produced malformed tool-call JSON that the provider rejected.

Better models shift failures from "doesn't try" to "tries the wrong thing confidently", and the fix is the same:
say what the tool accepts, and make errors say what to do instead.

## What this means for MCP server authors

1. **State exact semantics in the tool description**: matching rules, defaults, ordering, which parameters are
   optional. Agents take descriptions literally, and small models can't recover from ambiguity.
2. **Never return a bare empty result.** Say what was searched and how to widen it:
   *"No matches. Patterns are relative to `path`; use `**/` for subfolders."*
   *"No commits in this time range; omit the timestamps to see the latest commits."*
3. **Make required context discoverable**, or make the error tell the agent exactly what to do next. A
   path-discovery tool or a default `repo_path` removes a whole failure class. Long opaque IDs get mis-copied
   even by strong models: accept a default wherever you can.
4. **Say what syntax a parameter does *not* accept** when it looks like a familiar CLI flag or argument
   ("`target` takes one branch or commit; ranges like `a..b` are not supported").
5. **Test with the small models your users will actually run.** A strong model hides most of these problems.

## Limitations

- **Small samples:** 12-15 runs per variant. Intervals are wide; we only claim differences where intervals separate
  or the effect replicated.
- **Two models.** Most variant experiments ran on the 4B local model. The 120B model was run on both servers'
  baselines, plus the key fix on the filesystem server, but not on every variant.
- **Synthetic, small datasets** with questions we wrote. Real repositories and real users differ.
- **We wrote the variants.** The improved descriptions were deliberately generic (no task data), but an author who
  knows the tasks can still unintentionally bias wording.
- **Hosted models drift:** Groq reported 41 different `system_fingerprint`s in 159 calls of the same model id.
  Hosted results hold "as of that date".
- **Our own mistakes along the way** (fixed, each with a regression test): a grader that passed a wrong answer, a
  failure category that hid 92% of failures, one experiment that changed two things at once, and one model error
  first blamed on our infrastructure. Listed in [PROJECT.md](PROJECT.md#5-mistakes-and-what-they-taught).

## Reproduce

```bash
git clone https://github.com/Tanishq67m/AgentGrade.git && cd AgentGrade && uv sync
ollama pull qwen3:4b-instruct
uv run agentgrade run suites/shop.yaml          # filesystem, 6 variants
uv run agentgrade run suites/git.yaml           # git, 4 variants
uv run agentgrade run suites/shop.yaml --model model_configs/groq-gpt-oss-120b.yaml --variants baseline,glob-rules-only
uv run agentgrade run suites/git.yaml --model model_configs/groq-gpt-oss-120b.yaml --variants baseline,repo-path-given
```

Raw reports: [`results/`](../results/). Every run's trace is written to `runs/<id>/traces/`.
