"""`agentgrade init`: the example suites are copied with their fixtures and still load."""

from pathlib import Path

import pytest

from agentgrade import __version__
from agentgrade.cli import main
from agentgrade.examples import EXAMPLE_SUITES, copy_examples, examples_root
from agentgrade.suite import load_suite


def test_examples_resolve_from_a_source_checkout():
    root = examples_root()
    assert (root / "suites" / "shop.yaml").is_file()


def test_init_copies_loadable_suites(tmp_path: Path, capsys):
    dest = tmp_path / "evals"
    assert main(["init", str(dest)]) == 0
    assert "agentgrade run suites/shop.yaml" in capsys.readouterr().out
    assert sorted(p.name for p in (dest / "suites").iterdir()) == sorted(EXAMPLE_SUITES)
    shop = load_suite(dest / "suites" / "shop.yaml")
    assert shop.server.fixture == (dest / "fixtures" / "shop").resolve()
    git = load_suite(dest / "suites" / "git.yaml")
    build_repo = Path(git.server.setup[0][1]).resolve()
    assert build_repo == (dest / "fixtures" / "git_repo" / "build_repo.py").resolve()
    assert build_repo.is_file()
    assert (dest / "model_configs" / "groq-gpt-oss-120b.yaml").is_file()
    assert not list(dest.rglob("__pycache__"))


def test_init_refuses_a_non_empty_folder(tmp_path: Path):
    (tmp_path / "x").write_text("mine")
    with pytest.raises(FileExistsError):
        copy_examples(tmp_path)
    assert main(["init", str(tmp_path)]) == 2


def test_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.strip() == f"agentgrade {__version__}"
