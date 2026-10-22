# 0012. Taxonomy and variants revised after the first suite run

- **Status:** Accepted
- **Date:** 2026-10-22
- **Decided by:** Tanishq (asked to continue toward the showcase; recommendations accepted)
- **Amends:** [0011](0011-suites-variants-reports.md)

## Evidence (suite run `20261022T093534Z-654798`, qwen3:4b-instruct, temp 0.7, 3 repeats)
- baseline 1/12, clear-search-description **9/12** (95% CI 47-91% vs 1-35%, no overlap), no-search 1/12.
- **23 of 25 failures**: the model answered on step 1 **without calling any tool**
  ("I don't have access to any system or database that tracks orders..."). The classifier called these
  `wrong_answer`, which hid the real failure.
- The winning description contained **two ideas** (precise glob rules + "explore the layout first"), so
  the improvement couldn't be attributed. The traces show both being used.
- The official `search_files` description opens with "Recursively search...", although patterns are only
  recursive with `**/`.

## Decisions
1. **New category `gave_up`**: the run failed AND answered without calling a single tool. Checked before
   `no_answer` / `wrong_answer`; `wrong_answer` now means "used tools, still wrong".
2. **Categories are derived, observations are not.** `categorize()` works on recorded data, and
   `agentgrade report <run_dir>` re-renders a report with the current rules. Raw answers, checks and
   signals in `results.json` are never rewritten.
3. **Ablation variants** split the two ideas: `glob-rules-only`, `explore-first-only` (the original text
   word for word + one sentence), and the combined `clear-search-description`.
4. **Agent-side variants**: `Variant.system_prompt_suffix` appends one generic sentence to the agent's
   system prompt (`agent-context`), so a server-side fix can be compared with an agent-side fix.

## Consequences and limitations
- 6 variants x 4 tasks x 3 repeats = 72 runs per full suite run.
- `gave_up` is structural (zero tool calls), not text matching, so it's deterministic.
  A model that calls one useless tool and then refuses still counts as `wrong_answer`.
- Still one small local model and one dataset. Findings are about this model until re-run on others.
