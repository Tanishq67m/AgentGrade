# Architecture Decision Records

Each file records one meaningful decision: the problem, the options, the trade-offs, the choice and its consequences.

Status values: **Proposed** (draft, awaiting Tanishq's approval) · **Accepted** · **Superseded by NNNN**.
An accepted record is never edited to change the decision - write a new record that supersedes it.

| # | Decision | Status |
|---|---|---|
| [0001](0001-mvp-scope.md) | MVP scope: MCP stdio servers, trusted targets, read-only tasks, deterministic validation | Accepted |
| [0002](0002-architecture-cli-and-files.md) | Modular monolith, CLI + file-based results first; FastAPI/Postgres/React deferred | Accepted |
| [0003](0003-python-tooling.md) | Python 3.12, uv, pytest, ruff, src layout | Accepted |
| [0004](0004-model-provider.md) | Free local models via Ollama behind our own adapter interface; paid providers later | Accepted |
| [0005](0005-mvp-execution-isolation.md) | MVP isolation: trusted servers + fixture data only, no Docker yet | Accepted |
| [0006](0006-repository-and-license.md) | Public GitHub repo, owner pushes manually, MIT license | Accepted |
| [0007](0007-agent-loop-design.md) | Async agent loop, Pydantic types, jsonschema validation, errors fed back, httpx Ollama adapter | Accepted (amended by 0008) |
| [0008](0008-thinking-models.md) | Separate model reasoning from answers; default model `qwen3:4b-instruct` | Accepted |
| [0009](0009-mcp-client.md) | Official MCP SDK v2, MCP tools adapted into `Tool`, explicit read-only allowlist, pinned server | Accepted |
| [0010](0010-run-tracing.md) | JSONL run traces, environment + model digest capture, whole-word secret redaction, numeric answer check | Accepted |
| [0011](0011-suites-variants-reports.md) | YAML suites, one-change variants (tool subset / description overrides), repeats, failure classification, Wilson-interval reports | Accepted |
| [0012](0012-taxonomy-and-variants-from-first-suite-run.md) | `gave_up` category, re-derivable categories (`agentgrade report`), ablation variants, agent-side `system_prompt_suffix` | Accepted |
| [0013](0013-openai-compatible-models.md) | One OpenAI-compatible adapter (Groq/Cerebras/OpenRouter/OpenAI), model config files, 429 handling, keys via env | Accepted |
| [0014](0014-second-server-git.md) | Second server: mcp-server-git, suite `setup` step, deterministic git fixture, server logs to file, `{root}` in prompts | Accepted |

Template: [TEMPLATE.md](TEMPLATE.md)
