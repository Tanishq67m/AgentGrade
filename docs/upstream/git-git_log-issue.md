<!-- Use the "Feature request" form (usability improvement). Server: git. -->

**Title:** git: `git_log` description doesn't say results are newest-first or that timestamp filters are optional; small models filter to an empty window

**Body:**

**Server:** git, `mcp-server-git==2026.10.10`. I checked that 2026.11.11 still has the same `git_log` description and
the same empty output.
**Run with:** `uvx mcp-server-git --repository <repo>`, stdio transport, protocol 2025-11-25.
**Client:** AgentGrade (open-source evaluation harness, built on the MCP Python SDK 2.3.0 client), macOS,
model `qwen3:4b-instruct` via Ollama, temperature 0.7.

**Problem.** `git_log`'s description is "Shows the commit logs". It doesn't say that results come newest first, or that
`start_timestamp` / `end_timestamp` are optional. Asked "Who made the most recent commit on the main branch?", the
model repeatedly called:

```json
{"repo_path": "<repo>", "max_count": 1, "start_timestamp": "now", "end_timestamp": "now"}
```

The server returned an empty `Commit history:`, and the agent concluded *"the commit history is empty… unknown author"*.

**Measured.** Deterministic repository (identical commit hashes every run), 5 read-only questions x 3 runs,
answers checked in code. Changing **only** `git_log`'s description took the suite from **13/15 to 15/15**, and the
"most recent commit" task from **1/6** (two independent runs) to **3/3**.

**Suggested description:**

> Shows the commit log, newest commit first. To see the latest commits, call it with just repo_path (and
> optionally max_count). start_timestamp and end_timestamp are OPTIONAL filters for a specific date range - leave
> them out unless the user asks about particular dates, because a narrow range returns no commits.

**Also suggested:**
- When no commits match, say so with a hint ("No commits in this range; omit the timestamps to see the latest
  commits") instead of an empty `Commit history:`.
- The `repo_path` error ("outside the allowed repository '<path>'") already contains the fix, which is great. Small
  models still usually stopped there instead of retrying (all 9 failures in one run), and a 120B model mis-copied
  the long path twice. A default `repo_path` (the configured `--repository`) would remove that failure class.

(We also saw `git_diff` reject `main..feature` in 2026.10.10. Thanks for already fixing that in #5194.)

Case study (method, all tables, caveats): https://github.com/Tanishq67m/AgentGrade/blob/main/docs/CASE_STUDY.md
Raw reports: https://github.com/Tanishq67m/AgentGrade/tree/main/results
