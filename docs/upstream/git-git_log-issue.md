<!-- Draft issue for github.com/modelcontextprotocol/servers. Search existing issues for "git_log" first. -->

**Title:** git: `git_log` description doesn't say results are newest-first or that timestamp filters are optional; agents filter to an empty window

**Body:**

`git_log`'s description is "Shows the commit logs". It doesn't say that results come newest first, or that
`start_timestamp` / `end_timestamp` are optional. When asked "who made the most recent commit?", a small model
(qwen3:4b-instruct) repeatedly called:

```json
{"repo_path": "<repo>", "max_count": 1, "start_timestamp": "now", "end_timestamp": "now"}
```

The server returned an empty `Commit history:`, and the agent concluded the repository had no commits.

In an evaluation of `mcp-server-git==2026.10.10` (5 read-only tasks, 3 repeats, temperature 0.7, deterministic
checks), changing only the description to the text below took the suite from **13/15 to 15/15**, and the
"most recent commit" task from **1/6 to 3/3**:

> Shows the commit log, newest commit first. To see the latest commits, call it with just repo_path (and
> optionally max_count). start_timestamp and end_timestamp are OPTIONAL filters for a specific date range -
> leave them out unless the user asks about particular dates, because a narrow range returns no commits.

Two smaller suggestions in the same spirit:
- When no commits match, say so with a hint ("No commits in this range; omit the timestamps to see the latest
  commits") instead of an empty `Commit history:`.
- The `repo_path` error ("outside the allowed repository '<path>'") already contains the fix, which is great. In our
  runs, though, small models usually stopped instead of retrying, so a default `repo_path` (the configured
  `--repository`) would remove that failure entirely.

- `git_diff`'s `target` rejects range syntax (`main..feature`) with "did not resolve to an object". A stronger
  model (gpt-oss-120b) tried 4-6 range variants and ran out of steps in 2/30 runs. One sentence in the
  description ("one branch or commit; ranges like a..b aren't supported") would prevent that.

Method, results and traces: <link to docs/CASE_STUDY.md and results/ in your repo>. Happy to open a PR for the
description change.
