"""Shared severity contract for planning and template validators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

Severity = Literal["warning", "error"]

HISTORICAL_WARNING_CODES = {
    "planning_metadata_error",
    "planning_reference_error",
    "template_metadata_error",
    "template_selection_missing",
    "template_selection_invalid",
    "template_section_missing",
    "template_section_empty",
    "template_document_type_mismatch",
}

ALWAYS_WARNING_CODES = {
    "template_selection_legacy_missing",
    "template_selection_missing",
}

HISTORICAL_COSMETIC_CODES = {
    "template_document_type_mismatch",
}

CONSUMED_BLOCKING_CODES = {
    "planning_frontmatter_malformed",
    "planning_authority_invalid",
    "planning_dependency_invalid",
    "planning_workspace_invalid",
    "planning_proof_missing",
    "planning_integrity_error",
    "planning_security_error",
    "planning_runtime_error",
    "template_selection_invalid",
    "template_required_section_missing",
    "template_required_section_empty",
}


@dataclass(frozen=True)
class ValidationFinding:
    category: str
    path: str
    message: str
    severity: Severity = "error"

    @property
    def code(self) -> str:
        return self.category


def severity_for(
    code: str,
    *,
    status: str | None,
    selected: bool,
    consumed_by_current_work: bool,
) -> Severity:
    if code in ALWAYS_WARNING_CODES:
        return "warning"
    if code in HISTORICAL_COSMETIC_CODES and status in {"completed", "superseded"}:
        return "warning"
    if code in CONSUMED_BLOCKING_CODES:
        return "error"
    if selected or consumed_by_current_work:
        return "error"
    if status in {"completed", "superseded"} and code in HISTORICAL_WARNING_CODES:
        return "warning"
    return "error"


def reclassify(
    findings: Iterable[ValidationFinding],
    *,
    status: str | None,
    selected: bool = False,
    consumed_by_current_work: bool = False,
) -> list[ValidationFinding]:
    return [
        ValidationFinding(
            finding.category,
            finding.path,
            finding.message,
            severity_for(
                finding.code,
                status=status,
                selected=selected,
                consumed_by_current_work=consumed_by_current_work,
            ),
        )
        for finding in findings
    ]


def has_blocking_findings(findings: Iterable[ValidationFinding]) -> bool:
    return any(finding.severity == "error" for finding in findings)


__all__ = [
    "ALWAYS_WARNING_CODES",
    "CONSUMED_BLOCKING_CODES",
    "HISTORICAL_WARNING_CODES",
    "HISTORICAL_COSMETIC_CODES",
    "Severity",
    "ValidationFinding",
    "has_blocking_findings",
    "reclassify",
    "severity_for",
]
