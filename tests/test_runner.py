"""The agent loop, driven by a scripted model so every scenario is deterministic."""

import pytest

from agentgrade.models.fake import ScriptedModel, ScriptExhaustedError, call_tool, final_answer
from agentgrade.runner import RunLimits, run_agent
from agentgrade.types import Usage

TASK = "What is the shipping cost for order A17?"


async def test_two_tool_task_reaches_final_answer(registry, counter):
    model = ScriptedModel(
        [
            call_tool("lookup_order", order_id="A17"),
            call_tool("get_shipping_cost", country="IN", weight_kg=2.0),
            final_answer("12.50 USD"),
        ]
    )

    result = await run_agent(model, registry, TASK)

    assert result.stop_reason == "final_answer"
    assert result.final_answer == "12.50 USD"
    assert len(result.steps) == 3
    assert counter.counts == {"lookup_order": 1, "get_shipping_cost": 1}
    # Conversation shape: system, user, (assistant, tool) x2, assistant
    assert [m.role for m in result.messages] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
        "tool",
        "assistant",
    ]


async def test_tool_results_are_fed_back_to_the_model(registry):
    model = ScriptedModel([call_tool("lookup_order", order_id="A17"), final_answer("done")])

    await run_agent(model, registry, TASK)

    second_call_messages = model.received[1]
    tool_message = second_call_messages[-1]
    assert tool_message.role == "tool"
    assert tool_message.tool_name == "lookup_order"
    assert '"country": "IN"' in tool_message.content
    # the tool message answers the exact call the model made
    assert tool_message.tool_call_id == second_call_messages[-2].tool_calls[0].id


async def test_max_steps_stops_a_looping_model(registry):
    looping = ScriptedModel([call_tool("lookup_order", order_id="A17") for _ in range(10)])

    result = await run_agent(looping, registry, TASK, limits=RunLimits(max_steps=3))

    assert result.stop_reason == "max_steps"
    assert result.final_answer is None
    assert len(result.steps) == 3
    assert len(looping.received) == 3  # the model was not called a 4th time


async def test_unknown_tool_error_is_shown_to_model_which_can_recover(registry):
    model = ScriptedModel(
        [
            call_tool("track_parcel", order_id="A17"),
            call_tool("lookup_order", order_id="A17"),
            final_answer("IN, 2 kg"),
        ]
    )

    result = await run_agent(model, registry, TASK)

    first = result.steps[0].tool_results[0]
    assert first.error_type == "unknown_tool"
    assert model.received[1][-1].content.startswith("ERROR (unknown_tool)")
    assert result.stop_reason == "final_answer"


async def test_invalid_arguments_are_rejected_before_execution(registry, counter):
    model = ScriptedModel(
        [call_tool("get_shipping_cost", country="IN", weight_kg="two"), final_answer("unknown")]
    )

    result = await run_agent(model, registry, TASK)

    assert result.steps[0].tool_results[0].error_type == "invalid_arguments"
    assert "get_shipping_cost" not in counter.counts


async def test_usage_is_summed_across_steps(registry):
    model = ScriptedModel(
        [
            call_tool(
                "lookup_order", usage=Usage(input_tokens=100, output_tokens=10), order_id="A17"
            ),
            final_answer("ok", usage=Usage(input_tokens=150, output_tokens=5)),
        ]
    )

    result = await run_agent(model, registry, TASK)

    assert result.usage == Usage(input_tokens=250, output_tokens=15)


async def test_model_errors_are_not_swallowed(registry):
    model = ScriptedModel([])  # no responses -> the "model" fails on the first call

    with pytest.raises(ScriptExhaustedError):
        await run_agent(model, registry, TASK)


async def test_thinking_is_kept_in_steps_but_not_sent_back_or_used_as_answer(registry):
    from agentgrade.types import ModelResponse

    model = ScriptedModel(
        [
            ModelResponse(
                thinking="I should look up the order first.",
                tool_calls=call_tool("lookup_order", order_id="A17").tool_calls,
            ),
            ModelResponse(thinking="2 kg * 6.25 = 12.5", content="12.5 USD"),
        ]
    )

    result = await run_agent(model, registry, TASK)

    assert result.final_answer == "12.5 USD"
    assert result.steps[0].response.thinking == "I should look up the order first."
    sent_back = " ".join(m.content for m in model.received[1])
    assert "look up the order first" not in sent_back


def test_regression_fake_call_tool_accepts_an_argument_called_name():
    # Bug found in M2: call_tool("read_note", name="todo") raised
    # "got multiple values for argument 'name'".
    response = call_tool("read_note", name="todo")
    assert response.tool_calls[0].name == "read_note"
    assert response.tool_calls[0].arguments == {"name": "todo"}


async def test_rate_limit_wait_is_excluded_from_latency_and_traced(registry, tmp_path):
    from agentgrade.trace import TraceWriter, read_trace
    from agentgrade.types import ModelResponse

    model = ScriptedModel([ModelResponse(content="12.5", rate_limit_wait_ms=5_000)])
    with TraceWriter.create(tmp_path, run_id="r") as trace:
        result = await run_agent(model, registry, TASK, trace=trace)
    assert result.steps[0].model_latency_ms < 1_000  # not inflated by the 5 s queue wait
    assert read_trace(trace.path)[1]["rate_limit_wait_ms"] == 5_000
