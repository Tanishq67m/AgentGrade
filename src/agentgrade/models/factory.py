"""Build a model adapter from a ModelConfig."""

from __future__ import annotations

from agentgrade.models.base import ModelAdapter
from agentgrade.models.ollama import OllamaModel
from agentgrade.models.openai_compat import OpenAICompatModel
from agentgrade.suite import ModelConfig


def build_model(config: ModelConfig) -> ModelAdapter:
    if config.provider == "ollama":
        return OllamaModel(config.name, temperature=config.temperature)
    return OpenAICompatModel.from_env(
        config.name,
        base_url=config.base_url,
        api_key_env=config.api_key_env,
        temperature=config.temperature,
        requests_per_minute=config.requests_per_minute,
    )
