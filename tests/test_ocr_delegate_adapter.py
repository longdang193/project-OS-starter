from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import ocr_delegate_adapter as adapter


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def _repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "old.txt").write_text("old\n", encoding="utf-8")
    _git(repo, "add", "old.txt")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "old.txt").rename(repo / "new.txt")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "head")
    return repo, base, _git(repo, "rev-parse", "HEAD")


def _range(repo: Path, base: str, head: str, *entries: adapter.GitInventoryEntry) -> adapter.ReviewRange:
    return adapter.ReviewRange(repo, base, head, entries or (adapter.GitInventoryEntry("R", "old.txt", "new.txt"),))


def _preview(review: adapter.ReviewRange, *, schema: str = "1", reviewable: list[str] | None = None, excluded: list[str] | None = None) -> dict:
    reviewable = reviewable if reviewable is not None else [entry.review_path for entry in review.inventory]
    excluded = excluded if excluded is not None else []
    file_entry = lambda path: {"path": path, "status": "modified", "insertions": 1, "deletions": 0}
    return {"schema_version": schema, "mode": "range", "repository": str(review.repo), "from": review.base_sha, "to": review.head_sha, "merge_base": review.base_sha, "total_files": len(reviewable) + len(excluded), "reviewable_count": len(reviewable), "excluded_count": len(excluded), "total_insertions": 1, "total_deletions": 0, "reviewable_files": [file_entry(path) for path in reviewable], "excluded_files": [file_entry(path) for path in excluded]}


def _mock_ocr(monkeypatch: pytest.MonkeyPatch, preview: dict, rules: dict | None = None, *, version: str = "OpenCodeReview v1.12.4", returncode: int = 0, preview_returncode: int | None = None):
    calls: list[tuple[list[str], dict]] = []
    rules = rules or {"schema_version": "1", "groups": [{"group_id": 1, "source": "root", "pattern": "*.txt", "files": ["new.txt"], "rule": "check"}]}

    class Completed:
        def __init__(self, stdout: str, code: int = 0):
            self.stdout, self.stderr, self.returncode = stdout, "", code

    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[-1] == "--version":
            return Completed(version, returncode)
        if "preview" in command:
            return Completed(json.dumps(preview), returncode if preview_returncode is None else preview_returncode)
        return Completed(json.dumps(rules), returncode)

    monkeypatch.setattr(adapter.shutil, "which", lambda _: "/usr/bin/ocr")
    monkeypatch.setattr(adapter.subprocess, "run", run)
    return calls


def test_prepared_uses_inventory_and_safe_rule_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    calls = _mock_ocr(monkeypatch, _preview(review))
    result = adapter.OcrDelegateAdapter().prepare(review)
    assert result.status == "prepared"
    assert result.reviewable_paths == ("new.txt",)
    assert result.inventory[0].old_path == "old.txt"
    assert calls[-1][0][-2] == "--"
    assert calls[-1][0][-1] == "new.txt"
    assert all(call[1]["env"]["OCR_NO_UPDATE"] == "1" for call in calls)
    assert calls[1][0][2:] == ["preview", "--repo", str(repo), "--from", base, "--to", head, "--format", "json"]


def test_lowercase_deletion_uses_old_path_for_review() -> None:
    entry = adapter.GitInventoryEntry("d", old_path="old.txt")

    assert entry.review_path == "old.txt"


@pytest.mark.parametrize("case", ["missing", "nonancestor", "mergebase", "unsafe", "duplicate", "inconsistent"])
def test_invalid_project_input_is_contract_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    repo, base, head = _repo(tmp_path)
    if case == "missing":
        review = _range(repo, "0" * 40, head)
    elif case == "nonancestor":
        review = _range(repo, head, base)
    elif case == "mergebase":
        review = _range(repo, base, head)
        monkeypatch.setattr(adapter, "_GIT_RUN", lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "f" * 40 + "\n", ""))
    elif case == "unsafe":
        review = adapter.ReviewRange(repo, base, head, (object(),))  # type: ignore[arg-type]
    elif case == "duplicate":
        review = adapter.ReviewRange(repo, base, head, (adapter.GitInventoryEntry("M", new_path="new.txt"), adapter.GitInventoryEntry("A", new_path="new.txt")))
    else:
        with pytest.raises(adapter.ContractError):
            adapter.GitInventoryEntry("D", old_path="old.txt", new_path="new.txt")
        return
    with pytest.raises(adapter.ContractError):
        adapter.validate_input(review)


@pytest.mark.parametrize("reason", ["executable_missing", "version_probe_failed", "command_failed", "timeout", "malformed_json", "unsupported_schema", "unsafe_path", "preview_count_mismatch"])
def test_ocr_failures_return_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    if reason == "executable_missing":
        monkeypatch.setattr(adapter.shutil, "which", lambda _: None)
    elif reason == "version_probe_failed":
        _mock_ocr(monkeypatch, _preview(review), version="unknown")
    elif reason == "timeout":
        monkeypatch.setattr(adapter.shutil, "which", lambda _: "/usr/bin/ocr")
        def run(*args, **kwargs):
            raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
        monkeypatch.setattr(adapter.subprocess, "run", run)
    else:
        preview = _preview(review, schema="9" if reason == "unsupported_schema" else "1")
        if reason == "command_failed":
            _mock_ocr(monkeypatch, preview, preview_returncode=1)
        elif reason == "malformed_json":
            monkeypatch.setattr(adapter.shutil, "which", lambda _: "/usr/bin/ocr")
            def run(*args, **kwargs):
                if args[0][-1] == "--version":
                    return subprocess.CompletedProcess(args[0], 0, "OpenCodeReview v1.12.4", "")
                return subprocess.CompletedProcess(args[0], 0, "{", "")
            monkeypatch.setattr(adapter.subprocess, "run", run)
        elif reason == "unsafe_path":
            preview["reviewable_files"][0]["path"] = "../bad"
            _mock_ocr(monkeypatch, preview)
        elif reason == "preview_count_mismatch":
            preview["total_files"] = 99
            _mock_ocr(monkeypatch, preview)
        else:
            _mock_ocr(monkeypatch, preview)
    result = adapter.OcrDelegateAdapter().prepare(review)
    assert result.status == "fallback"
    assert result.reason == reason
    assert not result.inventory


def test_rule_batches_are_bounded_and_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = adapter.ReviewRange(repo, base, head, tuple(adapter.GitInventoryEntry("M", new_path=f"file-{i}.txt") for i in range(4)))
    obj = adapter.OcrDelegateAdapter(max_rule_argument_length=14)
    batches = obj._rule_batches([entry.review_path for entry in review.inventory])
    assert batches == (("file-0.txt",), ("file-1.txt",), ("file-2.txt",), ("file-3.txt",))


def test_normalize_rules_merges_groups_and_requires_coverage() -> None:
    payload = {"schema_version": "1", "groups": [{"group_id": 2, "source": "b", "pattern": "*.txt", "files": ["b.txt"], "rule": "B"}, {"group_id": 1, "source": "a", "pattern": "*.txt", "files": ["a.txt"], "rule": "A"}]}
    rules = adapter.normalize_rules([payload], ["a.txt", "b.txt"])
    assert [rule["source"] for rule in rules] == ["a", "b"]
    with pytest.raises(adapter.OcrPayloadError, match="rule_count_mismatch"):
        adapter.normalize_rules([payload], ["a.txt", "b.txt", "c.txt"])
