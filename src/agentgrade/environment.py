"""Capture the environment a run happened in, so results can be reproduced and compared.

Everything here is best-effort: a missing tool (no git, no node) is recorded as None,
never an error.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

import agentgrade

PACKAGES = ("mcp", "pydantic", "httpx", "jsonschema")


def collect_environment(repo_dir: Path | None = None) -> dict[str, Any]:
    return {
        "agentgrade_version": agentgrade.__version__,
        "python": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "packages": {name: _package_version(name) for name in PACKAGES},
        "node": _command_output(["node", "--version"]),
        "git": _git_info(repo_dir),
    }


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _command_output(cmd: list[str], cwd: Path | None = None) -> str | None:
    if shutil.which(cmd[0]) is None:
        return None
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10, check=True)
    except (subprocess.SubprocessError, OSError):
        return None
    return out.stdout.strip()


def _git_info(repo_dir: Path | None) -> dict[str, Any] | None:
    commit = _command_output(["git", "rev-parse", "HEAD"], cwd=repo_dir)
    if commit is None:
        return None
    status = _command_output(["git", "status", "--porcelain"], cwd=repo_dir)
    # "dirty" = uncommitted changes: the code that ran is NOT exactly this commit
    return {"commit": commit, "dirty": bool(status)}
