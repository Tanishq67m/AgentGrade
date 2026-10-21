"""Smoke test: proves the package is installed and importable.

If this fails, the problem is the project setup (pyproject, src layout, venv),
not any AgentGrade logic.
"""

import agentgrade


def test_package_imports_and_has_version() -> None:
    assert isinstance(agentgrade.__version__, str)
    assert agentgrade.__version__ != ""
