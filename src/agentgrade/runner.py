"""The agent loop: model asks -> we validate & run tools -> feed results back -> repeat.

Stops when the model answers without requesting tools, or when it hits max_steps.
One "step" = one model call.
"""

from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from agentgrade.models.base import ModelAdapter
from agentgrade.tools import ToolRegistry, ToolResult
from agentgrade.trace import TraceWriter
from agentgrade.types import Message, ModelResponse, Usage

StopReason = Literal["final_answer", "max_steps"]

DEFAULT_SYSTEM_PROMPT = (
    "You are an agent that completes tasks by calling the provided tools. "
    "Use tools to look up facts instead of guessing. "
    "When you have enough information, reply with the final answer only."
)


class RunLimits(BaseModel):
    max_steps: int = Field(default=8, ge=1)


class StepRecord(BaseModel):
    index: int
    response: ModelResponse
    tool_results: list[ToolResult] = Field(default_factory=list)
    model_latency_ms: float


class RunResult(BaseModel):
    model: str
    task: str
    stop_reason: StopReason
    final_answer: str | None
    steps: list[StepRecord]
    messages: list[Message]
    usage: Usage
    duration_ms: float


async def run_agent(
    model: ModelAdapter,
    tools: ToolRegistry,
    task: str,
    *,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    limits: RunLimits | None = None,
    trace: TraceWriter | None = None,
    metadata: dict[str, Any] | None = None,
) -> RunResult:
    """Run one task. If `trace` is given, every event is written to it as it happens."""
    limits = limits or RunLimits()
    if trace:
        trace.event(
            "run_started",
            run_id=trace.run_id,
            model=model.name,
            task=task,
            system_prompt=system_prompt,
            limits=limits.model_dump(),
            tools=[spec.model_dump() for spec in tools.specs()],
            metadata=metadata or {},
        )
    try:
        result = await _loop(model, tools, task, system_prompt, limits, trace)
    except BaseException as exc:
        # Record, then re-raise: a crash must be visible in the trace AND to the caller.
        if trace:
            trace.event("run_failed", error_type=type(exc).__name__, error=str(exc))
        raise
    if trace:
        trace.event(
            "run_finished",
            stop_reason=result.stop_reason,
            final_answer=result.final_answer,
            steps=len(result.steps),
            usage=result.usage.model_dump(),
            duration_ms=result.duration_ms,
        )
    return result


async def _loop(
    model: ModelAdapter,
    tools: ToolRegistry,
    task: str,
    system_prompt: str,
    limits: RunLimits,
    trace: TraceWriter | None,
) -> RunResult:
    messages = [Message(role="system", content=system_prompt), Message(role="user", content=task)]
    steps: list[StepRecord] = []
    usage = Usage()
    run_start = time.perf_counter()

    for index in range(1, limits.max_steps + 1):
        call_start = time.perf_counter()
        response = await model.complete(messages, tools.specs())
        # rate-limit waits are the provider's queue, not the model's speed
        elapsed_ms = (time.perf_counter() - call_start) * 1000
        latency_ms = max(elapsed_ms - response.rate_limit_wait_ms, 0.0)
        usage = usage + response.usage
        if trace:
            trace.event(
                "model_call",
                step=index,
                latency_ms=latency_ms,
                rate_limit_wait_ms=response.rate_limit_wait_ms,
                provider_meta=response.provider_meta,
                usage=response.usage.model_dump(),
                content=response.content,
                thinking=response.thinking,
                tool_calls=[c.model_dump() for c in response.tool_calls],
            )

        messages.append(
            Message(role="assistant", content=response.content, tool_calls=response.tool_calls)
        )
        step = StepRecord(index=index, response=response, model_latency_ms=latency_ms)
        steps.append(step)

        if not response.tool_calls:
            return _result(
                model, task, "final_answer", response.content, steps, messages, usage, run_start
            )

        for call in response.tool_calls:
            tool_start = time.perf_counter()
            result = await tools.execute(call)
            result = result.model_copy(
                update={"latency_ms": (time.perf_counter() - tool_start) * 1000}
            )
            step.tool_results.append(result)
            if trace:
                trace.event(
                    "tool_result",
                    step=index,
                    call_id=call.id,
                    tool_name=call.name,
                    arguments=call.arguments,
                    ok=result.ok,
                    error_type=result.error_type,
                    content=result.content,
                    latency_ms=result.latency_ms,
                )
            messages.append(
                Message(
                    role="tool",
                    content=result.content,
                    tool_call_id=call.id,
                    tool_name=call.name,
                )
            )

    return _result(model, task, "max_steps", None, steps, messages, usage, run_start)


def _result(
    model: ModelAdapter,
    task: str,
    stop_reason: StopReason,
    final_answer: str | None,
    steps: list[StepRecord],
    messages: list[Message],
    usage: Usage,
    run_start: float,
) -> RunResult:
    return RunResult(
        model=model.name,
        task=task,
        stop_reason=stop_reason,
        final_answer=final_answer,
        steps=steps,
        messages=messages,
        usage=usage,
        duration_ms=(time.perf_counter() - run_start) * 1000,
    )
