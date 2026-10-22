# 0011. Suites, variants, repeated runs and reports (Milestone 4)

- **Status:** Accepted
- **Date:** 2026-10-22
- **Decided by:** Tanishq (asked for a stage that ends in a meaningful showcase; recommendations accepted)

## Problem
One hand-written demo per task can't answer the questions a team actually has:
"how reliable is it?", "why does it fail?" and "did my fix help?". The showcase needs the loop
**fail → trace → fix → repeatable before/after numbers**.

## Decisions

| Question | Choice | Why |
|---|---|---|
| Suite format | **YAML** validated by strict Pydantic models (`extra="forbid"`); new dependency **PyYAML** | Human-editable; typos (`repats:`) fail loudly instead of being ignored. |
| Before/after mechanism | **Variants**, each changing ONE thing vs baseline: tool subset, or `description_overrides` | A difference in pass rate can be attributed to one change. Overrides let a server author test a better tool description **without redeploying the server**. |
| Run isolation | **Fresh fixture copy + fresh server process per run** | No state leaks between runs; each run is independently reproducible. Costs ~1-2 s of startup per run. |
| Checks | `answer_number`, `answer_contains`, `answer_regex`, `tool_called` (all code, at least one per task) | Deterministic; covers answer correctness and process. |
| Failure classification | One primary category per run (`pass`, `loop`, `step_limit`, `no_answer`, `wrong_answer`, `harness_error`) + counted signals | Rule-based from the trace. `loop` = the same tool returned an identical result >= 3 times in a row, which is the pattern of real run 1. |
| Uncertainty | Pass rate shown as k/n with a **95% Wilson interval**; small-sample warning under 10 repeats | 3/3 is not "100% reliable" (the interval is 44-100%). |
| Temperature | Set explicitly per suite (shop suite: **0.7**) and recorded | Real deployments sample; at temperature 0 repeats are near-identical and say little about reliability. |
| Errors | Setup errors (Ollama down, model missing, server won't start) **stop the suite**; any other per-run error is recorded as `harness_error` and the suite continues | Don't burn 36 runs on a broken setup; don't let one odd failure lose the rest. |
| CLI | `agentgrade run <suite>` (`[project.scripts]` entry point, argparse) with `--repeats/--variants/--tasks` | Still no new CLI dependency. |
| Output | `runs/<id>/results.json` (everything), `report.md` (human), `traces/<variant>__<task>__r<n>.jsonl` | One folder per suite run = one shareable artifact. |

## Rules for writing variants
- Description overrides must be **generic**. They must never contain hints about the task's data or
  answer, otherwise the comparison measures the leak, not the description.
- One change per variant.

## Consequences and limitations
- The loop heuristic only catches *identical* repeated results. Varied-but-pointless exploration shows up as `step_limit`.
- Runs are sequential (8 GB laptop, one local model). 4 tasks x 3 variants x 3 repeats = 36 runs, roughly 10-25 min.
- Multiple checks per task are ANDed; there's no partial credit.
