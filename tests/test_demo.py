"""The demo's tools + ground truth, run through the real runner with a scripted model."""

from agentgrade.demo import EXPECTED, TASK, build_registry
from agentgrade.models.fake import ScriptedModel, call_tool, final_answer
from agentgrade.runner import run_agent


async def test_demo_tools_produce_the_expected_ground_truth():
    model = ScriptedModel(
        [
            call_tool("lookup_order", order_id="A17"),
            call_tool("get_shipping_cost", country="IN", weight_kg=2.0),
            final_answer("12.5 USD"),
        ]
    )
    result = await run_agent(model, build_registry(), TASK)

    cost_result = result.steps[1].tool_results[0]
    assert cost_result.ok
    assert '"cost_usd": 12.5' in cost_result.content
    assert EXPECTED in result.final_answer
