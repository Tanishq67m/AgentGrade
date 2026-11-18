# Patch check: community patch for #5553 and #5552 (2026-11-18)

Comments posted on [#5553](https://github.com/modelcontextprotocol/servers/issues/5553) and
[#5552](https://github.com/modelcontextprotocol/servers/issues/5552) after measuring fork commit
`b3c9386b` (shivamm-gupta) against its parent `e1d154ee`, on real builds ([ADR 0017](../decisions/0017-measure-proposed-patches.md)).
Suites: [`pr-5553-filesystem.yaml`](../../suites/pr-5553-filesystem.yaml), [`pr-5552-git.yaml`](../../suites/pr-5552-git.yaml).

---

## Comment on #5553 (filesystem)

Thanks @shivamm-gupta for putting this together. Before it lands I measured the patch on real builds (your
commit `b3c9386b` vs its parent `e1d154ee`, filesystem 2.3.0). I also need to correct the scope of this issue.

**Setup:** `qwen3:4b-instruct` (Ollama, temperature 0.7), the same 4 file-lookup tasks as in the issue, 3 repeats
each (12 runs per row), every answer checked in code.

| `search_files` on 2.3.0 | Passed |
|---|---|
| main `e1d154ee` | 1/24 (two runs) |
| patch `b3c9386b`, as built | 2/12 |
| patch, with the user-data examples from this issue instead | 2/12 |
| patch, first sentence softened | 0/12 |
| main + the full description from this issue | 4/12 |

Almost every failure is the same as before: the model answers "I don't have access to any database" without
calling a tool.

**Correction:** the 3/12 → 9/12 result in this issue was measured on **2.0.0**. It still holds there (7/12 in a
re-run today). On **2.3.0**, realistic examples alone no longer change the behavior, whether they're the
patch's examples or ours.

To find what changed between 2.0.0 and 2.3.0, I ran a 2×2. Every cell uses the description from this issue:

| | 2.0.0 descriptions on the other tools | 2.3.0 descriptions on the other tools |
|---|---|---|
| **2.0.0 input schemas** | 7/12 | 6/12 |
| **2.3.0 input schemas** | 5/12 | 4/12 |

The new parameter descriptions (e.g. "…it must resolve inside the allowed directories" on every `path`) and the
reworded `list_directory` / `directory_tree` / `get_file_info` descriptions each seem to cost a little. With 12
runs per cell I can't separate them further.

So my honest read: the patch is a harmless clarity improvement, but I wouldn't expect it to fix the refusals,
and I don't have a measured fix for 2.3.0 yet. I'm happy to run any candidate wording through the same A/B
before it's merged; it takes about 15 minutes per variant.

Suite: https://github.com/Tanishq67m/AgentGrade/blob/main/suites/pr-5553-filesystem.yaml
Reports: https://github.com/Tanishq67m/AgentGrade/tree/main/results (files `2026-11-18-pr5553-*`)

---

## Comment on #5552 (git)

I measured the patch for this one the same way (`b3c9386b` vs `e1d154ee`, mcp-server-git 2026.11.11,
`qwen3:4b-instruct`, 5 tasks × 3 repeats, with the repository path given to the agent):

| `git_log` on 2026.11.11 | Passed |
|---|---|
| main `e1d154ee` | 14/15 |
| patch `b3c9386b` | 15/15 |
| main + the description suggested in this issue | 15/15 |

Main's one failure was exactly this bug: the agent concluded "the commit history is empty". Neither description
variant hit it. On 2026.10.10 the same task failed 6 of 6 times with the path given, so 2026.11.11 already
behaves much better here, and 15 runs can't show a significant difference. The patch looks good to me. It
removes the failure we saw and doesn't regress anything else.

The other suggestion still stands. An empty `Commit history:` with a hint ("No commits in this range; omit the
timestamps to see the latest commits") would cover the case where a model still adds filters.

Suite: https://github.com/Tanishq67m/AgentGrade/blob/main/suites/pr-5552-git.yaml
Report: https://github.com/Tanishq67m/AgentGrade/blob/main/results/2026-11-18-pr5552-git-patch.md
