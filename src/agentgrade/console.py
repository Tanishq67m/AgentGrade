"""Human-readable printing of a run (the trace file is the full record)."""

from __future__ import annotations

from agentgrade.runner import RunResult


def print_run(result: RunResult) -> None:
    print(f"\nModel: {result.model}\nTask:  {result.task}\n")
    for step in result.steps:
        print(f"--- step {step.index}  ({step.model_latency_ms:.0f} ms)")
        if step.response.thinking:
            print(f"  (model reasoning hidden: {len(step.response.thinking)} chars)")
        if step.response.content:
            print(f"  model says: {step.response.content.strip()}")
        for call, outcome in zip(step.response.tool_calls, step.tool_results, strict=False):
            status = "ok" if outcome.ok else outcome.error_type
            content = (
                outcome.content if len(outcome.content) <= 300 else outcome.content[:300] + " ..."
            )
            print(f"  tool call:  {call.name}({call.arguments})")
            print(f"  result:     [{status}] {content}")
    print(f"\nStop reason:  {result.stop_reason}")
    print(f"Final answer: {result.final_answer!r}")
    print(f"Tokens:       {result.usage.input_tokens} in / {result.usage.output_tokens} out")
    print(f"Duration:     {result.duration_ms / 1000:.1f} s")
