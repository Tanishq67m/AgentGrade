"""M1 demo: run one task with two in-process tools against a local Ollama model.

Usage:
    uv run python -m agentgrade.demo --model qwen3:4b-instruct

This is a manual check, not a test - real models don't behave identically every run.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from agentgrade.checks import answer_has_number
from agentgrade.console import print_run
from agentgrade.models.ollama import OllamaError, OllamaModel
from agentgrade.runner import RunLimits, run_agent
from agentgrade.tools import Tool, ToolRegistry

ORDERS = {
    "A17": {"order_id": "A17", "country": "IN", "weight_kg": 2.0},
    "B42": {"order_id": "B42", "country": "US", "weight_kg": 0.5},
}
RATE_PER_KG_USD = {"IN": 6.25, "US": 9.00}

TASK = "What is the shipping cost in USD for order A17?"
EXPECTED = 12.5  # ground truth: 2.0 kg * 6.25 USD/kg


def lookup_order(order_id: str) -> dict:
    if order_id not in ORDERS:
        raise KeyError(f"No order with id {order_id!r}")
    return ORDERS[order_id]


def get_shipping_cost(country: str, weight_kg: float) -> dict:
    if country not in RATE_PER_KG_USD:
        raise KeyError(f"No shipping rate for country {country!r}")
    return {
        "country": country,
        "weight_kg": weight_kg,
        "cost_usd": RATE_PER_KG_USD[country] * weight_kg,
    }


def build_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            Tool(
                name="lookup_order",
                description="Look up an order by its ID. Returns destination country and weight.",
                input_schema={
                    "type": "object",
                    "properties": {"order_id": {"type": "string", "description": "e.g. A17"}},
                    "required": ["order_id"],
                    "additionalProperties": False,
                },
                func=lookup_order,
            ),
            Tool(
                name="get_shipping_cost",
                description="Get the shipping cost in USD for a destination country and weight.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "country": {"type": "string", "description": "ISO country code, e.g. IN"},
                        "weight_kg": {"type": "number"},
                    },
                    "required": ["country", "weight_kg"],
                    "additionalProperties": False,
                },
                func=get_shipping_cost,
            ),
        ]
    )


async def main(model_name: str, max_steps: int) -> int:
    model = OllamaModel(model_name, temperature=0)
    try:
        result = await run_agent(
            model, build_registry(), TASK, limits=RunLimits(max_steps=max_steps)
        )
    except OllamaError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        await model.aclose()
    print_run(result)
    passed = answer_has_number(result.final_answer, EXPECTED)
    print(f"Check:        answer contains the number {EXPECTED} -> {'PASS' if passed else 'FAIL'}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentGrade M1 demo (local Ollama model)")
    parser.add_argument("--model", default="qwen3:4b-instruct")
    parser.add_argument("--max-steps", type=int, default=6)
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.model, args.max_steps)))
