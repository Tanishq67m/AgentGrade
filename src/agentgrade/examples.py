"""The example suites, fixtures and model configs, for `agentgrade init`.

In an installed wheel they live in `agentgrade/examples/` (see pyproject's force-include).
In a source checkout they are the repo's own `suites/`, `fixtures/` and `model_configs/`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
EXAMPLE_SUITES = ["shop.yaml", "git.yaml", "memory.yaml", "sqlite.yaml", "time.yaml"]
EXAMPLE_FIXTURES = ["shop", "git_repo", "shop_sqlite", "team_memory"]


def examples_root() -> Path:
    bundled = PACKAGE_DIR / "examples"
    if (bundled / "suites").is_dir():
        return bundled
    checkout = PACKAGE_DIR.parents[1]  # src/agentgrade -> repo root
    if (checkout / "suites").is_dir() and (checkout / "fixtures").is_dir():
        return checkout
    raise FileNotFoundError("The example suites are not available in this installation.")


def copy_examples(dest: Path) -> list[Path]:
    """Copy the examples into `dest` (which must not exist or be empty). Returns the suites."""
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"{dest} already exists and is not empty")
    src = examples_root()
    (dest / "suites").mkdir(parents=True, exist_ok=True)
    suites = []
    for name in EXAMPLE_SUITES:
        shutil.copy2(src / "suites" / name, dest / "suites" / name)
        suites.append(dest / "suites" / name)
    for name in EXAMPLE_FIXTURES:
        shutil.copytree(
            src / "fixtures" / name,
            dest / "fixtures" / name,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    shutil.copytree(src / "model_configs", dest / "model_configs")
    return suites
