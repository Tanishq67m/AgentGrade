# 0003. Python tooling

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decided by:** Tanishq (delegated: "choose what is best for the long run")

## Problem
Choose the Python version, dependency manager, test runner, linter and project layout.

## Options considered
- Dependency management: **uv** vs **venv + pip** vs Poetry.
- Python: 3.11 / **3.12** / 3.13.
- Lint/format: **ruff** vs flake8 + black + isort.
- Layout: **src/** vs flat.

## Trade-offs
- uv: one tool for Python install, venv, deps and a **lockfile** (reproducible installs); very fast; increasingly the default in new projects. One more tool to learn.
- venv + pip: familiar, but no lockfile by default → "works on my machine" drift.
- Python 3.12: mature, broadly supported by the MCP SDK and LLM libraries; 3.13 is newer with less library certainty.
- ruff: replaces flake8/black/isort with one fast tool.
- src layout: tests run against the *installed* package, which catches packaging mistakes early.

## Decision
Python **>=3.12** (pinned via `.python-version`), **uv** with committed `uv.lock`, **pytest**, **ruff** (lint + format), **src/** layout, **hatchling** build backend.

## Rationale
Reproducibility (lockfile) and low tooling overhead matter most for a long-lived public project.

## Consequences and limitations
- Contributors need uv installed.
- `uv.lock` must be committed and updated with every dependency change.
