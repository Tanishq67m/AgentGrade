# 0008. Handling "thinking" models; default local model changed

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (approved after the first real demo run)
- **Amends:** [0007](0007-agent-loop-design.md) - the "Local model" row and the adapter's `think` default

## Problem
First real run (`qwen3:4b`, 2026-10-21): the task passed, but the model's whole reasoning
monologue ended up in `final_answer`, and our "contains 12.5" check still passed.

Root cause (confirmed): on Ollama, `qwen3:4b` has the same digest (`359d7dd4bcda`) as
`qwen3:4b-thinking-2507`, an always-thinking model. It ignores `"think": false`. Its chat template
inserts the opening `<think>` itself, so the output held reasoning + only a closing `</think>` +
the answer. The adapter treated all of `content` as the answer.

## Options considered
1. Only switch to a non-thinking model.
2. Only fix the adapter.
3. Both.

## Decision
Option 3:
- Default demo model: **`qwen3:4b-instruct`** (non-thinking, same 2.5 GB size).
- `ModelResponse` gets a **`thinking`** field. The adapter fills it from Ollama's `message.thinking`,
  and from any reasoning leaked into `content` before the last `</think>`.
- Reasoning is kept in step records (useful for explaining failures) but is **never** sent back into
  the conversation and **never** treated as the answer.
- The adapter's `think` default changes from `False` to `None` (don't send the option unless chosen),
  because always-thinking models ignore it anyway.
- Regression tests reproduce the exact leaked output.

## Consequences and limitations
- The `</think>` split is a model-specific workaround; other model families may need their own.
- **Lesson for M4:** substring checks ("contains 12.5") are too weak; validators must run on the
  clean answer and be stricter (e.g. extract the number and compare exactly).
- Model load time isn't recorded separately yet (step 1 took 134 s, including a cold load). Record
  Ollama's `load_duration` in M3 traces.
