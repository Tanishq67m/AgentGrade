# 0009. MCP client (Milestone 2)

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (delegated: "based on your recommendation take the decision")

## Problem
Connect to MCP servers over stdio, discover their tools, and expose them to the M1 agent loop
without breaking the read-only / trusted-only rules of ADR 0005.

## Decisions

| Question | Options | Choice | Why |
|---|---|---|---|
| SDK | official `mcp` Python SDK / hand-written JSON-RPC | **official `mcp` v2 (`>=2.3,<3`)** | Protocol handshake, version negotiation, pagination and process shutdown are already solved and maintained. v2's `Client` API differs from v1, so the version is bounded. |
| Integration point | new runner for MCP / **adapt MCP tools into `Tool`** | **`McpConnection.agent_tools()` returns normal `Tool`s** | The M1 runner and `ToolRegistry` work unchanged; schema validation runs before anything reaches the server. |
| Which tools the model sees | everything / filter by server hints / **explicit allowlist** | **explicit allowlist + read-only check** | `readOnlyHint` comes from the server, which is untrusted input. The allowlist is the real control. Allowlisted tools without `readOnlyHint: true` are refused unless `allow_non_read_only=True`. Typos in the allowlist fail loudly. |
| Test target | official filesystem server only / **own Python fixture server + official server for the demo** | **both** | `tests/fixtures/notes_server.py` is deterministic, needs no Node.js and runs as a real stdio subprocess. The official server proves it works on a real third-party server. |
| Real server version | `latest` / **pinned** | **`@modelcontextprotocol/server-filesystem@2.0.0`** | A moving tag can silently change what we evaluate (lesson from ADR 0008). |
| Data the server sees | the repo / **a temp copy of `fixtures/shop`** | **temp copy** | Even if a write slipped through, it would only touch a throwaway folder. |
| Tool results | everything / **text only** | **text; other content types replaced by `[<type> content omitted]`** | MVP tasks are text. Explicit placeholders mean a model never silently gets nothing. |
| JSON Schema draft | 2020-12 only / **honour `$schema`** | **`validator_for(schema)`, default 2020-12** | MCP servers commonly send draft-07 schemas. |

## Consequences and limitations
- Tool descriptions from the server go straight into the model prompt: a malicious server could
  attempt prompt injection. Acceptable only because MVP servers are trusted (ADR 0005).
- The SDK passes the server only a minimal environment (HOME, PATH, ...). Servers that need extra
  env vars must get them via `McpServerConfig.env`.
- If the server process dies during startup, the client currently waits for the full
  `initialize` timeout before reporting it (observed: 60 s). Early-exit detection is a later improvement.
- stdio transport only; HTTP transports are out of the MVP.
- The real server listed 14 tools while its README lists 13 (an extra, deprecated `read_file`).
  Live behaviour, not documentation, is the source of truth.
