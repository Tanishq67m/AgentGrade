<!-- Draft issue for github.com/modelcontextprotocol/servers. Search existing issues for "search_files" first. -->

**Title:** filesystem: concrete examples in `search_files`' description stop small models refusing to search (measured, 2.2.0)

**Body:**

Thanks for the 2.2.0 rewrite of `search_files`' description (relative paths, `**/` for any depth). We measured it,
and it clearly fixes *how* agents search. A small model that does search now finds files reliably.

We also found something it doesn't fix. On questions like "How many orders are there?", qwen3:4b-instruct usually
doesn't search at all. It answers on step 1, *"I don't have access to any database or system that would contain
order information"*, while the data sits one call away. In a controlled test, the **example patterns** in the
description decided this:

| `search_files` description (all on 2.0.0, 4 tasks x 3 runs, temp 0.7, code-checked answers) | Pass |
|---|---|
| 2.0.0 original | 2/12 |
| 2.2.0's text | 2/12 |
| precise rules + generic examples `'**/*.ext'`, `'**/name'` | 3/12 |
| precise rules + concrete examples `'**/*.json'`, `'**/*invoice*'` | **9/12** (reproduced in 3 separate runs) |

The only difference between the last two rows is the two example patterns. On the two affected tasks they went from
0/6 to 6/6, and with the concrete examples the model searched for `**/*order*` and found the data. (2.2.0 as
released, with its other tool changes, scored 3/12.)

Suggestions:
1. Use one or two realistic examples alongside the generic ones, e.g. `'**/*.json'`, `'**/*report*'`. Small models
   seem to read abstract placeholders as "this is a file utility", not "the user's data is here".
2. Replace the bare `No matches found` with a hint, e.g. "No matches for '<pattern>' under '<path>'. Patterns are
   relative to path; use '**/' to search subdirectories." In earlier runs, agents repeated non-recursive patterns
   up to 9 times after a bare empty result.

Caveats: one small local model, synthetic data, 12 runs per row. A larger model (gpt-oss-120b) solved 11/12 even
with the original 2.0.0 description, so this mainly affects small, cheap models.

Method, data and traces: <link to docs/CASE_STUDY.md and results/ in your repo>. Happy to open a PR.
