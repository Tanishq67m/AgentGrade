"""Model config files, the factory, and .env loading."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agentgrade.cli import load_dotenv
from agentgrade.models.factory import build_model
from agentgrade.models.ollama import OllamaModel
from agentgrade.models.openai_compat import OpenAICompatModel
from agentgrade.suite import ModelConfig, load_model_config

CONFIG_DIR = Path(__file__).parents[1] / "model_configs"


@pytest.mark.parametrize("path", sorted(CONFIG_DIR.glob("*.yaml")), ids=lambda p: p.name)
def test_shipped_model_configs_are_valid(path):
    load_model_config(path)


def test_openai_compatible_needs_a_base_url():
    with pytest.raises(ValidationError, match="base_url"):
        ModelConfig(provider="openai_compatible", name="m")


def test_a_pasted_key_instead_of_a_variable_name_is_rejected():
    with pytest.raises(ValidationError, match="NAME of an environment variable"):
        ModelConfig(
            provider="openai_compatible", name="m", base_url="https://x", api_key_env="gsk_abc123"
        )


def test_factory_builds_the_right_adapter(monkeypatch):
    assert isinstance(build_model(ModelConfig(name="qwen3:4b-instruct")), OllamaModel)
    monkeypatch.setenv("GROQ_API_KEY", "k")
    groq = load_model_config(CONFIG_DIR / "groq-gpt-oss-120b.yaml")
    assert isinstance(build_model(groq), OpenAICompatModel)


def test_load_dotenv_sets_missing_vars_only(tmp_path, monkeypatch):
    monkeypatch.setenv("AG_EXISTING", "from-shell")
    monkeypatch.delenv("AG_NEW", raising=False)
    monkeypatch.delenv("AG_QUOTED", raising=False)
    env = tmp_path / ".env"
    env.write_text('# comment\nAG_NEW=abc\nexport AG_QUOTED="q v"\nAG_EXISTING=from-file\n\n')
    load_dotenv(env)
    import os

    assert os.environ["AG_NEW"] == "abc"
    assert os.environ["AG_QUOTED"] == "q v"
    assert os.environ["AG_EXISTING"] == "from-shell"  # the shell wins


def test_load_dotenv_without_file_is_a_no_op(tmp_path):
    load_dotenv(tmp_path / "missing.env")
