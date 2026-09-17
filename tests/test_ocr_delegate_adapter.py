from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import ocr_delegate_adapter as adapter


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ocr_delegate"


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
    (repo / "new.txt").write_text("old\n", encoding="utf-8")
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
            completed = Completed(version, returncode)
        elif "preview" in command:
            completed = Completed(json.dumps(preview), returncode if preview_returncode is None else preview_returncode)
        else:
            completed = Completed(json.dumps(rules), returncode)
        return adapter.OwnedProcessResult(
            "success" if completed.returncode == 0 else "command_failed",
            completed.returncode,
            completed.stdout.encode(),
            completed.stderr.encode(),
        )

    monkeypatch.setattr(adapter.shutil, "which", lambda _: "/usr/bin/ocr")
    monkeypatch.setattr(adapter, "run_owned_process", lambda command, **kwargs: run(command, **kwargs))
    return calls


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _fixture_review(tmp_path: Path) -> adapter.ReviewRange:
    repo, base, head = _repo(tmp_path)
    inventory = (
        adapter.GitInventoryEntry("A", new_path="src/app.py"),
        adapter.GitInventoryEntry("A", new_path="README.md"),
        adapter.GitInventoryEntry("M", new_path="tests/test_app.py"),
        adapter.GitInventoryEntry("D", old_path="gone.py"),
        adapter.GitInventoryEntry("R", old_path="old_name.py", new_path="renamed.py"),
        adapter.GitInventoryEntry("C", old_path="source.py", new_path="copied.py"),
        adapter.GitInventoryEntry("A", new_path="-leading-name.py"),
        adapter.GitInventoryEntry("M", new_path="notes.xyz"),
        adapter.GitInventoryEntry("M", new_path="assets/logo.bin"),
        adapter.GitInventoryEntry("M", new_path="vendor/generated.py"),
    )
    return adapter.ReviewRange(repo, base, head, inventory)


def _fixture_payloads(review: adapter.ReviewRange) -> tuple[dict, dict]:
    preview = _fixture("preview-v1.json")
    preview.update({"repository": str(review.repo), "from": review.base_sha, "to": review.head_sha, "merge_base": review.base_sha})
    return preview, _fixture("rules-v1.json")


def _fake_executable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    preview: dict,
    rules: dict,
    *,
    mode: str = "ok",
    version: str = "OpenCodeReview v1.12.4",
) -> Path:
    payload_dir = tmp_path / "fake-ocr-payloads"
    payload_dir.mkdir()
    (payload_dir / "preview.json").write_text(json.dumps(preview), encoding="utf-8")
    (payload_dir / "rules.json").write_text(json.dumps(rules), encoding="utf-8")
    log_path = tmp_path / "fake-ocr.log"
    script = tmp_path / "fake_ocr.py"
    script.write_text(
        """import json
import os
import sys
import time
from pathlib import Path

mode = os.environ["FAKE_OCR_MODE"]
payload_dir = Path(os.environ["FAKE_OCR_PAYLOAD_DIR"])
log_path = Path(os.environ["FAKE_OCR_LOG"])
args = sys.argv[1:]
with log_path.open("a", encoding="utf-8") as log:
    log.write(json.dumps({"args": args, "ocr_no_update": os.environ.get("OCR_NO_UPDATE")}) + "\\n")
if mode == "timeout":
    time.sleep(2)
if args == ["--version"]:
    print(os.environ["FAKE_OCR_VERSION"])
    raise SystemExit(0 if mode != "nonzero" else 7)
if mode == "nonzero":
    raise SystemExit(7)
if mode == "malformed":
    print("{")
    raise SystemExit(0)
if "preview" in args:
    payload = json.loads((payload_dir / "preview.json").read_text(encoding="utf-8"))
    if mode == "schema2":
        payload["schema_version"] = "2"
    if mode == "missing":
        del payload["reviewable_files"][0]["insertions"]
    print(json.dumps(payload))
    raise SystemExit(0)
if "rule" in args:
    payload = json.loads((payload_dir / "rules.json").read_text(encoding="utf-8"))
    paths = args[args.index("--") + 1:]
    groups = []
    for group in payload["groups"]:
        files = [path for path in group["files"] if path in paths]
        if files:
            group = dict(group)
            group["files"] = files
            groups.append(group)
    print(json.dumps({"schema_version": payload["schema_version"], "groups": groups}))
    raise SystemExit(0)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    if os.name == "nt":
        executable = tmp_path / "ocr.cmd"
        executable.write_text(f'@"{sys.executable}" "{script}" %*\n', encoding="utf-8")
    else:
        executable = tmp_path / "ocr"
        executable.write_text(f"#!{sys.executable}\n" + script.read_text(encoding="utf-8"), encoding="utf-8")
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(adapter.shutil, "which", lambda _: str(executable))
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: value)
    monkeypatch.setenv("FAKE_OCR_MODE", mode)
    monkeypatch.setenv("FAKE_OCR_VERSION", version)
    monkeypatch.setenv("FAKE_OCR_PAYLOAD_DIR", str(payload_dir))
    monkeypatch.setenv("FAKE_OCR_LOG", str(log_path))
    return log_path


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


def test_git_inventory_is_complete_and_nul_parsed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    caller = (
        adapter.GitInventoryEntry("R", "old.txt", "new.txt"),
        adapter.GitInventoryEntry("C", "old.txt", "copy.txt"),
        adapter.GitInventoryEntry("D", old_path="gone.txt"),
        adapter.GitInventoryEntry("A", new_path="-leading-name.txt"),
    )
    outputs = {
        "rev-parse": [base.encode() + b"\n", head.encode() + b"\n"],
        "merge-base": [b"", base.encode() + b"\n"],
        "diff": [b"R100\0old.txt\0new.txt\0C100\0old.txt\0copy.txt\0D\0gone.txt\0A\0-leading-name.txt\0"],
    }

    def run(command, **kwargs):
        key = next(item for item in ("rev-parse", "merge-base", "diff") if item in command)
        value = outputs[key].pop(0)
        return subprocess.CompletedProcess(command, 0, value, b"")

    monkeypatch.setattr(adapter, "_GIT_RUN", run)
    result = adapter.validate_input(adapter.ReviewRange(repo, base, head, caller))

    assert result.inventory == caller
    assert [entry.review_path for entry in result.inventory] == ["new.txt", "copy.txt", "gone.txt", "-leading-name.txt"]


def test_fallback_preserves_validated_identity_and_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    inventory = (adapter.GitInventoryEntry("R", "old.txt", "new.txt"),)
    review = adapter.ReviewRange(repo, base, head, inventory)
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: review)
    monkeypatch.setattr(adapter.shutil, "which", lambda _: None)

    result = adapter.OcrDelegateAdapter().prepare(review)

    assert result.status == "fallback"
    assert result.inventory == inventory
    assert result.scope_identity["base_sha"] == base
    assert result.scope_identity["head_sha"] == head
    assert result.scope_identity["inventory_sha256"] == adapter.inventory_digest(inventory)


def test_rule_invocation_carries_exact_range(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    calls = _mock_ocr(monkeypatch, _preview(review))

    assert adapter.OcrDelegateAdapter().prepare(review).status == "prepared"
    rule = calls[-1][0]
    assert rule[rule.index("--from") + 1] == base
    assert rule[rule.index("--to") + 1] == head
    assert rule[rule.index("--") + 1:] == ["new.txt"]


@pytest.mark.parametrize(
    ("stdout", "reason"),
    [(b"\xff", "invalid_utf8"), (b"null", "non_object_json"), (b"[]", "non_object_json"), (b"{", "malformed_json")],
)
def test_ocr_json_boundary_failures_are_stable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stdout: bytes, reason: str) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: review)
    monkeypatch.setattr(adapter.shutil, "which", lambda _: "ocr")

    def run(command, **kwargs):
        return adapter.OwnedProcessResult("success", 0, b"OpenCodeReview v1.2.3" if command[-1] == "--version" else stdout, b"")

    monkeypatch.setattr(adapter, "run_owned_process", run)
    result = adapter.OcrDelegateAdapter().prepare(review)

    assert result.status == "fallback"
    assert result.reason == reason


def test_ocr_cleanup_uncertainty_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: review)
    monkeypatch.setattr(adapter.shutil, "which", lambda _: "ocr")
    monkeypatch.setattr(adapter, "run_owned_process", lambda *args, **kwargs: adapter.OwnedProcessResult("BLOCKED", reason="timeout", cleanup_confirmed=False))

    result = adapter.OcrDelegateAdapter().prepare(review)

    assert result.status == "BLOCKED"
    assert result.inventory == review.inventory
    assert result.reviewable_paths == ()


def test_ocr_output_limit_falls_back_with_validated_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: review)
    monkeypatch.setattr(adapter.shutil, "which", lambda _: "ocr")
    monkeypatch.setattr(adapter, "run_owned_process", lambda *args, **kwargs: adapter.OwnedProcessResult("output_limit"))

    result = adapter.OcrDelegateAdapter().prepare(review)

    assert result.status == "fallback"
    assert result.reason == "output_too_large"
    assert result.inventory == review.inventory


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
        monkeypatch.setattr(adapter, "run_owned_process", lambda *args, **kwargs: adapter.OwnedProcessResult("timeout"))
    else:
        preview = _preview(review, schema="9" if reason == "unsupported_schema" else "1")
        if reason == "command_failed":
            _mock_ocr(monkeypatch, preview, preview_returncode=1)
        elif reason == "malformed_json":
            monkeypatch.setattr(adapter.shutil, "which", lambda _: "/usr/bin/ocr")
            def run(command, **kwargs):
                if command[-1] == "--version":
                    return adapter.OwnedProcessResult("success", 0, b"OpenCodeReview v1.12.4", b"")
                return adapter.OwnedProcessResult("success", 0, b"{", b"")
            monkeypatch.setattr(adapter, "run_owned_process", run)
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
    assert result.inventory == review.inventory


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


def test_v1_fixtures_reconcile_statuses_and_preserve_inventory_authority(tmp_path: Path) -> None:
    review = _fixture_review(tmp_path)
    preview, rules_payload = _fixture_payloads(review)

    reconciled = adapter.reconcile_preview(preview, review)
    assert reconciled["reviewable"] == ("src/app.py", "README.md", "tests/test_app.py", "gone.py", "renamed.py", "copied.py", "-leading-name.py")
    assert reconciled["excluded"] == ("notes.xyz", "assets/logo.bin", "vendor/generated.py")
    assert [entry["status"] for entry in reconciled["files"]["reviewable"]] == ["modified", "added", "modified", "deleted", "renamed", "copied", "added"]
    assert [entry["exclude_reason"] for entry in reconciled["files"]["excluded"]] == ["unsupported_extension", "binary", "excluded"]

    rules = adapter.normalize_rules([rules_payload], reconciled["reviewable"])
    assert [rule["source"] for rule in rules] == ["docs", "project"]
    assert {path for rule in rules for path in rule["files"]} == set(reconciled["reviewable"])
    assert all("additive_fixture_field" not in rule for rule in rules)
    assert {entry.review_path for entry in review.inventory} == set(reconciled["reviewable"]) | set(reconciled["excluded"])
    assert review.inventory[3].old_path == "gone.py"
    assert review.inventory[4].old_path == "old_name.py"
    assert review.inventory[4].new_path == "renamed.py"


def test_fake_executable_prepares_fixture_and_records_observed_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    review = _fixture_review(tmp_path)
    preview, rules = _fixture_payloads(review)
    log_path = _fake_executable(monkeypatch, tmp_path, preview, rules, version="OpenCodeReview v9.9.9")

    result = adapter.OcrDelegateAdapter(timeout_seconds=5).prepare(review)

    assert result.status == "prepared"
    assert result.observed_version == "9.9.9"
    assert result.schema_versions == ("1",)
    assert result.inventory == review.inventory
    assert set(result.reviewable_paths) | set(result.excluded_paths) == {entry.review_path for entry in review.inventory}
    assert set(result.reviewable_paths).isdisjoint(result.excluded_paths)
    assert result.scope_identity["inventory_sha256"] == adapter.inventory_digest(review.inventory)
    calls = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(calls) == 3
    assert all(call["ocr_no_update"] == "1" for call in calls)
    assert calls[1]["args"][:7] == ["delegate", "preview", "--repo", str(review.repo), "--from", review.base_sha, "--to"]
    assert calls[2]["args"][calls[2]["args"].index("--") + 1:] == sorted(result.reviewable_paths)


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("schema2", "unsupported_schema"),
        ("missing", "invalid insertions"),
        ("malformed", "malformed_json"),
        ("nonzero", "version_probe_failed"),
        ("timeout", "timeout"),
    ],
)
def test_fake_executable_failures_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, reason: str) -> None:
    review = _fixture_review(tmp_path)
    preview, rules = _fixture_payloads(review)
    _fake_executable(monkeypatch, tmp_path, preview, rules, mode=mode)

    timeout_seconds = 0.1 if mode == "timeout" else 5
    result = adapter.OcrDelegateAdapter(timeout_seconds=timeout_seconds).prepare(review)

    assert result.status == "fallback"
    assert result.reason == reason
    assert result.inventory == review.inventory


def test_schema_and_required_fields_rejected_before_reconciliation(tmp_path: Path) -> None:
    review = _fixture_review(tmp_path)
    preview, rules = _fixture_payloads(review)

    schema_two = copy.deepcopy(preview)
    schema_two["schema_version"] = "2"
    with pytest.raises(adapter.OcrPayloadError, match="unsupported_schema"):
        adapter.reconcile_preview(schema_two, review)

    missing_preview_field = copy.deepcopy(preview)
    del missing_preview_field["reviewable_files"][0]["status"]
    with pytest.raises(adapter.OcrPayloadError, match="malformed_json"):
        adapter.reconcile_preview(missing_preview_field, review)

    missing_rules_field = copy.deepcopy(rules)
    del missing_rules_field["groups"][0]["rule"]
    with pytest.raises(adapter.OcrPayloadError, match="malformed_json"):
        adapter.normalize_rules([missing_rules_field], [item["path"] for item in preview["reviewable_files"]])


def test_empty_ocr_reviewable_set_keeps_excluded_paths_and_prepares(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    review = _fixture_review(tmp_path)
    preview, rules = _fixture_payloads(review)
    all_paths = [entry.review_path for entry in review.inventory]
    preview["reviewable_files"] = []
    preview["excluded_files"] = [
        {"path": path, "status": "modified", "insertions": 0, "deletions": 0, "exclude_reason": "not_reviewable"}
        for path in all_paths
    ]
    preview.update({"total_files": len(all_paths), "reviewable_count": 0, "excluded_count": len(all_paths), "total_insertions": 0, "total_deletions": 0})
    _fake_executable(monkeypatch, tmp_path, preview, rules)

    result = adapter.OcrDelegateAdapter(timeout_seconds=5).prepare(review)

    assert result.status == "prepared"
    assert result.reviewable_paths == ()
    assert result.excluded_paths == tuple(all_paths)
    assert result.rules == ()
    assert result.inventory == review.inventory


def test_project_os_policy_protects_old_and_new_paths_and_keeps_rule_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo, base, head = _repo(tmp_path)
    review = adapter.ReviewRange(
        repo,
        base,
        head,
        (
            adapter.GitInventoryEntry("R", old_path="old/.env", new_path="safe.txt"),
            adapter.GitInventoryEntry("M", new_path="src/app.py"),
            adapter.GitInventoryEntry("M", new_path="src/other.py"),
        ),
    )
    preview = _preview(review, reviewable=["safe.txt", "src/app.py", "src/other.py"])
    preview["total_insertions"] = 3
    rules = {
        "schema_version": "1",
        "groups": [
            {"group_id": 1, "source": "system", "pattern": "*.py", "files": ["src/app.py"], "rule": "system hint"},
            {"group_id": 2, "source": "project", "pattern": "*.py", "files": ["src/other.py"], "rule": "branch text"},
        ],
    }
    _mock_ocr(monkeypatch, preview, rules)
    monkeypatch.setattr(adapter, "validate_input", lambda value, deadline=None: value)

    result = adapter.OcrDelegateAdapter().prepare(review)

    assert result.status == "prepared"
    assert result.reviewable_paths == ("src/app.py", "src/other.py")
    assert result.protected_paths == ("old/.env", "safe.txt")
    assert result.protected_entries[0]["old_path"] == "old/.env"
    assert result.exclusion_metadata[0]["path"] == "safe.txt"
    assert {rule["source"] for rule in result.rules} == {"project", "system"}
    assert [rule["source"] for rule in result.advisory_hints] == ["system"]


def test_preparation_identity_rejects_stale_scope_and_non_prepared_hints(tmp_path: Path) -> None:
    repo, base, head = _repo(tmp_path)
    review = _range(repo, base, head)
    manifest = {
        "status": "prepared",
        "scope_identity": adapter._scope_identity(review),
        "advisory_hints": [{"source": "system"}],
    }

    assert adapter.validate_preparation_identity(manifest, review) == manifest

    stale = copy.deepcopy(manifest)
    stale["scope_identity"]["head_sha"] = base
    with pytest.raises(adapter.ContractError, match="preparation identity mismatch"):
        adapter.validate_preparation_identity(stale, review)

    fallback = copy.deepcopy(manifest)
    fallback["status"] = "fallback"
    with pytest.raises(adapter.ContractError, match="hints require prepared status"):
        adapter.validate_preparation_identity(fallback, review)


def test_live_ocr_range_compatibility_is_opt_in(tmp_path: Path) -> None:
    if os.environ.get("PROJECT_OS_OCR_LIVE_TEST") != "1":
        pytest.skip("live OCR disabled; set PROJECT_OS_OCR_LIVE_TEST=1")
    executable = adapter.shutil.which("ocr")
    if not executable:
        pytest.fail("live OCR enabled but ocr executable not installed")

    repo = tmp_path / "live-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "src/app.py").write_text("return 1\n", encoding="utf-8")
    (repo / "tests/test_app.py").write_text("assert True\n", encoding="utf-8")
    (repo / "old_name.py").write_text("return 1\n", encoding="utf-8")
    (repo / "source.py").write_text("return 1\n", encoding="utf-8")
    (repo / "deleted.py").write_text("deleted content\n", encoding="utf-8")
    (repo / "-leading-name.py").write_text("return 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "src/app.py").write_text("return 2\n", encoding="utf-8")
    (repo / "README.md").write_text("# live\n", encoding="utf-8")
    (repo / "tests/test_app.py").write_text("assert 2 == 2\n", encoding="utf-8")
    (repo / "-leading-name.py").write_text("return 2\n", encoding="utf-8")
    (repo / "copied.py").write_text((repo / "source.py").read_text(encoding="utf-8"), encoding="utf-8")
    (repo / "deleted.py").unlink()
    (repo / "notes.xyz").write_text("unsupported\n", encoding="utf-8")
    (repo / "assets").mkdir()
    (repo / "assets/logo.bin").write_bytes(b"\x00\x01")
    _git(repo, "mv", "old_name.py", "renamed.py")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=test@example.com", "-c", "user.name=test", "commit", "-qm", "head")
    head = _git(repo, "rev-parse", "HEAD")
    review = adapter.ReviewRange(
        repo,
        base,
        head,
        None,
    )

    result = adapter.OcrDelegateAdapter(timeout_seconds=60).prepare(review)

    assert result.status == "prepared"
    assert result.observed_version
    assert result.schema_versions == ("1",)
    assert {entry.review_path for entry in result.inventory} == {"src/app.py", "README.md", "tests/test_app.py", "deleted.py", "renamed.py", "copied.py", "-leading-name.py", "notes.xyz", "assets/logo.bin"}
    assert set(result.reviewable_paths) | set(result.excluded_paths) == {entry.review_path for entry in result.inventory}
    assert {"renamed.py", "copied.py", "-leading-name.py"}.issubset(result.reviewable_paths)
    assert "deleted.py" in result.excluded_paths
    assert {"notes.xyz", "assets/logo.bin"}.issubset(result.excluded_paths)
    assert {path for rule in result.rules for path in rule["files"]} == set(result.reviewable_paths)
