# 0004. Model provider: free local models first

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq ("keep everything free for now, paid later")

## Problem
The agent loop needs an LLM with tool calling. Budget is zero for now.

## Options considered
1. **Ollama** running an open-weight, tool-calling model locally.
2. Free tiers of hosted APIs (rate-limited, terms can change).
3. Paid API (Anthropic/OpenAI) - not allowed for now.

## Trade-offs
- Ollama: free, unlimited runs, no API key, fully reproducible (pinned model + version). Small local models are weaker at tool use and slower on a laptop.
- Free hosted tiers: stronger models, but rate limits break repeated runs, and benchmark reproducibility depends on someone else's free tier.

## Decision
- Use **Ollama** locally for development and early evaluations.
- All model access goes through **our own small `ModelAdapter` interface**, so adding a paid provider later is a new adapter, not a rewrite.
- Unit tests use a **scripted fake model** (zero cost, deterministic).
- The specific local model and the client library are decided in Milestone 1.

## Rationale
Zero cost and reproducible. A weaker model is acceptable - it actually surfaces more tool-usability failures - as long as every report states which model was used.

## Consequences and limitations
- Early results reflect small-model behaviour and must be labelled with model name and version; they must not be presented as how frontier models behave.
- Requires Ollama installed and enough RAM for the chosen model.
