"""Shared test fixtures."""

import pytest

from agentgrade.tools import Tool, ToolRegistry

ORDERS = {"A17": {"country": "IN", "weight_kg": 2.0}}


class CallCounter:
    """Spy that records how many times each tool function actually ran."""

    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def hit(self, name: str) -> None:
        self.counts[name] = self.counts.get(name, 0) + 1


@pytest.fixture
def counter() -> CallCounter:
    return CallCounter()


@pytest.fixture
def registry(counter: CallCounter) -> ToolRegistry:
    def lookup_order(order_id: str) -> dict:
        counter.hit("lookup_order")
        if order_id not in ORDERS:
            raise KeyError(f"order {order_id} not found")
        return ORDERS[order_id]

    async def get_shipping_cost(country: str, weight_kg: float) -> dict:
        counter.hit("get_shipping_cost")
        return {"country": country, "weight_kg": weight_kg, "cost_usd": 6.25 * weight_kg}

    return ToolRegistry(
        [
            Tool(
                name="lookup_order",
                description="Look up an order by ID.",
                input_schema={
                    "type": "object",
                    "properties": {"order_id": {"type": "string"}},
                    "required": ["order_id"],
                    "additionalProperties": False,
                },
                func=lookup_order,
            ),
            Tool(
                name="get_shipping_cost",
                description="Shipping cost in USD for a country and weight.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "country": {"type": "string"},
                        "weight_kg": {"type": "number"},
                    },
                    "required": ["country", "weight_kg"],
                    "additionalProperties": False,
                },
                func=get_shipping_cost,
            ),
        ]
    )
