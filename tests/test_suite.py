"""Suite files: validation catches mistakes before any run starts."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agentgrade.suite import Suite, load_suite

BASE = {
    "name": "s",
    "model": {"name": "m"},
    "server": {"command": "x"},
    "tools": ["read", "list"],
    "tasks": [{"id": "t1", "prompt": "p", "checks": [{"type": "answer_number", "expected": 1}]}],
}


def make(**changes) -> Suite:
    return Suite.model_validate({**BASE, **changes})


def test_defaults():
    suite = make()
    assert [v.name for v in suite.variants] == ["baseline"]
    assert suite.repeats == 3 and suite.max_steps == 10
    assert suite.tools_for(suite.variants[0]) == ["read", "list"]


# fmt: off
@pytest.mark.parametrize(
    "changes, message",
    [
        ({"variants": [{"name": "v", "tools": ["write"]}]}, "outside the suite allowlist"),
        ({"variants": [{"name": "v", "tools": ["read"], "description_overrides": {"list": "x"}}]},
         "doesn't use"),
        ({"variants": [{"name": "a"}, {"name": "a"}]}, "Duplicate variant name"),
        ({"tasks": [{"id": "t", "prompt": "p", "checks": []}]}, "at least 1"),
        ({"tasks": [{"id": "t", "prompt": "p", "checks": [{"type": "tool_called", "tool": "write"}]}]},
         "not in allowlist"),
        ({"tasks": [{"id": "t", "prompt": "p", "checks": [{"type": "answer_numbr", "expected": 1}]}]},
         "does not match any of the expected tags"),
        ({"repats": 5}, "Extra inputs are not permitted"),  # typo in a key fails loudly
    ],
)
# fmt: on
def test_invalid_suites_are_rejected(changes, message):
    with pytest.raises(ValidationError, match=message):
        make(**changes)


def test_load_suite_resolves_fixture_relative_to_the_file(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "s.yaml").write_text(
        "name: s\nmodel: {name: m}\nserver: {command: x, fixture: data}\ntools: [read]\n"
        "tasks: [{id: t, prompt: p, checks: [{type: answer_contains, expected: hi}]}]\n"
    )
    assert load_suite(tmp_path / "s.yaml").server.fixture == (tmp_path / "data").resolve()


def test_missing_fixture_directory_is_an_error(tmp_path: Path):
    (tmp_path / "s.yaml").write_text(
        "name: s\nmodel: {name: m}\nserver: {command: x, fixture: nope}\ntools: [read]\n"
        "tasks: [{id: t, prompt: p, checks: [{type: answer_contains, expected: hi}]}]\n"
    )
    with pytest.raises(ValueError, match="Fixture directory not found"):
        load_suite(tmp_path / "s.yaml")


def test_the_shipped_shop_suite_is_valid():
    suite = load_suite(Path(__file__).parents[1] / "suites" / "shop.yaml")
    assert suite.server.fixture.is_dir()
    assert {v.name for v in suite.variants} >= {"baseline"}
