"""Pure local capability normalization and evidence semantics."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

DEFAULT_LOCAL_CAPABILITIES = ("git", "py")
_LOCAL_CAPABILITY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._+-]*$")


class AttemptContractError(ValueError):
    """Raised when runtime contract values cannot be normalized."""


def normalize_local_capabilities(value: object) -> list[str]:
    if value is None:
        return []
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
        or not all(isinstance(item, str) for item in value)
    ):
        raise AttemptContractError("local_capabilities must be a sequence of strings")
    normalized = [item.lower() for item in value]
    if any(not _LOCAL_CAPABILITY_PATTERN.fullmatch(item) or ".." in item for item in normalized):
        raise AttemptContractError("local_capabilities must contain safe command basenames")
    if len(normalized) != len(set(normalized)):
        raise AttemptContractError("local_capabilities cannot contain duplicates")
    return normalized


def effective_local_capabilities(value: object) -> list[str]:
    requested = normalize_local_capabilities(value)
    return requested or list(DEFAULT_LOCAL_CAPABILITIES)


def capability_digest(value: object) -> str:
    normalized = normalize_local_capabilities(value)
    return hashlib.sha256(
        json.dumps(normalized, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def capability_evidence_matches(
    expected: Mapping[str, Any], actual: object
) -> bool:
    if not isinstance(expected, Mapping) or not isinstance(actual, Mapping):
        return False
    if not {
        "requested",
        "effective",
        "digest",
    }.issubset(expected) or "requested" not in actual or "digest" not in actual:
        return False
    if "effective" not in actual and "passed_to_worker" not in actual:
        return False
    if "passed_to_worker" in actual and "validated_available" not in actual:
        return False
    try:
        expected_requested = normalize_local_capabilities(expected.get("requested", []))
        expected_effective = normalize_local_capabilities(expected.get("effective", []))
        actual_requested = normalize_local_capabilities(actual.get("requested", []))
        actual_effective = normalize_local_capabilities(
            actual.get("effective", actual.get("passed_to_worker"))
        )
        passed_to_worker = (
            normalize_local_capabilities(actual["passed_to_worker"])
            if "passed_to_worker" in actual
            else actual_effective
        )
        validated = normalize_local_capabilities(
            actual.get("validated_available", actual_effective)
        )
    except (AttemptContractError, TypeError):
        return False
    if (
        actual_requested != expected_requested
        or actual_effective != expected_effective
        or passed_to_worker != actual_effective
        or validated != expected_effective
        or actual.get("validation_error") is not None
    ):
        return False
    if "verification_commands" in actual:
        try:
            verification_commands = normalize_local_capabilities(actual["verification_commands"])
        except AttemptContractError:
            return False
        if verification_commands != actual_effective:
            return False
    expected_digest = expected.get("digest")
    actual_digest = actual.get("digest")
    return (
        expected_digest == capability_digest(expected_effective)
        and actual_digest == capability_digest(actual_effective)
        and actual_digest == expected_digest
    )


__all__ = [
    "AttemptContractError",
    "DEFAULT_LOCAL_CAPABILITIES",
    "capability_digest",
    "capability_evidence_matches",
    "effective_local_capabilities",
    "normalize_local_capabilities",
]
