# 0002. Architecture: modular monolith, CLI + file-based results

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (delegated: "choose what is best for the long run")

## Problem
How should the MVP be shaped and where should results live?

## Options considered
- **A. CLI + JSON/JSONL files**, one Python package with focused modules.
- **B. FastAPI + PostgreSQL + React** from day one.
- **C. Plain-Python tools, no MCP** (used as Milestone 1 only, not the whole design).

## Trade-offs
- A: fully inspectable (open the trace file), nothing to deploy, cheap to change while the data model is unstable. No multi-user access, no history queries.
- B: looks impressive; forces schema design before we know what a trace needs → migration churn.
- C: isolates the agent-loop concept, but doesn't touch the actual product question.

## Decision
Option A. Modules: suite loader, runner (agent loop + limits), model adapter, MCP client, trace recorder, validator + failure classifier, reporter. Results under `runs/<run_id>/`.

## Rationale
Smallest architecture that answers the core question; data shapes get proven by real runs before they're frozen into a database schema.

## Consequences and limitations
- FastAPI (run trigger + results API) and PostgreSQL (run history, before/after comparisons) are **deferred, not dropped**. Revisit once the result format has stayed stable across real runs (around M6-M7).
- Module boundaries must stay clean so an API layer can wrap the runner later without a rewrite.
