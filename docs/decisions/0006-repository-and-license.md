# 0006. Repository, publishing and license

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq

## Problem
Where does the code live, who publishes it, and under what license?

## Decision
- Public GitHub repository under `Tanishq67m`, published from the first commit (build in public).
- **Tanishq runs all git commits and pushes himself.** The assistant does not push.
- No AI co-author trailers in commit messages.
- **MIT license.**

## Rationale
Public history from day one supports the build-in-public strategy. MIT is the most permissive common license, so it doesn't put off people who want to try the tool or companies evaluating the work.

## Consequences and limitations
- Everything committed is public: secrets must never enter the repo (`.env` is git-ignored).
