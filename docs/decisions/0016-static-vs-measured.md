# 0016. Static vs measured: re-implement TDQS and score the descriptions we already measured

- **Status:** Accepted
- **Date:** 2026-11-17
- **Decided by:** Tanishq (delegated: "now let's go ahead" with the recommended first step of ADR 0015)

## Problem
ADR 0015 rests on one claim: a static description score does not tell you whether an agent will
succeed with a tool. We have measured pass rates for 6 descriptions of filesystem `search_files` and
2 descriptions of git `git_log`, each differing from its reference in the description only. The test:
score those exact descriptions with a real, published static grader and see whether the scores follow
the measured pass rates.

## Which static grader
**Glama's Tool Definition Quality Score (TDQS).** It is the only one that publishes the full method:
rubric, verbatim prompts, weights, rounding and tiers. That makes it "sufficient to reimplement TDQS end
to end" in its own words. Arcade ToolBench's method is described but not published at prompt level.

## Decisions
| Question | Choice | Why |
|---|---|---|
| Prompt text | **Downloaded at runtime** from the TDQS repo, pinned to commit `b9881b0` (2026-09-03), and extracted from Appendix A. Not copied into our repo. | The TDQS repo has no license file. Fetching the published text keeps us faithful to the spec without redistributing it. Pinning makes every score reproducible. |
| Pipeline fidelity | Stage 1 context signals, stage 2 hard gates (no description; tautology cap), stage 3 one LLM call returning six 1-5 scores, stage 4 cap and smells; weights 25/20/20/15/10/10; integer `round1`; tiers A ≥ 3.5, B ≥ 3.0, C ≥ 2.0, D | Same numbers as Glama's code for the same LLM output. |
| Tool definitions | Taken live from the pinned server (`tools/list`): description, input schema, annotations, output schema. Siblings = all tools the server offers. Variant `description_overrides` replace only the description. | Exactly what TDQS sees for a real server, and exactly what the agent saw in our runs. |
| Judge model | `gpt-oss-120b` on Groq, temperature 0 (TDQS asks for a fast, inexpensive OpenAI-compatible model); `gpt-oss-20b` as a second judge | Free tier. Two judges show whether a conclusion depends on the judge. |
| Judge noise | Each description scored 5 times; report mean and min-max | One LLM call can't be told apart from noise. |
| Measured side | Pass rates pooled from **existing** run folders (`results.json`), same model only, never typed by hand | No new agent runs needed; no transcription errors. |
| Comparison | Per variant: TDQS and pass rate relative to a reference variant (Δ vs Δ), plus Spearman rank correlation when ≥ 4 variants | With n = 6 a correlation coefficient alone means little; paired deltas are the readable result. |

## Predictions (written before running)
1. `glob-rules-only` (18/24) and `glob-rules-generic-examples` (3/12) differ only in two example
   strings. **TDQS will score them within 0.3 of each other.**
2. `upstream-2.2.0-description` (2/12) will score **tier B or higher**, i.e. "passing", despite failing
   10 of 12 runs.
3. Across the 6 filesystem descriptions, TDQS will **not** reliably rank the measured winners first
   (Spearman below 0.5).

If predictions 1 and 3 fail, meaning TDQS clearly separates the 9/12 descriptions from the 3/12 ones,
ADR 0015's positioning is weakened and we say so publicly.

## Consequences and limitations
- New command `agentgrade static-score` (it also becomes a cheap first-pass check in later milestones).
- `McpToolInfo` now keeps `title`, `annotations` and `output_schema` (needed for TDQS inputs).
- Small n: 8 descriptions, 2 servers, one agent model. The result is indicative. It can reject "TDQS
  predicts behavior here"; it cannot prove "TDQS never predicts behavior".
- Glama's production judge model isn't named, so our absolute scores may differ from glama.ai's.
  Relative comparisons between our own variants are what matter here.

## Outcome (2026-11-18)
All three predictions held (70 scorings, 0 failed). Full write-up: [CASE_STUDY.md, Finding 6](../CASE_STUDY.md#finding-6-a-published-static-score-could-not-see-the-difference).
1. Realistic vs generic examples: **3.92 vs 3.92** (120B judge). The 20B judge put the generic version *higher*
   (4.46 vs 4.26). Measured: 18/24 vs 3/12.
2. Upstream 2.2.0 description: **A in 10/10 scorings**. Measured: 2/12.
3. Spearman across 6 filesystem descriptions: **-0.09** (120B), **+0.20** (20B).

Not predicted: on git, TDQS **did** separate the one-line `git_log` description (2.70, C) from the rewrite
(3.98, A), matching the measured direction (83% → 100%). Static scoring catches missing information, not
misleading information. Also observed: at temperature 0 the same input scored up to 0.8 apart across repeats (3.7-4.5).
