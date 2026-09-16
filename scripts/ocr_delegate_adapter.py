"""Optional OpenCodeReview delegation for immutable Git ranges."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Literal, Sequence

try:
    from owned_process import OwnedProcessResult, run_owned_process
except ModuleNotFoundError:
    from scripts.owned_process import OwnedProcessResult, run_owned_process
try:
    from review_content_policy import classify_inventory
except ModuleNotFoundError:
    from scripts.review_content_policy import classify_inventory

SUPPORTED_DELEGATE_SCHEMA = "1"
MAX_RULE_ARGUMENT_LENGTH = 24_000
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SAFE_STATUSES = {"A", "C", "D", "M", "R", "T", "U", "X", "added", "copied", "deleted", "modified", "renamed", "type_changed", "unmerged", "unknown"}

_GIT_RUN = subprocess.run


class ContractError(ValueError):
    """Invalid Project OS input; never converted to OCR fallback."""


class OcrPayloadError(ValueError):
    """Invalid or unsupported OCR output."""


@dataclass(frozen=True)
class GitInventoryEntry:
    status: str
    old_path: str | None = None
    new_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, str) or (self.status not in _SAFE_STATUSES and self.status.upper() not in _SAFE_STATUSES):
            raise ContractError(f"unsupported inventory status: {self.status!r}")
        for name in ("old_path", "new_path"):
            value = getattr(self, name)
            if value is not None:
                _validate_path(value, f"inventory {name}")
        status = self.status.lower()
        status_code = self.status.upper()
        if status == "deleted" or status_code == "D":
            if not self.old_path or self.new_path is not None:
                raise ContractError("deleted inventory entry requires old_path only")
        elif status == "renamed" or status_code == "R":
            if not self.old_path or not self.new_path:
                raise ContractError("renamed inventory entry requires old_path and new_path")
        elif status == "copied" or status_code == "C":
            if not self.old_path or not self.new_path:
                raise ContractError("copied inventory entry requires old_path and new_path")
        elif self.old_path is not None:
            raise ContractError("inventory old_path is valid only for deleted, renamed, or copied entries")
        elif not self.new_path:
            raise ContractError("inventory entry requires new_path")

    @property
    def review_path(self) -> str:
        return self.old_path if self.status.upper() == "D" or self.status.lower() == "deleted" else self.new_path  # type: ignore[return-value]

    def as_dict(self) -> dict[str, str | None]:
        return {"status": self.status, "old_path": self.old_path, "new_path": self.new_path}


@dataclass(frozen=True)
class ReviewRange:
    repo: Path
    base_sha: str
    head_sha: str
    inventory: tuple[GitInventoryEntry, ...] | Sequence[GitInventoryEntry] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "repo", Path(self.repo).expanduser().resolve())
        object.__setattr__(self, "base_sha", self.base_sha.lower() if isinstance(self.base_sha, str) else self.base_sha)
        object.__setattr__(self, "head_sha", self.head_sha.lower() if isinstance(self.head_sha, str) else self.head_sha)
        if self.inventory is not None:
            object.__setattr__(self, "inventory", tuple(self.inventory))


@dataclass(frozen=True)
class PreparationResult:
    status: Literal["prepared", "fallback", "BLOCKED"]
    reason: str | None = None
    inventory: tuple[GitInventoryEntry, ...] = ()
    reviewable_paths: tuple[str, ...] = ()
    excluded_paths: tuple[str, ...] = ()
    protected_paths: tuple[str, ...] = ()
    protected_entries: tuple[dict[str, Any], ...] = ()
    exclusion_metadata: tuple[dict[str, Any], ...] = ()
    rules: tuple[dict[str, Any], ...] = ()
    advisory_hints: tuple[dict[str, Any], ...] = ()
    observed_version: str | None = None
    schema_versions: tuple[str, ...] = ()
    executable: str | None = None
    scope_identity: dict[str, Any] = field(default_factory=dict)
    payload_digests: dict[str, str] = field(default_factory=dict)

    @classmethod
    def fallback(
        cls,
        reason: str,
        *,
        inventory: Iterable[GitInventoryEntry] = (),
        scope_identity: dict[str, Any] | None = None,
        protected_paths: Iterable[str] = (),
        protected_entries: Iterable[dict[str, Any]] = (),
        exclusion_metadata: Iterable[dict[str, Any]] = (),
        executable: str | None = None,
        observed_version: str | None = None,
    ) -> "PreparationResult":
        return cls(
            status="fallback",
            reason=reason,
            inventory=tuple(inventory),
            executable=executable,
            observed_version=observed_version,
            scope_identity=scope_identity or {},
            protected_paths=tuple(protected_paths),
            protected_entries=tuple(protected_entries),
            exclusion_metadata=tuple(exclusion_metadata),
        )

    @classmethod
    def blocked(
        cls,
        reason: str,
        *,
        inventory: Iterable[GitInventoryEntry],
        scope_identity: dict[str, Any],
        protected_paths: Iterable[str] = (),
        protected_entries: Iterable[dict[str, Any]] = (),
        exclusion_metadata: Iterable[dict[str, Any]] = (),
        executable: str | None = None,
        observed_version: str | None = None,
    ) -> "PreparationResult":
        return cls(
            status="BLOCKED",
            reason=reason,
            inventory=tuple(inventory),
            executable=executable,
            observed_version=observed_version,
            scope_identity=scope_identity,
            protected_paths=tuple(protected_paths),
            protected_entries=tuple(protected_entries),
            exclusion_metadata=tuple(exclusion_metadata),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "inventory": [entry.as_dict() for entry in self.inventory],
            "reviewable_paths": list(self.reviewable_paths),
            "excluded_paths": list(self.excluded_paths),
            "protected_paths": list(self.protected_paths),
            "protected_entries": list(self.protected_entries),
            "exclusion_metadata": list(self.exclusion_metadata),
            "rules": list(self.rules),
            "advisory_hints": list(self.advisory_hints),
            "observed_version": self.observed_version,
            "schema_versions": list(self.schema_versions),
            "executable": self.executable,
            "scope_identity": self.scope_identity,
            "payload_digests": self.payload_digests,
        }


def _validate_path(value: object, label: str = "path") -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise ContractError(f"unsafe {label}: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", value) or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(f"unsafe {label}: {value!r}")
    return value


def inventory_digest(inventory: Iterable[GitInventoryEntry]) -> str:
    payload = [entry.as_dict() for entry in inventory]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_result(
    review_range: ReviewRange,
    deadline: float,
    *args: str,
) -> subprocess.CompletedProcess[bytes]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ContractError("Git validation timed out")
    try:
        result = _GIT_RUN(
            ["git", "-C", str(review_range.repo), *args],
            capture_output=True,
            text=False,
            check=False,
            timeout=remaining,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError("Git validation failed") from exc
    if result.returncode:
        raise ContractError("Git validation failed")
    return result


def _git_stdout(result: subprocess.CompletedProcess[bytes], label: str) -> bytes:
    value = result.stdout
    if isinstance(value, str):
        try:
            return value.encode("utf-8")
        except UnicodeError as exc:
            raise ContractError(f"invalid Git {label}") from exc
    if not isinstance(value, bytes):
        raise ContractError(f"invalid Git {label}")
    if len(value) > MAX_OUTPUT_BYTES:
        raise ContractError(f"Git {label} output too large")
    return value


def derive_inventory(review_range: ReviewRange, deadline: float | None = None) -> tuple[GitInventoryEntry, ...]:
    deadline = deadline if deadline is not None else time.monotonic() + 60
    result = _git_result(
        review_range,
        deadline,
        "diff",
        "--name-status",
        "-z",
        "--find-renames",
        "--find-copies",
        "--find-copies-harder",
        review_range.base_sha,
        review_range.head_sha,
        "--",
    )
    fields = _git_stdout(result, "inventory").split(b"\0")
    entries: list[GitInventoryEntry] = []
    index = 0
    while index < len(fields) and fields[index] == b"":
        index += 1
    while index < len(fields):
        status_field = fields[index]
        index += 1
        if not status_field:
            continue
        try:
            status_text = status_field.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ContractError("invalid Git inventory status") from exc
        status = status_text[0]
        if status in {"R", "C"}:
            if index + 1 >= len(fields):
                raise ContractError("incomplete Git rename/copy inventory")
            try:
                old_path = fields[index].decode("utf-8")
                new_path = fields[index + 1].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ContractError("invalid UTF-8 in Git inventory") from exc
            index += 2
            entries.append(GitInventoryEntry(status, old_path, new_path))
        else:
            if index >= len(fields):
                raise ContractError("incomplete Git inventory")
            try:
                new_path = fields[index].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ContractError("invalid UTF-8 in Git inventory") from exc
            index += 1
            entries.append(GitInventoryEntry(status, new_path=new_path) if status != "D" else GitInventoryEntry(status, old_path=new_path))
    seen: set[str] = set()
    for entry in entries:
        if entry.review_path in seen:
            raise ContractError(f"duplicate inventory path: {entry.review_path}")
        seen.add(entry.review_path)
    return tuple(entries)


def _scope_identity(review_range: ReviewRange) -> dict[str, Any]:
    return {
        "repo": str(review_range.repo),
        "base_sha": review_range.base_sha,
        "head_sha": review_range.head_sha,
        "inventory_sha256": inventory_digest(review_range.inventory),
    }


def validate_preparation_identity(preparation: object, review_range: ReviewRange) -> dict[str, Any]:
    if not isinstance(preparation, dict):
        raise ContractError("preparation manifest must be an object")
    if preparation.get("status") not in {"prepared", "fallback", "BLOCKED"}:
        raise ContractError("invalid preparation status")
    identity = preparation.get("scope_identity")
    if not isinstance(identity, dict):
        raise ContractError("preparation identity is missing")
    expected = _scope_identity(review_range)
    for key in ("base_sha", "head_sha", "inventory_sha256"):
        if identity.get(key) != expected[key]:
            raise ContractError(f"preparation identity mismatch: {key}")
    if preparation.get("status") != "prepared" and preparation.get("advisory_hints"):
        raise ContractError("hints require prepared status")
    return preparation


def validate_input(review_range: ReviewRange, *, deadline: float | None = None) -> ReviewRange:
    if not isinstance(review_range, ReviewRange):
        raise ContractError("review range must be ReviewRange")
    if not review_range.repo.is_dir():
        raise ContractError(f"repository does not exist: {review_range.repo}")
    for name, value in (("base_sha", review_range.base_sha), ("head_sha", review_range.head_sha)):
        if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
            raise ContractError(f"{name} must be a full 40-character commit SHA")
    caller_inventory = review_range.inventory
    seen: set[str] = set()
    for entry in caller_inventory or ():
        if not isinstance(entry, GitInventoryEntry):
            raise ContractError("inventory entries must be GitInventoryEntry")
        path = entry.review_path
        if path in seen:
            raise ContractError(f"duplicate inventory path: {path}")
        seen.add(path)

    deadline = deadline if deadline is not None else time.monotonic() + 60

    for name, value in (("base_sha", review_range.base_sha), ("head_sha", review_range.head_sha)):
        result = _git_result(review_range, deadline, "rev-parse", "--verify", f"{value}^{{commit}}")
        if _git_stdout(result, name).strip().lower() != value.encode("ascii"):
            raise ContractError(f"invalid {name}: {value}")
    try:
        _git_result(review_range, deadline, "merge-base", "--is-ancestor", review_range.base_sha, review_range.head_sha)
    except ContractError as exc:
        raise ContractError("base_sha is not an ancestor of head_sha") from exc
    merge_base = _git_result(review_range, deadline, "merge-base", review_range.base_sha, review_range.head_sha)
    if _git_stdout(merge_base, "merge-base").strip().lower() != review_range.base_sha.encode("ascii"):
        raise ContractError("merge-base does not equal base_sha")
    canonical = derive_inventory(review_range, deadline)
    if caller_inventory is not None and seen != {entry.review_path for entry in canonical}:
        raise ContractError("caller inventory must equal complete Git-derived review paths")
    return ReviewRange(review_range.repo, review_range.base_sha, review_range.head_sha, canonical)


def _canonical_digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def _strict_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OcrPayloadError(f"invalid {label}")
    return value


def reconcile_preview(payload: object, review_range: ReviewRange) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != SUPPORTED_DELEGATE_SCHEMA:
        raise OcrPayloadError("unsupported_schema")
    if not isinstance(payload.get("repository"), str) or Path(payload["repository"]).resolve() != review_range.repo:
        raise OcrPayloadError("preview_scope_mismatch")
    if payload.get("mode") != "range" or payload.get("from") != review_range.base_sha or payload.get("to") != review_range.head_sha:
        raise OcrPayloadError("preview_scope_mismatch")
    if payload.get("merge_base") != review_range.base_sha:
        raise OcrPayloadError("preview_merge_base_mismatch")
    reviewable = payload.get("reviewable_files")
    excluded = payload.get("excluded_files")
    if not isinstance(reviewable, list) or not isinstance(excluded, list):
        raise OcrPayloadError("malformed_json")
    expected = [entry.review_path for entry in review_range.inventory]
    expected_set = set(expected)
    partitions: list[tuple[str, list[dict[str, Any]]]] = [("reviewable", reviewable), ("excluded", excluded)]
    paths: list[str] = []
    normalized: dict[str, list[dict[str, Any]]] = {"reviewable": [], "excluded": []}
    for partition, entries in partitions:
        for entry in entries:
            if not isinstance(entry, dict):
                raise OcrPayloadError("malformed_json")
            path = _safe_ocr_path(entry.get("path"))
            status = entry.get("status")
            if not isinstance(status, str) or not status:
                raise OcrPayloadError("malformed_json")
            _strict_int(entry.get("insertions"), "insertions")
            _strict_int(entry.get("deletions"), "deletions")
            if path in paths or path not in expected_set:
                raise OcrPayloadError("preview_inventory_mismatch")
            paths.append(path)
            normalized[partition].append({"path": path, "status": status, "insertions": entry["insertions"], "deletions": entry["deletions"], "exclude_reason": entry.get("exclude_reason")})
    counts = {
        "total_files": _strict_int(payload.get("total_files"), "total_files"),
        "reviewable_count": _strict_int(payload.get("reviewable_count"), "reviewable_count"),
        "excluded_count": _strict_int(payload.get("excluded_count"), "excluded_count"),
    }
    total_insertions = _strict_int(payload.get("total_insertions"), "total_insertions")
    total_deletions = _strict_int(payload.get("total_deletions"), "total_deletions")
    insertion_sum = sum(item["insertions"] for item in normalized["reviewable"] + normalized["excluded"])
    deletion_sum = sum(item["deletions"] for item in normalized["reviewable"] + normalized["excluded"])
    if counts != {"total_files": len(expected), "reviewable_count": len(reviewable), "excluded_count": len(excluded)} or set(paths) != expected_set or (total_insertions, total_deletions) != (insertion_sum, deletion_sum):
        raise OcrPayloadError("preview_count_mismatch")
    return {"reviewable": tuple(item["path"] for item in normalized["reviewable"]), "excluded": tuple(item["path"] for item in normalized["excluded"]), "files": normalized}


def _safe_ocr_path(value: object) -> str:
    try:
        return _validate_path(value, "OCR path")
    except ContractError as exc:
        raise OcrPayloadError("unsafe_path") from exc


def normalize_rules(payloads: Iterable[object], reviewable_paths: Iterable[str]) -> tuple[dict[str, Any], ...]:
    expected = set(reviewable_paths)
    seen: set[str] = set()
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    for payload in payloads:
        if not isinstance(payload, dict) or payload.get("schema_version") != SUPPORTED_DELEGATE_SCHEMA or not isinstance(payload.get("groups"), list):
            raise OcrPayloadError("unsupported_schema")
        for group in payload["groups"]:
            if not isinstance(group, dict) or isinstance(group.get("group_id"), bool) or not isinstance(group.get("group_id"), int) or group["group_id"] < 0:
                raise OcrPayloadError("malformed_json")
            source, pattern, rule, files = (group.get(name) for name in ("source", "pattern", "rule", "files"))
            if not all(isinstance(value, str) for value in (source, pattern, rule)) or not isinstance(files, list) or not files:
                raise OcrPayloadError("malformed_json")
            clean_files = []
            for path in files:
                path = _safe_ocr_path(path)
                if path not in expected or path in seen:
                    raise OcrPayloadError("rule_inventory_mismatch")
                seen.add(path)
                clean_files.append(path)
            key = (source, pattern, rule)
            target = merged.setdefault(key, {"group_id": group["group_id"], "source": source, "pattern": pattern, "rule": rule, "files": []})
            target["group_id"] = min(target["group_id"], group["group_id"])
            target["files"].extend(clean_files)
    if seen != expected:
        raise OcrPayloadError("rule_count_mismatch")
    return tuple({**group, "files": sorted(group["files"])} for group in sorted(merged.values(), key=lambda item: (item["source"], item["pattern"], item["rule"])))


def _policy_metadata(inventory: Iterable[GitInventoryEntry]) -> dict[str, Any]:
    policy = classify_inventory(inventory)
    return {
        "protected_paths": tuple(policy["protected_paths"]),
        "protected_review_paths": tuple(policy["protected_review_paths"]),
        "protected_entries": tuple(policy["protected_entries"]),
    }


def _ocr_exclusion_metadata(reconciled: dict[str, Any], protected_paths: set[str]) -> tuple[dict[str, Any], ...]:
    metadata: list[dict[str, Any]] = []
    for partition in ("reviewable", "excluded"):
        for entry in reconciled["files"][partition]:
            if entry["path"] in protected_paths or partition == "excluded":
                metadata.append(dict(entry, partition=partition))
    return tuple(metadata)


class OcrDelegateAdapter:
    def __init__(self, *, timeout_seconds: float = 60.0, max_output_bytes: int = MAX_OUTPUT_BYTES, max_rule_argument_length: int = MAX_RULE_ARGUMENT_LENGTH) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes
        self.max_rule_argument_length = max_rule_argument_length

    def prepare(self, review_range: ReviewRange) -> PreparationResult:
        deadline = time.monotonic() + self.timeout_seconds
        review_range = validate_input(review_range, deadline=deadline)
        identity = _scope_identity(review_range)
        policy = _policy_metadata(review_range.inventory)
        protected_paths = set(policy["protected_paths"])
        protected_review_paths = set(policy["protected_review_paths"])
        executable = shutil.which("ocr")
        if not executable:
            return PreparationResult.fallback("executable_missing", inventory=review_range.inventory, scope_identity=identity, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
        executable = str(Path(executable).resolve())
        env = dict(os.environ)
        env["OCR_NO_UPDATE"] = "1"
        version, reason = self._run_jsonless([executable, "--version"], review_range.repo, env, deadline)
        if reason:
            if reason == "BLOCKED":
                return PreparationResult.blocked(reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
            return PreparationResult.fallback("version_probe_failed" if reason == "command_failed" else reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
        observed_version = _parse_version(version)
        if observed_version is None:
            return PreparationResult.fallback("version_probe_failed", inventory=review_range.inventory, scope_identity=identity, executable=executable, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
        preview, reason = self._run_json([executable, "delegate", "preview", "--repo", str(review_range.repo), "--from", review_range.base_sha, "--to", review_range.head_sha, "--format", "json"], review_range.repo, env, deadline)
        if reason:
            if reason == "BLOCKED":
                return PreparationResult.blocked(reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
            return PreparationResult.fallback(reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
        try:
            reconciled = reconcile_preview(preview, review_range)
        except OcrPayloadError as exc:
            return PreparationResult.fallback(str(exc), inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"])
        exclusion_metadata = _ocr_exclusion_metadata(reconciled, protected_paths)
        reviewable_paths = tuple(path for path in reconciled["reviewable"] if path not in protected_review_paths)
        excluded_paths = tuple(path for path in reconciled["excluded"] if path not in protected_review_paths)
        rules_payloads: list[object] = []
        for batch in self._rule_batches(reviewable_paths):
            command = [executable, "delegate", "rule", "--repo", str(review_range.repo), "--from", review_range.base_sha, "--to", review_range.head_sha, "--format", "json", "--", *batch]
            payload, reason = self._run_json(command, review_range.repo, env, deadline)
            if reason:
                if reason == "BLOCKED":
                    return PreparationResult.blocked(reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"], exclusion_metadata=exclusion_metadata)
                return PreparationResult.fallback(reason, inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"], exclusion_metadata=exclusion_metadata)
            rules_payloads.append(payload)
        try:
            rules = normalize_rules(rules_payloads, reviewable_paths)
        except OcrPayloadError as exc:
            return PreparationResult.fallback(str(exc), inventory=review_range.inventory, scope_identity=identity, executable=executable, observed_version=observed_version, protected_paths=policy["protected_paths"], protected_entries=policy["protected_entries"], exclusion_metadata=exclusion_metadata)
        return PreparationResult(status="prepared", inventory=review_range.inventory, reviewable_paths=reviewable_paths, excluded_paths=excluded_paths, protected_paths=tuple(sorted(protected_paths)), protected_entries=policy["protected_entries"], exclusion_metadata=exclusion_metadata, rules=rules, advisory_hints=tuple(rule for rule in rules if rule["source"] == "system"), observed_version=observed_version, schema_versions=(SUPPORTED_DELEGATE_SCHEMA,), executable=executable, scope_identity=identity, payload_digests={"preview": _canonical_digest(preview), "rules": _canonical_digest(rules_payloads)})

    def _run_jsonless(self, command: list[str], cwd: Path, env: dict[str, str], deadline: float) -> tuple[str | None, str | None]:
        result = self._run(command, cwd, env, deadline)
        reason = self._run_reason(result)
        if reason:
            return None, reason
        try:
            return (result.stdout + result.stderr).decode("utf-8"), None
        except UnicodeDecodeError:
            return None, "invalid_utf8"

    def _run_json(self, command: list[str], cwd: Path, env: dict[str, str], deadline: float) -> tuple[object | None, str | None]:
        result = self._run(command, cwd, env, deadline)
        reason = self._run_reason(result)
        if reason:
            return None, reason
        try:
            payload = json.loads(result.stdout.decode("utf-8"))
        except UnicodeDecodeError:
            return None, "invalid_utf8"
        except json.JSONDecodeError:
            return None, "malformed_json"
        if not isinstance(payload, dict):
            return None, "non_object_json"
        return payload, None

    def _run(self, command: list[str], cwd: Path, env: dict[str, str], deadline: float) -> OwnedProcessResult:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return OwnedProcessResult("timeout")
        return run_owned_process(command, cwd=cwd, env=env, timeout=remaining, max_output_bytes=self.max_output_bytes)

    @staticmethod
    def _run_reason(result: OwnedProcessResult) -> str | None:
        if result.status == "success":
            return None
        if result.status == "BLOCKED":
            return "BLOCKED"
        return {
            "timeout": "timeout",
            "output_limit": "output_too_large",
            "nonzero_exit": "command_failed",
            "command_failed": "command_failed",
            "spawn_failed": "command_failed",
        }[result.status]

    def _rule_batches(self, paths: Iterable[str]) -> tuple[tuple[str, ...], ...]:
        batches: list[tuple[str, ...]] = []
        current: list[str] = []
        size = 0
        for path in sorted(paths):
            cost = len(path) + 1
            if cost > self.max_rule_argument_length:
                raise ContractError("rule path exceeds argument limit")
            if current and size + cost > self.max_rule_argument_length:
                batches.append(tuple(current))
                current, size = [], 0
            current.append(path)
            size += cost
        if current:
            batches.append(tuple(current))
        return tuple(batches)


def _parse_version(output: str) -> str | None:
    match = re.search(r"(\d+\.\d+\.\d+)", output)
    return match.group(1) if match else None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--inventory", default="-", help="JSON file, or - for stdin")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.inventory == "-" else Path(args.inventory).read_text(encoding="utf-8")
        decoded = json.loads(raw)
        if not isinstance(decoded, list):
            raise ContractError("inventory JSON must be a list")
        entries = tuple(GitInventoryEntry(**item) for item in decoded)
        result = OcrDelegateAdapter().prepare(ReviewRange(Path(args.repo), args.base_sha, args.head_sha, entries))
    except (ContractError, OSError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "contract_error", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
