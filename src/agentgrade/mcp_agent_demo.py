"""M3: a local model solves a task using ONLY a real MCP server's tools, fully traced.

Usage (needs Ollama + Node.js):
    uv run python -m agentgrade.mcp_agent_demo
    uv run python -m agentgrade.mcp_agent_demo --model qwen3:4b-instruct --max-steps 12
    uv run python -m agentgrade.mcp_agent_demo --tools list_directory,directory_tree,read_text_file

The model gets the official filesystem server (read-only allowlist) on a throwaway copy of
fixtures/shop. It has to find the order, find the shipping rates, and compute the cost.
Every event is written to runs/<run_id>/trace.jsonl as it happens.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

from agentgrade.checks import answer_has_number
from agentgrade.console import print_run
from agentgrade.environment import collect_environment
from agentgrade.mcp_client import McpError, ToolPolicyError, connect
from agentgrade.models.ollama import OllamaError, OllamaModel
from agentgrade.runner import RunLimits, run_agent
from agentgrade.servers import (
    FILESYSTEM_READ_ONLY_TOOLS,
    FILESYSTEM_SERVER_PACKAGE,
    REPO_ROOT,
    SHOP_FIXTURE,
    filesystem_server,
)
from agentgrade.tools import ToolRegistry
from agentgrade.trace import TraceWriter

TASK_ID = "shop.shipping_cost_a17"
TASK = (
    "What is the shipping cost in USD for order A17? "
    "The order data and the shipping rates are in the files you can access."
)
EXPECTED = 12.5  # fixtures/shop: A17 weighs 2.0 kg to IN; IN rate is 6.25 USD/kg


def select_tools(requested: str | None) -> list[str]:
    """Narrow the read-only allowlist for an experiment. Can never widen it."""
    if not requested:
        return list(FILESYSTEM_READ_ONLY_TOOLS)
    names = [n.strip() for n in requested.split(",") if n.strip()]
    outside = [n for n in names if n not in FILESYSTEM_READ_ONLY_TOOLS]
    if outside:
        raise ValueError(
            f"Not in the read-only allowlist: {outside}. Allowed: {FILESYSTEM_READ_ONLY_TOOLS}"
        )
    return names


async def main(model_name: str, max_steps: int, runs_dir: Path, tool_names: list[str]) -> int:
    for tool in ("npx",):
        if shutil.which(tool) is None:
            print(
                f"Error: `{tool}` not found. Install Node.js (brew install node@24).",
                file=sys.stderr,
            )
            return 1

    model = OllamaModel(model_name, temperature=0)
    with tempfile.TemporaryDirectory(prefix="agentgrade-") as tmp:
        root = Path(tmp).resolve() / "shop"  # resolve(): macOS /var -> /private/var
        shutil.copytree(SHOP_FIXTURE, root)

        try:
            async with connect(filesystem_server(root)) as conn:
                registry = ToolRegistry(conn.agent_tools(tool_names))
                metadata = {
                    "task_id": TASK_ID,
                    "expected": EXPECTED,
                    "environment": collect_environment(REPO_ROOT),
                    "model_info": await model.describe(),
                    "server": {**conn.describe(), "package": FILESYSTEM_SERVER_PACKAGE},
                    "tool_allowlist": tool_names,
                    "sandbox_root": str(root),
                }
                with TraceWriter.create(runs_dir) as trace:
                    print(f"Trace: {trace.path}")
                    result = await run_agent(
                        model,
                        registry,
                        TASK,
                        limits=RunLimits(max_steps=max_steps),
                        trace=trace,
                        metadata=metadata,
                    )
                    passed = answer_has_number(result.final_answer, EXPECTED)
                    trace.event(
                        "check",
                        check="answer_has_number",
                        expected=EXPECTED,
                        passed=passed,
                    )
        except (McpError, ToolPolicyError, OllamaError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        finally:
            await model.aclose()

    print_run(result)
    print(f"Check:        answer contains the number {EXPECTED} -> {'PASS' if passed else 'FAIL'}")
    print(f"\nFull trace:   {trace.path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentGrade M3: local model + real MCP server")
    parser.add_argument("--model", default="qwen3:4b-instruct")
    parser.add_argument("--max-steps", type=int, default=10)
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument(
        "--tools",
        help="comma-separated subset of the read-only allowlist (experiments only)",
    )
    args = parser.parse_args()
    try:
        tools = select_tools(args.tools)
    except ValueError as exc:
        parser.error(str(exc))
    sys.exit(asyncio.run(main(args.model, args.max_steps, args.runs_dir, tools)))
