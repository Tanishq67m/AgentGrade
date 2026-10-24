"""Build the deterministic "shop-api" git repository used by suites/git.yaml.

    python build_repo.py <empty-or-new-directory>

Same names, emails, dates and file contents every time, so every run gets a repository with
IDENTICAL commit hashes. The user's own git config is ignored (no signing prompts, no hooks).

Ground truth (verified by tests/test_git_fixture.py):
  - most recent commit on main ..... "Bump version to 1.1.0" by Ben Okafor
  - rounding bug fixed by .......... Chen Li ("Fix rounding bug in shipping cost")
  - version at HEAD (VERSION) ...... 1.1.0
  - uncommitted change ............. README.md (modified, not staged)
  - branch not merged into main .... feature/discounts
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ASHA = ("Asha Rao", "asha@example.com")
BEN = ("Ben Okafor", "ben@example.com")
CHEN = ("Chen Li", "chen@example.com")

README = "# shop-api\n\nTiny order and shipping service.\n"
APP = (
    "from orders import shipping_cost\n\n"
    'if __name__ == "__main__":\n    print(shipping_cost("IN", 2.0))\n'
)
ORDERS_V1 = (
    "import json\n\nRATES = json.load(open('rates.json'))\n\n\n"
    "def shipping_cost(country, weight_kg):\n"
    "    return int(RATES[country] * weight_kg)  # truncates!\n"
)
ORDERS_V2 = (
    "import json\n\nRATES = json.load(open('rates.json'))\n\n\n"
    "def shipping_cost(country, weight_kg):\n"
    "    return round(RATES[country] * weight_kg, 2)\n"
)
RATES = '{"IN": 6.25, "US": 9.0}\n'

# (date, author, message, files)  - main branch history, oldest first
# fmt: off
MAIN = [
    ("2026-01-05T10:00:00+05:30", ASHA, "Initial commit: README and app skeleton",
     {"README.md": README, "app.py": APP}),
    ("2026-01-12T15:30:00+05:30", BEN, "Add order model", {"orders.py": ORDERS_V1}),
    ("2026-02-02T09:15:00+05:30", ASHA, "Add shipping rate table", {"rates.json": RATES}),
    ("2026-02-20T18:45:00+05:30", CHEN, "Fix rounding bug in shipping cost", {"orders.py": ORDERS_V2}),
    ("2026-03-03T11:00:00+05:30", BEN, "Bump version to 1.1.0", {"VERSION": "1.1.0\n"}),
]
# fmt: on
FEATURE = (
    "2026-03-10T16:20:00+05:30",
    CHEN,
    "WIP: discount codes",
    {"discounts.py": "CODES = {'WELCOME10': 0.10}\n"},
)  # fmt: skip
UNCOMMITTED = {"README.md": README + "\nTODO: document the discounts API.\n"}


def main(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,  # ignore the user's ~/.gitconfig (signing, hooks, ...)
        "GIT_CONFIG_NOSYSTEM": "1",
    }

    def git(*args: str, extra: dict[str, str] | None = None) -> None:
        subprocess.run(["git", *args], cwd=root, env={**env, **(extra or {})}, check=True,
                       capture_output=True, text=True)  # fmt: skip

    def commit(date: str, author: tuple[str, str], message: str, files: dict[str, str]) -> None:
        write(files)
        git("add", "-A")
        name, email = author
        git("commit", "-q", "-m", message, extra={
            "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": date,
        })  # fmt: skip

    def write(files: dict[str, str]) -> None:
        for path, content in files.items():
            (root / path).write_text(content, encoding="utf-8")

    git("init", "-q", "-b", "main")
    for entry in MAIN:
        commit(*entry)
    git("checkout", "-q", "-b", "feature/discounts")
    commit(*FEATURE)
    git("checkout", "-q", "main")
    write(UNCOMMITTED)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: build_repo.py <directory>")
    main(Path(sys.argv[1]))
