# AgentGrade

**Can an AI agent successfully complete a real task using your product's tools - and can we explain why it succeeded or failed?**

AgentGrade runs an AI agent against an MCP server on a defined set of tasks, records every step,
checks the outcome with deterministic (code-based) validation, repeats each task to measure
variability, and reports success rate, failure types, latency, tokens and cost.

> Status: early development (Milestone 1 - agent loop). A demo runs one task against a local model.
> See [docs/STATUS.md](docs/STATUS.md) and [docs/decisions/](docs/decisions/).

## Development setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync          # creates .venv, installs Python 3.12 if needed, installs dev tools
uv run pytest    # run the tests
uv run ruff check .   # lint
uv run ruff format .  # auto-format
```

## Demo (free, local model)

Install [Ollama](https://ollama.com), then:

```bash
ollama pull qwen3:4b-instruct
uv run python -m agentgrade.demo --model qwen3:4b-instruct
```

## License

MIT
