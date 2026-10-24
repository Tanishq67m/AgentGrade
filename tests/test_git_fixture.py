"""The git fixture is deterministic and its ground truth matches suites/git.yaml.

If someone edits build_repo.py and changes an answer, these tests fail before any agent
is graded against a wrong expected value.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agentgrade.suite import AnswerContainsCheck, load_suite

ROOT = Path(__file__).parents[1]
BUILD = ROOT / "fixtures" / "git_repo" / "build_repo.py"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def build(path: Path) -> Path:
    subprocess.run([sys.executable, str(BUILD), str(path)], check=True)
    return path


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True,
                          text=True).stdout.strip()  # fmt: skip


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> Path:
    return build(tmp_path_factory.mktemp("git") / "repo")


def test_builds_are_byte_identical(repo, tmp_path):
    again = build(tmp_path / "again")
    assert git(repo, "rev-parse", "HEAD") == git(again, "rev-parse", "HEAD")
    assert git(repo, "rev-parse", "feature/discounts") == git(
        again, "rev-parse", "feature/discounts"
    )


def test_ground_truth(repo):
    assert git(repo, "branch", "--show-current") == "main"
    assert git(repo, "log", "-1", "--format=%an|%s", "main") == "Ben Okafor|Bump version to 1.1.0"
    fix = git(repo, "log", "--format=%an", "--grep=rounding bug", "main")
    assert fix == "Chen Li"
    assert git(repo, "show", "HEAD:VERSION") == "1.1.0"
    assert git(repo, "status", "--porcelain") == "M README.md"
    assert git(repo, "branch", "--no-merged", "main") == "feature/discounts"


def test_suite_expectations_match_the_fixture():
    suite = load_suite(ROOT / "suites" / "git.yaml")
    expected = {t.id: [c.expected for c in t.checks if isinstance(c, AnswerContainsCheck)]
                for t in suite.tasks}  # fmt: skip
    assert expected == {
        "last_commit_author": ["Ben"],
        "rounding_fix_author": ["Chen"],
        "current_version": ["1.1.0"],
        "uncommitted_file": ["README"],
        "unmerged_branch": ["feature/discounts"],
    }
    # {suite_dir} was resolved at load time and points at the real build script
    setup_script = Path(suite.server.setup[0][1]).resolve()
    assert setup_script == BUILD.resolve()
