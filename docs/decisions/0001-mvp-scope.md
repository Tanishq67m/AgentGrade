# 0001. MVP scope

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (approved the proposed MVP as-is)

## Problem
AgentGrade's long-term vision is large (MCP, OpenAPI, docs, auth targets, leaderboard, CI). We need the smallest product that proves the core value.

## Options considered
1. **MCP servers over stdio** first.
2. **OpenAPI-described HTTP APIs** first.
3. **Product documentation** (agent reads docs, then acts) first.

## Trade-offs
- MCP: tool discovery is built into the protocol (`list_tools` returns names, descriptions, JSON schemas). No spec-to-tool conversion. Most relevant to the current "agent usability" question.
- OpenAPI: huge ecosystem, but needs spec-to-tool conversion, real HTTP, usually auth.
- Docs: hardest to validate; very open-ended.

## Decision
- **First user:** an MCP server maintainer who wants to know whether agents can use their server (initially: Tanishq, evaluating public servers).
- **First target:** MCP servers over **stdio**, starting with **trusted reference servers** (e.g. the official filesystem server) pointed at **fixture data**.
- **Tasks:** **read-only** only.
- **Success:** a task passes only when a **deterministic, code-based check** passes (e.g. final answer contains a value known from fixture data; expected tool called with schema-valid arguments). **No LLM judge in the MVP.**
- **Reporting:** pass rate over N repeated runs per task, failure categories, steps, latency, tokens, estimated cost; small samples are labelled as such.
- **Workflow:** `agentgrade run suite.yaml` → start server → list tools → agent loop with limits → trace → validate → repeat → report.

### Explicitly out of the MVP
Web UI/React, PostgreSQL, FastAPI, multiple model providers, remote/HTTP MCP transports, authenticated or state-changing tasks, user-submitted servers, docs-based evaluation, LLM judges, leaderboard, CI integration, Docker, queues.

## Rationale
One command that produces a trustworthy report is the smallest thing that demonstrates value. Deterministic checks make results defensible.

## Consequences and limitations
- Results only say something about the tasks we wrote; task design quality matters a lot.
- Read-only tasks miss failure modes in state-changing workflows (deferred).
