# Static vs measured - git-repo

| | |
|---|---|
| Server | mcp-git 2026.10.10 |
| Static score | Glama TDQS, spec commit `b9881b0` (sha256 `3df9d731cb06`) |
| Judge | `openai/gpt-oss-120b`, 5 scoring(s) per definition |
| Generated | 2026-11-17 16:35 UTC |

TDQS reads only the tool definition (1.0-5.0; tier A >= 3.5, B >= 3.0 = passing, C >= 2.0, D). Measured = pass rate of real agent runs with that definition.

| Variant | Tools | TDQS mean (min-max) | Tier | Purp | Use | Behav | Param | Conc | Compl | Measured pass rate |
|---|---|---|---|---|---|---|---|---|---|---|
| repo-path-given | git_log | 2.70 (2.7-2.7) | C | 4 | 2 | 2 | 2 | 4 | 2 | 25/30 (83%, CI 66%-93%) |
| path-given-clear-log | git_log | 3.98 (3.9-4.1) | A | 4 | 4 | 4 | 4 | 5 | 3 | 15/15 (100%, CI 80%-100%) |

## Change vs `repo-path-given`

| Variant | Δ TDQS | Δ measured pass rate |
|---|---|---|
| path-given-clear-log | +1.28 | +17 points |

## What the judge said (first scoring of each distinct definition)

### git_log - repo-path-given (TDQS 2.7, tier C)

> Shows the commit logs

*Summary:* The description conveys the basic purpose of the tool but is overly terse, offering no usage guidance, parameter explanation, or output details. It aligns with the read‑only annotations but adds little value, resulting in low to moderate scores across most dimensions.

- **Purp 4** - The description states the verb and resource – it "Shows the commit logs" – which is clear, but it does not elaborate on scope (e.g., which repository) or differentiate from sibling tools.
- **Use 2** - No guidance is given about when to invoke this tool versus alternatives such as git_show or git_diff; the description provides no usage conditions or prerequisites.
- **Behav 2** - The description adds no behavioral details beyond the annotations (read‑only, non‑destructive, idempotent). It does not mention pagination, default max_count, or timestamp filtering, so it contributes little extra insight.
- **Param 2** - Schema coverage is only 50% and the description does not explain any parameters (repo_path, max_count, timestamps). It fails to compensate for the missing schema documentation.
- **Conc 4** - The single‑sentence description is succinct and contains no filler, but its extreme brevity limits usefulness; nevertheless it is well‑structured and front‑loaded.
- **Compl 2** - With no output schema provided, the description should describe the shape of the returned logs, but it does not. Hence the overall description is incomplete for the tool’s context.

### git_log - path-given-clear-log (TDQS 4.0, tier A)

> Shows the commit log, newest commit first. To see the latest commits, call it with just repo_path (and optionally max_count). start_timestamp and end_timestamp are OPTIONAL filters for a specific date range - leave them out unless the user asks about particular dates, because a narrow range returns no commits.

*Summary:* The git_log description is clear about its function and provides solid usage guidance and behavioral nuances, compensating for modest schema coverage. It is concise and well‑structured but lacks detail on the output format, limiting its overall completeness.

- **Purp 4** - The description clearly states the tool "Shows the commit log, newest commit first," providing a specific verb and resource. It does not explicitly differentiate from sibling tools, but the purpose is unambiguous.
- **Use 4** - It advises calling the tool with only `repo_path` (and optionally `max_count`) for the latest commits and recommends omitting `start_timestamp`/`end_timestamp` unless the user asks for a date range. This gives concrete guidance on parameter usage, though it does not compare to alternative tools.
- **Behav 4** - Beyond the read‑only, non‑destructive annotations, the description reveals ordering (newest first) and a practical caveat that a narrow date range may return no commits. No contradictions with the annotations are present.
- **Param 4** - With only 50 % schema coverage, the description adds valuable meaning for each parameter: it explains the optional nature of `max_count` and the filtering role of the timestamps, plus the recommendation to omit them unless needed. This compensates for the limited schema detail.
- **Conc 5** - The description is only two sentences, each delivering essential information without filler. It is well‑structured and front‑loaded.
- **Compl 3** - The description covers the tool's purpose and input usage but does not describe the shape or content of the returned commit log, and no output schema is provided. Given the lack of output details, completeness is moderate.

## Caveats

- Small n: a handful of definitions and one agent model. This can show that TDQS did not track measured behavior here, not that it never does.
- Glama's production judge model is not published; absolute scores may differ from glama.ai. Compare variants with each other.
