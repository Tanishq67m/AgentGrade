# 0007. Agent loop design (Milestone 1)

- **Status:** Accepted - amended by [0008](0008-thinking-models.md) (local model, `think` default)
- **Date:** 2026-10-21
- **Decided by:** Tanishq (delegated: "based on your recommendation take the decision")

## Problem
How should the core agent loop, its data types and the first real model adapter be built?

## Decisions

| Question | Options | Choice | Why |
|---|---|---|---|
| Sync or async loop | sync now, async later / **async now** | **async** | The MCP Python SDK (M2) is async; writing sync now means rewriting the loop next milestone. |
| Data types | dataclasses / **Pydantic** | **Pydantic** for messages, responses, results | Validation + JSON serialization for traces (M3) and suite files (M4). `Tool` itself stays a dataclass because it holds a Python function. |
| Tool argument validation | hand-written checks / Pydantic per tool / **jsonschema** | **jsonschema** (Draft 2020-12) | MCP tools arrive as raw JSON Schema (M2), so the same validator works for in-process and MCP tools. |
| Bad tool calls (unknown tool, invalid args, tool exception) | end the run / **feed the error back** | **feed back as an `ERROR (...)` tool result** | Recovery from mistakes is exactly what AgentGrade measures. Each error is still recorded with a type. |
| Ollama client | official `ollama` lib / OpenAI-compatible SDK / **httpx** | **httpx** against `/api/chat` | Exact JSON visible (learning goal); we already own the adapter interface. |
| Async tests | anyio plugin / **pytest-asyncio** | **pytest-asyncio**, `asyncio_mode = "auto"` | Most common choice; no decorators needed. |
| Local model (8 GB RAM Mac) | qwen3:4b / llama3.2:3b / others | **qwen3:4b** default, `llama3.2:3b` fallback | Small enough for 8 GB; tool-capable on Ollama. Confirm with `ollama show qwen3:4b` (look for `tools` under Capabilities). |

New dependencies: `pydantic`, `httpx`, `jsonschema` (runtime); `pytest-asyncio` (dev).

## Consequences and limitations
- Model/provider exceptions (e.g. Ollama not running) are **not** caught by the runner - they surface immediately. Per-run error handling for whole suites belongs to M5.
- `max_steps` is the only limit so far; token/time/cost limits come later.
- Ollama does not document tool-call IDs, so the adapter generates them.
- 3-4B local models are weak at tool use. Fine for development; results must always be labelled with the model name, and not presented as frontier-model behaviour.
