"""ToolRegistry: validation happens before execution, and errors become data."""

import json

import pytest

from agentgrade.tools import Tool, ToolRegistry
from agentgrade.types import ToolCall


async def test_valid_call_runs_tool_and_returns_json(registry, counter):
    result = await registry.execute(
        ToolCall(id="1", name="lookup_order", arguments={"order_id": "A17"})
    )
    assert result.ok
    assert json.loads(result.content) == {"country": "IN", "weight_kg": 2.0}
    assert counter.counts == {"lookup_order": 1}


async def test_async_tool_function_is_awaited(registry):
    call = ToolCall(id="1", name="get_shipping_cost", arguments={"country": "IN", "weight_kg": 2})
    result = await registry.execute(call)
    assert result.ok
    assert json.loads(result.content)["cost_usd"] == 12.5


async def test_unknown_tool_is_reported_with_available_tools(registry):
    result = await registry.execute(ToolCall(id="1", name="track_parcel", arguments={}))
    assert not result.ok
    assert result.error_type == "unknown_tool"
    assert "get_shipping_cost, lookup_order" in result.content


@pytest.mark.parametrize(
    "arguments, expected_fragment",
    [
        ({}, "'order_id' is a required property"),
        ({"order_id": 17}, "order_id: 17 is not of type 'string'"),
        ({"order_id": "A17", "extra": 1}, "Additional properties are not allowed"),
    ],
)
async def test_invalid_arguments_never_reach_the_function(
    registry, counter, arguments, expected_fragment
):
    result = await registry.execute(ToolCall(id="1", name="lookup_order", arguments=arguments))
    assert not result.ok
    assert result.error_type == "invalid_arguments"
    assert expected_fragment in result.content
    assert counter.counts == {}  # the function never ran


async def test_exception_inside_tool_becomes_tool_error(registry):
    result = await registry.execute(
        ToolCall(id="1", name="lookup_order", arguments={"order_id": "ZZ"})
    )
    assert not result.ok
    assert result.error_type == "tool_error"
    assert "KeyError" in result.content


def test_duplicate_tool_names_are_rejected():
    tool = Tool(name="t", description="d", input_schema={"type": "object"}, func=lambda: None)
    with pytest.raises(ValueError, match="already registered"):
        ToolRegistry([tool, tool])


def test_broken_schema_is_rejected_at_registration():
    bad = Tool(name="t", description="d", input_schema={"type": "not-a-type"}, func=lambda: None)
    with pytest.raises(ValueError, match="Invalid input_schema"):
        ToolRegistry([bad])
