"""The agent loop: model asks -> we validate & run tools -> feed results back -> repeat.

Stops when the model answers without requesting tools, or when it hits max_steps.
One "step" = one model call.
"""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field

from agentgrade.models.base import ModelAdapter
from agentgrade.tools import ToolRegistry, ToolResult
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
) -> RunResult:
    limits = limits or RunLimits()
    messages = [Message(role="system", content=system_prompt), Message(role="user", content=task)]
    steps: list[StepRecord] = []
    usage = Usage()
    run_start = time.perf_counter()

    for index in range(1, limits.max_steps + 1):
        call_start = time.perf_counter()
        response = await model.complete(messages, tools.specs())
        latency_ms = (time.perf_counter() - call_start) * 1000
        usage = usage + response.usage

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
            result = await tools.execute(call)
            step.tool_results.append(result)
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
