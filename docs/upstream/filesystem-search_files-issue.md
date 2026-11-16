<!-- Use the "Feature request" form (usability improvement). Server: filesystem. Follow-up to #896 and #3419. -->

**Title:** filesystem: realistic examples in `search_files`' description stop small models refusing to search (measured; follow-up to #896 / #3419)

**Body:**

**Server:** filesystem. Measured on `@modelcontextprotocol/server-filesystem` 2.0.0 and 2.2.0; I checked that 2.3.0
ships the same `search_files` description and the same empty result.
**Run with:** `npx -y @modelcontextprotocol/server-filesystem@<version> <dir>`, stdio transport, protocol 2026-07-28, Node 24.
**Client:** AgentGrade (open-source evaluation harness, built on the MCP Python SDK 2.3.0 client), macOS,
model `qwen3:4b-instruct` via Ollama, temperature 0.7.

Thanks for the rewrite from #896 / #3419 (relative paths, `**/` for any depth). We measured it, and it clearly fixes
*how* agents search: a small model that does search now finds files reliably.

**What it doesn't fix.** On questions like "How many orders are there in total?", the model usually doesn't search at
all. It answers on step 1, *"I don't have access to any database or system that would contain order information"*,
while the data sits one tool call away. In a controlled test the **example patterns** in the description decided this:

| `search_files` description (server 2.0.0, 4 tasks x 3 runs, answers checked in code) | Pass |
|---|---|
| 2.0.0 original | 2/12 |
| 2.2.0 / 2.3.0 text | 2/12 |
| precise rules + generic examples `'**/*.ext'`, `'**/name'` | 3/12 |
| precise rules + concrete examples `'**/*.json'`, `'**/*invoice*'` | **9/12** (reproduced in 3 separate runs) |

The only difference between the last two rows is the two example patterns. On the two affected tasks they went from
0/6 to 6/6, and with the concrete examples the model searched `**/*order*` and found the data. (2.2.0 as released,
with its other tool changes, scored 3/12.)

**Suggestions:**
1. Add one or two realistic examples next to the generic ones, e.g. `'**/*.json'`, `'**/*report*'`. Small models seem
   to read abstract placeholders as "this is a file utility", not "the user's data is here".
2. Replace the bare `No matches found` with a hint, e.g. "No matches for '<pattern>' under '<path>'. Patterns are
   relative to path; use '**/' to search subdirectories." In earlier runs, agents repeated non-recursive patterns up
   to 9 times after a bare empty result.

**Caveats.** One small local model, synthetic data, 12 runs per row. A larger model (gpt-oss-120b) solved 11/12 even
with the original 2.0.0 description, so this mainly affects small, cheap models.

Case study (method, all tables, caveats): https://github.com/Tanishq67m/AgentGrade/blob/main/docs/CASE_STUDY.md
Raw reports: https://github.com/Tanishq67m/AgentGrade/tree/main/results
