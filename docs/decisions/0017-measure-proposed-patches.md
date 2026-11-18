# 0017. Variants can run a different server build: measure proposed patches before they merge

- **Status:** Accepted
- **Date:** 2026-11-18
- **Decided by:** Tanishq ("build whatever you suggested")

## Problem
Our issues #5552 and #5553 were triaged into the v2.6.0 milestone, and a contributor posted a patch
(fork commit `b3c9386b`) for both. This repo takes prompts rather than PRs, so maintainers will likely write
the final change from that patch's prompt. The patch differs from what we measured. It keeps the generic
examples first, uses developer-file examples (`package.json`, `*config*`) and sits on top of 2.2.0's
wording (2/12 in our runs). It also changes the `pattern` *parameter* description, which a
`description_overrides` variant can't reproduce. Nobody knows whether it works.

## Options considered
| Option | For | Against |
|---|---|---|
| Re-type the patch's text as `description_overrides` | No new code | Misses parameter-schema changes; a transcription risk; not the real code |
| A separate suite file per build | No new code | Two copies of every task; separate run folders make the A/B comparison manual |
| **`server:` override per variant** (command/args), real builds checked out by a script | Measures the actual patched code in one run, one report; reusable for any server PR | Small feature + a build script |

## Decision
- `Variant.server` (`command`, `args`, `label`): only the process changes. Fixture, setup, tasks, model and
  timeout stay the suite's. `Suite.server_for(variant)` merges them; `{suite_dir}` is resolved in both.
- Results record each variant's server (`SuiteResult.servers`, with label and version). Reports show a
  "Server builds" row. `agentgrade static-score` snapshots each distinct build separately.
- `scripts/build_server_target.sh <repo> <commit> <name>` checks out one commit into `.targets/<name>/`
  (git-ignored) and builds the filesystem server. The git server needs no build (`uvx --from <path>`).
- Suites `pr-5553-filesystem.yaml` and `pr-5552-git.yaml`: parent commit vs patch, plus one variant
  each that changes a single thing on top (user-data examples / the wording from our issue).

## Rationale
This is the product thesis in action: a server author (or a maintainer reviewing a patch) gets measured
evidence on the real code before merging. A static review of the patch can't provide that (Finding 6).

## Consequences and limitations
- Comparing builds is only fair at the same base commit. Both suites pin the patch's own parent (`e1d154ee`).
- A build from someone's fork is untrusted code. These are read-only, sandboxed servers over fixture data
  (ADR 0005), and the commits are pinned by full hash. Container isolation is still on the roadmap.

## Outcome (2026-11-18)
- Filesystem 2.3.0: main 1/24, patch 2/12, patch with user-data examples 2/12, softened first sentence 0/12, and
  our own 9/12-on-2.0.0 description 4/12. A 2×2 (2.0.0 vs 2.3.0 schemas × other-tool descriptions) gave 7, 6, 5 and 4
  out of 12: both changes cost a little. The issue's claim held on 2.0.0 only, and we corrected it on #5553.
- Git 2026.11.11: main 14/15 (its one failure was the #5552 bug), patch 15/15, our wording 15/15.
- Case study Finding 7. Comments: [docs/upstream/2026-11-18-patch-check.md](../upstream/2026-11-18-patch-check.md).
