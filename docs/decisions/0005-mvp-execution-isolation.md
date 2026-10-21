# 0005. MVP execution isolation

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (approved the proposed MVP)

## Problem
A stdio MCP server is a local subprocess running with the user's permissions. What isolation does the MVP need?

## Options considered
1. **Trusted servers only + fixture data + read-only tasks**, plain subprocess.
2. Docker container per run with restricted network.
3. Full sandbox (VM/gVisor/firecracker).

## Trade-offs
- Option 1 is simple and enough when we run only well-known reference servers on throwaway fixture folders. It is **not** safe for arbitrary servers.
- Docker/sandboxing adds real security but also setup complexity that the MVP doesn't need yet.

## Decision
Option 1 for the MVP:
- Only trusted, well-known servers, configured explicitly in the suite file.
- Servers get only a fixture directory created for the run.
- Read-only tasks only.
- Tool arguments validated against the tool's JSON schema; tool descriptions, results and model output treated as untrusted input.
- Secrets never written to traces (redaction in the trace recorder).

## Rationale
Matches the risk of the MVP without adding infrastructure.

## Consequences and limitations
- **Hard rule:** before AgentGrade runs any server not personally vetted (e.g. user-submitted), isolation must be redesigned in a new ADR. This record does not cover that case.
