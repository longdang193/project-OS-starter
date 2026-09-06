from __future__ import annotations

from pathlib import Path

import pytest

from scripts.project_root import resolve_repo_root


def test_explicit_repo_root_wins(tmp_path: Path) -> None:
    assert resolve_repo_root(tmp_path) == tmp_path.resolve()


def test_missing_repo_root_blocks(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="does not exist"):
        resolve_repo_root(tmp_path / "missing")


def test_git_root_resolves_from_nested_directory() -> None:
    assert resolve_repo_root() == Path(__file__).resolve().parent.parent
