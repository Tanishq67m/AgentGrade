# Case study: what makes agents fail on MCP servers, and which fixes actually work

**312 evaluated agent runs on two official MCP servers** (filesystem, git), two models, every answer checked in
code, every run traced, plus 70 scorings of the same descriptions by a published static grader. Run with [AgentGrade](../README.md), October-November 2026.

> **Version 1.3, 2026-11-19:** adds [Finding 8](#finding-8-settling-a-design-question-with-data-5610), the measured options for #5610.
>
> **Version 1.2, 2026-11-18:** adds [Finding 7](#finding-7-a-fix-measured-on-one-version-did-not-survive-the-next),
> which re-tests the filesystem fix on current main (2.3.0) and corrects the scope of TL;DR 1 and issue #5553.
>
> **Version 1.1, 2026-11-18:** adds [Finding 6](#finding-6-a-published-static-score-could-not-see-the-difference),
> static description scores vs measured behavior.
>
> **Version 1, 2026-11-16.** All experiments complete. Raw reports are in [`results/`](../results/).
> Reported upstream with the data: [modelcontextprotocol/servers#5552](https://github.com/modelcontextprotocol/servers/issues/5552)
> (git `git_log`) and [#5553](https://github.com/modelcontextprotocol/servers/issues/5553) (filesystem `search_files` examples).

## TL;DR

1. **Concrete examples in a tool description decide whether a small model even tries.** Swapping two generic
   examples (`**/*.ext`, `**/name`) for realistic ones (`**/*.json`, `**/*invoice*`) in one tool's description took a
   4B model from **3/12 to 9/12**. With the generic examples it answered "I don't have access to any database"
   without calling a tool. Precise matching rules alone fixed *searching*, but not that refusal.
   **Measured on server 2.0.0.** On 2.3.0 the effect mostly disappears (Finding 7).
2. **The tool description is the highest-leverage fix.** Rewriting one tool's description raised a small model's
   pass rate from **1/12 to 9/12** on the filesystem server (the 9/12 reproduced in three separate runs), and from
   **13/15 to 15/15** on the git server (measured once so far).
3. **Generic advice in the agent's prompt barely helps.** "Explore with your tools first": 1/12 → 3/12.
   "If a tool errors, read it and retry": 7/15 → 8/15, fixing one task while breaking another.
   **Concrete facts help a lot**: telling the agent where the repository is took 7/15 → 13/15.
4. **Empty results with no guidance produce confident wrong answers.** On both servers an agent received an empty
   result, either `No matches found` or an empty `Commit history:`, after misusing a parameter, and concluded the
   data didn't exist.
5. **The most common failure wasn't bad tool use but no tool use.** The small model often answered
   "I don't have access to any database" without calling a tool, or gave up after one recoverable error.
   A strong model (gpt-oss-120b) did neither: **11/12** and **14/15** on the original servers. **Vague
   descriptions and unhelpful errors mostly hurt small, cheap models.**
6. **Strong models fail differently:** they assume real-CLI semantics the tool doesn't support (git range syntax),
   and mis-copy long opaque paths. They're better, not immune.

7. **A published static score couldn't see any of this.** We re-implemented Glama's Tool Definition Quality
   Score (TDQS) and had it grade the six `search_files` descriptions we had measured. All six were graded
   **A**, while measured pass rates ran from **8% to 75%**. The rank correlation was **-0.09** (and +0.20 with a
   second judge). The 3/12 and 9/12 descriptions got **the same score (3.92)**. Static scoring did flag the
   one-line `git_log` description (C vs A), so it catches *missing* information, not *misleading* information.

8. **A fix measured on one server version didn't survive the next.** On filesystem 2.3.0, a community patch
   adding realistic examples scored 2/12 (main: 1/24), and our own 9/12 description scored only 4/12. A 2×2
   showed the new parameter-schema text and the reworded descriptions of other tools each cost a little.
   On git, the community patch for `git_log` held: 15/15 vs main's 14/15.

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
| precise glob rules + concrete examples ("rules-only" variant) | - | **9/12** (CI 47-91%) |
| "explore the layout first" only | - | 1/12 |
| `search_files` removed | 1/12 | 1/12 |

The first "improved" description changed two things at once, so we ran the ablation: the gain was in the
rewritten matching rules, and the "explore the layout first" advice added nothing. Removing the tool didn't help
either, because the main failure happened before any tool was chosen (Finding 3).

**Upstream then shipped its own fix, and measuring it corrected us.** Filesystem server **2.2.0** (2026-11-04)
rewrote the description with the same precise rules (paths relative to `path`, `**/` to reach any depth):

| Same 4 tasks x 3 repeats | `shipping_cost` (prompt mentions files) | other 3 tasks | Total |
|---|---|---|---|
| 2.0.0 as shipped | 1/3 | 0/9 (9x `gave_up`) | 1/12 |
| **2.2.0 as shipped** | **3/3** | **0/9 (9x `gave_up`)** | **3/12** |
| 2.0.0 + our rewritten description | 3/3 | 6/9 | 9/12 |

Upstream's precise rules fixed the **searching**: whenever the model tried, it succeeded. They didn't fix the
**refusals**. So our ablation label was too strong. Our "rules-only" text also contained concrete, data-like
examples (`'**/*.json'`, `'**/*invoice*'`), while 2.2.0 uses generic ones (`'*.ext'`, `'**/name'`); we had separated
the rules from the exploration advice, but never the rules from the examples. (2.2.0 also changed `directory_tree`,
`get_file_info` and `read_text_file`, so it isn't a single-variable comparison.)

**So we tested the examples directly** (same pinned 2.0.0 server, one change per variant, all four run together):

| Variant (4 tasks x 3 repeats) | `shipping_cost` | `order_count` | `heaviest_order_customer` | Total |
|---|---|---|---|---|
| baseline | 2/3 | 0/3 | 0/3 | 2/12 |
| 2.2.0's `search_files` text only | 2/3 | 0/3 | 0/3 | 2/12 |
| our rules + **generic** examples (`'**/*.ext'`, `'**/name'`) | 3/3 | **0/3** | **0/3** | 3/12 |
| our rules + **concrete** examples (`'**/*.json'`, `'**/*invoice*'`) | 3/3 | **3/3** | **3/3** | **9/12** (3rd time) |

(`order_status_b42` was 0/3 everywhere; see Finding 3.) Changing **only the two example patterns** moved
`order_count` and `heaviest_order_customer` from 0/6 to 6/6. With generic examples, every one of those runs was a
step-1 refusal: *"I don't have access to any database or system that would contain order information."* With the
concrete examples the model searched for business data (`**/*order*` x4, `**/*.order` x3, and `**/*.invoice`, a
literal echo of the example) and found it.

**Our reading:** precise rules teach the model *how* to search; realistic examples tell it *that there is
something worth searching for*. For a small model, a filesystem tool described only in abstract terms
(`*.ext`) reads as "a file-system utility", not "where the user's orders live", so it declines before trying. This
is an interpretation of one model on one dataset, not a proven mechanism. Which example word does the work
(`json` or `invoice`) isn't separated yet.

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

| Model | Filesystem, original description | Filesystem, our rewritten description | Git, not told the path | Git, path given |
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
  4-6 range variants before hitting the 10-step limit (2 runs, both on `unmerged_branch`). *Upstream has since added
  range support to `git_diff` (mcp-server-git 2026.11.11, #5194).*
- **Mis-copying long opaque IDs.** Twice it re-typed the sandbox path as `…mdc1r4…` instead of `…mdc21r4…`, dropping
  the **same digit** both times. The server's error caught it, and it recovered in one run.
- One run (filesystem) produced malformed tool-call JSON that the provider rejected.

Better models shift failures from "doesn't try" to "tries the wrong thing confidently", and the fix is the same:
say what the tool accepts, and make errors say what to do instead.

## Finding 6: a published static score could not see the difference

**Question.** Static graders score a tool definition by reading it, without running an agent. Glama's TDQS is
the one that publishes its full method: six dimensions scored 1-5 by an LLM judge, then weighted, with tiers
A ≥ 3.5, B ≥ 3.0 (passing), C, D. Does a TDQS score predict what agents actually do?

**Method** ([ADR 0016](decisions/0016-static-vs-measured.md)).
- TDQS re-implemented from its spec at a pinned commit (`b9881b0`), including its exact prompts.
- We scored the exact definitions the agent saw in our runs: the server's real schema and annotations, with only
  the description changed per variant.
- Judges: `gpt-oss-120b` and `gpt-oss-20b` on Groq at temperature 0, 5 scorings per description.
- Measured pass rates were pooled from the existing `results.json` files (qwen3:4b-instruct). No new agent runs.
- Three predictions were written down **before** running.

**Filesystem `search_files`: six descriptions, all "A"**

| Description | TDQS, 120B judge | TDQS, 20B judge | Measured (4B agent) |
|---|---|---|---|
| baseline (2.0.0) | 3.62 A | 3.80 A | 4/36 (11%) |
| explore-first-only | **4.12 A** (tied highest) | 4.40 A | **1/12 (8%)**, the worst |
| upstream-2.2.0-description | 4.04 A | 4.38 A | 2/12 (17%) |
| glob-rules-generic-examples | 3.92 A | 4.46 A | 3/12 (25%) |
| clear-search-description | 4.12 A | 4.56 A | 17/24 (71%) |
| glob-rules-only (realistic examples) | 3.92 A | 4.26 A | **18/24 (75%)** |
| **Spearman rank correlation** | **-0.09** | **+0.20** | |

**Predictions vs outcome.**
1. *The realistic-examples and generic-examples versions score within 0.3 of each other.* **Held:** 3.92 vs 3.92
   (120B). The 20B judge ranked the generic version **higher** (4.46 vs 4.26), even though it passed 3/12 vs 18/24.
2. *Upstream 2.2.0's description is graded B or better despite failing 10 of 12.* **Held:** A in 10 of 10 scorings.
3. *TDQS does not reliably rank the measured winners first (Spearman < 0.5).* **Held:** -0.09 and +0.20.

Across 60 filesystem scorings, the justifications note that the description "gives examples" 13 times, but never
whether those examples are realistic or placeholders. That was the one detail that changed agent behavior 3×. It praised the matching rules, which our ablation showed
were *not* what helped.

**Git `git_log`: static scoring got this one right.** The original one-line description *"Shows the commit
logs"* scored **2.70 (C)** in all 5 scorings. The rewritten one scored **3.98 (A)**. Measured pass rate went 83% → 100%.
The judge named the real gap: the description *"does not explain any parameters"*.

**What this means.**
- Static scores catch **missing** information: a one-liner with undocumented parameters.
- They can't tell apart descriptions that are all complete and well written but behave very differently with
  a real model. That last-mile difference (8% vs 75% here) only shows up when you run agents.
- Static scoring is a useful, cheap **first pass**. It isn't evidence that agents will succeed.
- **Judge noise is as large as the differences.** At temperature 0, identical input scored 3.4-4.0, and
  in another case 3.7-4.5, across 5 scorings. A single static score per tool can cross a tier boundary by chance.

**Limits.** Six descriptions of one tool, one agent model, and our re-implementation run with open judges.
Glama's production judge model isn't published, so absolute scores may differ on glama.ai. This shows TDQS
did not track behavior *here*. It doesn't show it never does. Reports:
[120B](../results/2026-11-17-static-tdqs-filesystem-gpt-oss-120b.md),
[20B](../results/2026-11-18-static-tdqs-filesystem-gpt-oss-20b.md),
[git](../results/2026-11-17-static-tdqs-git-gpt-oss-120b.md).

## Finding 7: a fix measured on one version did not survive the next

**Context.** Both upstream issues were triaged into the v2.6.0 milestone, and a contributor posted a patch for
both (fork commit `b3c9386b`). AgentGrade can now run a variant against a different server **build**
([ADR 0017](decisions/0017-measure-proposed-patches.md)), so we measured the real patched code against its
parent commit `e1d154ee` before it merges. Same model (digest `0edcdef34593`, the same as all earlier runs),
same tasks.

**Filesystem 2.3.0: the examples fix no longer works.**

| `search_files` on 2.3.0 | Passed |
|---|---|
| main | 1/24 (two runs) |
| patch as built: realistic examples added after the generic ones, in the description and the `pattern` parameter | 2/12 |
| patch with user-data examples (`**/*invoice*`) instead | 2/12 |
| patch with its first sentence ("never reads or searches inside files") softened | 0/12 |
| main + our description (9/12 on 2.0.0) | 4/12 |

What changed between 2.0.0 and 2.3.0, apart from `search_files`: every parameter gained a long description
(`search_files`' schema grew from 141 to 789 characters, and "must resolve inside the allowed directories"
appears on every `path`), and `list_directory`, `directory_tree` and `get_file_info` were reworded. A 2×2,
with override texts copied verbatim from both servers and our description in every cell:

| | 2.0.0 descriptions (other tools) | 2.3.0 descriptions (other tools) |
|---|---|---|
| **2.0.0 input schemas** | 7/12 (control; pooled with earlier runs 25/36) | 6/12 |
| **2.3.0 input schemas** | 5/12 | 4/12 |

Both changes seem to cost a little, the schemas maybe more. At 12 runs per cell the intervals overlap, so we
don't claim more than that. One task, `order_status_b42`, was refused in every run of every cell, on both
versions.

**Git 2026.11.11: the patch held.** Main 14/15. Its one failure was the exact bug from #5552 ("the commit
history is empty"). The patch got 15/15, and our issue's wording got 15/15. The same task failed 6/6 on 2026.10.10, so
the newer server already does better, and 15 runs can't show a significant gain.

**What this means.**
- A description fix is a property of the **whole tool list the model sees**, not of one sentence. Unrelated
  edits elsewhere (parameter docs, sibling tools) can cancel it.
- Our own issue overstated how general the fix was. We corrected it on the issue with the data
  ([comments](upstream/2026-11-18-patch-check.md)).
- This is the case for re-measuring on every release, the way tests are re-run. A fix verified once can
  silently stop working.

Reports: [patch](../results/2026-11-18-pr5553-filesystem-1-patch.md),
[follow-up](../results/2026-11-18-pr5553-filesystem-2-followup.md),
[2×2](../results/2026-11-18-pr5553-filesystem-3-schemas-vs-descriptions.md),
[git](../results/2026-11-18-pr5552-git-patch.md).

## Finding 8: settling a design question with data (#5610)

After #5552 and #5553 were fixed and merged (PRs #5626 and #5620, v2.6.0), the maintainer opened
[#5610](https://github.com/modelcontextprotocol/servers/issues/5610): should `repo_path` default to the configured
`--repository`? We built each option from that issue on current `v2/main` and measured them with **no path
given to the agent** ([ADR 0018](decisions/0018-repo-path-options-5610.md)):

| Option | Passed | Path errors | Median time |
|---|---|---|---|
| today (required, mostly undescribed) | 9/15 | 14 of 33 calls | 35s |
| `repo_path` described with the allowed repository | 12/15 | 0 | 24s |
| server `instructions` name the repository | **15/15** | 0 | 22s |
| `repo_path` optional, defaulting to `--repository` | **15/15** | 4 (recovered) | **9s** |

Today vs the two winners is significant even at n = 15 (Fisher p ≈ 0.02); the options among themselves are not.
A model that can't see the one valid value of a required parameter guesses (`"."`), and an error that
names the right value is what lets it recover.
[Report](../results/2026-11-19-repo-path-5610-git.md).

## What this means for MCP server authors

*(Findings 1 and 2 were filed as [#5553](https://github.com/modelcontextprotocol/servers/issues/5553) and
[#5552](https://github.com/modelcontextprotocol/servers/issues/5552).)*

1. **State exact semantics in the tool description**: matching rules, defaults, ordering, which parameters are
   optional. Agents take descriptions literally, and small models can't recover from ambiguity.
2. **Use realistic examples, not placeholders.** `'**/*.json'` or `'**/*invoice*'` told a small model there was
   user data to look for; `'*.ext'` didn't (9/12 vs 3/12 on 2.0.0; on 2.3.0 examples alone were not enough, Finding 7).
   Expect models to copy examples literally.
3. **Never return a bare empty result.** Say what was searched and how to widen it:
   *"No matches. Patterns are relative to `path`; use `**/` for subfolders."*
   *"No commits in this time range; omit the timestamps to see the latest commits."*
4. **Make required context discoverable**, or make the error tell the agent exactly what to do next. A
   path-discovery tool or a default `repo_path` removes a whole failure class. Long opaque IDs get mis-copied
   even by strong models: accept a default wherever you can.
5. **Say what syntax a parameter does *not* accept** when it looks like a familiar CLI flag or argument
   ("`target` takes one branch or commit; ranges like `a..b` are not supported").
6. **Test with the small models your users will actually run.** A strong model hides most of these problems.
7. **Treat a description-quality grade as a lint, not a test.** It will catch a missing explanation. It won't
   catch an example that makes a small model give up. All six of our filesystem descriptions got an A.
   Measured, they ranged from 8% to 75%.
8. **Re-measure after every release.** Our filesystem fix went from 9/12 to 4/12 when other tools' parameter
   docs and descriptions changed around it (Finding 7).

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
- **Our own mistakes along the way** (fixed, each with a regression test where code was involved): a grader that
  passed a wrong answer, a failure category that hid 92% of failures, one experiment that changed two things at once,
  one model error first blamed on our infrastructure, and an ablation label ("rules only") that turned out to
  bundle rules with examples. Measuring upstream's real fix exposed that last one. Listed in [PROJECT.md](PROJECT.md#5-mistakes-and-what-they-taught).

## Reproduce

```bash
git clone https://github.com/Tanishq67m/AgentGrade.git && cd AgentGrade && uv sync
ollama pull qwen3:4b-instruct
uv run agentgrade run suites/shop.yaml          # filesystem, all variants
uv run agentgrade run suites/shop.yaml --variants baseline,glob-rules-only,upstream-2.2.0-description,glob-rules-generic-examples
uv run agentgrade run suites/shop-upstream-2.2.0.yaml
uv run agentgrade run suites/git.yaml           # git, 4 variants
uv run agentgrade run suites/shop.yaml --model model_configs/groq-gpt-oss-120b.yaml --variants baseline,glob-rules-only
uv run agentgrade run suites/git.yaml --model model_configs/groq-gpt-oss-120b.yaml --variants baseline,repo-path-given
# Finding 6: static scores (needs GROQ_API_KEY); --compare takes your own run folders
uv run agentgrade static-score suites/shop.yaml --judge model_configs/judge-groq-gpt-oss-120b.yaml --tools search_files \
  --variants baseline,glob-rules-only,explore-first-only,clear-search-description,upstream-2.2.0-description,glob-rules-generic-examples \
  --reference baseline --compare runs/<filesystem run folders>
```

Raw reports: [`results/`](../results/). Every run's trace is written to `runs/<id>/traces/`.
