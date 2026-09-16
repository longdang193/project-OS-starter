"""Project OS content eligibility policy for review artifacts."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import Any, Iterable


PROTECTED_PATTERNS = (".env", ".env.*", "*.private.*", "*.local.*")
REQUIRED_ENTRIES = PROTECTED_PATTERNS


def _validate_path(path: object) -> str:
    if not isinstance(path, str) or not path or "\x00" in path or "\\" in path:
        raise ValueError(f"unsafe path: {path!r}")
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError(f"unsafe path: {path!r}")
    return path


def protected_path_reason(path: str) -> str | None:
    path = _validate_path(path)
    basename = PurePosixPath(path).name
    return next((pattern for pattern in PROTECTED_PATTERNS if fnmatchcase(basename, pattern)), None)


def is_protected_path(path: str) -> bool:
    return protected_path_reason(path) is not None


def classify_inventory(inventory: Iterable[Any]) -> dict[str, Any]:
    protected_paths: list[str] = []
    protected_review_paths: list[str] = []
    ordinary_paths: list[str] = []
    protected_entries: list[dict[str, Any]] = []
    for entry in inventory:
        if isinstance(entry, dict):
            status = entry.get("status")
            old_path = entry.get("old_path")
            new_path = entry.get("new_path")
            values = {"status": status, "old_path": old_path, "new_path": new_path}
        else:
            status = getattr(entry, "status", None)
            old_path = getattr(entry, "old_path", None)
            new_path = getattr(entry, "new_path", None)
            values = {"status": status, "old_path": old_path, "new_path": new_path}
        paths = tuple(path for path in (old_path, new_path) if path is not None)
        reasons = {path: protected_path_reason(path) for path in paths}
        protected = any(reason is not None for reason in reasons.values())
        if protected:
            protected_paths.extend(path for path in paths if path not in protected_paths)
            review_path = old_path if str(status).upper() == "D" else new_path
            if review_path is not None and review_path not in protected_review_paths:
                protected_review_paths.append(review_path)
            protected_entries.append(
                {
                    **values,
                    "protected_paths": tuple(path for path, reason in reasons.items() if reason is not None),
                    "reasons": {path: reason for path, reason in reasons.items() if reason is not None},
                }
            )
        else:
            ordinary_paths.extend(path for path in paths if path not in ordinary_paths)
    return {
        "protected_paths": tuple(protected_paths),
        "protected_review_paths": tuple(protected_review_paths),
        "ordinary_paths": tuple(ordinary_paths),
        "protected_entries": tuple(protected_entries),
    }
